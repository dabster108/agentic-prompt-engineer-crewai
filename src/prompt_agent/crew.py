from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
import os
from dotenv import load_dotenv

load_dotenv()


@CrewBase
class PromptAgent:
    """PromptAgent crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        self.verbose = os.getenv("PROMPTFORGE_VERBOSE", "false").lower() == "true"
        self.groq_llm = LLM(
            model=os.getenv("PROMPTFORGE_LLM_MODEL", "groq/llama-3.1-8b-instant"),
            api_key=os.getenv("GROQ_API_KEY"),
            max_tokens=int(os.getenv("PROMPTFORGE_MAX_TOKENS", "900")),
        )
        self.fast_mode = os.getenv("PROMPTFORGE_FAST_MODE", "false").lower() == "true"
        self.max_rpm = int(os.getenv("PROMPTFORGE_MAX_RPM", "60"))
        process_name = os.getenv("PROMPTFORGE_PROCESS", "sequential").strip().lower()
        self.crew_process = Process.hierarchical if process_name == "hierarchical" else Process.sequential

    def _build_agent(self, config_key: str) -> Agent:
        return Agent(
            config=self.agents_config[config_key],
            verbose=self.verbose,
            llm=self.groq_llm,
            max_rpm=self.max_rpm,
        )

    @agent
    def researcher(self) -> Agent:
        return self._build_agent('researcher')

    @agent
    def reporting_analyst(self) -> Agent:
        return self._build_agent('reporting_analyst')

    @agent
    def requirement_interviewer(self) -> Agent:
        return self._build_agent('requirement_interviewer')

    @agent
    def context_analyzer(self) -> Agent:
        return self._build_agent('context_analyzer')

    @agent
    def prompt_architect(self) -> Agent:
        return self._build_agent('prompt_architect')

    @agent
    def prompt_critic(self) -> Agent:
        return self._build_agent('prompt_critic')

    @agent
    def prompt_refiner(self) -> Agent:
        return self._build_agent('prompt_refiner')

    @agent
    def qa_policy_reviewer(self) -> Agent:
        return self._build_agent('qa_policy_reviewer')

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'],
        )

    @task
    def requirement_interview_task(self) -> Task:
        return Task(
            config=self.tasks_config['requirement_interview_task'],
        )

    @task
    def context_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['context_analysis_task'],
        )

    @task
    def prompt_drafting_task(self) -> Task:
        return Task(
            config=self.tasks_config['prompt_drafting_task'],
        )

    @task
    def prompt_critique_task(self) -> Task:
        return Task(
            config=self.tasks_config['prompt_critique_task'],
        )

    @task
    def prompt_refinement_task(self) -> Task:
        return Task(
            config=self.tasks_config['prompt_refinement_task'],
        )

    @task
    def validation_task(self) -> Task:
        return Task(
            config=self.tasks_config['validation_task'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the PromptAgent crew"""
        task_sequence = [
            self.requirement_interview_task(),
            self.context_analysis_task(),
            self.prompt_drafting_task(),
        ]

        if not self.fast_mode:
            task_sequence.extend([
                self.prompt_critique_task(),
                self.prompt_refinement_task(),
                self.validation_task(),
            ])

        return Crew(
            agents=self.agents,
            tasks=task_sequence,
            process=self.crew_process,
            verbose=self.verbose,
        )