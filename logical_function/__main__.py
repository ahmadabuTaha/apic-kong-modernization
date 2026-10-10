import json
from pathlib import Path

from .mock import build_mock


result = build_mock(Path("."))
print(json.dumps(result["manifest"], indent=2, sort_keys=True))
