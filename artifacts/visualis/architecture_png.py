from pathlib import Path
import os

from graphviz import Digraph
import yaml

from graphviz_utils import render_png


def active_tasks(tasks_dict: dict, fast_mode: bool) -> list[str]:
    base = [
        "requirement_interview_task",
        "context_analysis_task",
        "prompt_drafting_task",
    ]
    full_tail = [
        "prompt_critique_task",
        "prompt_refinement_task",
        "validation_task",
    ]
    sequence = base if fast_mode else base + full_tail
    return [task for task in sequence if task in tasks_dict]


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    tasks_path = project_root / "src/prompt_agent/config/tasks.yaml"
    out_dir = project_root / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    with tasks_path.open("r", encoding="utf-8") as f:
        tasks = yaml.safe_load(f)

    fast_mode = os.getenv("PROMPTFORGE_FAST_MODE", "true").lower() == "true"
    model = os.getenv(
        "PROMPTFORGE_LLM_MODEL",
        os.getenv("PROMPTFORGE_MODEL", os.getenv("MODEL", "groq/llama-3.3-70b-versatile")),
    )
    process = os.getenv("PROMPTFORGE_PROCESS", "sequential")

    diagram = Digraph("promptforge_architecture", engine="dot")
    diagram.attr(
        rankdir="LR",
        splines="ortho",
        bgcolor="white",
        nodesep="0.6",
        ranksep="0.9",
        label=f"PromptForge Architecture | process={process} | fast_mode={fast_mode} | model={model}",
        labelloc="t",
        fontsize="14",
    )
    diagram.attr("node", fontname="Helvetica", fontsize="10", style="rounded,filled", color="#1f4b99")

    diagram.node("input", "User Input", shape="parallelogram", fillcolor="#e8f0fe")
    diagram.node("decision", "Fast Mode?", shape="diamond", fillcolor="#fff1cc")
    diagram.node("output", "Final Prompt", shape="parallelogram", fillcolor="#e8f0fe")

    diagram.edge("input", "decision")

    with diagram.subgraph(name="cluster_fast") as fast_cluster:
        fast_cluster.attr(label="Fast Path", color="#8cb3ff", style="rounded")
        for task_name in active_tasks(tasks, True):
            agent = tasks.get(task_name, {}).get("agent", "n/a")
            fast_cluster.node(task_name, f"{task_name}\nagent: {agent}", shape="box", fillcolor="#f3f7ff")

    with diagram.subgraph(name="cluster_full") as full_cluster:
        full_cluster.attr(label="Full Quality Path", color="#6aa84f", style="rounded")
        for task_name in active_tasks(tasks, False):
            agent = tasks.get(task_name, {}).get("agent", "n/a")
            full_cluster.node(f"full_{task_name}", f"{task_name}\nagent: {agent}", shape="box", fillcolor="#f3fff2")

    fast_sequence = active_tasks(tasks, True)
    full_sequence = active_tasks(tasks, False)

    diagram.edge("decision", fast_sequence[0], label="Yes", color="#1f4b99")
    diagram.edge("decision", f"full_{full_sequence[0]}", label="No", color="#2d6a1f")

    for idx in range(len(fast_sequence) - 1):
        diagram.edge(fast_sequence[idx], fast_sequence[idx + 1], color="#1f4b99")
    diagram.edge(fast_sequence[-1], "output", color="#1f4b99")

    for idx in range(len(full_sequence) - 1):
        diagram.edge(f"full_{full_sequence[idx]}", f"full_{full_sequence[idx + 1]}", color="#2d6a1f")
    diagram.edge(f"full_{full_sequence[-1]}", "output", color="#2d6a1f")

    render_png(diagram, out_dir / "architecture.png")


if __name__ == "__main__":
    main()
