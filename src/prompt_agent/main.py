import sys
import os
import uuid
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

def run():
    """
    Run the crew.
    """
    crew_instance = _create_tracked_crew()
    thread_id = os.getenv("OPIK_THREAD_ID", f"prompt-agent-{uuid.uuid4()}")
    try:
        result = crew_instance.kickoff(opik_args={"trace": {"thread_id": thread_id}})
    except TypeError:
        result = crew_instance.kickoff()
    print("\nFINAL RESULT:\n")
    print(result)

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {}
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
    inputs = {}
    try:
        _create_tracked_crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

if __name__ == "__main__":
    run()