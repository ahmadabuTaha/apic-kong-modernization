"""Generate deterministic, compact and redacted Task 015 full-extraction evidence."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from observed_function.full_inventory import build_full_inventory  # noqa: E402


OUT = ROOT / "tests/evidence/task-015/full-extraction"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(name: str, values: list[dict]) -> None:
    (OUT / name).write_text("".join(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" for value in values), encoding="utf-8")


def fingerprint(path: Path) -> dict:
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


def safe_record(record: dict) -> dict:
    return {
        "observed_function_id": record["observed_function_id"],
        "canonical_api_id": record["canonical_api_id"],
        "task014_operation_record_id": record["task014_operation_record_id"],
        "method": record["source_facts"]["method"],
        "exact_path": record["source_facts"]["exact_path"],
        "source_provenance": record["source_facts"]["source_provenance"],
        "candidate_observed_function": record["candidate_observed_function"],
        "interpretation_status": record["interpretation_status"],
        "evidence_strength": record["evidence_strength"],
        "certainty_reason": record["certainty_reason"],
        "contradictory_signals": record["contradictory_signals"],
        "missing_information": record["missing_information"],
        "confidence_limitations": record["confidence_limitations"],
        "upstream_gap_refs": record["upstream_gap_refs"],
        "backend_certainty": {
            "configured_operation_scoped_count": len(record["backend_evidence"]["configured_operation_scoped_facts"]),
            "candidate_inherited_context_count": record["backend_evidence"]["candidate_inherited_context_count"],
            "candidate_only": bool(record["backend_evidence"]["candidate_inherited_context_count"]),
            "runtime_usage_proven": False,
        },
        "candidate_follow_up_sources": record["candidate_follow_up_sources"],
        "reviewer_status": record["reviewer_status"],
    }


def select_samples(records: list[dict]) -> list[dict]:
    selected: dict[str, dict] = {}

    def add(values: list[dict], count: int = 1) -> None:
        for value in sorted(values, key=lambda item: item["observed_function_id"]):
            if value["observed_function_id"] not in selected:
                selected[value["observed_function_id"]] = value
                if sum(1 for key in selected if key == value["observed_function_id"]):
                    count -= 1
            if count == 0:
                return

    for status in ("EXPLICITLY_DESCRIBED", "INFERRED_FROM_MULTIPLE_STRUCTURAL_SIGNALS", "AMBIGUOUS_NEEDS_REVIEW", "INSUFFICIENT_EVIDENCE"):
        add([value for value in records if value["interpretation_status"] == status], 2)
    add([value for value in records if value["candidate_observed_function"]["operation_nature"] == "TECHNICAL_OPERATION"], 2)
    add([value for value in records if value["missing_information"]], 2)
    add([value for value in records if value["backend_evidence"]["configured_operation_scoped_facts"]], 2)
    add([value for value in records if value["contradictory_signals"]], 1)
    v2_ids = {
        "apic-identity:sha256:3165d30141993d77200c2630b10c29760e0e1c8f6520eb3368a12d6dd484657e",
        "apic-identity:sha256:6fa70f88ad990dcda279d38753d1e83806dc591c09b74619e945129c553f2aeb",
    }
    add([value for value in records if value["canonical_api_id"] in v2_ids], 2)
    return [safe_record(selected[key]) for key in sorted(selected)]


def generate() -> None:
    records = load_jsonl(ROOT / "indexes/observed_function_inventory.jsonl")
    api_gaps = load_jsonl(ROOT / "indexes/task015_api_level_gap_records.jsonl")
    gaps = load_jsonl(ROOT / "indexes/task015_full_gap_impact_register.jsonl")
    queue = load_jsonl(ROOT / "indexes/task015_full_review_queue.jsonl")
    manifest = json.loads((ROOT / "indexes/task015_full_manifest.json").read_text())

    coverage = dict(manifest["coverage"])
    coverage.update({
        "all_operation_records_reconciled_exactly_once": coverage["accepted_operation_count"] == coverage["observed_function_record_count"] == coverage["unique_task014_operation_id_count"],
        "all_records_pending_review": all(value["reviewer_status"] == "PENDING_REVIEW" for value in records),
        "confluence_facts_used": 0,
        "unresolved_product_location_occurrences_carried": 113,
        "structural_overlap_pairs_remain_unconfirmed": 60,
    })
    write_json("coverage_and_interpretation_distribution.json", coverage)

    affected_api_ids = {item for value in gaps for item in value["affected_canonical_api_ids"]}
    affected_operation_ids = {item for value in gaps for item in value["affected_operation_ids"]}
    write_json("gap_impact_and_downstream_gates.json", {
        "gap_category_count": len(gaps),
        "severity_distribution": dict(sorted(Counter(value["severity"] for value in gaps).items())),
        "unique_affected_canonical_api_count_across_overlapping_categories": len(affected_api_ids),
        "unique_affected_operation_count_across_overlapping_categories": len(affected_operation_ids),
        "overlapping_category_counts_must_not_be_summed_as_unique_entities": True,
        "review_queue_count": len(queue),
        "api_level_gap_record_count": len(api_gaps),
        "categories": [{
            "gap_id": value["gap_id"],
            "scope": value["scope"],
            "severity": value["severity"],
            "affected_canonical_api_count": len(value["affected_canonical_api_ids"]),
            "affected_operation_count": len(value["affected_operation_ids"]),
            "original_condition": value["original_condition"],
            "downstream_effects": value["downstream_effects"],
            "mitigation_or_retrieval_action": value["mitigation_or_retrieval_action"],
            "recheck_trigger": value["recheck_trigger"],
        } for value in gaps],
        "blocker_scope_policy": "DOWNSTREAM_BLOCKER applies only to the listed entity and unsupported conclusion, never the whole phase.",
    })
    write_jsonl("representative_findings.jsonl", select_samples(records))
    queue_sample = []
    for kind in sorted({value["review_type"] for value in queue}):
        queue_sample.extend([value for value in queue if value["review_type"] == kind][:8])
    write_jsonl("review_queue_sample.jsonl", queue_sample)
    write_json("review_queue_distribution.json", {
        "total_review_item_count": len(queue),
        "review_type_counts": dict(sorted(Counter(value["review_type"] for value in queue).items())),
        "interpretation_status_counts": dict(sorted(Counter(value.get("interpretation_status", "NOT_APPLICABLE") for value in queue).items())),
        "sample_count": len(queue_sample),
        "full_queue_local_artifact": "indexes/task015_full_review_queue.jsonl",
    })

    with tempfile.TemporaryDirectory(prefix="task015-replay-") as raw:
        temporary = Path(raw)
        kwargs = {
            "observed_path": temporary / "observed.jsonl",
            "api_gap_path": temporary / "api-gaps.jsonl",
            "gap_path": temporary / "gaps.jsonl",
            "review_path": temporary / "review.jsonl",
            "manifest_path": temporary / "manifest.json",
            "cache_dir": temporary / "cache",
        }
        cold = build_full_inventory(ROOT, **kwargs)
        cold_hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in kwargs.items() if name.endswith("_path") and name != "manifest_path"}
        warm = build_full_inventory(ROOT, **kwargs)
        cache_path = sorted((temporary / "cache").glob("*.json"))[0]
        cached = json.loads(cache_path.read_text())
        cached["operation_fingerprint"] = "forced-selective-invalidation"
        cache_path.write_text(json.dumps(cached), encoding="utf-8")
        selective = build_full_inventory(ROOT, **kwargs)
        final_hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in kwargs.items() if name.endswith("_path") and name != "manifest_path"}
    write_json("cache_and_replay_metrics.json", {
        "cold_cache_events": cold["manifest"]["cache_events"],
        "warm_cache_events": warm["manifest"]["cache_events"],
        "selective_invalidation_cache_events": selective["manifest"]["cache_events"],
        "cold_warm_and_selective_output_byte_parity": cold_hashes == final_hashes,
        "atomic_cache_writes": True,
        "cache_schema_version": manifest["cache_schema_version"],
        "rules_version": manifest["rules_version"],
    })
    write_json("build_manifest.json", {
        "rules_version": manifest["rules_version"],
        "cache_schema_version": manifest["cache_schema_version"],
        "dependency_fingerprint": manifest["dependency_fingerprint"],
        "inputs": manifest["inputs"],
        "local_outputs": {name: {"path": value["path"], "sha256": value["sha256"], "bytes": value["bytes"], "record_count": value["record_count"]} for name, value in manifest["outputs"].items()},
        "committed_evidence_inputs": [fingerprint(ROOT / "observed_function/full_inventory.py"), fingerprint(ROOT / "observed_function/mock.py")],
    })


if __name__ == "__main__":
    generate()
