# Project Knowledge Base

This document provides a detailed overview of the PromptAgent Crew project, including its structure, components, and configuration.

## Project Overview

The PromptAgent Crew is a multi-agent AI system built using the [crewAI](https://crewai.com) framework. It's designed to automate complex tasks by enabling a team of AI agents to collaborate effectively.

## Core Components

The project is structured into several key files and directories:

### 1. `main.py`

This is the main entry point for running the crew. It handles:

- Setting up the initial inputs for the crew (e.g., `topic`, `current_year`).
- Kicking off the crew's execution.
- Providing functions for training, replaying, and testing the crew.

### 2. `crew.py`

This file defines the crew's structure, including the agents and tasks.

- It uses the `@CrewBase` decorator to define the crew.
- Agents are defined using the `@agent` decorator, and their configurations are loaded from `agents.yaml`.
- Tasks are defined using the `@task` decorator, with configurations loaded from `tasks.yaml`.
- The `crew()` method assembles the agents and tasks into a `Crew` object, specifying the process (e.g., `Process.sequential`).

### 3. `config/agents.yaml`

This YAML file defines the properties of each agent in the crew. Each agent has:

- `role`: The agent's designated function (e.g., "Senior Data Researcher").
- `goal`: The agent's primary objective.
- `backstory`: A brief narrative that gives the agent context and personality.

**Agents:**

- **researcher**: Responsible for uncovering cutting-edge developments in a given topic.
- **reporting_analyst**: Responsible for creating detailed reports based on research findings.

### 4. `config/tasks.yaml`

This YAML file defines the tasks that the crew will perform. Each task has:

- `description`: A detailed explanation of what the task entails.
- `expected_output`: A description of the desired outcome of the task.
- `agent`: The agent assigned to perform the task.

**Tasks:**

- **research_task**: A task for the `researcher` agent to conduct thorough research on a topic.
- **reporting_task**: A task for the `reporting_analyst` agent to create a report from the research findings.

## How it Works

1.  The `run()` function in `main.py` is called.
2.  It initializes the `PromptAgent` crew from `crew.py`.
3.  The `PromptAgent` crew loads the agent and task configurations from the YAML files.
4.  The `crew().kickoff()` method starts the execution, passing the initial inputs.
5.  The agents perform their assigned tasks sequentially, with the output of one task potentially being the input for the next.
6.  The final output is saved to `report.md`.
