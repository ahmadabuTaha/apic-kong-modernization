"""Deterministic estate-wide Task 015 Observed Function inventory."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .mock import (
    V2_LEFT,
    V2_RIGHT,
    _atomic_json,
    _json_hash,
    _load_jsonl,
    _stable_id,
    _write_jsonl,
    build_gap_register,
    derive_observed_function,
)


FULL_RULES_VERSION = "task015-observed-function-full-v2"
FULL_CACHE_SCHEMA_VERSION = 1
OBSERVED_OUTPUT = Path("indexes/observed_function_inventory.jsonl")
API_GAP_OUTPUT = Path("indexes/task015_api_level_gap_records.jsonl")
GAP_OUTPUT = Path("indexes/task015_full_gap_impact_register.jsonl")
REVIEW_OUTPUT = Path("indexes/task015_full_review_queue.jsonl")
MANIFEST_OUTPUT = Path("indexes/task015_full_manifest.json")
CACHE_DIRECTORY = Path("indexes/cache/task015-observed-full-v2")

_URI = re.compile(r"(?i)\b(?:https?|ftp)://[^\s<>'\"]+")
_SECRET = re.compile(
    r"(?i)\b(password|passwd|client[_-]?secret|api[_-]?key|access[_-]?token)\b\s*[:=]\s*[^\s,;]+"
)


def _file_fingerprint(path: Path) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


def _redact_text(value: str | None) -> tuple[str | None, bool]:
    if value is None:
        return None, False
    redacted = _URI.sub("[REDACTED_URI]", value)
    redacted = _SECRET.sub(lambda match: f"{match.group(1)}=[REDACTED_SECRET]", redacted)
    return redacted, redacted != value


def cache_decision(
    cached: dict[str, Any] | None,
    *,
    operation_fingerprint: str,
    dependency_fingerprint: str,
    rules_version: str = FULL_RULES_VERSION,
) -> str:
    """Return the deterministic reason a full-inventory cache entry is reused or rebuilt."""
    if cached is None:
        return "MISS"
    if cached.get("cache_schema_version") != FULL_CACHE_SCHEMA_VERSION:
        return "INVALIDATED_CACHE_SCHEMA_CHANGE"
    if cached.get("rules_version") != rules_version:
        return "INVALIDATED_RULES_CHANGE"
    if cached.get("dependency_fingerprint") != dependency_fingerprint:
        return "INVALIDATED_DEPENDENCY_CHANGE"
    if cached.get("operation_fingerprint") != operation_fingerprint:
        return "INVALIDATED_OPERATION_CHANGE"
    if not isinstance(cached.get("record"), dict):
        return "INVALIDATED_PARTIAL_CACHE"
    return "HIT"


def _evidence_signals(operation: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[tuple[str, Any]] = [
        ("SOURCE_METHOD", operation["method"]),
        ("SOURCE_PATH", operation["exact_path"]),
        ("SOURCE_OPERATION_ID", operation.get("operation_id")),
        ("SOURCE_SUMMARY", operation.get("summary")),
        ("SOURCE_DESCRIPTION", operation.get("description")),
        ("SOURCE_PARAMETERS", operation["contract"]["parameters"]),
        ("SOURCE_REQUEST_CONTRACT", operation["contract"]["request"]),
        ("SOURCE_RESPONSE_CONTRACT", operation["contract"]["responses"]),
        ("CONFIGURED_OPERATION_SCOPED_BACKEND", operation["configured_backend_facts"]),
        ("CANDIDATE_API_SHARED_BACKEND_CONTEXT", operation["candidate_inherited_backend_context"]),
    ]
    return [
        {
            "evidence_id": _stable_id("task015-evidence", operation["semantic_operation_inventory_id"], kind),
            "evidence_type": kind,
            "present": bool(value),
            "value_fingerprint": _json_hash(value) if value else None,
        }
        for kind, value in signals
    ]


def derive_full_record(
    operation: dict[str, Any],
    api: dict[str, Any],
    *,
    structural_overlap_candidate: bool = False,
) -> dict[str, Any]:
    """Apply the approved mock contract to one accepted Task 014 HTTP operation."""
    record = derive_observed_function(operation, api, ["estate_wide_full_extraction"])
    record["observed_function_id"] = _stable_id(
        "observed-function-full", operation["semantic_operation_inventory_id"]
    )
    record["rules_version"] = FULL_RULES_VERSION
    record["mock_contract_compatibility"] = "ADDITIVE_COMPATIBLE_WITH_TASK015_MOCK_V3"
    record["evidence_signals"] = _evidence_signals(operation)

    redacted_fields = []
    for field in ("summary", "description"):
        original = record["source_facts"].get(field)
        safe, changed = _redact_text(original)
        record["source_facts"][field] = safe
        if changed:
            redacted_fields.append(field)
    record["safe_redaction"] = {
        "applied": bool(redacted_fields),
        "redacted_source_text_fields": redacted_fields,
        "original_text_fingerprints": {
            field: _json_hash(operation.get(field)) for field in redacted_fields
        },
    }
    limitations = []
    if record["missing_information"]:
        limitations.append("SOURCE_METADATA_MISSING")
    if record["backend_evidence"]["candidate_inherited_context_count"]:
        limitations.append("BACKEND_CONTEXT_CANDIDATE_ONLY")
    if record["contradictory_signals"]:
        limitations.append("SOURCE_SIGNALS_CONTRADICT")
    if record["interpretation_status"] in {"AMBIGUOUS_NEEDS_REVIEW", "INSUFFICIENT_EVIDENCE"}:
        limitations.append("FUNCTION_WORDING_REQUIRES_TARGETED_REVIEW")
    record["confidence_limitations"] = sorted(limitations)
    record["candidate_follow_up_sources"] = (
        ["CONFLUENCE_POTENTIAL_UNVERIFIED"]
        if record["interpretation_status"] in {"AMBIGUOUS_NEEDS_REVIEW", "INSUFFICIENT_EVIDENCE"}
        or bool(record["contradictory_signals"])
        else []
    )
    record["confluence_evidence_used"] = False
    if structural_overlap_candidate:
        record["upstream_gap_refs"] = sorted(set(record["upstream_gap_refs"]) | {"task014-gap:structural-overlap-candidates"})
    if operation["canonical_api_id"] in {V2_LEFT, V2_RIGHT}:
        record["upstream_gap_refs"] = sorted(set(record["upstream_gap_refs"]) | {"task014-gap:v2-schema-shape-difference"})
    return record


def build_api_level_gap_records(apis: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for api in apis:
        status = None
        gap_refs: list[str] = []
        if api["source_variant_classification"] == "REGISTRY_ONLY":
            status = "REGISTRY_ONLY_NO_OPERATIONS"
            gap_refs = ["task014-gap:registry-only-no-operations"]
        elif api["operation_count"] == 0:
            status = "NO_SUPPORTED_HTTP_PATHS"
            gap_refs = ["task014-gap:no-supported-path-items"]
        elif api.get("protocol") in {"graphql", "wsdl-to-rest"}:
            status = "UNSUPPORTED_PROTOCOL"
            gap_refs = ["task014-gap:native-protocol-semantics-not-extracted"]
        if status:
            records.append({
                "api_gap_record_id": _stable_id("task015-api-gap", api["canonical_api_id"], status),
                "canonical_api_id": api["canonical_api_id"],
                "status": status,
                "protocol": api.get("protocol"),
                "accepted_http_operation_count": api["operation_count"],
                "gap_refs": gap_refs,
                "source_provenance": api.get("accepted_source"),
                "reviewer_status": "PENDING_REVIEW",
                "fabricated_operation_count": 0,
            })
    return sorted(records, key=lambda value: value["api_gap_record_id"])


def _review_queue(
    records: list[dict[str, Any]],
    api_gaps: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    queue = []
    for record in records:
        if record["interpretation_status"] in {"AMBIGUOUS_NEEDS_REVIEW", "INSUFFICIENT_EVIDENCE"} or record["contradictory_signals"]:
            queue.append({
                "review_item_id": _stable_id("task015-review-full", record["observed_function_id"]),
                "review_type": "OBSERVED_FUNCTION_INTERPRETATION",
                "observed_function_id": record["observed_function_id"],
                "canonical_api_id": record["canonical_api_id"],
                "operation_id": record["task014_operation_record_id"],
                "interpretation_status": record["interpretation_status"],
                "reason": record["certainty_reason"],
                "candidate_follow_up_source": "CONFLUENCE_POTENTIAL_UNVERIFIED",
                "status": "PENDING_REVIEW",
                "responsible_role": "Integration Architect",
            })
    for value in api_gaps:
        queue.append({
            "review_item_id": _stable_id("task015-review-full", value["api_gap_record_id"]),
            "review_type": "API_LEVEL_EVIDENCE_GAP",
            "api_gap_record_id": value["api_gap_record_id"],
            "canonical_api_id": value["canonical_api_id"],
            "api_gap_status": value["status"],
            "reason": "No operation interpretation may be invented beyond accepted Task 014 HTTP records.",
            "candidate_follow_up_source": "CONFLUENCE_POTENTIAL_UNVERIFIED",
            "status": "PENDING_REVIEW",
            "responsible_role": "Integration Architect",
        })
    for value in candidates:
        queue.append({
            "review_item_id": _stable_id("task015-review-full", value["candidate_id"]),
            "review_type": "STRUCTURAL_OVERLAP_SEMANTIC_VALIDATION",
            "candidate_id": value["candidate_id"],
            "left_canonical_api_id": value["left_canonical_api_id"],
            "right_canonical_api_id": value["right_canonical_api_id"],
            "reason": "Structural overlap does not prove functional equivalence or duplication.",
            "candidate_follow_up_source": "CONFLUENCE_POTENTIAL_UNVERIFIED",
            "status": "PENDING_REVIEW",
            "responsible_role": "Integration Architect",
        })
    return sorted(queue, key=lambda value: value["review_item_id"])


def build_full_inventory(
    root: Path,
    *,
    observed_path: Path | None = None,
    api_gap_path: Path | None = None,
    gap_path: Path | None = None,
    review_path: Path | None = None,
    manifest_path: Path | None = None,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    observed_path = observed_path or root / OBSERVED_OUTPUT
    api_gap_path = api_gap_path or root / API_GAP_OUTPUT
    gap_path = gap_path or root / GAP_OUTPUT
    review_path = review_path or root / REVIEW_OUTPUT
    manifest_path = manifest_path or root / MANIFEST_OUTPUT
    cache_dir = cache_dir or root / CACHE_DIRECTORY

    input_paths = {
        "api_inventory": root / "indexes/semantic_api_inventory.jsonl",
        "operation_inventory": root / "indexes/semantic_operation_inventory.jsonl",
        "structural_candidates": root / "indexes/semantic_structural_overlap_candidates.jsonl",
        "task014_manifest": root / "indexes/semantic_cache_manifest.json",
    }
    inputs = {name: {**_file_fingerprint(path), "path": path.relative_to(root).as_posix()} for name, path in input_paths.items()}
    dependency_fingerprint = _json_hash(inputs)
    apis = _load_jsonl(input_paths["api_inventory"])
    operations = _load_jsonl(input_paths["operation_inventory"])
    candidates = _load_jsonl(input_paths["structural_candidates"])
    api_by_id = {value["canonical_api_id"]: value for value in apis}
    candidate_api_ids = {
        api_id
        for value in candidates
        for api_id in (value["left_canonical_api_id"], value["right_canonical_api_id"])
    }

    records = []
    events: Counter[str] = Counter()
    for operation in operations:
        operation_fingerprint = _json_hash(operation)
        suffix = operation["semantic_operation_inventory_id"].rsplit(":", 1)[-1]
        cache_path = cache_dir / f"{suffix}.json"
        cached = None
        if cache_path.is_file():
            try:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                cached = {}
        event = cache_decision(
            cached,
            operation_fingerprint=operation_fingerprint,
            dependency_fingerprint=dependency_fingerprint,
        )
        if event == "HIT":
            record = cached["record"]
        else:
            record = derive_full_record(
                operation,
                api_by_id[operation["canonical_api_id"]],
                structural_overlap_candidate=operation["canonical_api_id"] in candidate_api_ids,
            )
            _atomic_json(cache_path, {
                "cache_schema_version": FULL_CACHE_SCHEMA_VERSION,
                "rules_version": FULL_RULES_VERSION,
                "operation_id": operation["semantic_operation_inventory_id"],
                "operation_fingerprint": operation_fingerprint,
                "dependency_fingerprint": dependency_fingerprint,
                "record": record,
            })
        events[event] += 1
        records.append(record)

    records.sort(key=lambda value: value["observed_function_id"])
    api_gaps = build_api_level_gap_records(apis)
    gaps = build_gap_register(apis, operations, candidates)
    queue = _review_queue(records, api_gaps, candidates)
    _write_jsonl(observed_path, records)
    _write_jsonl(api_gap_path, api_gaps)
    _write_jsonl(gap_path, gaps)
    _write_jsonl(review_path, queue)

    output_values = {
        "observed_functions": (observed_path, len(records)),
        "api_level_gaps": (api_gap_path, len(api_gaps)),
        "gap_register": (gap_path, len(gaps)),
        "review_queue": (review_path, len(queue)),
    }
    outputs = {
        name: {**_file_fingerprint(path), "path": path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name, "record_count": count}
        for name, (path, count) in output_values.items()
    }
    coverage = {
        "accepted_api_count": len(apis),
        "accepted_operation_count": len(operations),
        "observed_function_record_count": len(records),
        "unique_observed_function_id_count": len({value["observed_function_id"] for value in records}),
        "unique_task014_operation_id_count": len({value["task014_operation_record_id"] for value in records}),
        "covered_canonical_api_count": len({value["canonical_api_id"] for value in records}),
        "interpretation_status_counts": dict(sorted(Counter(value["interpretation_status"] for value in records).items())),
        "evidence_strength_counts": dict(sorted(Counter(value["evidence_strength"] for value in records).items())),
        "api_level_gap_status_counts": dict(sorted(Counter(value["status"] for value in api_gaps).items())),
        "review_queue_type_counts": dict(sorted(Counter(value["review_type"] for value in queue).items())),
        "review_queue_count": len(queue),
        "gap_register_count": len(gaps),
        "gap_severity_counts": dict(sorted(Counter(value["severity"] for value in gaps).items())),
        "configured_operation_scoped_count": sum(bool(value["backend_evidence"]["configured_operation_scoped_facts"]) for value in records),
        "candidate_inherited_backend_count": sum(bool(value["backend_evidence"]["candidate_inherited_context_count"]) for value in records),
        "redacted_record_count": sum(value["safe_redaction"]["applied"] for value in records),
        "source_summary_present_count": sum(bool(value["source_facts"].get("summary")) for value in records),
        "source_description_present_count": sum(bool(value["source_facts"].get("description")) for value in records),
        "source_operation_id_present_count": sum(bool(value["source_facts"].get("operation_id")) for value in records),
        "source_request_body_present_count": sum(value["source_facts"]["contract"]["request"]["body_present"] for value in records),
        "source_response_contract_present_count": sum(bool(value["source_facts"]["contract"]["responses"]) for value in records),
        "model_use": "NONE_DETERMINISTIC_RULES_ONLY",
        "model_token_usage": 0,
        "confluence_retrieved": False,
        "functional_duplication_assertions": 0,
        "logical_api_assertions": 0,
        "domain_assertions": 0,
        "capability_assertions": 0,
        "fabricated_operation_count": 0,
    }
    manifest = {
        "rules_version": FULL_RULES_VERSION,
        "cache_schema_version": FULL_CACHE_SCHEMA_VERSION,
        "cache_events": dict(sorted(events.items())),
        "dependency_fingerprint": dependency_fingerprint,
        "inputs": inputs,
        "outputs": outputs,
        "coverage": coverage,
    }
    _atomic_json(manifest_path, manifest)
    return {"records": records, "api_gaps": api_gaps, "gaps": gaps, "review_queue": queue, "manifest": manifest}
