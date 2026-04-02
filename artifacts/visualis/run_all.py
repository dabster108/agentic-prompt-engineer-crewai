import subprocess
import sys
from pathlib import Path


def run_script(script_path: Path) -> None:
    print(f"Running {script_path.name}...")
    subprocess.check_call([sys.executable, str(script_path)])


def main() -> None:
    base = Path("artifacts/visualis")
    run_script(base / "model_png.py")
    run_script(base / "agents_png.py")
    run_script(base / "architecture_png.py")

    print("Done. Generated files:")
    print("- artifacts/model.png")
    print("- artifacts/agents.png")
    print("- artifacts/architecture.png")


if __name__ == "__main__":
    main()
