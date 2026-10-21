"""CLI for Phase 6 / Task 019-B all-module inventory normalization."""

import argparse
import json
from pathlib import Path

from .inventory_normalization import build_all_modules_inventory


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize all Modules for Phase 6 Task 019-B")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--input", type=Path)
    parser.add_argument("--index-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    result = build_all_modules_inventory(args.root, args.input, args.index_dir, args.output_dir)
    print(json.dumps(result["manifest"]["counts"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
