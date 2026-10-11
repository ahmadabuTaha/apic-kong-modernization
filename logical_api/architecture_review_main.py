from pathlib import Path

from .architecture_review import build_architecture_review


if __name__ == "__main__":
    print(build_architecture_review(Path.cwd())["manifest"]["summary"])
