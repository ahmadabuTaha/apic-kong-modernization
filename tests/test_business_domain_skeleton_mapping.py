from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from business_domain.skeleton_mapping import (
    CLASSIFICATION_STATUSES,
    EVIDENCE_ROLES,
    OUTPUTS,
    SKELETON,
    STOP_GATE,
    build_skeleton_mapping,
)


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/evidence/task-018/domain-skeleton-018b"


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_full_operation_coverage_identity_and_provenance() -> None:
    mappings = jsonl(ROOT / OUTPUTS["operations"])
    frozen = {row["task014_operation_id"]: row for row in jsonl(ROOT / "indexes/task017_full_operation_disposition.jsonl")}
    assert len(mappings) == len({row["task014_operation_id"] for row in mappings}) == len(frozen) == 2414
    for row in mappings:
        source = frozen[row["task014_operation_id"]]
        assert row["canonical_api_id"] == source["canonical_api_id"]
        assert row["method"] == source["method"] and row["exact_path"] == source["exact_path"]
        assert row["source_provenance"] == source["source_provenance"]
        assert row["classification_unit"] == "HTTP_OPERATION"
        assert row["enterprise_alignment"] == "PENDING"
        assert row["runtime_usage_inferred"] is False


def test_only_exact_ea_skeleton_candidates_are_used_without_forcing() -> None:
    assert SKELETON == ("Visa", "Establishment", "Contracts", "Nitaqat", "Payment", "Common", "User Management", "Work Permit", "Work Force", "Notification", "Certificate")
    used = set()
    mappings = jsonl(ROOT / OUTPUTS["operations"])
    for row in mappings:
        assessment = row["domain_assessment"]
        assert assessment["classification_status"] in CLASSIFICATION_STATUSES
        primary = assessment["proposed_primary"]
        alternatives = assessment["alternative_candidates"]
        used.update(alternatives)
        if primary:
            assert primary in SKELETON
            used.add(primary)
        if assessment["classification_status"] in {"UNRESOLVED_AMBIGUOUS", "UNRESOLVED_INSUFFICIENT_SEMANTICS", "TECHNICAL_OR_TEST_NO_DOMAIN_PRIMARY", "CONFLICTING_SOURCE_EVIDENCE"}:
            assert primary is None
        for candidate in assessment["candidate_evidence"]:
            assert candidate["candidate"] in SKELETON
            assert all(hit["evidence_source"] != "API_NAME" for hit in candidate["evidence_hits"])
    assert used == set(SKELETON)
    assert any(row["domain_assessment"]["proposed_primary"] == "Certificate" for row in mappings)


def test_all_canonical_apis_are_accounted_without_whole_api_assignment() -> None:
    footprints = jsonl(ROOT / OUTPUTS["apis"])
    mappings = jsonl(ROOT / OUTPUTS["operations"])
    assert len(footprints) == len({row["canonical_api_id"] for row in footprints}) == 2036
    assert sum(row["accepted_operation_count"] for row in footprints) == len(mappings) == 2414
    assert sum(row["accepted_operation_count"] == 0 for row in footprints) == 41
    assert all(row["whole_api_domain_assigned"] is False and row["domain_approved"] is False for row in footprints)
    assert all(row["source_inventory_operation_count"] == row["accepted_operation_count"] for row in footprints)


def test_targeted_yaml_register_has_all_roles_and_no_source_failures() -> None:
    objects = jsonl(ROOT / OUTPUTS["objects"])
    manifest = json.loads((ROOT / OUTPUTS["manifest"]).read_text(encoding="utf-8"))
    assert {row["evidence_role"] for row in objects} == EVIDENCE_ROLES
    assert all(row["selection_reason"].startswith(("CONFLICTING", "AMBIGUOUS", "BOUNDARY_SENSITIVE", "INSUFFICIENT")) for row in objects)
    assert all(row["business_ownership_proven"] is False for row in objects)
    assert all(row["source_path"].startswith("staging/") and row["source_sha256"] for row in objects)
    yaml_summary = manifest["summary"]["targeted_yaml"]
    assert 100 <= yaml_summary["selected_operation_count"] <= 220
    assert yaml_summary["source_hash_mismatch_count"] == 0
    assert yaml_summary["source_parse_error_count"] == 0
    assert yaml_summary["unresolved_local_schema_ref_count"] == 0
    states = [row for row in objects if row["evidence_role"] == "STATE_VALUE_CANDIDATE"]
    assert states and all("no transition" in " ".join(row["limitations"]).lower() for row in states)


def test_frozen_task017a_inputs_remain_complete() -> None:
    assert len(jsonl(ROOT / "indexes/task017a_all_71_architecture_reviews.jsonl")) == 71
    oversized = jsonl(ROOT / "indexes/task017a_five_oversized_adjunct.jsonl")
    assert len(oversized) == 5 and sum(row["operation_count"] for row in oversized) == 132
    assert len(jsonl(ROOT / "indexes/task017a_cross_api_opportunity_links.jsonl")) == 14
    assert len(jsonl(ROOT / "indexes/task017a_productization_decision_backlog.jsonl")) == 90


def test_manifest_guardrails_and_distributions_reconcile() -> None:
    manifest = json.loads((ROOT / OUTPUTS["manifest"]).read_text(encoding="utf-8"))
    summary = manifest["summary"]
    assert manifest["skeleton_candidates"] == list(SKELETON)
    assert manifest["stop_gate"] == {"position": STOP_GATE, "enterprise_architect_review": "PENDING"}
    assert all(value is False for value in manifest["guardrails"].values())
    assert sum(summary["classification_status_counts"].values()) == 2414
    assert sum(summary["primary_candidate_counts"].values()) == summary["classification_status_counts"]["PRIMARY_CANDIDATE_PROVISIONAL"]
    assert summary["enterprise_domain_approval_count"] == 0


def test_committed_review_outputs_point_to_complete_ledgers_and_are_redacted() -> None:
    expected = {
        "skeleton_contract.md",
        "operation_domain_initial_mapping.jsonl",
        "canonical_api_domain_footprint.jsonl",
        "business_object_candidate_register.jsonl",
        "domain_review_reclassification_backlog.md",
        "coverage_quality_and_unresolved.md",
        "build_manifest.json",
        "generate_domain_skeleton_evidence.py",
        "commands_and_results.txt",
    }
    assert expected <= {path.name for path in EVIDENCE.iterdir() if path.is_file()}
    for name, output, count in (
        ("operation_domain_initial_mapping.jsonl", "operations", 2414),
        ("canonical_api_domain_footprint.jsonl", "apis", 2036),
        ("business_object_candidate_register.jsonl", "objects", None),
    ):
        pointer = jsonl(EVIDENCE / name)
        assert len(pointer) == 1 and pointer[0]["record_type"] == "DETERMINISTIC_FULL_LEDGER_POINTER"
        assert pointer[0]["full_ledger_path"] == OUTPUTS[output].as_posix()
        assert pointer[0]["sha256"] == digest(ROOT / OUTPUTS[output])
        if count is not None:
            assert pointer[0]["record_count"] == count
    payload = "\n".join(path.read_text(encoding="utf-8") for path in EVIDENCE.iterdir() if path.is_file())
    assert "http://" not in payload.lower() and "https://" not in payload.lower()
    assert not re.search(r"(?i)(password|passwd|client[_-]?secret|access[_-]?token)\s*[:=]\s*[^\s,;]+", payload)


def test_rebuild_is_byte_deterministic(tmp_path: Path) -> None:
    paths = {name: tmp_path / path.name for name, path in OUTPUTS.items()}
    first = build_skeleton_mapping(ROOT, output_paths=paths)
    before = {name: digest(path) for name, path in paths.items() if name != "manifest"}
    second = build_skeleton_mapping(ROOT, output_paths=paths)
    after = {name: digest(path) for name, path in paths.items() if name != "manifest"}
    assert before == after
    assert first["manifest"]["summary"] == second["manifest"]["summary"]
    assert Counter(row["domain_assessment"]["classification_status"] for row in second["operations"]) == second["manifest"]["summary"]["classification_status_counts"]
