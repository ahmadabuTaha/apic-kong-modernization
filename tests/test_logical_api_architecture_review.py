from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from logical_api.architecture_review import NEXT_GATE, OUTPUTS, RECOMMENDATIONS, build_architecture_review


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/evidence/task-017/architecture-review-71"


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_all_71_baseline_ids_memberships_and_axes_are_preserved() -> None:
    baseline = jsonl(ROOT / "indexes/task017_full_logical_api_proposals.jsonl")
    reviews = jsonl(ROOT / OUTPUTS["reviews"])
    assert len(reviews) == len({v["baseline_logical_api_proposal_id"] for v in reviews}) == 71
    by_id = {v["logical_api_proposal_id"]: v for v in baseline}
    assert set(by_id) == {v["baseline_logical_api_proposal_id"] for v in reviews}
    for review in reviews:
        source = by_id[review["baseline_logical_api_proposal_id"]]
        assert {v["task014_operation_id"] for v in review["operations"]} == set(source["member_operation_ids"])
        assert review["baseline_evidence_sufficiency"] == source["three_result_axes"]["evidence_sufficiency"]
        assert review["original_membership_unchanged"] is True
        assert review["three_result_axes"]["technical_validation"] == "PASS"
        assert review["three_result_axes"]["architect_acceptance"] == "PENDING"
        assert review["recommendation"] in RECOMMENDATIONS


def test_each_review_has_case_evidence_r1_r7_and_exact_operation_context() -> None:
    reviews = jsonl(ROOT / OUTPUTS["reviews"])
    allowed = {"SUPPORTED", "CONTRADICTED", "NOT_EVIDENCED"}
    for review in reviews:
        assert set(review["review_rubric"]) == {f"R{i}" for i in range(1, 8)}
        assert all(v["status"] in allowed and v["rationale"] and v["evidence_refs"] for v in review["review_rubric"].values())
        assert review["positive_cohesion_evidence"] and review["specific_counterevidence"]
        for operation in review["operations"]:
            assert operation["method"] and operation["path"].startswith("/")
            assert operation["source_pointer"].startswith("staging/")
            assert operation["source_sha256"]
            assert operation["contract"]
            assert operation["backend_evidence_scope"]["runtime_egress_proven"] is False
            assert operation["exposure"]["operation_consumption_proven"] is False
            assert operation["exposure"]["runtime_activity_proven"] is False


def test_splits_are_direct_evidence_bounded_and_disjoint() -> None:
    reviews = jsonl(ROOT / OUTPUTS["reviews"])
    split = [v for v in reviews if v["recommendation"] == "SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES"]
    assert split
    for review in split:
        candidates = review["proposed_sub_boundaries"]
        ids = [operation_id for candidate in candidates for operation_id in candidate["member_operation_ids"]]
        assert len(candidates) >= 2 and len(ids) == len(set(ids))
        assert set(ids) | set(review["unassigned_after_split_operation_ids"]) == {v["task014_operation_id"] for v in review["operations"]}
        assert all(candidate["evidence_refs"] and candidate["architect_acceptance"] == "PENDING" for candidate in candidates)


def test_oversized_adjunct_is_five_132_and_outside_baseline() -> None:
    adjunct = jsonl(ROOT / OUTPUTS["oversized"])
    assert len(adjunct) == 5
    assert {v["current_api_name"] for v in adjunct} == {"osh", "osh-apis", "servicemanagement-supportcentre", "user-management", "user-management-privilege"}
    assert sum(v["operation_count"] for v in adjunct) == 132
    assert all(v["baseline_proposal_count_inclusion"] is False and v["cap_relaxed"] is False for v in adjunct)
    assert all(v["original_primary_dispositions_unchanged"] is True for v in adjunct)
    for value in adjunct:
        candidates = [x for c in value["subfamily_candidates"] for x in c["member_operation_ids"]]
        assert len(candidates) == len(set(candidates))
        assert set(candidates) | set(value["unresolved_operation_ids"]) == set(value["original_member_operation_ids"])


def test_cross_links_are_bounded_alternatives_and_sc_control_is_preserved() -> None:
    links = jsonl(ROOT / OUTPUTS["cross_links"])
    assert 0 < len(links) < 46
    assert all(len(v["canonical_api_ids"]) >= 2 for v in links)
    assert all(v["positive_evidence"] and v["contrary_evidence"] for v in links)
    assert all(v["primary_membership_created"] is False and v["functional_equivalence_approved"] is False and v["transitive_equivalence_inferred"] is False for v in links)
    sc = next(v for v in links if v["candidate_label"] == "SC Request Workflow")
    expanded = next(v for v in jsonl(ROOT / "tests/evidence/task-017/expanded-validation/expanded_sample_register.jsonl") if v["candidate_boundary_label"] == "SC Request Workflow")
    assert len(sc["member_operation_ids"]) == 2
    assert sorted({a for m in expanded["members"] for a in m["supported_actions"]}) == ["approve", "cancel", "reject"]
    assert expanded["result_axes"]["evidence_sufficiency"] == "PARTIAL"
    assert "Unified" in " ".join(sc["competing_alternatives"])
    assert "Decision" in " ".join(sc["competing_alternatives"])
    assert "Cancellation" in " ".join(sc["competing_alternatives"])


def test_backlog_has_all_components_and_correct_gate() -> None:
    backlog = jsonl(ROOT / OUTPUTS["backlog"])
    reviews = jsonl(ROOT / OUTPUTS["reviews"])
    links = jsonl(ROOT / OUTPUTS["cross_links"])
    assert len(backlog) == 71 + 5 + len(links)
    assert Counter(v["item_type"] for v in backlog) == {"BASELINE_PROPOSAL": 71, "OVERSIZED_ADJUNCT": 5, "CROSS_API_LINK": len(links)}
    assert {v["source_id"] for v in backlog if v["item_type"] == "BASELINE_PROPOSAL"} == {v["baseline_logical_api_proposal_id"] for v in reviews}
    assert all(v["next_gate"] == NEXT_GATE and v["architect_acceptance"] == "PENDING" and v["product_design_authorized"] is False for v in backlog)
    assert all("SHARED_LIFECYCLE_OWNER" in v["task018_019_cannot_prove"] for v in backlog)


def test_full_ledger_and_46_case_inputs_remain_unchanged() -> None:
    ledger = jsonl(ROOT / "indexes/task017_full_operation_disposition.jsonl")
    expanded = jsonl(ROOT / "tests/evidence/task-017/expanded-validation/expanded_sample_register.jsonl")
    assert len(ledger) == len({v["task014_operation_id"] for v in ledger}) == 2414
    assert sum(not v["task016_comparison_refs"] for v in ledger) == 1481
    assert len(expanded) == 46


def test_committed_evidence_is_complete_pending_and_redacted() -> None:
    register = jsonl(EVIDENCE / "all_71_decision_register.jsonl")
    adjunct = jsonl(EVIDENCE / "five_oversized_adjunct.jsonl")
    backlog = jsonl(EVIDENCE / "productization_decision_backlog.jsonl")
    assert len(register) == 71 and len(adjunct) == 5 and len(backlog) >= 76
    assert all(set(operation["membership_r1_r7"]) == {f"R{i}" for i in range(1, 8)} for review in register for operation in review["operations"])
    executive = (EVIDENCE / "executive_all_71_review.md").read_text(encoding="utf-8")
    assert sum(1 for line in executive.splitlines() if re.match(r"\| \d+ \|", line)) == 71
    payload = "\n".join(path.read_text(encoding="utf-8") for path in EVIDENCE.iterdir() if path.is_file())
    assert "EA acceptance remains PENDING" in payload or '"architect_acceptance":"PENDING"' in payload
    assert not re.search(r"(?i)(password|passwd|client[_-]?secret|access[_-]?token)\s*[:=]\s*[^\s,;]+", payload)
    assert "http://" not in payload.lower() and "https://" not in payload.lower()


def test_architecture_review_indexes_rebuild_byte_deterministically(tmp_path: Path) -> None:
    output_paths = {name: tmp_path / path.name for name, path in OUTPUTS.items()}
    first = build_architecture_review(ROOT, output_paths=output_paths)
    before = {name: digest(path) for name, path in output_paths.items() if name != "manifest"}
    second = build_architecture_review(ROOT, output_paths=output_paths)
    after = {name: digest(path) for name, path in output_paths.items() if name != "manifest"}
    assert before == after
    assert first["manifest"]["summary"] == second["manifest"]["summary"]
    assert second["manifest"]["full_task017_regenerated"] is False
    assert second["manifest"]["all_pairs_search_performed"] is False
    assert second["manifest"]["primary_memberships_changed"] == 0
