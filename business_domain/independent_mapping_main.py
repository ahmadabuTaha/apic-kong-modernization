from pathlib import Path

from .independent_mapping import build_independent_mapping


if __name__ == "__main__":
    result = build_independent_mapping(Path.cwd())
    print(result["manifest"]["summary"])
