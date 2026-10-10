from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

from observed_function.full_inventory import (
    FULL_CACHE_SCHEMA_VERSION,
    FULL_RULES_VERSION,
    build_full_inventory,
    cache_decision,
    derive_full_record,
)


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/evidence/task-015/full-extraction"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_full_inventory_reconciles_frozen_task014_and_preserves_boundaries() -> None:
    records = _jsonl(ROOT / "indexes/observed_function_inventory.jsonl")
    api_gaps = _jsonl(ROOT / "indexes/task015_api_level_gap_records.jsonl")
    manifest = json.loads((ROOT / "indexes/task015_full_manifest.json").read_text())
    assert len(records) == 2414
    assert len({value["observed_function_id"] for value in records}) == 2414
    assert len({value["task014_operation_record_id"] for value in records}) == 2414
    assert manifest["coverage"]["accepted_api_count"] == 2036
    assert manifest["coverage"]["accepted_operation_count"] == 2414
    assert manifest["coverage"]["observed_function_record_count"] == 2414
    assert manifest["coverage"]["api_level_gap_status_counts"] == {
        "NO_SUPPORTED_HTTP_PATHS": 5,
        "REGISTRY_ONLY_NO_OPERATIONS": 36,
        "UNSUPPORTED_PROTOCOL": 3,
    }
    assert len(api_gaps) == 44
    assert all(value["reviewer_status"] == "PENDING_REVIEW" for value in records)
    assert all(value["confluence_evidence_used"] is False for value in records)
    assert all(value["logical_function_asserted"] is False for value in records)
    assert all(value["logical_api_asserted"] is False for value in records)
    assert all(value["business_domain_asserted"] is False for value in records)
    assert all(value["business_capability_asserted"] is False for value in records)
    assert all(value["functional_duplication_asserted"] is False for value in records)
    candidates = _jsonl(ROOT / "indexes/semantic_structural_overlap_candidates.jsonl")
    candidate_api_ids = {api_id for value in candidates for api_id in (value["left_canonical_api_id"], value["right_canonical_api_id"])}
    candidate_records = [value for value in records if value["canonical_api_id"] in candidate_api_ids]
    assert candidate_records
    assert all("task014-gap:structural-overlap-candidates" in value["upstream_gap_refs"] for value in candidate_records)
    v2_ids = {
        "apic-identity:sha256:3165d30141993d77200c2630b10c29760e0e1c8f6520eb3368a12d6dd484657e",
        "apic-identity:sha256:6fa70f88ad990dcda279d38753d1e83806dc591c09b74619e945129c553f2aeb",
    }
    assert all("task014-gap:v2-schema-shape-difference" in value["upstream_gap_refs"] for value in records if value["canonical_api_id"] in v2_ids)


def test_source_fidelity_backend_certainty_and_no_fabricated_operations() -> None:
    source = {value["semantic_operation_inventory_id"]: value for value in _jsonl(ROOT / "indexes/semantic_operation_inventory.jsonl")}
    records = _jsonl(ROOT / "indexes/observed_function_inventory.jsonl")
    for record in records:
        operation = source[record["task014_operation_record_id"]]
        assert record["canonical_api_id"] == operation["canonical_api_id"]
        assert record["source_facts"]["method"] == operation["method"]
        assert record["source_facts"]["exact_path"] == operation["exact_path"]
        assert record["source_facts"]["source_provenance"] == operation["source_provenance"]
        assert len(record["evidence_signals"]) == 10
        assert all(value["runtime_usage_proven"] is False for value in record["backend_evidence"]["configured_operation_scoped_facts"])
        assert all(
            value["certainty"] == "CANDIDATE_ONLY"
            and value["proven_operation_egress"] is False
            and value["runtime_usage_proven"] is False
            for value in record["backend_evidence"]["candidate_inherited_context_projection"]
        )
    assert len(records) == len(source)


def test_cache_decision_supports_selective_invalidation() -> None:
    base = {
        "cache_schema_version": FULL_CACHE_SCHEMA_VERSION,
        "rules_version": FULL_RULES_VERSION,
        "operation_fingerprint": "operation-a",
        "dependency_fingerprint": "dependency-a",
        "record": {},
    }
    assert cache_decision(base, operation_fingerprint="operation-a", dependency_fingerprint="dependency-a") == "HIT"
    assert cache_decision(base, operation_fingerprint="operation-b", dependency_fingerprint="dependency-a") == "INVALIDATED_OPERATION_CHANGE"
    assert cache_decision(base, operation_fingerprint="operation-a", dependency_fingerprint="dependency-b") == "INVALIDATED_DEPENDENCY_CHANGE"
    changed = {**base, "rules_version": "different"}
    assert cache_decision(changed, operation_fingerprint="operation-a", dependency_fingerprint="dependency-a") == "INVALIDATED_RULES_CHANGE"


def test_safe_redaction_preserves_fingerprints_without_secret_or_host() -> None:
    operation = copy.deepcopy(_jsonl(ROOT / "indexes/semantic_operation_inventory.jsonl")[0])
    api = next(value for value in _jsonl(ROOT / "indexes/semantic_api_inventory.jsonl") if value["canonical_api_id"] == operation["canonical_api_id"])
    operation["description"] = "Call https://private.example/path client_secret=do-not-emit"
    record = derive_full_record(operation, api)
    assert record["safe_redaction"]["applied"] is True
    assert "https://" not in record["source_facts"]["description"]
    assert "do-not-emit" not in json.dumps(record)
    assert record["safe_redaction"]["original_text_fingerprints"]["description"]


def test_full_build_cold_warm_parity_selective_repair_and_frozen_integrity(tmp_path: Path) -> None:
    frozen = [
        ROOT / "semantic_inventory/full_inventory.py",
        ROOT / "indexes/semantic_api_inventory.jsonl",
        ROOT / "indexes/semantic_operation_inventory.jsonl",
        ROOT / "indexes/semantic_structural_overlap_candidates.jsonl",
        ROOT / "indexes/semantic_cache_manifest.json",
        ROOT / "tests/evidence/task-014/full-extraction/build_manifest.json",
    ]
    before = {path: _hash(path) for path in frozen}
    kwargs = {
        "observed_path": tmp_path / "observed.jsonl",
        "api_gap_path": tmp_path / "api_gaps.jsonl",
        "gap_path": tmp_path / "gaps.jsonl",
        "review_path": tmp_path / "review.jsonl",
        "manifest_path": tmp_path / "manifest.json",
        "cache_dir": tmp_path / "cache",
    }
    cold = build_full_inventory(ROOT, **kwargs)
    output_paths = [kwargs[key] for key in ("observed_path", "api_gap_path", "gap_path", "review_path")]
    cold_hashes = [_hash(path) for path in output_paths]
    warm = build_full_inventory(ROOT, **kwargs)
    assert cold["manifest"]["cache_events"] == {"MISS": 2414}
    assert warm["manifest"]["cache_events"] == {"HIT": 2414}
    assert cold_hashes == [_hash(path) for path in output_paths]
    cache_path = sorted((tmp_path / "cache").glob("*.json"))[0]
    cached = json.loads(cache_path.read_text())
    cached["operation_fingerprint"] = "forced-selective-invalidation"
    cache_path.write_text(json.dumps(cached), encoding="utf-8")
    repaired = build_full_inventory(ROOT, **kwargs)
    assert repaired["manifest"]["cache_events"] == {"HIT": 2413, "INVALIDATED_OPERATION_CHANGE": 1}
    assert cold_hashes == [_hash(path) for path in output_paths]
    assert before == {path: _hash(path) for path in frozen}


def test_committed_evidence_is_deterministic_bounded_and_redacted() -> None:
    command = [str(ROOT / ".venv/bin/python"), str(EVIDENCE / "generate_full_evidence.py")]
    subprocess.run(command, cwd=ROOT, check=True)
    first = {path.name: _hash(path) for path in EVIDENCE.iterdir() if path.is_file()}
    subprocess.run(command, cwd=ROOT, check=True)
    assert first == {path.name: _hash(path) for path in EVIDENCE.iterdir() if path.is_file()}
    samples = _jsonl(EVIDENCE / "representative_findings.jsonl")
    queue = _jsonl(EVIDENCE / "review_queue_sample.jsonl")
    assert 10 <= len(samples) <= 30
    assert len(queue) <= 30
    text = "\n".join(path.read_text(encoding="utf-8") for path in EVIDENCE.iterdir() if path.suffix in {".json", ".jsonl", ".md", ".txt"})
    assert not re.search(r"https?://", text, re.I)
    assert not re.search(r"(?i)(password|passwd|client[_-]?secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s,;]+", text)


def test_local_full_outputs_exclude_known_credential_values_and_uri_hosts() -> None:
    paths = [
        ROOT / "indexes/observed_function_inventory.jsonl",
        ROOT / "indexes/task015_api_level_gap_records.jsonl",
        ROOT / "indexes/task015_full_gap_impact_register.jsonl",
        ROOT / "indexes/task015_full_review_queue.jsonl",
    ]
    payload = b"".join(path.read_bytes() for path in paths)
    sensitive = []
    for path in (ROOT / "staging/credentials").glob("*.json"):
        for item in json.loads(path.read_text(encoding="utf-8")).get("results", []):
            for field in ("client_id", "client_secret", "client_secret_hashed"):
                if isinstance(item.get(field), str) and item[field]:
                    sensitive.append(item[field].encode())
    assert sensitive
    assert all(value not in payload for value in sensitive)
    assert b"http://" not in payload.lower()
    assert b"https://" not in payload.lower()
