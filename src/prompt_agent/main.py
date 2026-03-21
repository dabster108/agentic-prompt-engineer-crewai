import sys
import os
import re
import uuid
import time
from .crew import PromptAgent

try:
    from opik.integrations.crewai import track_crewai
except ImportError:
    track_crewai = None


def _create_tracked_crew():
    crew_instance = PromptAgent().crew()
    if track_crewai is not None:
        project_name = os.getenv("OPIK_PROJECT_NAME", "PromptForge")
        try:
            track_crewai(project_name=project_name, crew=crew_instance)
        except TypeError:
            track_crewai(project_name=project_name)
    return crew_instance


def _read_user_input() -> str:
    env_value = os.getenv("PROMPTFORGE_INPUT", "").strip()
    if env_value:
        return env_value

    print("\nEnter your prompt request for PromptForge:")
    user_input = input("> ").strip()
    if not user_input:
        raise ValueError("Input cannot be empty. Provide a prompt request and run again.")
    return user_input


def _kickoff_with_compatibility(crew_instance, inputs, thread_id):
    try:
        return crew_instance.kickoff(
            inputs=inputs,
            opik_args={"trace": {"thread_id": thread_id}},
        )
    except TypeError as error:
        if "opik_args" not in str(error):
            raise
        return crew_instance.kickoff(inputs=inputs)


def _run_with_rate_limit_retry(crew_instance, inputs, thread_id):
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
    thread_id = os.getenv("OPIK_THREAD_ID", f"prompt-agent-{uuid.uuid4()}")
    result = _run_with_rate_limit_retry(
        crew_instance=crew_instance,
        inputs={"user_input": user_input},
        thread_id=thread_id,
    )
    print("\nFINAL RESULT:\n")
    print(_sanitize_agent_output(_extract_crew_text(result)))

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