from pathlib import Path

from .mock import build_mock


if __name__ == "__main__":
    result = build_mock(Path.cwd())
    print(result["manifest"]["summary"])
