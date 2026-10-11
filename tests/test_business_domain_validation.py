from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from business_domain.domain_validation import ALIGNMENT_GATE, CLASSIFICATION_STATUSES, OUTPUTS, build_domain_validation


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/evidence/task-018/domain-validation"


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_sample_is_bounded_distinct_and_operation_centered() -> None:
    cases = jsonl(ROOT / OUTPUTS["cases"])
    operations = [op for case in cases for op in case["sampled_operations"]]
    operation_ids = [op["task014_operation_id"] for op in operations]
    assert 40 <= len(cases) == 51 <= 60
    assert 70 <= len(operation_ids) == len(set(operation_ids)) == 92 <= 100
    assert len({case["domain_case_id"] for case in cases}) == len(cases)
    assert all(case["api_whole_classified"] is False for case in cases)
    assert all(case["enterprise_domain_alignment"] == "PENDING" for case in cases)
    assert all(case["logical_api_or_product_inferred"] is False for case in cases)


def test_exact_operation_identity_and_provenance_match_frozen_ledger() -> None:
    cases = jsonl(ROOT / OUTPUTS["cases"])
    ledger = {v["task014_operation_id"]: v for v in jsonl(ROOT / "indexes/task017_full_operation_disposition.jsonl")}
    for case in cases:
        for operation in case["sampled_operations"]:
            source = ledger[operation["task014_operation_id"]]
            assert operation["task015_observed_function_id"] == source["task015_observed_function_id"]
            assert operation["canonical_api_id"] == source["canonical_api_id"]
            assert operation["method"] == source["method"] and operation["exact_path"] == source["exact_path"]
            assert operation["source_provenance"] == source["source_provenance"]
            assert operation["logical_api_membership_changed"] is False
            assert operation["production_usage_inferred"] is False


def test_classification_semantics_do_not_force_uncertain_primary_domains() -> None:
    taxonomy = json.loads((ROOT / OUTPUTS["taxonomy"]).read_text(encoding="utf-8"))
    taxonomy_by_id = {v["candidate_domain_id"]: v for v in taxonomy["candidates"]}
    assert taxonomy["taxonomy_status"] == "APIC_DERIVED_CANDIDATE_NOT_ENTERPRISE_APPROVED"
    assert taxonomy["enterprise_alignment"] == "PENDING"
    for case in jsonl(ROOT / OUTPUTS["cases"]):
        for operation in case["sampled_operations"]:
            assessment = operation["domain_assessment"]
            assert assessment["classification_status"] in CLASSIFICATION_STATUSES
            assert assessment["enterprise_alignment"] == "PENDING"
            candidates = {v["candidate_domain_id"] for v in assessment["alternative_candidates"]}
            primary = assessment["primary_domain_candidate_id"]
            if primary:
                assert primary in candidates
                assert taxonomy_by_id[primary]["candidate_type"] in {"DOMAIN_CANDIDATE", "SUBDOMAIN_CANDIDATE"}
            if assessment["classification_status"] in {"MULTIPLE_DOMAIN_CANDIDATES", "CONFLICTING_EVIDENCE", "INSUFFICIENT_BUSINESS_SEMANTICS", "TECHNICAL_UTILITY_EVIDENCED", "TEST_OR_POC_EVIDENCED"}:
                assert primary is None


def test_process_state_capability_and_event_are_not_invented() -> None:
    cases = jsonl(ROOT / OUTPUTS["cases"])
    for case in cases:
        for operation in case["sampled_operations"]:
            dimensions = operation["domain_assessment"]["semantic_dimensions"]
            for dimension in ("process", "state", "capability_signal", "event"):
                assert dimensions[dimension]["status"] == "NOT_EVIDENCED_FROM_APIC"
                assert dimensions[dimension]["values"] == []
                assert dimensions[dimension]["limitation"]
            assert dimensions["business_object"]["status"] in {"DIRECTLY_EVIDENCED", "PROVISIONAL_SIGNAL", "NOT_EVIDENCED_FROM_APIC"}
            assert dimensions["documented_action"]["status"] in {"DIRECTLY_EVIDENCED", "PROVISIONAL_SIGNAL", "NOT_EVIDENCED_FROM_APIC"}


def test_required_strata_oversized_links_and_sc_control_are_preserved() -> None:
    cases = jsonl(ROOT / OUTPUTS["cases"])
    origins = Counter(v["case_origin"] for v in cases)
    assert origins == {"CROSS_API_LINK": 14, "OVERSIZED_ADJUNCT": 5, "TASK017A_PROPOSAL": 32}
    strata = Counter(value for case in cases for value in case["strata"])
    assert strata["HARD_NEGATIVE_CONTROL"] >= 6
    assert strata["CHALLENGING_BOUNDARY"] >= 8
    assert strata["VERSION_OR_VARIANT"] >= 1
    for recommendation in (
        "RETAIN_PROVISIONAL_COHESIVE_BOUNDARY", "SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES",
        "KEEP_AS_IS_EXPOSURE_NO_LOGICAL_BOUNDARY_ASSERTION", "REQUIRES_TARGETED_EVIDENCE",
        "TECHNICAL_OR_TEST_EXPOSURE_REVIEW",
    ):
        assert strata[recommendation] > 0
    assert {v["case_label"].split(" oversized")[0] for v in cases if v["case_origin"] == "OVERSIZED_ADJUNCT"} == {"osh", "osh-apis", "servicemanagement-supportcentre", "user-management", "user-management-privilege"}
    sc = next(v for v in cases if v["case_label"] == "SC Request Workflow")
    assert len(sc["sampled_operations"]) == 2
    assert sc["frozen_task017_control"]["supported_action_intents"] == ["approve", "cancel", "reject"]
    assert sc["frozen_task017_control"]["evidence_sufficiency"] == "PARTIAL"
    assert sc["frozen_task017_control"]["architect_acceptance"] == "PENDING"


def test_api_footprints_are_sample_views_not_whole_api_assignments() -> None:
    cases = jsonl(ROOT / OUTPUTS["cases"])
    footprints = jsonl(ROOT / OUTPUTS["footprints"])
    sampled_ids = {op["task014_operation_id"] for case in cases for op in case["sampled_operations"]}
    footprint_ids = [operation_id for value in footprints for operation_id in value["sampled_operation_ids"]]
    assert len(footprints) == 62
    assert set(footprint_ids) == sampled_ids and len(footprint_ids) == len(set(footprint_ids))
    assert all(v["sampled_operations_only"] is True and v["whole_api_domain_classified"] is False for v in footprints)
    assert all(v["enterprise_alignment"] == "PENDING" and v["domain_approved"] is False for v in footprints)


def test_all_90_task017a_backlog_items_are_enriched_without_mutation() -> None:
    enrichment = jsonl(ROOT / OUTPUTS["enrichment"])
    backlog = jsonl(ROOT / "indexes/task017a_productization_decision_backlog.jsonl")
    assert len(enrichment) == len(backlog) == 90
    assert {v["task017a_backlog_id"] for v in enrichment} == {v["backlog_id"] for v in backlog}
    assert Counter(v["task017a_item_type"] for v in enrichment) == {"BASELINE_PROPOSAL": 71, "OVERSIZED_ADJUNCT": 5, "CROSS_API_LINK": 14}
    assert all(v["enrichment_only"] is True and v["baseline_rewritten"] is False for v in enrichment)
    assert all(v["logical_api_membership_changed"] is False and v["productization_decision_changed"] is False for v in enrichment)
    assert all(v["domain_similarity_proves_functional_equivalence"] is False and v["enterprise_alignment"] == "PENDING" for v in enrichment)


def test_frozen_full_coverage_and_prior_controls_remain_intact() -> None:
    ledger = jsonl(ROOT / "indexes/task017_full_operation_disposition.jsonl")
    reviews = jsonl(ROOT / "indexes/task017a_all_71_architecture_reviews.jsonl")
    oversized = jsonl(ROOT / "indexes/task017a_five_oversized_adjunct.jsonl")
    links = jsonl(ROOT / "indexes/task017a_cross_api_opportunity_links.jsonl")
    expanded = jsonl(ROOT / "tests/evidence/task-017/expanded-validation/expanded_sample_register.jsonl")
    assert len(ledger) == len({v["task014_operation_id"] for v in ledger}) == 2414
    assert sum(not v["task016_comparison_refs"] for v in ledger) == 1481
    assert len(reviews) == 71 and len(oversized) == 5 and sum(v["operation_count"] for v in oversized) == 132
    assert len(links) == 14 and len(expanded) == 46


def test_committed_evidence_is_complete_readable_pending_and_redacted() -> None:
    cases = jsonl(EVIDENCE / "sampled_operation_domain_cases.jsonl")
    footprints = jsonl(EVIDENCE / "api_domain_footprint_sample.jsonl")
    enrichment = jsonl(EVIDENCE / "task017a_domain_enrichment_links.jsonl")
    summary = json.loads((EVIDENCE / "sample_coverage_and_gaps.json").read_text(encoding="utf-8"))
    assert len(cases) == 51 and len(footprints) == 62 and len(enrichment) == 90
    assert summary["sample_bounds"]["duplicate_operation_occurrences"] == 0
    assert summary["result_axes"] == {"technical_validation": "PASS", "domain_evidence_sufficiency": "MIXED", "enterprise_architect_acceptance": "PENDING"}
    executive = (EVIDENCE / "executive_sample_review.md").read_text(encoding="utf-8")
    assert sum(1 for line in executive.splitlines() if re.match(r"\| \d+ \|", line)) == 51
    assert executive.count("### ") >= 12
    payload = "\n".join(path.read_text(encoding="utf-8") for path in EVIDENCE.iterdir() if path.is_file())
    assert "http://" not in payload.lower() and "https://" not in payload.lower()
    assert not re.search(r"(?i)(password|passwd|client[_-]?secret|access[_-]?token)\s*[:=]\s*[^\s,;]+", payload)


def test_domain_validation_indexes_rebuild_byte_deterministically(tmp_path: Path) -> None:
    output_paths = {name: tmp_path / path.name for name, path in OUTPUTS.items()}
    first = build_domain_validation(ROOT, output_paths=output_paths)
    before = {name: digest(path) for name, path in output_paths.items() if name != "manifest"}
    second = build_domain_validation(ROOT, output_paths=output_paths)
    after = {name: digest(path) for name, path in output_paths.items() if name != "manifest"}
    assert before == after
    assert first["manifest"]["summary"] == second["manifest"]["summary"]
    assert second["manifest"]["full_task018_performed"] is False
    assert second["manifest"]["task019_performed"] is False
    assert second["manifest"]["all_pairs_search_performed"] is False
    assert second["manifest"]["enterprise_alignment_gate"] == {"position": ALIGNMENT_GATE, "architect_acceptance": "PENDING"}
