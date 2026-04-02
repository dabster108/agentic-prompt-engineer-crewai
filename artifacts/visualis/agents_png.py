from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import yaml


def main() -> None:
    config_path = Path("src/prompt_agent/config/agents.yaml")
    out_dir = Path("artifacts")
    out_dir.mkdir(parents=True, exist_ok=True)

    with config_path.open("r", encoding="utf-8") as f:
        agents = yaml.safe_load(f)

    rows = []
    for name, body in agents.items():
        role = (body.get("role") or "").strip().replace("\n", " ")
        goal = (body.get("goal") or "").strip().replace("\n", " ")
        rows.append(
            {
                "agent": name,
                "role_len": len(role),
                "goal_len": len(goal),
                "total_context_chars": len(role) + len(goal),
            }
        )

    df = pd.DataFrame(rows).sort_values("total_context_chars", ascending=False)

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(df["agent"], df["total_context_chars"], color="#1f77b4")
    ax.invert_yaxis()
    ax.set_xlabel("Role + Goal Character Count")
    ax.set_ylabel("Agent")
    ax.set_title("PromptForge Agents Profile", fontsize=16, weight="bold")

    for bar in bars:
        x = bar.get_width()
        y = bar.get_y() + bar.get_height() / 2
        ax.text(x + 1.5, y, f"{int(x)}", va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(out_dir / "agents.png", dpi=200)
    plt.close()


if __name__ == "__main__":
    main()
