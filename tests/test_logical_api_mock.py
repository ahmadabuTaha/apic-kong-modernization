from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/evidence/task-017/mock"


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_bounded_diverse_sample_and_stable_traceable_members() -> None:
    cases = jsonl(EVIDENCE / "representative_boundary_cases.jsonl")
    assert len(cases) == 10
    assert {v["disposition"] for v in cases} == {
        "COHESIVE_LOGICAL_API_CANDIDATE", "PARTIAL_OR_VARIANT_BOUNDARY_REVIEW",
        "INSUFFICIENT_EVIDENCE_TO_FORM", "SEPARATE_LOGICAL_APIS_SUPPORTED",
    }
    for case in cases:
        assert case["logical_api_candidate_id"].startswith("logical-api-proposal:sha256:")
        member_ids = [v["task014_operation_id"] for v in case["candidate_members"]]
        assert len(member_ids) == len(set(member_ids))
        assert {v["member_operation_id"] for v in case["membership_graph"]} == set(member_ids)
        for member in case["candidate_members"]:
            assert member["canonical_api_id"].startswith("apic-identity:sha256:")
            assert member["task015_observed_function_id"].startswith("observed-function-full:sha256:")
            assert member["source_provenance"]["source_pointer"].startswith("/paths/")
            assert len(member["source_provenance"]["source_sha256"]) == 64


def test_cohesion_and_functional_equivalence_are_independent_and_actions_not_collapsed() -> None:
    cases = jsonl(EVIDENCE / "representative_boundary_cases.jsonl")
    sc = next(v for v in cases if v["provisional_business_neutral_label"] == "SC Request Workflow")
    assert sc["formation_asserted"] is True
    assert {v["action"] for v in sc["intended_logical_operations"]} >= {"approve", "reject", "cancel"}
    assert len({v["logical_operation_id"] for v in sc["intended_logical_operations"]}) == len(sc["intended_logical_operations"])
    training = next(v for v in cases if v["provisional_business_neutral_label"] == "Establishment Training Disclosure")
    assert training["functional_equivalence"]["task016_refinement_verdict"] == "DIFFERENT_BUSINESS_ACTION_SUPPORTED"
    assert training["logical_api_cohesion"]["status"] == "COHESIVE_LOGICAL_API_CANDIDATE"
    for case in cases:
        assert case["functional_equivalence"]["equivalence_approved"] is False
        assert case["functional_equivalence"]["member_ids_collapsed"] is False


def test_no_transitive_fallacy_or_unresolved_evidence_promotion() -> None:
    cases = jsonl(EVIDENCE / "representative_boundary_cases.jsonl")
    for case in cases:
        assert case["transitive_equivalence_inferred"] is False
        assert case["unresolved_members_contaminate_group_certainty"] is False
        for member in case["candidate_members"]:
            assert member["runtime_activity_proven"] is False
            assert member["operation_consumption_proven"] is False
            assert member["backend_context"]["runtime_egress_proven"] is False
    bulk = next(v for v in cases if v["provisional_business_neutral_label"] == "Bulk Contract Workflow")
    assert len(bulk["candidate_members"]) == 4
    assert any(v["interpretation_status"] == "INSUFFICIENT_EVIDENCE" for v in bulk["candidate_members"])
    assert bulk["disposition"] == "PARTIAL_OR_VARIANT_BOUNDARY_REVIEW"


def test_false_positive_nonformation_product_and_decision_guardrails() -> None:
    cases = jsonl(EVIDENCE / "representative_boundary_cases.jsonl")
    appointment = next(v for v in cases if v["provisional_business_neutral_label"] == "Appointment Status Workflow")
    assert appointment["formation_asserted"] is False
    assert appointment["functional_equivalence"]["task016_refinement_verdict"] == "CONFLICTING_SEMANTICS_REVIEW"
    technical = next(v for v in cases if v["disposition"] == "SEPARATE_LOGICAL_APIS_SUPPORTED")
    assert technical["formation_asserted"] is False
    for case in cases:
        assert case["domain_assignment"] is None
        assert case["capability_assignment"] is None
        assert case["kong_topology"] is None
        assert case["retirement_decision"] is None
        assert case["migration_safety"] == "NOT_ASSESSED_OR_AUTHORIZED"
        assert all(member["product_is_logical_api"] is False for member in case["candidate_members"])
        if not case["formation_asserted"]:
            assert all(v["assertion_status"] == "NOT_ASSERTED_NONFORMATION_CASE" for v in case["membership_graph"])


def test_deterministic_regeneration_preserves_frozen_inputs_and_redacts_outputs() -> None:
    frozen = [
        ROOT / "indexes/semantic_api_inventory.jsonl", ROOT / "indexes/semantic_operation_inventory.jsonl",
        ROOT / "indexes/observed_function_inventory.jsonl", ROOT / "indexes/task016_semantic_refinement_pairs.jsonl",
        ROOT / "indexes/task016_semantic_refinement_focused_cases.jsonl", ROOT / "logical_function/refinement.py",
    ]
    before = {path: digest(path) for path in frozen}
    command = [str(ROOT / ".venv/bin/python"), str(EVIDENCE / "generate_mock_evidence.py")]
    subprocess.run(command, cwd=ROOT, check=True)
    first = {path.name: digest(path) for path in EVIDENCE.iterdir() if path.is_file()}
    subprocess.run(command, cwd=ROOT, check=True)
    assert first == {path.name: digest(path) for path in EVIDENCE.iterdir() if path.is_file()}
    assert before == {path: digest(path) for path in frozen}
    payload = b"".join(path.read_bytes() for path in EVIDENCE.iterdir() if path.is_file())
    assert b"http://" not in payload.lower()
    assert b"https://" not in payload.lower()
    text = payload.decode("utf-8")
    assert not re.search(r"(?i)(password|passwd|client[_-]?secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s,;]+", text)


def test_review_queue_is_bounded_and_does_not_require_all_pairs() -> None:
    cases = jsonl(EVIDENCE / "representative_boundary_cases.jsonl")
    queue = jsonl(EVIDENCE / "review_queue.jsonl")
    assert len(queue) == len(cases) == 10
    assert {v["boundary_case_id"] for v in queue} == {v["boundary_case_id"] for v in cases}
    assert all(v["review_all_task016_pairs_required"] is False for v in queue)
    report = json.loads((EVIDENCE / "coverage_and_nonformation_report.json").read_text())
    assert report["full_estate_coverage_claimed"] is False
    assert report["task016_pair_recall_reassessed"] is False
