import sys
import os
import re
import time
import json
from typing import Any
from .crew import PromptAgent


def _create_tracked_crew():
    return PromptAgent().crew()


def _read_user_input() -> str:
    env_value = os.getenv("PROMPTFORGE_INPUT", "").strip()
    if env_value:
        return env_value

    print("\nEnter your prompt request for PromptForge:")
    user_input = input("> ").strip()
    if not user_input:
        raise ValueError("Input cannot be empty. Provide a prompt request and run again.")
    return user_input


def _get_generation_controls() -> tuple[str, str, str]:
    model = os.getenv("PROMPTFORGE_MODEL", "groq/llama-3.3-70b-versatile").strip()
    prompt_mode = os.getenv("PROMPTFORGE_PROMPT_MODE", "prompt_engineering").strip()
    response_length = os.getenv("PROMPTFORGE_RESPONSE_LENGTH", "balanced").strip()
    return model, prompt_mode, response_length


def _build_generation_brief(
    user_input: str,
    model: str,
    prompt_mode: str,
    response_length: str,
    regeneration_context: str = "",
) -> str:
    brief = (
        "user_request:\n"
        f"{user_input.strip()}\n\n"
        "generation_preferences:\n"
        f"model: {model}\n"
        f"prompt_mode: {prompt_mode}\n"
        f"response_length: {response_length}\n\n"
        "delivery_expectation:\n"
        "Return one final copy-ready prompt package that follows the selected mode "
        "and requested response length. Keep language natural, direct, and practical."
    )
    if regeneration_context:
        brief = f"{brief}\n\nregeneration_context:\n{regeneration_context.strip()}"
    return brief


def _kickoff_with_compatibility(crew_instance, inputs):
    return crew_instance.kickoff(inputs=inputs)


def _run_with_rate_limit_retry(crew_instance, inputs):
    max_attempts = int(os.getenv("PROMPTFORGE_MAX_RETRIES", "2"))
    wait_seconds = int(os.getenv("PROMPTFORGE_RETRY_WAIT_SECONDS", "35"))

    for attempt in range(1, max_attempts + 1):
        try:
            return _kickoff_with_compatibility(crew_instance, inputs)
        except Exception as error:
            error_text = str(error).lower()
            is_rate_limit = "rate limit" in error_text or "rate_limit_exceeded" in error_text
            if not is_rate_limit or attempt == max_attempts:
                raise
            print(f"\nRate limit reached. Waiting {wait_seconds}s before retry {attempt + 1}/{max_attempts}...")
            time.sleep(wait_seconds)


def _sanitize_agent_output(text: str) -> str:
    """Normalize model output to plain readable text for terminal output."""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.replace("```", "")
    cleaned = re.sub(r"(?m)^\s*#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*[-*+]\s+", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*\d+\.\s+", "", cleaned)
    cleaned = cleaned.replace("*", "")
    cleaned = cleaned.replace("`", "")
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


def _extract_crew_text(result: object) -> str:
    for attr in ("raw", "result", "output"):
        value = getattr(result, attr, None)
        if value:
            return str(value).strip()
    return str(result).strip()

def run():
    """
    Run the crew.
    """
    crew_instance = _create_tracked_crew()
    user_input = _read_user_input()
    model, prompt_mode, response_length = _get_generation_controls()
    min_score = int(os.getenv("PROMPTFORGE_MIN_SCORE", "80"))
    max_regen = int(os.getenv("PROMPTFORGE_REGEN_MAX_ATTEMPTS", "1"))
    regeneration_context = ""

    for attempt in range(max_regen + 1):
        inputs = {
            "user_input": user_input,
            "model": model,
            "prompt_mode": prompt_mode,
            "response_length": response_length,
            "generation_brief": _build_generation_brief(
                user_input,
                model,
                prompt_mode,
                response_length,
                regeneration_context,
            ),
            "regeneration_context": regeneration_context,
            "regeneration_attempt": str(attempt),
        }
        result = _run_with_rate_limit_retry(
            crew_instance=crew_instance,
            inputs=inputs,
        )
        raw_text = _extract_crew_text(result)
        prompt_text, _, validation_report = _extract_prompt_and_metadata(raw_text)
        if attempt == max_regen or not _should_regenerate(validation_report, min_score):
            print("\nFINAL RESULT:\n")
            print(prompt_text)
            if os.getenv("PROMPTFORGE_VERBOSE", "false").lower() == "true" and validation_report:
                print("\nQUALITY REPORT:\n")
                print(json.dumps(validation_report, ensure_ascii=True, indent=2))
            break

        regeneration_context = _format_regeneration_context(validation_report)
        crew_instance = _create_tracked_crew()

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {"user_input": _read_user_input()}
    try:
        _create_tracked_crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        _create_tracked_crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {"user_input": _read_user_input()}
    try:
        _create_tracked_crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

if __name__ == "__main__":
    run()