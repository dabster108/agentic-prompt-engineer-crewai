from datetime import datetime, timezone
import os
import time
import uuid

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .crew import PromptAgent

try:
    from opik.integrations.crewai import track_crewai
except ImportError:
    track_crewai = None


class PromptRequest(BaseModel):
    user_input: str = Field(min_length=1, max_length=2000)
    model: str = Field(default="Haiku 4.5", min_length=1, max_length=100)


class PromptResponse(BaseModel):
    prompt: str
    style: str
    generated_at: str


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


def _kickoff_with_compatibility(crew_instance, inputs: dict[str, str], thread_id: str):
    try:
        return crew_instance.kickoff(
            inputs=inputs,
            opik_args={"trace": {"thread_id": thread_id}},
        )
    except TypeError as error:
        if "opik_args" not in str(error):
            raise
        return crew_instance.kickoff(inputs=inputs)


def _run_with_rate_limit_retry(crew_instance, inputs: dict[str, str], thread_id: str):
    max_attempts = int(os.getenv("PROMPTFORGE_MAX_RETRIES", "2"))
    wait_seconds = int(os.getenv("PROMPTFORGE_RETRY_WAIT_SECONDS", "35"))

    for attempt in range(1, max_attempts + 1):
        try:
            return _kickoff_with_compatibility(crew_instance, inputs, thread_id)
        except Exception as error:
            error_text = str(error).lower()
            is_rate_limit = "rate limit" in error_text or "rate_limit_exceeded" in error_text
            if not is_rate_limit or attempt == max_attempts:
                raise
            time.sleep(wait_seconds)

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
def create_prompt(payload: PromptRequest) -> PromptResponse:
    thread_id = os.getenv("OPIK_THREAD_ID", f"prompt-agent-{uuid.uuid4()}")
    # Keep UI-selected model visible to agents without changing existing task templates.
    user_input = f"{payload.user_input.strip()}\n\nPreferred model: {payload.model}"

    try:
        crew_instance = _create_tracked_crew()
        crew_result = _run_with_rate_limit_retry(
            crew_instance=crew_instance,
            inputs={"user_input": user_input},
            thread_id=thread_id,
        )
        prompt_text = _extract_crew_text(crew_result)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"CrewAI failed: {error}") from error

    return PromptResponse(
        prompt=prompt_text,
        style="crew",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
