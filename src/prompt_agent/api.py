import asyncio
from datetime import datetime, timezone
import os
import re
from typing import Literal
import uuid

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from .crew import PromptAgent

try:
    from opik.integrations.crewai import track_crewai
except ImportError:
    track_crewai = None


class PromptRequest(BaseModel):
    user_input: str = Field(min_length=1, max_length=2000)
    model: str = Field(default="Haiku 4.5", min_length=1, max_length=100)
    prompt_mode: Literal["prompt_engineering", "vibe_coding"] = "prompt_engineering"
    response_length: Literal["short", "balanced", "long"] = "balanced"


class PromptResponse(BaseModel):
    prompt: str
    style: str
    model: str
    prompt_mode: str
    response_length: str
    generated_at: str


def _build_generation_brief(payload: PromptRequest) -> str:
    """Build a structured, model-friendly brief to improve reliability and control."""
    return (
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


def _create_tracked_crew():
    crew_instance = PromptAgent().crew()
    if track_crewai is not None:
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


async def _kickoff_with_compatibility(crew_instance, inputs: dict[str, str], thread_id: str):
    try:
        return await run_in_threadpool(
            crew_instance.kickoff,
            inputs=inputs,
            opik_args={"trace": {"thread_id": thread_id}},
        )
    except TypeError as error:
        if "opik_args" not in str(error):
            raise
        return await run_in_threadpool(crew_instance.kickoff, inputs=inputs)


async def _run_with_rate_limit_retry(crew_instance, inputs: dict[str, str], thread_id: str):
    max_attempts = int(os.getenv("PROMPTFORGE_MAX_RETRIES", "2"))
    wait_seconds = int(os.getenv("PROMPTFORGE_RETRY_WAIT_SECONDS", "35"))

    for attempt in range(1, max_attempts + 1):
        try:
            return await _kickoff_with_compatibility(crew_instance, inputs, thread_id)
        except Exception as error:
            error_text = str(error).lower()
            is_rate_limit = "rate limit" in error_text or "rate_limit_exceeded" in error_text
            if not is_rate_limit or attempt == max_attempts:
                raise
            await asyncio.sleep(wait_seconds)

    raise RuntimeError("CrewAI execution failed after retries")


app = FastAPI(title="PromptForge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/prompt", response_model=PromptResponse)
async def create_prompt(payload: PromptRequest) -> PromptResponse:
    thread_id = os.getenv("OPIK_THREAD_ID", f"prompt-agent-{uuid.uuid4()}")
    generation_brief = _build_generation_brief(payload)

    try:
        crew_instance = _create_tracked_crew()
        crew_result = await _run_with_rate_limit_retry(
            crew_instance=crew_instance,
            inputs={
                "user_input": payload.user_input.strip(),
                "model": payload.model,
                "prompt_mode": payload.prompt_mode,
                "response_length": payload.response_length,
                "generation_brief": generation_brief,
            },
            thread_id=thread_id,
        )
        prompt_text = _sanitize_agent_output(_extract_crew_text(crew_result))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Prompt generation failed while executing CrewAI. "
                f"Details: {error}"
            ),
        ) from error

    return PromptResponse(
        prompt=prompt_text,
        style="crew",
        model=payload.model,
        prompt_mode=payload.prompt_mode,
        response_length=payload.response_length,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
