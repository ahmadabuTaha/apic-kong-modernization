from __future__ import annotations

import json
from pathlib import Path

from .full_formation import build_full_formation


if __name__ == "__main__":
    result = build_full_formation(Path.cwd())
    print(json.dumps(result["manifest"]["summary"], sort_keys=True, indent=2))
