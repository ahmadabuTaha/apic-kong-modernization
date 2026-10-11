import json
from pathlib import Path

from .refinement import build_refinement


result = build_refinement(Path("."))
print(json.dumps(result["manifest"], indent=2, sort_keys=True))
