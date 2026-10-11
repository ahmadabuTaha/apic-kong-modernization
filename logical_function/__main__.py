import json
from pathlib import Path

from .full_inventory import build_full


result = build_full(Path("."))
print(json.dumps(result["manifest"], indent=2, sort_keys=True))
