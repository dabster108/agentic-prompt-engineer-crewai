from pathlib import Path
import os

import matplotlib.pyplot as plt


def main() -> None:
    out_dir = Path("artifacts")
    out_dir.mkdir(parents=True, exist_ok=True)

    model = os.getenv(
        "PROMPTFORGE_LLM_MODEL",
        os.getenv("PROMPTFORGE_MODEL", os.getenv("MODEL", "groq/llama-3.3-70b-versatile")),
    )
    max_tokens = int(os.getenv("PROMPTFORGE_MAX_TOKENS", "512"))
    fast_mode = os.getenv("PROMPTFORGE_FAST_MODE", "true").lower() == "true"
    response_length = os.getenv("PROMPTFORGE_RESPONSE_LENGTH", "short")
    opik_disabled = os.getenv("PROMPTFORGE_DISABLE_OPIK", "true")

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.axis("off")
    ax.set_title("PromptForge Model Runtime", fontsize=18, weight="bold", pad=16)

    rows = [
        ("Provider", "Groq"),
        ("Model", model),
        ("Max Tokens", str(max_tokens)),
        ("Fast Mode", str(fast_mode)),
        ("Response Length", response_length),
        ("OPIK Disabled", opik_disabled),
    ]

    table = ax.table(
        cellText=[[k, v] for k, v in rows],
        colLabels=["Setting", "Value"],
        colWidths=[0.35, 0.65],
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2)

    for (r, _c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#0b3d91")
            cell.set_text_props(color="white", weight="bold")
        else:
            cell.set_facecolor("#f3f6fc" if r % 2 == 0 else "#ffffff")

    plt.tight_layout()
    plt.savefig(out_dir / "model.png", dpi=200)
    plt.close()


if __name__ == "__main__":
    main()
