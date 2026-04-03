import os
from pathlib import Path
import shutil

from graphviz import Digraph
from graphviz.backend import ExecutableNotFound


def _ensure_dot_on_path() -> str | None:
    dot = shutil.which("dot")
    if dot:
        return dot

    common_locations = [
        "/opt/homebrew/bin/dot",
        "/usr/local/bin/dot",
        "/opt/local/bin/dot",
    ]

    for candidate in common_locations:
        if Path(candidate).exists():
            candidate_dir = str(Path(candidate).parent)
            os.environ["PATH"] = f"{candidate_dir}:{os.environ.get('PATH', '')}"
            return candidate

    return None


def render_png(diagram: Digraph, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    detected_dot = _ensure_dot_on_path()

    try:
        diagram.render(
            filename=output_path.stem,
            directory=str(output_path.parent),
            format="png",
            cleanup=True,
        )
    except ExecutableNotFound as exc:
        dot_path = output_path.with_suffix(".dot")
        diagram.save(filename=dot_path.name, directory=str(dot_path.parent))
        hint = "Install with: brew install graphviz"
        if detected_dot:
            hint = f"Detected dot at {detected_dot} but Graphviz could not execute it. Check PATH and executable permissions."
        raise RuntimeError(
            "Graphviz executable 'dot' was not found. Install Graphviz and rerun. "
            f"{hint}. DOT source has been saved to {dot_path}."
        ) from exc
