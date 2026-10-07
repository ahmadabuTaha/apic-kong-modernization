"""Generate deterministic architecture-review evidence for Phase 3 Task 008."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from relationship_builder import APPROVED_RELATIONSHIP_TYPES, build_relationships


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _samples(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        by_type[edge["relationship_type"]].append(edge)

    samples: list[dict[str, Any]] = []
    for relationship_type in APPROVED_RELATIONSHIP_TYPES:
        candidates = by_type.get(relationship_type, [])
        if not candidates:
            continue
        selected: list[dict[str, Any]] = []
        for category_pattern in (
            ["authoritative_artifact", "registry_reference"],
            ["authoritative_artifact"],
            ["registry_reference"],
        ):
            candidate = next(
                (
                    edge
                    for edge in candidates
                    if edge["evidence_source_categories"] == category_pattern
                    and edge not in selected
                ),
                None,
            )
            if candidate is not None:
                selected.append(candidate)
        if not selected:
            selected.append(candidates[0])
        samples.extend(selected)
    return samples


def generate(
    phase2_path: Path, phase1_path: Path, output_directory: Path
) -> dict[str, Any]:
    phase2 = json.loads(phase2_path.read_text(encoding="utf-8"))
    result = build_relationships(phase2, _load_jsonl(phase1_path))
    samples = _samples(result["edges"])
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "relationship_counts.json").write_text(
        json.dumps(result["summary"], ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (output_directory / "relationship_coverage.json").write_text(
        json.dumps(result["coverage"], ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (output_directory / "relationship_samples.jsonl").write_text(
        "".join(
            json.dumps(sample, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for sample in samples
        ),
        encoding="utf-8",
    )
    return {
        "summary": result["summary"],
        "coverage": result["coverage"],
        "sample_count": len(samples),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase2",
        type=Path,
        default=Path("indexes/apic_identity_resolution.json"),
    )
    parser.add_argument(
        "--phase1", type=Path, default=Path("indexes/extracted_records.jsonl")
    )
    parser.add_argument(
        "--output-directory", type=Path, default=Path("tests/evidence/task-008")
    )
    args = parser.parse_args()
    result = generate(args.phase2, args.phase1, args.output_directory)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
