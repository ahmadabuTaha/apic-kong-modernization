import hashlib
from pathlib import Path

import business_capability_kg.contracts_main_icd_mapping as mapping
from business_capability_kg.icd_capability_extraction import parse_document


def test_reviewed_page_registry_has_exact_contracts_coverage_without_duplicate_inflation() -> None:
    assignments = mapping._page_assignments()
    assert len(assignments) == 169
    assert sum(len(keys) for keys in assignments.values()) == 169
    assert set(assignments) == {page for pages in mapping.PAGES_BY_CAPABILITY.values() for page in pages}


def test_contracts_capability_names_are_meaningful_noun_phrases() -> None:
    for label, _definition in mapping.MAIN_CAPABILITIES.values():
        assert "/" not in label
        assert len(label.split()) > 1
        assert label.endswith(("Management", "Monitoring", "Administration", "Synchronization"))


def test_document_title_alone_is_not_mapping_evidence() -> None:
    parsed = parse_document(b"<h1>External Contract Lifecycle</h1><p>Technical interface details only.</p>")
    assert mapping._evidence_for("external-management", parsed) is None


def test_full_narrative_semantics_supply_stable_evidence_pointer() -> None:
    parsed = parse_document(
        b"<h2>Purpose</h2><p>This service is used to create an external contract for a candidate.</p>"
    )
    evidence = mapping._evidence_for("external-management", parsed)
    assert evidence is not None
    assert evidence["block_id"] == "b000002"
    assert evidence["char_end"] > evidence["char_start"]


def _fake_corpus():
    assignments = mapping._page_assignments()
    icd_service_keys = [f"module-contracts::service-fixture-{index:03d}" for index in range(159)]
    no_icd_service_keys = [f"module-contracts::service-isd-only-{index:02d}" for index in range(12)]
    service_keys = icd_service_keys + no_icd_service_keys
    assert len(service_keys) == mapping.EXPECTED_SERVICES
    services = [
        {
            "module_key": mapping.MODULE_KEY, "service_key": key,
            "service_name": key.rsplit("::", 1)[-1], "occurrence_count": 1,
        }
        for key in service_keys
    ]
    samples = {
        "employment-lifecycle": "This service is used to maintain contract details.",
        "template-management": "This service is used to maintain a contract template.",
        "termination-management": "This service is used to submit a contract termination request.",
        "training-management": "This service is used to maintain a training contract.",
        "external-management": "This service is used to create an external contract.",
        "validation-eligibility": "This service is used to validate contract eligibility.",
        "wage-management": "This service is used to update an employee wage.",
        "authentication-compliance": "This service measures contract authentication.",
        "reference-data": "This service returns contract terms.",
        "authority-synchronization": "This service sends a contract to GOSI.",
    }
    documents, bodies = [], {}
    for index, (page_id, capability_keys) in enumerate(sorted(assignments.items())):
        service_key = icd_service_keys[index % len(icd_service_keys)]
        body = ("<h2>Purpose</h2>" + "".join(f"<p>{samples[key]}</p>" for key in capability_keys)).encode()
        digest = hashlib.sha256(body).hexdigest()
        size_bytes = len(body)
        if page_id == mapping.RECOVERED_PAGE:
            digest = mapping.RECOVERED_PAGE_SHA256
            size_bytes = mapping.RECOVERED_PAGE_SIZE
        document_key = f"document-icd-{index:03d}"
        bodies[document_key] = body
        documents.append({
            "module_key": mapping.MODULE_KEY, "module_name": mapping.MODULE_NAME,
            "service_key": service_key, "service_name": service_key, "occurrence_id": f"occ-{index:03d}",
            "document_key": document_key, "document_type": "ICD", "source_row_number": index + 1,
            "reference_ordinal": 1, "physical_identity": f"confluence-page:{page_id}", "page_id": page_id,
            "status": "FETCHED", "blob_sha256": digest, "blob_relative_path": f"documents/blobs/{digest}.html",
            "size_bytes": size_bytes, "mime_type": "text/html", "title": f"ICD {page_id}",
            "source_version": "1", "retrieved_at": "", "error_class": "", "error_detail": "",
        })
    isds = []
    for index, service_key in enumerate(no_icd_service_keys):
        isds.append({
            **documents[0], "service_key": service_key, "document_type": "ISD",
            "page_id": str(8000000000 + index), "document_key": f"document-isd-{index}",
            "occurrence_id": f"isd-occ-{index}", "title": f"ISD {index}",
        })
    return services, documents, isds, bodies


def test_bounded_build_closes_every_contracts_icd_and_keeps_isd_only_separate(
    tmp_path: Path, monkeypatch
) -> None:
    services, documents, isds, bodies = _fake_corpus()

    class FakeCatalog:
        def __init__(self, *_args, **_kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        def list_modules(self): return [{"module_key": mapping.MODULE_KEY, "module_name": mapping.MODULE_NAME}]
        def list_services(self, _module): return services
        def list_documents(self, _module, document_type=None): return documents if document_type == "ICD" else isds
        def load_document(self, document_key): return {"status": "ok"}, bodies[document_key]

    monkeypatch.setattr(mapping, "DocumentCatalog", FakeCatalog)
    monkeypatch.setattr(mapping, "_validated_recovery", lambda _root: (
        tmp_path / "catalog", {"catalog": {"sha256": "recovery-hash"}}
    ))
    index_root, output_root = tmp_path / "indexes", tmp_path / "outputs"
    frozen = tmp_path / "frozen.marker"
    frozen.write_text("unchanged")
    first = mapping.build_main_icd_mapping(tmp_path, index_root, output_root)
    first_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in index_root.glob("*.csv")}
    second = mapping.build_main_icd_mapping(tmp_path, index_root, output_root)
    second_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in index_root.glob("*.csv")}

    assert first["counts"]["unique_icds"] == 169
    assert first["counts"]["mapped_unique_icds"] == 169
    assert first["counts"]["unresolved_icds"] == 0
    assert first["counts"]["main_icd_links"] == 169
    assert first["counts"]["isd_only_no_icd_services"] == 12
    assert first_hashes == second_hashes
    assert frozen.read_text() == "unchanged"
    summary = (output_root / "review_summary.md").read_text()
    assert "169 unique ICDs mapped, 0 unresolved ICDs" in summary
    assert "470,298-byte blob" in summary


def test_only_authorized_artifacts_are_emitted(tmp_path: Path, monkeypatch) -> None:
    services, documents, isds, bodies = _fake_corpus()

    class FakeCatalog:
        def __init__(self, *_args, **_kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        def list_modules(self): return [{"module_key": mapping.MODULE_KEY, "module_name": mapping.MODULE_NAME}]
        def list_services(self, _module): return services
        def list_documents(self, _module, document_type=None): return documents if document_type == "ICD" else isds
        def load_document(self, document_key): return {"status": "ok"}, bodies[document_key]

    monkeypatch.setattr(mapping, "DocumentCatalog", FakeCatalog)
    monkeypatch.setattr(mapping, "_validated_recovery", lambda _root: (
        tmp_path / "catalog", {"catalog": {"sha256": "recovery-hash"}}
    ))
    index_root, output_root = tmp_path / "indexes", tmp_path / "outputs"
    mapping.build_main_icd_mapping(tmp_path, index_root, output_root)
    assert {path.name for path in index_root.iterdir()} == {
        "main_capabilities.csv", "main_icd_links.csv", "coverage_exceptions.csv"
    }
    assert {path.name for path in output_root.iterdir()} == {"review_summary.md"}
