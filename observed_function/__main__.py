from pathlib import Path
import json

from .full_inventory import build_full_inventory


result = build_full_inventory(Path("."))
print(json.dumps(result["manifest"], indent=2, sort_keys=True))
