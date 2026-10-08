"""Run the Task 014 Gate A evidence generator."""

from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).parents[1] / "tests/evidence/task-014/architecture-preflight/generate_preflight.py"), run_name="__main__")
