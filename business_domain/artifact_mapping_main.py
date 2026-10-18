import json
from pathlib import Path

from .artifact_mapping import build_artifact_first_mapping


if __name__ == "__main__":
    result = build_artifact_first_mapping(Path.cwd())
    print(json.dumps(result["manifest"]["coverage"], indent=2, sort_keys=True))
