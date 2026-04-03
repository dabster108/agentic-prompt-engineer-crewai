from pathlib import Path
import os

from graphviz import Digraph

from graphviz_utils import render_png


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    out_dir = project_root / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    model = os.getenv(
        "PROMPTFORGE_LLM_MODEL",
        os.getenv("PROMPTFORGE_MODEL", os.getenv("MODEL", "groq/llama-3.3-70b-versatile")),
    )
    max_tokens = int(os.getenv("PROMPTFORGE_MAX_TOKENS", "512"))
    fast_mode = os.getenv("PROMPTFORGE_FAST_MODE", "true").lower() == "true"
    response_length = os.getenv("PROMPTFORGE_RESPONSE_LENGTH", "short")
    opik_disabled = os.getenv("PROMPTFORGE_DISABLE_OPIK", "true")

    diagram = Digraph("promptforge_model_runtime", engine="dot")
    diagram.attr(
        rankdir="TB",
        splines="ortho",
        bgcolor="white",
        label="PromptForge Model Runtime Decision Flow",
        labelloc="t",
        fontsize="14",
    )
    diagram.attr("node", fontname="Helvetica", fontsize="10", style="rounded,filled", color="#0b3d91")

    diagram.node("env", "Load Environment Variables", shape="box", fillcolor="#e8f0fe")
    diagram.node("provider", "Provider: Groq", shape="box", fillcolor="#f3f7ff")
    diagram.node("model", f"Model: {model}", shape="box", fillcolor="#f3f7ff")
    diagram.node("tokens", f"Max Tokens: {max_tokens}", shape="box", fillcolor="#f3f7ff")
    diagram.node("fast_mode", f"Fast Mode Enabled?\n{fast_mode}", shape="diamond", fillcolor="#fff1cc")
    diagram.node("response", f"Response Length: {response_length}", shape="box", fillcolor="#f3f7ff")
    diagram.node("opik", f"OPIK Disabled: {opik_disabled}", shape="box", fillcolor="#f3f7ff")
    diagram.node("runtime", "Runtime Ready", shape="parallelogram", fillcolor="#e8f0fe")

    diagram.edge("env", "provider")
    diagram.edge("provider", "model")
    diagram.edge("model", "tokens")
    diagram.edge("tokens", "fast_mode")
    diagram.edge("fast_mode", "response", label="Yes")
    diagram.edge("fast_mode", "response", label="No")
    diagram.edge("response", "opik")
    diagram.edge("opik", "runtime")

    render_png(diagram, out_dir / "model.png")


if __name__ == "__main__":
    main()
