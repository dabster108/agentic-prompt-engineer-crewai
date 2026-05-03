import asyncio
import logging
import random
from datetime import datetime, timezone
import os
import re
import json
from typing import Any, Literal
import uuid

from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from .crew import PromptAgent

try:
    from opik.integrations.crewai import track_crewai
except ImportError:
    track_crewai = None


logger = logging.getLogger("promptforge.api")


class PromptRequest(BaseModel):
    user_input: str = Field(min_length=1, max_length=2000)
    model: str = Field(default="groq/llama-3.3-70b-versatile", min_length=1, max_length=100)
    prompt_mode: Literal["prompt_engineering", "vibe_coding"] = "prompt_engineering"
    response_length: Literal["short", "balanced", "long"] = "balanced"


class PromptResponse(BaseModel):
    prompt: str
    style: str
    model: str
    prompt_mode: str
    response_length: str
    generated_at: str
    metadata: dict[str, Any] | None = None


def _build_generation_brief(payload: PromptRequest, regeneration_context: str = "") -> str:
    """Build a structured, model-friendly brief to improve reliability and control."""
    brief = (
        "user_request:\n"
        f"{payload.user_input.strip()}\n\n"
        "generation_preferences:\n"
        f"model: {payload.model}\n"
        f"prompt_mode: {payload.prompt_mode}\n"
        f"response_length: {payload.response_length}\n\n"
        "delivery_expectation:\n"
        "Return one final copy-ready prompt package that follows the selected mode "
        "and requested response length. Keep language natural, direct, and practical."
    )
    if regeneration_context:
        brief = f"{brief}\n\nregeneration_context:\n{regeneration_context.strip()}"
    return brief


def _create_tracked_crew():
    crew_instance = PromptAgent().crew()
    disable_opik = os.getenv("PROMPTFORGE_DISABLE_OPIK", "false").lower() == "true"
    if track_crewai is not None and not disable_opik:
        project_name = os.getenv("OPIK_PROJECT_NAME", "PromptForge")
        try:
            track_crewai(project_name=project_name, crew=crew_instance)
        except TypeError:
            track_crewai(project_name=project_name)
    return crew_instance


def _extract_crew_text(result: object) -> str:
    # CrewAI return types vary by version; normalize into a display-safe string.
    for attr in ("raw", "result", "output"):
        value = getattr(result, attr, None)
        if value:
            return str(value).strip()
    return str(result).strip()


def _sanitize_agent_output(text: str) -> str:
    """Normalize model output to plain readable text for API consumers."""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.replace("```", "")

    # Remove common markdown heading markers and list markers.
    cleaned = re.sub(r"(?m)^\s*#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*[-*+]\s+", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*\d+\.\s+", "", cleaned)

    # Remove emphasis-style asterisks and backticks.
    cleaned = cleaned.replace("*", "")
    cleaned = cleaned.replace("`", "")

    # Collapse excessive blank lines to keep the response flow compact.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _try_parse_json(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def _find_prompt_text(payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key in ("final_prompt_lines", "optimized_prompt_lines", "prompt_lines"):
            value = payload.get(key)
            if isinstance(value, list) and all(isinstance(item, str) for item in value):
                return "\n".join(value).strip()
        for key in ("final_prompt", "optimized_prompt", "prompt"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in payload.values():
            nested = _find_prompt_text(value)
            if nested:
                return nested
    elif isinstance(payload, list):
        for value in payload:
            nested = _find_prompt_text(value)
            if nested:
                return nested
    return None


def _find_validation_report(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, dict):
        if payload.get("artifact") == "validation_report":
            data = payload.get("data")
            return data if isinstance(data, dict) else payload
        if "overall_score" in payload or "final_status" in payload:
            return payload
        for value in payload.values():
            nested = _find_validation_report(value)
            if nested:
                return nested
    elif isinstance(payload, list):
        for value in payload:
            nested = _find_validation_report(value)
            if nested:
                return nested
    return None


def _should_regenerate(report: dict[str, Any] | None, min_score: int) -> bool:
    if not report:
        return False
    status = str(report.get("final_status", "")).strip().lower()
    if status and status != "approved":
        return True
    score = report.get("overall_score")
    if isinstance(score, (int, float)) and score < min_score:
        return True
    return False


def _format_regeneration_context(report: dict[str, Any] | None) -> str:
    if not report:
        return ""
    return json.dumps(report, ensure_ascii=True)


def _extract_prompt_and_metadata(raw_text: str) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    payload = _try_parse_json(raw_text)
    if payload:
        prompt_text = _find_prompt_text(payload)
        if prompt_text:
            return prompt_text, payload, _find_validation_report(payload)
    return _sanitize_agent_output(raw_text), payload, _find_validation_report(payload) if payload else None


async def _kickoff_with_compatibility(
    crew_instance,
    inputs: dict[str, str],
    thread_id: str,
):
    try:
        if os.getenv("PROMPTFORGE_DISABLE_OPIK", "false").lower() == "true":
            return await run_in_threadpool(crew_instance.kickoff, inputs=inputs)
        return await run_in_threadpool(
            crew_instance.kickoff,
            inputs=inputs,
            opik_args={"trace": {"thread_id": thread_id}},
        )
    except TypeError as error:
        if "opik_args" not in str(error):
            raise
        return await run_in_threadpool(crew_instance.kickoff, inputs=inputs)


def _is_retryable_error(error: Exception) -> bool:
    error_text = str(error).lower()
    return "rate limit" in error_text or "rate_limit_exceeded" in error_text


def _compute_backoff_seconds(attempt: int) -> float:
    base_delay = float(os.getenv("PROMPTFORGE_RETRY_BASE_SECONDS", "2"))
    max_delay = float(os.getenv("PROMPTFORGE_RETRY_MAX_SECONDS", "40"))
    jitter = float(os.getenv("PROMPTFORGE_RETRY_JITTER_SECONDS", "0.5"))
    delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
    return delay + random.uniform(0, jitter)


async def _run_with_rate_limit_retry(
    crew_instance,
    inputs: dict[str, str],
    thread_id: str,
):
    max_attempts = int(os.getenv("PROMPTFORGE_MAX_RETRIES", "3"))

    for attempt in range(1, max_attempts + 1):
        try:
            return await _kickoff_with_compatibility(crew_instance, inputs, thread_id)
        except Exception as error:
            if not _is_retryable_error(error) or attempt == max_attempts:
                raise
            await asyncio.sleep(_compute_backoff_seconds(attempt))

    raise RuntimeError("CrewAI execution failed after retries")


app = FastAPI(title="PromptForge API", version="0.1.0")

max_in_flight = int(os.getenv("PROMPTFORGE_MAX_IN_FLIGHT", "8"))
_crew_semaphore = asyncio.Semaphore(max_in_flight)


def _get_allowed_models() -> set[str]:
    allowed = os.getenv("PROMPTFORGE_ALLOWED_MODELS", "").strip()
    if not allowed:
        return set()
    return {item.strip() for item in allowed.split(",") if item.strip()}


def _validate_model_choice(model_name: str) -> None:
    allowed = _get_allowed_models()
    if allowed and model_name not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Requested model is not allowed.",
        )


def _require_api_key(api_key_header: str | None, authorization: str | None) -> None:
    require_key = os.getenv("PROMPTFORGE_REQUIRE_API_KEY", "false").lower() == "true"
    if not require_key:
        return

    configured_key = os.getenv("PROMPTFORGE_API_KEY", "").strip()
    if not configured_key:
        raise HTTPException(
            status_code=500,
            detail="Server is missing API key configuration.",
        )

    candidate = ""
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            candidate = parts[1].strip()
    if not candidate and api_key_header:
        candidate = api_key_header.strip()

    if not candidate or candidate != configured_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

cors_origins = [origin.strip() for origin in os.getenv("PROMPTFORGE_CORS_ORIGINS", "*").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/prompt", response_model=PromptResponse)
async def create_prompt(
    payload: PromptRequest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> PromptResponse:
    _require_api_key(x_api_key, authorization)
    _validate_model_choice(payload.model)

    request_id = str(uuid.uuid4())
    thread_id = os.getenv("OPIK_THREAD_ID", f"prompt-agent-{request_id}")
    generation_brief = _build_generation_brief(payload)
    min_score = int(os.getenv("PROMPTFORGE_MIN_SCORE", "80"))
    max_regen = int(os.getenv("PROMPTFORGE_REGEN_MAX_ATTEMPTS", "1"))
    regeneration_context = ""
    validation_report = None
    prompt_text = ""
    raw_payload = None

    try:
        async with _crew_semaphore:
            timeout_seconds = float(os.getenv("PROMPTFORGE_REQUEST_TIMEOUT_SECONDS", "120"))
            for attempt in range(max_regen + 1):
                crew_instance = _create_tracked_crew()
                generation_brief = _build_generation_brief(payload, regeneration_context)
                crew_result = await asyncio.wait_for(
                    _run_with_rate_limit_retry(
                        crew_instance=crew_instance,
                        inputs={
                            "user_input": payload.user_input.strip(),
                            "model": payload.model,
                            "prompt_mode": payload.prompt_mode,
                            "response_length": payload.response_length,
                            "generation_brief": generation_brief,
                            "regeneration_context": regeneration_context,
                            "regeneration_attempt": str(attempt),
                        },
                        thread_id=thread_id,
                    ),
                    timeout=timeout_seconds,
                )
                raw_text = _extract_crew_text(crew_result)
                prompt_text, raw_payload, validation_report = _extract_prompt_and_metadata(raw_text)

                if attempt == max_regen or not _should_regenerate(validation_report, min_score):
                    break

                regeneration_context = _format_regeneration_context(validation_report)

            logger.info("prompt_generated", extra={"request_id": request_id})
    except asyncio.TimeoutError as error:
        logger.warning("prompt_timeout", extra={"request_id": request_id})
        raise HTTPException(status_code=504, detail="Prompt generation timed out.") from error
    except Exception as error:
        logger.exception("prompt_failure", extra={"request_id": request_id})
        debug_enabled = os.getenv("PROMPTFORGE_DEBUG", "false").lower() == "true"
        detail = "Prompt generation failed while executing CrewAI."
        if debug_enabled:
            detail = f"{detail} Details: {error}"
        raise HTTPException(status_code=500, detail=detail) from error

    include_metadata = os.getenv("PROMPTFORGE_INCLUDE_METADATA", "false").lower() == "true"
    metadata = validation_report if include_metadata else None
    if include_metadata and not metadata and raw_payload:
        metadata = raw_payload

    return PromptResponse(
        prompt=prompt_text,
        style="crew",
        model=payload.model,
        prompt_mode=payload.prompt_mode,
        response_length=payload.response_length,
        generated_at=datetime.now(timezone.utc).isoformat(),
        metadata=metadata,
    )
