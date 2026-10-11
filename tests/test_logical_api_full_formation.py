from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from logical_api.full_formation import OUTPUTS, build_full_formation


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/evidence/task-017/full-extraction"


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_full_operation_ledger_reconciles_task014_task015_and_task016() -> None:
    ledger = jsonl(ROOT / OUTPUTS["operation_disposition"])
    task016 = jsonl(ROOT / "indexes/task016_full_operation_catalog.jsonl")
    operation_ids = [row["task014_operation_id"] for row in ledger]
    assert len(ledger) == len(set(operation_ids)) == 2414
    assert {row["task015_observed_function_id"] for row in ledger} == {
        row["task015_observed_function_id"] for row in task016
    }
    assert sum(not row["task016_comparison_refs"] for row in ledger) == 1481
    assert all(row["source_provenance"]["source_sha256"] for row in ledger)
    assert all(row["logical_api_proposal_ids"] or row["primary_disposition"] in {
        "SINGLETON_UNFORMED", "UNFORMED_INSUFFICIENT"
    } for row in ledger)


def test_api_gaps_are_separate_and_no_http_operations_are_fabricated() -> None:
    coverage = json.loads((EVIDENCE / "estate_coverage_and_disposition.json").read_text())
    assert coverage["task015_api_level_gap_record_count"] == 44
    assert coverage["task015_api_level_gap_status_counts"] == {
        "NO_SUPPORTED_HTTP_PATHS": 5,
        "REGISTRY_ONLY_NO_OPERATIONS": 36,
        "UNSUPPORTED_PROTOCOL": 3,
    }
    assert coverage["registry_only_no_operations"] == 36
    assert coverage["source_backed_no_supported_http_paths"] == 5
    assert coverage["fabricated_http_operation_count"] == 0
    gaps = coverage["api_level_gap_inventory"]
    assert sum(row["source_provenance_status"] != "PRESENT" for row in gaps) == 36
    assert all(row["fabricated_operation_count"] == 0 for row in gaps)


def test_proposals_have_r1_r7_and_independent_decision_axes() -> None:
    proposals = jsonl(ROOT / OUTPUTS["proposals"])
    allowed = {"SUPPORTED", "CONTRADICTED", "NOT_EVIDENCED"}
    assert proposals
    for proposal in proposals:
        assert set(proposal["candidate_rubric"]) == {f"R{i}" for i in range(1, 8)}
        assert all(
            value["status"] in allowed and value["rationale"] and value["evidence_refs"]
            for value in proposal["candidate_rubric"].values()
        )
        assert proposal["three_result_axes"]["technical_validation"] in {"PASS", "FAIL"}
        assert proposal["three_result_axes"]["architect_acceptance"] == "PENDING"
        assert proposal["functional_equivalence_approved"] is False
        assert proposal["transitive_equivalence_inferred"] is False
        for assertion in proposal["direct_member_assertions"]:
            assert set(assertion["criteria"]) == {f"R{i}" for i in range(1, 8)}
            assert assertion["task014_operation_id"] in proposal["member_operation_ids"]
            assert assertion["source_provenance"]["source_sha256"]
            assert assertion["source_provenance"]["source_pointer"]
            exposure = assertion["relationship_exposure_context"]
            assert exposure["consumer_identifiers_omitted"] is True
            assert exposure["operation_consumption_proven"] is False
            assert exposure["runtime_activity_proven"] is False
            assert exposure["subscription_evidence_state"]
    assert all(proposal["proposal_scope"] == "WITHIN_ONE_CURRENT_CANONICAL_APIC_API" for proposal in proposals)


def test_provisional_groups_require_resource_action_and_direct_path_evidence() -> None:
    proposals = jsonl(ROOT / OUTPUTS["proposals"])
    sufficient = [
        proposal for proposal in proposals
        if proposal["three_result_axes"]["evidence_sufficiency"] == "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY"
    ]
    assert len(sufficient) == 5
    for proposal in sufficient:
        assert proposal["candidate_rubric"]["R1"]["status"] == "SUPPORTED"
        assert proposal["candidate_rubric"]["R2"]["status"] == "SUPPORTED"
        assert proposal["candidate_rubric"]["R7"]["status"] == "SUPPORTED"
        assert proposal["candidate_rubric"]["R3"]["status"] == "NOT_EVIDENCED"
        assert proposal["three_result_axes"]["architect_acceptance"] == "PENDING"


def test_operation_intents_preserve_source_operations_and_sc_request() -> None:
    intents = jsonl(ROOT / OUTPUTS["operation_intents"])
    ledger = jsonl(ROOT / OUTPUTS["operation_disposition"])
    intent_sources = {row["source_task014_operation_id"] for row in intents}
    assert intent_sources == {row["task014_operation_id"] for row in ledger}
    assert all(row["distinct_source_operation_preserved"] for row in intents)
    assert all(row["architect_approved"] is False for row in intents)
    sc = jsonl(EVIDENCE / "reviewable_boundary_examples.jsonl")
    sc_case = next(row for row in sc if row["label"] == "SC Request Workflow")
    assert sc_case["frozen_sample_evidence_sufficiency"] == "PARTIAL"
    assert len(sc_case["members"]) == 2
    assert sorted(
        action for member in sc_case["members"] for action in member["supported_actions"]
    ) == ["approve", "cancel", "reject"]
    assert sc_case["full_estate_reassessment"] == "CROSS_API_NOT_FORMED_OR_NO_MATCHING_PROPOSAL"


def test_full_sample_crosscheck_has_no_silent_changes_and_46_cases() -> None:
    cases = jsonl(EVIDENCE / "case_regression_crosscheck.jsonl")
    assert len(cases) == 46
    states = Counter(row["change_state"] for row in cases)
    assert states == {
        "NOT_COMPARABLE_OR_NO_PRIMARY_PROPOSAL": 41,
        "UNCHANGED": 5,
    }
    changed = [row for row in cases if row["change_state"] == "STATUS_DIFFERENCE_REQUIRES_REVIEW"]
    assert changed == []
    assert all(row["architect_acceptance"] == "PENDING" for row in cases)


def test_reviewable_examples_are_bounded_redacted_and_traceable() -> None:
    examples = jsonl(EVIDENCE / "reviewable_boundary_examples.jsonl")
    assert len(examples) == 50
    assert sum(row["example_type"] == "FROZEN_TASK017_REGRESSION_CASE" for row in examples) == 46
    assert sum(row["example_type"] == "FULL_ESTATE_CANONICAL_API_PROPOSAL" for row in examples) == 4
    payload = (EVIDENCE / "reviewable_boundary_examples.jsonl").read_text(encoding="utf-8")
    assert "SC Request Workflow" in payload
    assert "http://" not in payload.lower() and "https://" not in payload.lower()
    assert not re.search(
        r"(?i)(password|passwd|client[_-]?secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s,;]+",
        payload,
    )
    for example in examples:
        assert example["architect_acceptance"] == "PENDING"
        for member in example["members"]:
            assert member["task014_operation_id"]
            assert member["source_provenance"]["source_sha256"]
            assert member["source_provenance"]["source_pointer"]
            assert "backend_path" not in member and "backend_host" not in member


def test_full_formation_regeneration_is_byte_deterministic() -> None:
    paths = [ROOT / path for name, path in OUTPUTS.items() if name != "manifest"]
    paths.extend(
        EVIDENCE / name
        for name in (
            "estate_coverage_and_disposition.json",
            "reviewable_boundary_examples.jsonl",
            "case_regression_crosscheck.jsonl",
        )
    )
    before = {path: digest(path) for path in paths}
    first = build_full_formation(ROOT)
    middle = {path: digest(path) for path in paths}
    second = build_full_formation(ROOT)
    after = {path: digest(path) for path in paths}
    assert before == middle == after
    assert first["manifest"]["summary"] == second["manifest"]["summary"]
    assert first["manifest"]["all_pairs_search_performed"] is False
