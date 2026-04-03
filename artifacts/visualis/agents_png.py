from pathlib import Path

from graphviz import Digraph
import yaml

from graphviz_utils import render_png


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "src/prompt_agent/config/agents.yaml"
    out_dir = project_root / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    with config_path.open("r", encoding="utf-8") as f:
        agents = yaml.safe_load(f)

    diagram = Digraph("promptforge_agents", engine="dot")
    diagram.attr(
        rankdir="LR",
        splines="ortho",
        bgcolor="white",
        nodesep="0.7",
        ranksep="0.9",
        label="PromptForge Agent Pipeline",
        labelloc="t",
        fontsize="14",
    )
    diagram.attr("node", shape="box", style="rounded,filled", fillcolor="#f3f7ff", color="#1f4b99", fontname="Helvetica")

    ordered_agents = [
        "requirement_interviewer",
        "context_analyzer",
        "prompt_architect",
        "prompt_critic",
        "prompt_refiner",
        "qa_policy_reviewer",
    ]

    diagram.node("input", "User Request", shape="parallelogram", fillcolor="#e8f0fe")
    diagram.node("output", "Validated Final Prompt", shape="parallelogram", fillcolor="#e8f0fe")

    for name in ordered_agents:
        body = agents.get(name, {})
        role = (body.get("role") or "n/a").strip().replace("\n", " ")
        goal = (body.get("goal") or "").strip().replace("\n", " ")
        short_goal = goal[:95] + "..." if len(goal) > 95 else goal
        diagram.node(name, f"{name}\nrole: {role}\ngoal: {short_goal}")

    diagram.edge("input", ordered_agents[0])
    for idx in range(len(ordered_agents) - 1):
        diagram.edge(ordered_agents[idx], ordered_agents[idx + 1])
    diagram.edge(ordered_agents[-1], "output")

    with diagram.subgraph(name="cluster_optional") as optional_cluster:
        optional_cluster.attr(label="Optional Research Agents", color="#9aa0a6", style="dashed")
        for name in ["researcher", "reporting_analyst"]:
            if name in agents:
                role = (agents[name].get("role") or "n/a").strip().replace("\n", " ")
                optional_cluster.node(name, f"{name}\nrole: {role}", fillcolor="#f8f9fa", color="#6c757d")

        if "researcher" in agents and "reporting_analyst" in agents:
            optional_cluster.edge("researcher", "reporting_analyst", style="dashed", color="#6c757d")

    render_png(diagram, out_dir / "agents.png")


if __name__ == "__main__":
    main()
