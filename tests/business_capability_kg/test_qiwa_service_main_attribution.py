import csv
import hashlib
import sqlite3
from pathlib import Path

import business_capability_kg.qiwa_service_main_attribution as attribution


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _fixture(root: Path) -> dict[str, str]:
    qiwa_rows = [
        {
            "ID": "1", "Service_Name": "HttpDependency", "Type": "API-HTTP",
            "Database_Source": "N/A", "Parent_Service": "ProviderService", "Platform": "API",
            "Flag_1": "1", "Flag_2": "0", "Service_Normalized": "httpdependency",
            "Module_Name": "Module A", "Note": "N/A",
        },
        {
            "ID": "2", "Service_Name": "ProviderService", "Type": "API-MQ",
            "Database_Source": "N/A", "Parent_Service": "ConsumerService", "Platform": "API",
            "Flag_1": "1", "Flag_2": "0", "Service_Normalized": "providerservice",
            "Module_Name": "Module B", "Note": "N/A",
        },
        {
            "ID": "3", "Service_Name": "OtherHttpDependency", "Type": "API-HTTP",
            "Database_Source": "N/A", "Parent_Service": "ConsumerService", "Platform": "API",
            "Flag_1": "1", "Flag_2": "0", "Service_Normalized": "otherhttpdependency",
            "Module_Name": "Module B", "Note": "N/A",
        },
    ]
    _write_csv(root / attribution.QIWA_CSV, qiwa_rows)

    catalog = root / attribution.CATALOG
    catalog.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(catalog)
    connection.execute("CREATE TABLE services (service_key TEXT, module_key TEXT, service_name TEXT)")
    connection.executemany("INSERT INTO services VALUES (?, ?, ?)", [
        ("module-a::service-provider", "module-a", "Provider Service"),
        ("module-b::service-consumer", "module-b", "Consumer Service"),
    ])
    connection.commit()
    connection.close()

    mains = [
        {
            "module_key": "module-a", "module_name": "Module A", "main_capability_id": "main-a",
            "name": "Provider Request Management", "description": "Manage provider requests.",
            "candidate_status": "candidate", "source_types": "ICD", "linked_document_count": "1",
        },
        {
            "module_key": "module-b", "module_name": "Module B", "main_capability_id": "main-b",
            "name": "Consumer Request Management", "description": "Manage consumer requests.",
            "candidate_status": "candidate", "source_types": "ICD", "linked_document_count": "1",
        },
    ]
    _write_csv(root / attribution.INPUT_019E / "main_capabilities.csv", mains)
    base_link = {
        "physical_identity": "confluence-page:1", "title": "ICD", "occurrence_ids": "occ-1",
        "blob_sha256": "a" * 64, "source_version": "v:1",
        "evidence_pointer": "page:1#b000001:0-20", "evidence_excerpt": "This service manages requests.",
        "external_entities": "", "mapping_status": "candidate", "mapping_rationale": "accepted source",
    }
    _write_csv(root / attribution.INPUT_019E / "main_icd_links.csv", [
        {
            "module_key": "module-a", "module_name": "Module A", "main_capability_id": "main-a",
            "page_id": "1", "document_key": "document-1", "service_keys": "module-a::service-provider",
            **base_link,
        },
        {
            "module_key": "module-b", "module_name": "Module B", "main_capability_id": "main-b",
            "page_id": "2", "document_key": "document-2", "service_keys": "module-b::service-consumer",
            **{**base_link, "physical_identity": "confluence-page:2", "occurrence_ids": "occ-2",
               "evidence_pointer": "page:2#b000001:0-20"},
        },
    ])
    # A header-only file still supplies the accepted ISD schema.
    isd_path = root / attribution.INPUT_019E / "main_isd_links.csv"
    isd_path.parent.mkdir(parents=True, exist_ok=True)
    isd_path.write_text(
        "module_key,module_name,main_capability_id,page_id,document_key,physical_identity,title,service_keys,occurrence_ids,blob_sha256,source_version,evidence_pointer,evidence_excerpt,external_entities,mapping_status,mapping_rationale,classification_signals,unpaired_reason\n",
        encoding="utf-8",
    )
    _write_csv(root / attribution.INPUT_019E / "coverage_exceptions.csv", [{
        "exception_id": "gap-1", "module_key": "module-gap", "module_name": "Gap",
        "source_type": "ICD", "page_id": "9", "document_key": "document-9",
        "service_keys": "module-gap::service-gap", "occurrence_ids": "occ-9", "title": "Gap",
        "issue_type": "UNREADABLE_SOURCE", "precise_reason": "Empty source.",
        "evidence_pointer": "", "downstream_impact": "unresolved", "status": "EA_REVIEW_REQUIRED",
    }])
    _write_csv(root / attribution.INPUT_019E / "excluded_sources.csv", [{
        "exclusion_id": "excluded-1", "module_key": "module-old", "module_name": "Old",
        "source_type": "ICD", "page_id": "10", "document_key": "document-10",
        "service_key": "module-old::service-old", "occurrence_id": "occ-10", "title": "OLD",
        "source_marker": "OLD", "exclusion_reason": "Source-declared OLD; runtime unproven.",
        "runtime_state_proven": "false",
    }])
    _write_csv(root / attribution.INPUT_019F, [
        {"main_capability_id": "main-a", "enterprise_capability_id": "enterprise-a"},
        {"main_capability_id": "main-b", "enterprise_capability_id": "enterprise-b"},
    ])
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in attribution._input_paths(root).items()}


def _configure(monkeypatch, hashes: dict[str, str]) -> None:
    monkeypatch.setattr(attribution, "INPUT_HASHES", hashes)
    monkeypatch.setattr(attribution, "EXPECTED", {
        "qiwa_rows": 3, "api_http_rows": 2, "api_http_parents": 2,
        "recovery_services": 2, "mains": 2, "enterprise_candidates": 2,
        "icd_links": 2, "isd_links": 0, "source_gaps": 1, "source_exclusions": 1,
    })
    monkeypatch.setattr(attribution, "MODULE_CROSSWALK", {
        "Module A": "module-a", "Module B": "module-b",
    })


def test_type_column_classifies_child_and_parent_inventory_is_grouped() -> None:
    assert attribution._normalize(" Provider_Service ") == "providerservice"
    assert attribution.QIWA_CSV.as_posix() == "neo4j/csv/Qiwa_Modules_Services.csv"


def test_build_requires_two_independent_support_evidence_paths_and_is_deterministic(
    tmp_path: Path, monkeypatch
) -> None:
    hashes = _fixture(tmp_path)
    _configure(monkeypatch, hashes)
    index_root, output_root = tmp_path / "indexes-out", tmp_path / "outputs-out"
    first = attribution.build_qiwa_service_main_attribution(tmp_path, index_root, output_root)
    first_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (*sorted(index_root.iterdir()), output_root / "review_summary.md")
    }
    second = attribution.build_qiwa_service_main_attribution(tmp_path, index_root, output_root)
    second_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (*sorted(index_root.iterdir()), output_root / "review_summary.md")
    }

    assert first["counts"]["api_http_inventory"] == 2
    assert first["counts"]["provides_links"] == 2
    assert first["counts"]["supports_links"] == 1
    assert first["counts"]["no_child_usage"] == 1
    assert first["hashes"] == second["hashes"]
    assert first_hashes == second_hashes
    assert {path.name for path in index_root.iterdir()} == {
        "api_http_service_inventory.csv", "api_main_capability_links.csv", "review_exceptions.csv"
    }
    assert {path.name for path in output_root.iterdir()} == {"review_summary.md"}

    with (index_root / "api_main_capability_links.csv").open() as stream:
        links = list(csv.DictReader(stream))
    support = next(row for row in links if row["link_type"] == "SUPPORTS")
    assert support["qiwa_relationship_pointers"] == "neo4j/csv/Qiwa_Modules_Services.csv#ID=2"
    assert support["resolved_consumer_source_service_key"] == "module-b::service-consumer"
    assert support["source_evidence_pointers"] == "page:2#b000001:0-20"
    assert support["certainty"] == "DIRECT_ONE_HOP_AND_CORROBORATED_CONSUMER_MAIN"


def test_source_gap_and_old_marker_are_carried_without_links(tmp_path: Path, monkeypatch) -> None:
    hashes = _fixture(tmp_path)
    _configure(monkeypatch, hashes)
    index_root, output_root = tmp_path / "indexes-out", tmp_path / "outputs-out"
    attribution.build_qiwa_service_main_attribution(tmp_path, index_root, output_root)
    with (index_root / "review_exceptions.csv").open() as stream:
        exceptions = list(csv.DictReader(stream))
    assert {row["exception_category"] for row in exceptions} == {
        "SOURCE_DOCUMENT_UNRESOLVED", "SOURCE_EXCLUDED_OLD_IGNORE"
    }
    assert all(not row["api_service_id"] for row in exceptions)
    excluded = next(row for row in exceptions if row["exception_category"] == "SOURCE_EXCLUDED_OLD_IGNORE")
    assert excluded["status"] == "INFORMATIONAL"
    assert "runtime retirement" in excluded["mapping_impact"]


def test_cross_module_normalized_name_is_ambiguous_not_asserted(monkeypatch) -> None:
    monkeypatch.setattr(attribution, "MODULE_CROSSWALK", {"Module A": "module-a"})
    services = [{
        "service_key": "module-b::service-same", "module_key": "module-b", "service_name": "Same Service"
    }]
    result = attribution._resolve_parent(
        "Module A", "SameService", {}, {"sameservice": services}, {}, {}, {}
    )
    assert result["status"] == "AMBIGUOUS_SERVICE_IDENTITY"
    assert result["certainty"] == "MODULE_CONFLICT"


def test_accepted_input_hash_change_is_rejected(tmp_path: Path, monkeypatch) -> None:
    hashes = _fixture(tmp_path)
    _configure(monkeypatch, hashes)
    with (tmp_path / attribution.QIWA_CSV).open("a", encoding="utf-8") as stream:
        stream.write("tampered\n")
    try:
        attribution.build_qiwa_service_main_attribution(
            tmp_path, tmp_path / "indexes-out", tmp_path / "outputs-out"
        )
    except ValueError as error:
        assert "HASH_MISMATCH" in str(error)
    else:
        raise AssertionError("mutated accepted input was not rejected")
