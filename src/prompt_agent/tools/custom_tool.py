from crewai.tools import BaseTool
from crewai_tools import SerperDevTool
from typing import Any, Type
from pydantic import BaseModel, Field


class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Description of the argument.")

class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = (
        "Clear description for what this tool is useful for, your agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "this is an example of a tool output, ignore it and move along."


class BraveSearchInput(BaseModel):
    query: str = Field(..., description="Web search query")


class BraveSearchTool(BaseTool):
    name: str = "brave_search"
    description: str = (
        "Search the web for recent information and return concise results. "
        "Use this when you need up-to-date facts, papers, or news."
    )
    args_schema: Type[BaseModel] = BraveSearchInput

    def _run(self, query: str, **_: Any) -> str:
        # CrewAI tools are executed server-side; keep failures informative.
        # Serper requires SERPER_API_KEY in the environment.
        return str(SerperDevTool().run(search_query=query))
