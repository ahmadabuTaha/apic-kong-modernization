from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from logical_function import build_mock


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/evidence/task-016/mock"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_mock_selection_statuses_and_hard_boundaries() -> None:
    comparisons = _jsonl(ROOT / "indexes/task016_mock_candidate_comparisons.jsonl")
    manifest = json.loads((ROOT / "indexes/task016_mock_manifest.json").read_text())
    assert len(comparisons) == 10
    assert len({value["comparison_id"] for value in comparisons}) == 10
    assert manifest["status_distribution"] == {
        "CLEARLY_DIFFERENT_SUPPORTED": 2,
        "NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE": 1,
        "POSSIBLE_SAME_LOGICAL_FUNCTION": 4,
        "REVIEW_REQUIRED_CONFLICTING_SIGNALS": 3,
    }
    assert manifest["structural_candidate_pair_count"] == 8
    assert manifest["indexed_negative_control_count"] == 2
    assert manifest["full_estate_grouping_performed"] is False
    categories = {item for value in comparisons for item in value["sample_categories"]}
    assert {"V2_REQUIRED", "DIFFERENT_NAMES", "SAME_BACKEND_DIFFERING_ACTION_OR_PAYLOAD", "TASK015_AMBIGUOUS", "TASK015_INSUFFICIENT", "MULTI_OPERATION_APIS", "TECHNICAL_SECURITY", "NEGATIVE_CONTROL"} <= categories
    for value in comparisons:
        assert value["reviewer_status"] == "PENDING_REVIEW"
        assert value["status_is_proposal_not_approval"] is True
        assert value["left"]["canonical_api_id"] != value["right"]["canonical_api_id"]
        assert value["canonical_apis_merged"] is False
        assert value["operations_collapsed"] is False
        assert value["confirmed_duplicate"] is False
        assert value["safe_replacement_asserted"] is False
        assert value["runtime_equivalence_asserted"] is False
        assert value["logical_api_asserted"] is False


def test_provenance_task015_links_and_backend_certainty_are_preserved() -> None:
    operations = {value["semantic_operation_inventory_id"]: value for value in _jsonl(ROOT / "indexes/semantic_operation_inventory.jsonl")}
    observed = {value["observed_function_id"]: value for value in _jsonl(ROOT / "indexes/observed_function_inventory.jsonl")}
    comparisons = _jsonl(ROOT / "indexes/task016_mock_candidate_comparisons.jsonl")
    for comparison in comparisons:
        for side in ("left", "right"):
            value = comparison[side]
            source = operations[value["task014_operation_id"]]
            assert value["task015_observed_function_id"] in observed
            assert observed[value["task015_observed_function_id"]]["task014_operation_record_id"] == value["task014_operation_id"]
            assert value["source_provenance"] == source["source_provenance"]
            assert value["source_variant_fingerprint"] == source["source_variant_fingerprint"]
            assert value["method"] == source["method"]
            assert value["exact_path"] == source["exact_path"]
            backend = value["backend_evidence"]
            assert backend["runtime_usage_proven"] is False
            assert backend["operation_egress_proven"] is False
            if backend["candidate_api_shared_count"]:
                assert backend["candidate_certainty"] == "CANDIDATE_ONLY"


def test_v2_uses_actual_safe_schema_differences_without_replacement_claim() -> None:
    comparison = next(value for value in _jsonl(ROOT / "indexes/task016_mock_candidate_comparisons.jsonl") if value["selection_key"] == "seasonal_visa_v2_contract_change")
    safe = comparison["actual_safe_schema_comparison"]
    assert comparison["comparison_status"] == "POSSIBLE_SAME_LOGICAL_FUNCTION"
    assert {comparison["left"]["canonical_api_id"], comparison["right"]["canonical_api_id"]} == {
        "apic-identity:sha256:3165d30141993d77200c2630b10c29760e0e1c8f6520eb3368a12d6dd484657e",
        "apic-identity:sha256:6fa70f88ad990dcda279d38753d1e83806dc591c09b74619e945129c553f2aeb",
    }
    assert any(value["pointer"].endswith("/SortBy") and value["difference"] == "PRESENCE_DIFFERENCE" for value in safe["request_shape_differences"])
    assert any(value["pointer"].endswith("/InsertDate/type") and {value["left"], value["right"]} == {"number", "integer"} for value in safe["response_shape_differences"])
    assert comparison["confirmed_duplicate"] is False
    assert comparison["safe_replacement_asserted"] is False


def test_controls_prevent_false_positive_and_preserve_missing_evidence() -> None:
    comparisons = {value["selection_key"]: value for value in _jsonl(ROOT / "indexes/task016_mock_candidate_comparisons.jsonl")}
    assert comparisons["technical_health_vs_token"]["comparison_status"] == "CLEARLY_DIFFERENT_SUPPORTED"
    assert comparisons["payment_token_generate_vs_delete"]["comparison_status"] == "CLEARLY_DIFFERENT_SUPPORTED"
    missing = comparisons["root_get_missing_evidence"]
    assert missing["comparison_status"] == "NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE"
    assert "SOURCE_EVIDENCE_NOT_AVAILABLE" in missing["limitations"]
    assert missing["left"]["task015_interpretation_status"] == "INSUFFICIENT_EVIDENCE"
    assert missing["right"]["task015_interpretation_status"] == "INSUFFICIENT_EVIDENCE"
    assert comparisons["appointment_action_conflict"]["comparison_status"] == "REVIEW_REQUIRED_CONFLICTING_SIGNALS"


def test_deterministic_replay_and_frozen_task014_task015_source_integrity(tmp_path: Path) -> None:
    frozen = [
        ROOT / "semantic_inventory/full_inventory.py",
        ROOT / "observed_function/full_inventory.py",
        ROOT / "indexes/semantic_api_inventory.jsonl",
        ROOT / "indexes/semantic_operation_inventory.jsonl",
        ROOT / "indexes/semantic_structural_overlap_candidates.jsonl",
        ROOT / "indexes/observed_function_inventory.jsonl",
        ROOT / "indexes/task015_full_gap_impact_register.jsonl",
        ROOT / "tests/evidence/task-014/full-extraction/build_manifest.json",
        ROOT / "tests/evidence/task-015/full-extraction/build_manifest.json",
    ]
    local_manifest = json.loads((ROOT / "indexes/task016_mock_manifest.json").read_text())
    frozen.extend(ROOT / value["path"] for value in local_manifest["inputs"]["targeted_source_documents"])
    before = {path: _hash(path) for path in frozen}
    kwargs = {
        "comparison_path": tmp_path / "comparisons.jsonl",
        "review_path": tmp_path / "review.jsonl",
        "manifest_path": tmp_path / "manifest.json",
    }
    first = build_mock(ROOT, **kwargs)
    hashes = {path.name: _hash(path) for path in tmp_path.iterdir()}
    second = build_mock(ROOT, **kwargs)
    assert first["manifest"]["status_distribution"] == second["manifest"]["status_distribution"]
    assert hashes == {path.name: _hash(path) for path in tmp_path.iterdir()}
    assert before == {path: _hash(path) for path in frozen}


def test_evidence_generator_is_deterministic_and_redacted() -> None:
    command = [str(ROOT / ".venv/bin/python"), str(EVIDENCE / "generate_mock_evidence.py")]
    subprocess.run(command, cwd=ROOT, check=True)
    first = {path.name: _hash(path) for path in EVIDENCE.iterdir() if path.is_file()}
    subprocess.run(command, cwd=ROOT, check=True)
    assert first == {path.name: _hash(path) for path in EVIDENCE.iterdir() if path.is_file()}
    text = "\n".join(path.read_text(encoding="utf-8") for path in EVIDENCE.iterdir() if path.suffix in {".json", ".jsonl", ".md", ".txt"})
    assert not re.search(r"https?://", text, re.I)
    assert not re.search(r"(?i)(password|passwd|client[_-]?secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s,;]+", text)


def test_local_outputs_exclude_known_credential_values_and_hosts() -> None:
    payload = (ROOT / "indexes/task016_mock_candidate_comparisons.jsonl").read_bytes() + (ROOT / "indexes/task016_mock_review_queue.jsonl").read_bytes()
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
