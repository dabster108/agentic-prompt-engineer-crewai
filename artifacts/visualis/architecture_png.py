from pathlib import Path
import os

import matplotlib.pyplot as plt
import yaml


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


def draw_box(ax, x: float, y: float, w: float, h: float, text: str, fc: str = "#e8f0fe", ec: str = "#1f4b99") -> None:
    rect = plt.Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10, wrap=True)


def main() -> None:
    tasks_path = Path("src/prompt_agent/config/tasks.yaml")
    out_dir = Path("artifacts")
    out_dir.mkdir(parents=True, exist_ok=True)

    with tasks_path.open("r", encoding="utf-8") as f:
        tasks = yaml.safe_load(f)

    fast_mode = os.getenv("PROMPTFORGE_FAST_MODE", "true").lower() == "true"
    model = os.getenv(
        "PROMPTFORGE_LLM_MODEL",
        os.getenv("PROMPTFORGE_MODEL", os.getenv("MODEL", "groq/llama-3.3-70b-versatile")),
    )
    process = os.getenv("PROMPTFORGE_PROCESS", "sequential")

    sequence = active_tasks(tasks, fast_mode)

    fig, ax = plt.subplots(figsize=(15, 6))
    ax.set_xlim(0, max(10, len(sequence) * 2.2 + 3))
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title(f"PromptForge Architecture ({process}, fast_mode={fast_mode})", fontsize=16, weight="bold", pad=14)

    x = 0.8
    y = 2.2
    w = 1.8
    h = 1.4

    draw_box(ax, 0.2, y, 1.2, h, "Input")
    ax.annotate("", xy=(x, y + h / 2), xytext=(1.4, y + h / 2), arrowprops=dict(arrowstyle="->", lw=1.5))

    for idx, task_name in enumerate(sequence):
        agent = tasks.get(task_name, {}).get("agent", "n/a")
        label = f"{task_name}\n({agent})"
        draw_box(ax, x, y, w, h, label)
        if idx < len(sequence) - 1:
            ax.annotate(
                "",
                xy=(x + w + 0.3, y + h / 2),
                xytext=(x + w, y + h / 2),
                arrowprops=dict(arrowstyle="->", lw=1.5),
            )
        x += 2.2

    draw_box(ax, x, y, 1.4, h, "Output")
    ax.annotate("", xy=(x, y + h / 2), xytext=(x - 0.3, y + h / 2), arrowprops=dict(arrowstyle="->", lw=1.5))

    ax.text(0.2, 0.5, f"LLM Model: {model}", fontsize=11)
    ax.text(0.2, 0.15, "Source: crew.py and tasks.yaml runtime sequence", fontsize=9, color="#4b4b4b")

    plt.tight_layout()
    plt.savefig(out_dir / "architecture.png", dpi=220)
    plt.close()


if __name__ == "__main__":
    main()
