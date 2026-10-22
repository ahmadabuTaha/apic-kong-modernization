import hashlib
from pathlib import Path

import business_capability_kg.final_main_capability_mapping as mapping
from business_capability_kg.icd_capability_extraction import parse_document


def test_explicit_source_markers_do_not_treat_incidental_old_as_retired() -> None:
    assert mapping._source_marker("Service", "*IGNORE* - draft") == "SOURCE_DECLARED_UNUSED_OR_IGNORED"
    assert mapping._source_marker("Service", "Get Contract (Old Design)") == "OLD_DESIGN"
    assert mapping._source_marker("Get HRSD Old Visas", "Current ICD") == ""


def test_contract_precedents_remain_direct_and_distinct() -> None:
    assert mapping._contract_page_rule("5516591134", "Admission Journey") .key == "compliance"
    assert mapping._contract_page_rule("4837113943", "external contract created outside Qiwa").key == "employment-lifecycle"
    assert mapping._contract_page_rule("3997073409", "send contract status to GOSI").key == "gosi-integration"


def test_title_only_technical_text_is_not_semantic_evidence() -> None:
    parsed = parse_document(b"<h1>GOSI Integration</h1><p>Technical interface details only.</p>")
    rule = next(rule for rule in mapping.MODULE_RULES["module-certificates"] if rule.key == "gosi")
    assert mapping._evidence_for(rule, parsed, is_isd=False) is None


def test_narrative_evidence_has_a_stable_body_pointer() -> None:
    parsed = parse_document(
        b"<h2>Purpose</h2><p>This service is used to send certificate information to GOSI.</p>"
    )
    rule = next(rule for rule in mapping.MODULE_RULES["module-certificates"] if rule.key == "gosi")
    evidence = mapping._evidence_for(rule, parsed, is_isd=False)
    assert evidence is not None
    assert evidence["block_id"] == "b000002"
    assert evidence["char_end"] > evidence["char_start"]


def _fake_corpus():
    modules = [
        {"module_key": module_key, "module_name": module_key.removeprefix("module-").replace("-", " ").title()}
        for module_key in mapping.MODULE_RULES
    ]
    services_by_module, documents_by_module, bodies = {}, {}, {}
    for index, module in enumerate(modules):
        module_key = module["module_key"]
        service_key = f"{module_key}::service-fixture"
        services_by_module[module_key] = [{
            "module_key": module_key, "service_key": service_key,
            "service_name": "Fixture Service", "occurrence_count": 1,
        }]
        body = f"<h2>Purpose</h2><p>This service is used to manage {module['module_name']} records.</p>".encode()
        digest = hashlib.sha256(body).hexdigest()
        document_key = f"document-icd-{index:02d}"
        bodies[document_key] = body
        base = {
            "module_key": module_key, "module_name": module["module_name"],
            "service_key": service_key, "service_name": "Fixture Service",
            "occurrence_id": f"occ-icd-{index:02d}", "document_key": document_key,
            "document_type": "ICD", "source_row_number": index + 1, "reference_ordinal": 1,
            "physical_identity": f"confluence-page:{7000000000 + index}",
            "page_id": str(7000000000 + index), "status": "FETCHED",
            "blob_sha256": digest, "blob_relative_path": f"documents/blobs/{digest}.html",
            "size_bytes": len(body), "mime_type": "text/html", "title": "Fixture ICD",
            "source_version": "1", "retrieved_at": "", "error_class": "", "error_detail": "",
        }
        documents_by_module[module_key] = [base]

    first_key = modules[0]["module_key"]
    unpaired_service = f"{first_key}::service-isd-only"
    services_by_module[first_key].append({
        "module_key": first_key, "service_key": unpaired_service,
        "service_name": "ISD Only Service", "occurrence_count": 1,
    })
    isd_body = b"<h2>Introduction</h2><p>This service is used to manage a request.</p>"
    isd_digest = hashlib.sha256(isd_body).hexdigest()
    bodies["document-isd-unpaired"] = isd_body
    documents_by_module[first_key].append({
        **documents_by_module[first_key][0], "service_key": unpaired_service,
        "occurrence_id": "occ-isd-unpaired", "document_key": "document-isd-unpaired",
        "document_type": "ISD", "physical_identity": "confluence-page:8000000000",
        "page_id": "8000000000", "blob_sha256": isd_digest,
        "blob_relative_path": f"documents/blobs/{isd_digest}.html", "size_bytes": len(isd_body),
        "title": "Unpaired ISD",
    })
    # This ISD is associated with the active-ICD Service and must never be parsed.
    documents_by_module[first_key].append({
        **documents_by_module[first_key][0], "occurrence_id": "occ-isd-paired",
        "document_key": "document-isd-paired", "document_type": "ISD",
        "physical_identity": "confluence-page:8000000001", "page_id": "8000000001",
        "title": "Paired ISD",
    })
    return modules, services_by_module, documents_by_module, bodies


def test_all_module_build_is_icd_first_resumable_and_deterministic(tmp_path: Path, monkeypatch) -> None:
    modules, services_by_module, documents_by_module, bodies = _fake_corpus()
    loads = []

    class FakeCatalog:
        def __init__(self, *_args, **_kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        def list_modules(self): return modules
        def list_services(self, module_key): return services_by_module[module_key]
        def list_documents(self, module_key): return documents_by_module[module_key]
        def load_document(self, document_key):
            loads.append(document_key)
            return {"status": "ok"}, bodies[document_key]

    monkeypatch.setattr(mapping, "DocumentCatalog", FakeCatalog)
    monkeypatch.setattr(mapping, "_validated_recovery", lambda _root: (
        tmp_path / "catalog", {"catalog": {"sha256": "recovery-hash"}}
    ))
    monkeypatch.setattr(mapping, "EXPECTED", {
        "modules": 32, "services": 33, "icd_occurrences": 32, "isd_occurrences": 2,
    })
    index_root, output_root = tmp_path / "indexes", tmp_path / "outputs"
    first = mapping.build_final_mapping(tmp_path, index_root, output_root)
    first_hashes = {
        path.relative_to(tmp_path).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (*sorted(index_root.glob("*.csv")), output_root / "review_summary.md")
    }
    assert "document-isd-paired" not in loads
    assert loads.index("document-icd-00") < loads.index("document-isd-unpaired")
    assert first["telemetry"]["module_checkpoint_misses"] == 32
    assert first["counts"]["icd_links"] == 32
    assert first["counts"]["isd_links"] == 1

    loads.clear()
    second = mapping.build_final_mapping(tmp_path, index_root, output_root)
    second_hashes = {
        path.relative_to(tmp_path).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (*sorted(index_root.glob("*.csv")), output_root / "review_summary.md")
    }
    assert loads == []
    assert second["telemetry"]["module_checkpoint_hits"] == 32
    assert first_hashes == second_hashes
    assert {path.name for path in index_root.iterdir()} == {
        "main_capabilities.csv", "main_icd_links.csv", "main_isd_links.csv",
        "excluded_sources.csv", "coverage_exceptions.csv", "module_coverage.csv",
    }
    assert len(list((output_root / "modules").glob("module-*.json"))) == 32
