import csv
import hashlib
from pathlib import Path

import business_capability_kg.enterprise_capability_consolidation as consolidation


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _fixture_inputs(input_root: Path) -> dict[str, str]:
    main_a, main_b = "main-a", "main-b"
    _write_csv(input_root / "main_capabilities.csv", [
        {
            "module_key": "module-a", "module_name": "Module A", "main_capability_id": main_a,
            "name": "Shared Request Management", "description": "Manage the same request lifecycle.",
            "candidate_status": "candidate", "source_types": "ICD", "linked_document_count": "1",
        },
        {
            "module_key": "module-b", "module_name": "Module B", "main_capability_id": main_b,
            "name": "Shared Request Management", "description": "Manage the same request lifecycle.",
            "candidate_status": "candidate", "source_types": "ISD", "linked_document_count": "1",
        },
    ])
    common_link = {
        "physical_identity": "confluence-page:1", "title": "Source", "service_keys": "service-1",
        "occurrence_ids": "occ-1", "blob_sha256": "a" * 64, "source_version": "v:1",
        "evidence_pointer": "page:1#b000001:0-30", "evidence_excerpt": "This service manages a request.",
        "external_entities": "", "mapping_status": "candidate", "mapping_rationale": "Indexed evidence.",
    }
    _write_csv(input_root / "main_icd_links.csv", [{
        "module_key": "module-a", "module_name": "Module A", "main_capability_id": main_a,
        "page_id": "1", "document_key": "document-icd-1", **common_link,
    }])
    _write_csv(input_root / "main_isd_links.csv", [{
        "module_key": "module-b", "module_name": "Module B", "main_capability_id": main_b,
        "page_id": "2", "document_key": "document-isd-2",
        **{**common_link, "physical_identity": "confluence-page:2", "service_keys": "service-2",
           "occurrence_ids": "occ-2", "evidence_pointer": "page:2#b000001:0-30"},
        "classification_signals": "request", "unpaired_reason": "No active ICD relationship",
    }])
    _write_csv(input_root / "excluded_sources.csv", [{
        "exclusion_id": "excluded-1", "module_key": "module-a", "module_name": "Module A",
        "source_type": "ICD", "page_id": "3", "document_key": "document-icd-3",
        "service_key": "service-3", "occurrence_id": "occ-3", "title": "OLD Source",
        "source_marker": "OLD", "exclusion_reason": "Source-declared OLD; runtime state unproven.",
        "runtime_state_proven": "false",
    }])
    _write_csv(input_root / "coverage_exceptions.csv", [{
        "exception_id": "exception-1", "module_key": "module-b", "module_name": "Module B",
        "source_type": "ISD", "page_id": "4", "document_key": "document-isd-4",
        "service_keys": "service-4", "occurrence_ids": "occ-4", "title": "Empty Source",
        "issue_type": "UNREADABLE_SOURCE", "precise_reason": "No supported blocks.",
        "evidence_pointer": "", "downstream_impact": "Future mapping may be unresolved.",
        "status": "EA_REVIEW_REQUIRED",
    }])
    _write_csv(input_root / "module_coverage.csv", [
        {"module_key": "module-a", "module_name": "Module A"},
        {"module_key": "module-b", "module_name": "Module B"},
    ])
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in input_root.glob("*.csv")
    }


def _configure_fixture(monkeypatch, hashes: dict[str, str]) -> None:
    monkeypatch.setattr(consolidation, "INPUT_HASHES", hashes)
    monkeypatch.setattr(consolidation, "EXPECTED", {
        "modules": 2, "mains": 2, "icd_links": 1, "isd_links": 1,
        "exclusions": 1, "exceptions": 1,
    })
    monkeypatch.setattr(consolidation, "EXPECTED_EXCEPTION_PAGES", {"4"})
    monkeypatch.setattr(consolidation, "MERGE_GROUPS", {
        "shared-request": {
            "name": "Shared Request Management",
            "definition": "Manage the same request lifecycle.",
            "members": ("main-a", "main-b"),
            "rationale": "Both candidates have the same evidenced outcome and object.",
        }
    })
    monkeypatch.setattr(consolidation, "BOUNDARY_REVIEWS", ())
    monkeypatch.setattr(consolidation, "RELATED_MAIN_IDS", set())
    monkeypatch.setattr(consolidation, "SINGLETON_NAME_OVERRIDES", {})


def test_declared_equivalent_groups_are_disjoint_and_conservative() -> None:
    members = [member for group in consolidation.MERGE_GROUPS.values() for member in group["members"]]
    assert len(consolidation.MERGE_GROUPS) == 9
    assert len(members) == 18
    assert len(members) == len(set(members))
    assert "integration-management" not in consolidation.MERGE_GROUPS


def test_index_only_build_preserves_both_source_paths_and_is_deterministic(
    tmp_path: Path, monkeypatch
) -> None:
    input_root = tmp_path / "019e_final"
    hashes = _fixture_inputs(input_root)
    _configure_fixture(monkeypatch, hashes)
    index_root, report_root = tmp_path / "019f", tmp_path / "reports"

    first = consolidation.build_enterprise_consolidation(
        tmp_path, input_root, index_root, report_root
    )
    first_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (*sorted(index_root.iterdir()), report_root / "review_summary.md")
    }
    second = consolidation.build_enterprise_consolidation(
        tmp_path, input_root, index_root, report_root
    )
    second_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (*sorted(index_root.iterdir()), report_root / "review_summary.md")
    }

    assert first["counts"] == {
        "enterprise_capabilities": 1, "main_enterprise_links": 2,
        "traceability_rows": 2, "review_queue": 2, "coverage_reconciliation": 4,
    }
    assert first["hashes"] == second["hashes"]
    assert first_hashes == second_hashes
    assert {path.name for path in index_root.iterdir()} == {
        "enterprise_capabilities.csv", "main_enterprise_links.csv",
        "enterprise_source_traceability.csv", "review_queue.csv",
        "coverage_reconciliation.csv",
    }
    assert {path.name for path in report_root.iterdir()} == {"review_summary.md"}

    with (index_root / "enterprise_source_traceability.csv").open() as stream:
        traces = list(csv.DictReader(stream))
    assert {(row["source_type"], row["page_id"], row["document_key"]) for row in traces} == {
        ("ICD", "1", "document-icd-1"), ("ISD", "2", "document-isd-2")
    }
    assert len({row["enterprise_capability_id"] for row in traces}) == 1


def test_gap_and_exclusion_remain_separate_without_enterprise_links(tmp_path: Path, monkeypatch) -> None:
    input_root = tmp_path / "019e_final"
    hashes = _fixture_inputs(input_root)
    _configure_fixture(monkeypatch, hashes)
    index_root, report_root = tmp_path / "019f", tmp_path / "reports"
    consolidation.build_enterprise_consolidation(tmp_path, input_root, index_root, report_root)

    with (index_root / "review_queue.csv").open() as stream:
        review = list(csv.DictReader(stream))
    assert {row["review_type"] for row in review} == {
        "UNRESOLVED_SOURCE_CARRY_FORWARD", "SOURCE_EXCLUSION_CARRY_FORWARD"
    }
    assert all(not row["enterprise_capability_ids"] for row in review)
    gap = next(row for row in review if row["review_type"] == "UNRESOLVED_SOURCE_CARRY_FORWARD")
    excluded = next(row for row in review if row["review_type"] == "SOURCE_EXCLUSION_CARRY_FORWARD")
    assert (gap["page_id"], gap["document_key"]) == ("4", "document-isd-4")
    assert "runtime" in excluded["decision_needed"]


def test_changed_accepted_input_is_rejected_before_output(tmp_path: Path, monkeypatch) -> None:
    input_root = tmp_path / "019e_final"
    hashes = _fixture_inputs(input_root)
    _configure_fixture(monkeypatch, hashes)
    with (input_root / "main_capabilities.csv").open("a", encoding="utf-8") as stream:
        stream.write("tampered\n")
    try:
        consolidation.build_enterprise_consolidation(
            tmp_path, input_root, tmp_path / "019f", tmp_path / "reports"
        )
    except ValueError as error:
        assert "INPUT_HASH_MISMATCH" in str(error)
    else:
        raise AssertionError("mutated accepted input was not rejected")
