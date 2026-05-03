from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
import os
from dotenv import load_dotenv

from .tools import RepoContextTool

load_dotenv()


@CrewBase
class PromptAgent:
    """PromptAgent crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        self.verbose = os.getenv("PROMPTFORGE_VERBOSE", "false").lower() == "true"
        model_name = os.getenv("PROMPTFORGE_MODEL", "groq/llama-3.3-70b-versatile")
        self.groq_llm = LLM(
            model=model_name,
            api_key=os.getenv("GROQ_API_KEY"),
            max_tokens=int(os.getenv("PROMPTFORGE_MAX_TOKENS", "900")),
        )
        self.fast_mode = os.getenv("PROMPTFORGE_FAST_MODE", "false").lower() == "true"
        self.max_rpm = int(os.getenv("PROMPTFORGE_MAX_RPM", "60"))
        process_name = os.getenv("PROMPTFORGE_PROCESS", "sequential").strip().lower()
        self.crew_process = Process.hierarchical if process_name == "hierarchical" else Process.sequential

    def _resolve_tools(self, config_key: str) -> list:
        if config_key == "context_gatherer":
            return [RepoContextTool()]
        return []

    def _build_agent(self, config_key: str) -> Agent:
        tools = self._resolve_tools(config_key)
        return Agent(
            config=self.agents_config[config_key],
            verbose=self.verbose,
            llm=self.groq_llm,
            max_rpm=self.max_rpm,
            tools=tools,
        )

    @agent
    def intent_detector(self) -> Agent:
        return self._build_agent("intent_detector")

    @agent
    def task_classifier(self) -> Agent:
        return self._build_agent("task_classifier")

    @agent
    def complexity_estimator(self) -> Agent:
        return self._build_agent("complexity_estimator")

    @agent
    def context_gatherer(self) -> Agent:
        return self._build_agent("context_gatherer")

    @agent
    def info_gap_detector(self) -> Agent:
        return self._build_agent("info_gap_detector")

    @agent
    def prompt_strategy_selector(self) -> Agent:
        return self._build_agent("prompt_strategy_selector")

    @agent
    def prompt_architect(self) -> Agent:
        return self._build_agent("prompt_architect")

    @agent
    def prompt_constructor(self) -> Agent:
        return self._build_agent("prompt_constructor")

    @agent
    def reflection_critic(self) -> Agent:
        return self._build_agent("reflection_critic")

    @agent
    def prompt_optimizer(self) -> Agent:
        return self._build_agent("prompt_optimizer")

    @agent
    def validation_scorer(self) -> Agent:
        return self._build_agent("validation_scorer")

    @task
    def intent_detection_task(self) -> Task:
        return Task(
            config=self.tasks_config["intent_detection_task"],
        )

    @task
    def task_classification_task(self) -> Task:
        return Task(
            config=self.tasks_config["task_classification_task"],
        )

    @task
    def complexity_estimation_task(self) -> Task:
        return Task(
            config=self.tasks_config["complexity_estimation_task"],
        )

    @task
    def context_gathering_task(self) -> Task:
        return Task(
            config=self.tasks_config["context_gathering_task"],
        )

    @task
    def missing_information_task(self) -> Task:
        return Task(
            config=self.tasks_config["missing_information_task"],
        )

    @task
    def prompt_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["prompt_strategy_task"],
        )

    @task
    def prompt_architecture_task(self) -> Task:
        return Task(
            config=self.tasks_config["prompt_architecture_task"],
        )

    @task
    def prompt_construction_task(self) -> Task:
        return Task(
            config=self.tasks_config["prompt_construction_task"],
        )

    @task
    def reflection_critique_task(self) -> Task:
        return Task(
            config=self.tasks_config["reflection_critique_task"],
        )

    @task
    def prompt_optimization_task(self) -> Task:
        return Task(
            config=self.tasks_config["prompt_optimization_task"],
        )

    @task
    def validation_task(self) -> Task:
        return Task(
            config=self.tasks_config["validation_task"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the PromptAgent crew"""
        task_sequence = [
            self.intent_detection_task(),
            self.task_classification_task(),
            self.complexity_estimation_task(),
            self.context_gathering_task(),
            self.missing_information_task(),
            self.prompt_strategy_task(),
            self.prompt_architecture_task(),
            self.prompt_construction_task(),
        ]

        if self.fast_mode:
            task_sequence.append(self.validation_task())
        else:
            task_sequence.extend([
                self.reflection_critique_task(),
                self.prompt_optimization_task(),
                self.validation_task(),
            ])

        return Crew(
            agents=self.agents,
            tasks=task_sequence,
            process=self.crew_process,
            verbose=self.verbose,
        )