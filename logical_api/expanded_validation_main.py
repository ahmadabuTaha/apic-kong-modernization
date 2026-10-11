from pathlib import Path

from .expanded_validation import build_expanded_validation


if __name__ == "__main__":
    print(build_expanded_validation(Path.cwd())["manifest"]["summary"])
