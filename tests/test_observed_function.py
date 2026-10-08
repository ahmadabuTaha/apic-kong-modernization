from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from observed_function import build_mock


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/evidence/task-015/mock"
V2_IDS = {
    "apic-identity:sha256:3165d30141993d77200c2630b10c29760e0e1c8f6520eb3368a12d6dd484657e",
    "apic-identity:sha256:6fa70f88ad990dcda279d38753d1e83806dc591c09b74619e945129c553f2aeb",
}


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_mock_selection_contract_statuses_and_no_downstream_assertions() -> None:
    records = [json.loads(line) for line in (ROOT / "indexes/observed_function_sample.jsonl").read_text().splitlines()]
    manifest = json.loads((ROOT / "indexes/task015_mock_manifest.json").read_text())
    assert len(records) == 15
    assert len({value["task014_operation_record_id"] for value in records}) == 15
    assert manifest["coverage"]["selected_operation_count"] == 15
    categories = {category.split(":", 1)[0] for values in manifest["selection"]["categories_by_operation"].values() for category in values}
    assert {
        "v2_pair",
        "explicit_description_and_operation_id",
        "missing_text_with_path_and_schema",
        "ambiguous_generic_insufficient",
        "exact_operation_scoped_single_operation",
        "exact_operation_scoped_multi_operation",
        "conditional_multi_target_candidate_context",
        "contradictory_source_semantics",
        "explicitly_technical_operation",
        "structural_overlap_pair",
    } <= categories
    assert {value["category"] for value in manifest["selection"]["api_level_gap_representatives"]} == {"registry_only_no_operations", "source_backed_no_supported_path_items"}
    assert {value["interpretation_status"] for value in records} == {"EXPLICITLY_DESCRIBED", "INFERRED_FROM_MULTIPLE_STRUCTURAL_SIGNALS", "AMBIGUOUS_NEEDS_REVIEW", "INSUFFICIENT_EVIDENCE"}
    assert all(value["reviewer_status"] == "PENDING_REVIEW" for value in records)
    for value in records:
        assert value["source_facts"]["source_provenance"]
        assert value["runtime_usage_proven"] is False
        assert value["logical_function_asserted"] is False
        assert value["logical_api_asserted"] is False
        assert value["business_domain_asserted"] is False
        assert value["business_capability_asserted"] is False
        assert value["functional_duplication_asserted"] is False
        assert all(item["certainty"] == "CANDIDATE_ONLY" and item["proven_operation_egress"] is False for item in value["backend_evidence"]["candidate_inherited_context_projection"])


def test_gap_register_carries_mandatory_impacts_and_exact_baselines() -> None:
    gaps = {value["gap_id"]: value for value in map(json.loads, (ROOT / "indexes/task015_upstream_gap_impact_register.jsonl").open())}
    assert len(gaps) == 11
    assert gaps["task014-gap:missing-summary"]["impacted_record_count"] == 2338
    assert gaps["task014-gap:missing-description"]["impacted_record_count"] == 757
    assert gaps["task014-gap:missing-operationid"]["impacted_record_count"] == 767
    assert gaps["task014-gap:registry-only-no-operations"]["impacted_record_count"] == 36
    assert gaps["task014-gap:no-supported-path-items"]["impacted_record_count"] == 5
    assert gaps["task014-gap:native-protocol-semantics-not-extracted"]["affected_protocol_api_count"] == 3
    assert gaps["task014-gap:unresolved-product-location"]["source_occurrence_count"] == 113
    assert gaps["task014-gap:api-shared-backend-candidate-context"]["impacted_record_count"] == 2282
    assert gaps["task014-gap:structural-overlap-candidates"]["source_candidate_pair_count"] == 60
    assert gaps["task014-gap:v2-schema-shape-difference"]["impacted_record_count"] == 2
    assert all(set(value["downstream_effects"]) == {"015", "016", "017", "018", "019"} for value in gaps.values())
    assert all(value["status"] == "CARRIED_FORWARD" and value["frozen_upstream_evidence_changed"] is False for value in gaps.values())


def test_v2_pair_preserves_difference_evidence_without_duplicate_claim() -> None:
    records = [value for value in map(json.loads, (ROOT / "indexes/observed_function_sample.jsonl").open()) if value["canonical_api_id"] in V2_IDS]
    assert len(records) == 2
    assert {value["candidate_observed_function"]["concise_description"] for value in records} == {"search seasonal visa requests"}
    assert all("task014-gap:v2-schema-shape-difference" in value["upstream_gap_refs"] for value in records)
    assert all(value["functional_duplication_asserted"] is False for value in records)
    safe_diff = json.loads((ROOT / "indexes/task015_mock_manifest.json").read_text())["v2_safe_schema_diff"]
    assert any(value["pointer"].endswith("/SortBy") and value["difference"] == "PRESENCE_DIFFERENCE" for value in safe_diff["request_shape_differences"])
    assert any(value["pointer"].endswith("/InsertDate/type") and value["left"] == "number" and value["right"] == "integer" for value in safe_diff["response_shape_differences"])
    assert safe_diff["semantic_equivalence_conclusion"] == "NOT_MADE_REQUIRES_VALIDATION"


def test_cold_warm_mock_cache_is_deterministic_and_task014_is_frozen(tmp_path: Path) -> None:
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
        "gap_path": tmp_path / "gaps.jsonl",
        "review_path": tmp_path / "review.jsonl",
        "manifest_path": tmp_path / "manifest.json",
        "cache_dir": tmp_path / "cache",
    }
    cold = build_mock(ROOT, **kwargs)
    cold_hashes = {path.name: _hash(path) for path in tmp_path.iterdir() if path.is_file() and path.name != "manifest.json"}
    warm = build_mock(ROOT, **kwargs)
    assert cold["manifest"]["cache_events"] == {"MISS": 15}
    assert warm["manifest"]["cache_events"] == {"HIT": 15}
    assert cold["manifest"]["outputs"] == warm["manifest"]["outputs"]
    assert cold_hashes == {path.name: _hash(path) for path in tmp_path.iterdir() if path.is_file() and path.name != "manifest.json"}
    assert before == {path: _hash(path) for path in frozen}


def test_evidence_generator_is_deterministic_bounded_and_redacted() -> None:
    subprocess.run([str(ROOT / ".venv/bin/python"), str(EVIDENCE / "generate_mock_evidence.py")], cwd=ROOT, check=True)
    first = {path.name: _hash(path) for path in EVIDENCE.iterdir() if path.is_file()}
    subprocess.run([str(ROOT / ".venv/bin/python"), str(EVIDENCE / "generate_mock_evidence.py")], cwd=ROOT, check=True)
    assert first == {path.name: _hash(path) for path in EVIDENCE.iterdir() if path.is_file()}
    committed_gaps = [json.loads(line) for line in (EVIDENCE / "upstream_gap_impact_register.jsonl").read_text().splitlines()]
    assert all(len(value["affected_canonical_api_id_sample"]) <= 8 and len(value["affected_operation_id_sample"]) <= 8 for value in committed_gaps)
    text = "\n".join(path.read_text(encoding="utf-8") for path in EVIDENCE.iterdir() if path.suffix in {".json", ".jsonl", ".md", ".txt"})
    assert not re.search(r"https?://", text, re.I)
    assert not re.search(r"(?i)(password|passwd|client[_-]?secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s,;]+", text)


def test_local_mock_outputs_exclude_source_credential_values() -> None:
    payload = (ROOT / "indexes/observed_function_sample.jsonl").read_bytes() + (ROOT / "indexes/task015_upstream_gap_impact_register.jsonl").read_bytes()
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
