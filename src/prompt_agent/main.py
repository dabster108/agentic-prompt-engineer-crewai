import sys
from .crew import PromptAgent

def run():
    """
    Run the crew.
    """
    result = PromptAgent().crew().kickoff()
    print("\nFINAL RESULT:\n")
    print(result)

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {}
    try:
        PromptAgent().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        PromptAgent().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {}
    try:
        PromptAgent().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

if __name__ == "__main__":
    run()