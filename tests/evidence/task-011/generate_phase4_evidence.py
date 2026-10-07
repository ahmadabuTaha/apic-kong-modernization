"""Generate deterministic review evidence for Phase 4 Task 011."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend_target_resolver import build_resolution_indexes  # noqa: E402


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _safe_sample(record: dict, scenario: str, interpretation: str) -> dict:
    return {
        "scenario": scenario,
        "target_observation_id": record["target_observation_id"],
        "canonical_api_id": record["canonical_api_id"],
        "api_name": record["api_name"],
        "api_version": record["api_version"],
        "source_path": record["source_path"],
        "source_pointer": record["source_pointer"],
        "operation_scope": record["operation_scope"],
        "scope_classification": record["scope_classification"],
        "invocation_mechanism": record["invocation_mechanism"],
        "invoke_title": record["invoke_title"],
        "http_verb": record["http_verb"],
        "backend_type": record["backend_type"],
        "symbolic_property_tokens": record["symbolic_property_tokens"],
        "property_lookup_results": record["property_lookup_results"],
        "target_path_suffix_or_template": record["target_path_suffix_or_template"],
        "target_classification": record["target_classification"],
        "resolution_status": record["resolution_status"],
        "resolution_reason": record["resolution_reason"],
        "evidence_state": record["evidence_state"],
        "expected_review_interpretation": interpretation,
        "infrastructure_value_omitted_from_committed_evidence": True,
    }


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(root: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="task-011-") as temporary:
        temp = Path(temporary)
        cold = build_resolution_indexes(
            root,
            property_index_path=temp / "catalog_properties.jsonl",
            target_index_path=temp / "backend_target_resolution.jsonl",
            cache_path=temp / "cache.sqlite3",
        )
        cold_property_hash = _hash(temp / "catalog_properties.jsonl")
        cold_target_hash = _hash(temp / "backend_target_resolution.jsonl")
        warm = build_resolution_indexes(
            root,
            property_index_path=temp / "catalog_properties.jsonl",
            target_index_path=temp / "backend_target_resolution.jsonl",
            cache_path=temp / "cache.sqlite3",
        )
        warm_property_hash = _hash(temp / "catalog_properties.jsonl")
        warm_target_hash = _hash(temp / "backend_target_resolution.jsonl")

    records = cold.pop("records")
    warm.pop("records")
    property_summary = cold["property_summary"]
    target_summary = cold["target_summary"]
    pattern_inventory = cold["pattern_inventory"]

    resolved = next(
        item
        for item in records
        if item["target_classification"] == "CATALOG_PROPERTY_RESOLVED"
        and item["target_path_suffix_or_template"]
    )
    missing = next(
        item
        for item in records
        if any(
            lookup["lookup_status"] == "MISSING"
            for lookup in item["property_lookup_results"]
        )
    )
    protected = next(
        item
        for item in records
        if any(
            lookup["lookup_status"] == "PROTECTED_OR_REDACTED"
            for lookup in item["property_lookup_results"]
        )
    )
    operation = next(item for item in records if item["operation_scope"])
    static = next(item for item in records if item["target_classification"] == "STATIC_LITERAL")
    mixed = next(item for item in records if item["target_classification"] == "MIXED_PARAMETERIZED")
    samples = [
        _safe_sample(resolved, "catalog_property_resolved", "Exact symbolic token matched one safe catalog property; infrastructure value is intentionally omitted from committed evidence."),
        _safe_sample(missing, "missing_catalog_property", "At least one exact symbolic token has no catalog-property record and remains unresolved."),
        _safe_sample(protected, "protected_or_redacted_catalog_property", "The property exists but its sensitive value is not exposed or used for concrete resolution."),
        _safe_sample(operation, "operation_scoped_invoke", "Operation verb/path scope is preserved from an explicit operation-switch case."),
        _safe_sample(static, "static_literal", "Explicit literal invocation target is preserved as configuration evidence, not runtime-use evidence."),
        _safe_sample(mixed, "mixed_parameterized", "Resolved and unresolved/runtime portions remain explicitly mixed; no concrete target is fabricated."),
    ]
    samples.sort(key=lambda item: item["scenario"])

    cache_performance = {
        "cache_schema_version": cold["cache"]["cache_schema_version"],
        "parser_version": cold["cache"]["parser_version"],
        "cold": {
            "property_file_parse_seconds": cold["cache"]["property_file_parse_seconds"],
            "target_resolution_build_seconds": cold["cache"]["build_seconds"],
            "files_parsed": cold["cache"]["files_parsed"],
            "parsed_source_cache_hits": cold["cache"]["parsed_source_cache_hits"],
            "resolution_cache_hits": cold["cache"]["resolution_cache_hits"],
            "resolution_cache_misses": cold["cache"]["resolution_cache_misses"],
        },
        "warm": {
            "property_file_parse_seconds": warm["cache"]["property_file_parse_seconds"],
            "cached_build_seconds": warm["cache"]["build_seconds"],
            "files_reparsed": warm["cache"]["files_parsed"],
            "parsed_source_cache_hits": warm["cache"]["parsed_source_cache_hits"],
            "resolution_cache_hits": warm["cache"]["resolution_cache_hits"],
            "resolution_cache_misses": warm["cache"]["resolution_cache_misses"],
        },
        "cold_property_index_sha256": cold_property_hash,
        "warm_property_index_sha256": warm_property_hash,
        "cold_target_index_sha256": cold_target_hash,
        "warm_target_index_sha256": warm_target_hash,
        "property_output_identical": cold_property_hash == warm_property_hash,
        "target_output_identical": cold_target_hash == warm_target_hash,
        "warm_avoided_all_yaml_reparsing": warm["cache"]["files_parsed"] == 0,
    }
    _write_json(output / "catalog_property_summary.json", property_summary)
    _write_json(output / "target_resolution_summary.json", target_summary)
    _write_json(output / "target_pattern_inventory.json", pattern_inventory)
    _write_json(output / "cache_performance.json", cache_performance)
    (output / "target_resolution_samples.jsonl").write_text(
        "".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for item in samples
        ),
        encoding="utf-8",
    )
    return {
        "property_summary": property_summary,
        "target_summary": target_summary,
        "cache_performance": cache_performance,
        "sample_count": len(samples),
        "overall_pass": all(
            (
                property_summary["catalog_property_record_count"] == 326,
                target_summary["total_canonical_apis"] == 2036,
                target_summary["apis_inspected"] == 2036,
                cold["cache"]["files_parsed"] == 2000,
                warm["cache"]["files_parsed"] == 0,
                warm["cache"]["resolution_cache_hits"] == 2000,
                cache_performance["property_output_identical"],
                cache_performance["target_output_identical"],
            )
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    result = generate(args.root.resolve(), args.output.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
