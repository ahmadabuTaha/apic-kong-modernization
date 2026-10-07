import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "tests/evidence/task-007"
PHASE1 = ROOT / "indexes/extracted_records.jsonl"
PHASE2 = ROOT / "indexes/apic_identity_resolution.json"
INVESTIGATOR = EVIDENCE / "investigate_unresolved.py"


def _load_investigator():
    spec = importlib.util.spec_from_file_location("task_007_investigator", INVESTIGATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_committed_evidence_enumerates_every_unresolved_occurrence() -> None:
    rows = _load_jsonl(EVIDENCE / "unresolved_product_location_apis.jsonl")
    summary = json.loads(
        (EVIDENCE / "investigation_summary.json").read_text(encoding="utf-8")
    )
    ids = [row["extracted_record_id"] for row in rows]

    assert len(rows) == 113
    assert len(ids) == len(set(ids)) == 113
    assert ids == sorted(ids, key=lambda value: next(
        (row["source_relative_path"], row["extracted_record_id"])
        for row in rows
        if row["extracted_record_id"] == value
    ))
    assert summary["total_product_location_api_occurrences"] == 2357
    assert summary["attached_product_location_api_occurrences"] == 2244
    assert summary["unresolved_product_location_api_occurrences"] == 113
    assert summary["arithmetic_proof"] == {
        "equals_enumerated_unresolved_count": True,
        "total_minus_attached": 113,
    }
    assert summary["enumerated_ids_equal_phase2_unresolved_ids"] is True
    assert summary["attached_and_unresolved_id_overlap_count"] == 0


def test_diagnostic_name_version_and_hash_evidence_never_promotes_an_occurrence() -> None:
    rows = _load_jsonl(EVIDENCE / "unresolved_product_location_apis.jsonl")
    for row in rows:
        assert row["product_ref_occurrence_count"] == 0
        assert row["observed_apic_self_url"] is None
        assert row["observed_apic_object_id"] is None
        assert row["exact_self_url_or_id_scope_registry_candidate_count"] == 0
        assert row["exact_name_version_authoritative_candidate_count"] == 1
        assert row["exact_name_version_registry_candidate_count"] == 1
        assert row["hash_equal_authoritative_candidate_count"] == 1
        assert row["approved_api_bridge_exists"] is True
        assert row["approved_api_bridge_authoritative_candidate_count"] == 1
        assert row["approved_product_ref_and_registry_convergence_exists"] is False
        assert (
            row[
                "registry_product_membership_is_admissible_occurrence_attachment_evidence"
            ]
            is False
        )
        assert row["task_006_resolution_outcome"] == "UNRESOLVED"
        assert row["resolver_defect_demonstrated"] is False
        assert all(
            sibling["source_relative_path"] != row["source_relative_path"]
            for sibling in row["same_name_version_product_location_siblings"]
        )


@pytest.mark.skipif(
    not PHASE1.is_file() or not PHASE2.is_file(),
    reason="local ignored Phase 1/2 indexes are required for full-corpus reproduction",
)
def test_full_corpus_reproduction_is_deterministic_complete_and_source_safe() -> None:
    investigator = _load_investigator()
    phase2 = json.loads(PHASE2.read_text(encoding="utf-8"))
    phase1 = _load_jsonl(PHASE1)
    committed_rows = _load_jsonl(EVIDENCE / "unresolved_product_location_apis.jsonl")
    committed_summary = json.loads(
        (EVIDENCE / "investigation_summary.json").read_text(encoding="utf-8")
    )
    staging = ROOT / "staging"
    before = _tree_hashes(staging)

    first_rows, first_summary = investigator.build_investigation(phase2, phase1)
    second_rows, second_summary = investigator.build_investigation(phase2, phase1)

    assert first_rows == second_rows == committed_rows
    assert first_summary == second_summary == committed_summary
    assert _tree_hashes(staging) == before

    attached_ids = {
        occurrence_id
        for identity in phase2["canonical_identity_records"]
        if identity["canonical_object_type"] == "api_artifact"
        for occurrence_id in identity["product_location_occurrence_ids"]
    }
    unresolved_ids = {row["extracted_record_id"] for row in first_rows}
    product_location_ids = {
        record["extracted_record_id"]
        for record in phase1
        if record.get("canonical_object_type_candidate") == "api_artifact"
        and record.get("source_schema_family") == "OPENAPI_DOCUMENT"
        and record["source_relative_path"].startswith("staging/products/_catalog/")
    }
    assert attached_ids | unresolved_ids == product_location_ids
    assert not attached_ids & unresolved_ids

    evidence_bytes = b"".join(
        path.read_bytes()
        for path in (
            EVIDENCE / "unresolved_product_location_apis.jsonl",
            EVIDENCE / "investigation_summary.json",
            PHASE2,
        )
    )
    sensitive_values: list[bytes] = []
    for path in (staging / "credentials").glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("results", []):
            for field in ("client_id", "client_secret", "client_secret_hashed"):
                value = item.get(field)
                if isinstance(value, str) and value:
                    sensitive_values.append(value.encode())
    assert sensitive_values
    assert all(value not in evidence_bytes for value in sensitive_values)
