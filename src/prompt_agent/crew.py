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
        self.groq_llm = LLM(
            model="groq/llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY"),
        )

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            verbose=True,
            llm=self.groq_llm
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],
            verbose=True,
            llm=self.groq_llm
        )

    @agent
    def requirement_interviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['requirement_interviewer'],
            verbose=True,
            llm=self.groq_llm
        )

    @agent
    def context_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['context_analyzer'],
            verbose=True,
            llm=self.groq_llm
        )

    @agent
    def prompt_architect(self) -> Agent:
        return Agent(
            config=self.agents_config['prompt_architect'],
            verbose=True,
            llm=self.groq_llm
        )

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

    @crew
    def crew(self) -> Crew:
        """Creates the PromptAgent crew"""
        return Crew(
            agents=self.agents,
            tasks=[
                self.requirement_interview_task(),
                self.context_analysis_task(),
                self.prompt_drafting_task(),
            ],
            process=Process.sequential,
            verbose=True,
           
        )