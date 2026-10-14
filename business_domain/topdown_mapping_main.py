from pathlib import Path

from .topdown_mapping import build_topdown_mapping


if __name__ == "__main__":
    result = build_topdown_mapping(Path.cwd())
    print(result["manifest"]["coverage"])
