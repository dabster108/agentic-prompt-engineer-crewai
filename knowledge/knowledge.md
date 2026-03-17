# PromptForge Knowledge Base

This document defines what PromptForge is intended to become, how the multi-agent architecture should work, and how the current code maps to that target.

## Product Intention

PromptForge is intended to be an agentic prompt engineering studio.

The end goal is to take a rough user idea and produce a production-ready prompt package that includes:

- A high-quality final prompt
- Assumptions and constraints
- Suggested model/settings
- Validation checklist
- Optional prompt variants (strict, creative, concise)

## Current State vs Target

Current implementation is an early foundation:

- 2 agents: `researcher` and `reporting_analyst`
- 2 tasks: `research_task` and `reporting_task`
- Sequential flow using CrewAI

Target implementation is a full prompt-engineering pipeline with specialized agents and explicit artifacts at each stage.

## Target Multi-Agent Architecture

### 1) Requirement Interviewer Agent

Purpose:

- Turn a vague user request into clear requirements.

Input:

- User idea or problem statement.

Output artifact:

- `requirements_spec` containing goal, audience, tone, constraints, success criteria, and missing info.

### 2) Context Analyzer Agent

Purpose:

- Gather relevant project/domain context from docs, code, and optional web search.

Input:

- `requirements_spec`

Output artifact:

- `context_brief` with key facts, dependencies, edge cases, and assumptions.

### 3) Prompt Architect Agent

Purpose:

- Build a structured first draft prompt using best-practice prompting patterns.

Input:

- `requirements_spec`, `context_brief`

Output artifact:

- `prompt_draft_v1` with sections like role, objective, context, instructions, constraints, and output format.

### 4) Prompt Critic Agent

Purpose:

- Critically review prompt quality and identify ambiguity or failure risks.

Input:

- `prompt_draft_v1`

Output artifact:

- `critique_report` with weaknesses, risk score, and concrete revisions.

### 5) Prompt Refiner Agent

Purpose:

- Apply critique improvements and generate robust final prompt versions.

Input:

- `prompt_draft_v1`, `critique_report`

Output artifact:

- `prompt_final` and optional variants (`strict`, `balanced`, `creative`).

### 6) QA and Policy Agent

Purpose:

- Validate completeness, formatting, and policy/safety alignment.

Input:

- `prompt_final`

Output artifact:

- `validation_report` and approved publishable package.

## End-to-End Workflow

1. Collect/clarify user intent.
2. Build requirements spec.
3. Collect context and constraints.
4. Generate prompt draft.
5. Critique and score.
6. Refine into final prompt package.
7. Validate quality and safety.
8. Return final output with rationale and usage notes.

## Codebase Mapping

Current files:

- `src/prompt_agent/crew.py`: crew definition, agent wiring, task wiring.
- `src/prompt_agent/config/agents.yaml`: agent personas/goals.
- `src/prompt_agent/config/tasks.yaml`: task descriptions and expected output.
- `src/prompt_agent/main.py`: entry points (`run`, `train`, `replay`, `test`).
- `src/prompt_agent/tools/custom_tool.py`: external tool integration (currently search).

Near-term implementation direction:

- Expand `agents.yaml` from 2 agents to the 6 target agents.
- Expand `tasks.yaml` so each task emits one clear artifact.
- Update `crew.py` to include the new agent and task methods.
- Pass structured inputs (user_intent, domain, constraints, output_style) from `main.py`.
- Add artifact persistence (for example in `knowledge/` or `outputs/`) for traceability.

## Immediate Next Build Step

Implement Phase 1 with 4 agents first:

- Requirement Interviewer
- Context Analyzer
- Prompt Architect
- Prompt Critic

Then add Refiner and QA/Policy in Phase 2.

This phased build keeps complexity manageable while moving the codebase directly toward the intended PromptForge architecture.
