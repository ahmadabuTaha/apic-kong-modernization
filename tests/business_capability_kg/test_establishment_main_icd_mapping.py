import hashlib
from pathlib import Path

import business_capability_kg.establishment_main_icd_mapping as mapping
from business_capability_kg.icd_capability_extraction import parse_document


def test_reviewed_page_registry_has_exact_coverage_without_duplicate_inflation() -> None:
    assignments = mapping._page_assignments()
    assert len(assignments) == 149
    assert sum(len(keys) for keys in assignments.values()) == 152
    assert {page for page, keys in assignments.items() if len(keys) > 1} == {
        "3694166278", "4151542188", "4904353793"
    }


def test_document_title_alone_is_not_mapping_evidence() -> None:
    parsed = parse_document(b"<h1>Open Establishment</h1><p>Technical interface details only.</p>")
    assert mapping._evidence_for("registration-opening", parsed) is None


def test_full_narrative_semantics_supply_stable_evidence_pointer() -> None:
    parsed = parse_document(
        b"<h2>Purpose</h2><p>This service is used to transfer ownership of an establishment.</p>"
    )
    evidence = mapping._evidence_for("ownership-representation", parsed)
    assert evidence is not None
    assert evidence["block_id"] == "b000002"
    assert evidence["char_end"] > evidence["char_start"]


def _fake_corpus():
    assignments = mapping._page_assignments()
    no_icd = {
        "module-establishment::service-terminate-establishments-punishments-icd",
        "module-establishment::service-violation-management-interface-specification-documents",
        "module-establishment::service-establishment-logo-isds",
    }
    distinct_flagged = list(dict.fromkeys(mapping.FLAGGED_SERVICE_INPUT))
    fillers = [f"module-establishment::service-fixture-{index:03d}" for index in range(122)]
    service_keys = distinct_flagged + fillers
    assert len(service_keys) == 142
    services = [
        {
            "module_key": mapping.MODULE_KEY, "service_key": key,
            "service_name": key.rsplit("::", 1)[-1], "occurrence_count": 1,
        }
        for key in service_keys
    ]
    icd_service_pool = [key for key in service_keys if key not in no_icd]
    samples = {
        "registration-opening": "This service is used to open a new establishment file.",
        "activity-management": "This service is used to manage establishment activity eligibility.",
        "location-management": "This service is used to update an establishment location.",
        "license-management": "This service is used to maintain an establishment license.",
        "ownership-representation": "This service is used to transfer ownership of an establishment.",
        "record-hierarchy": "This service is used to update a CR record and unified number.",
        "request-agent": "This service is used to submit a government agent request.",
        "closure": "This service is used to close an establishment.",
        "compliance-violation": "This service is used to manage an establishment violation.",
        "logo-management": "This service is used to add an establishment logo.",
        "stakeholder-notification": "This service is used to send email notification to the owner.",
    }
    documents, bodies = [], {}
    for index, (page_id, capability_keys) in enumerate(sorted(assignments.items())):
        service_key = icd_service_pool[index % len(icd_service_pool)]
        body = ("<h2>Purpose</h2>" + "".join(f"<p>{samples[key]}</p>" for key in capability_keys)).encode()
        digest = hashlib.sha256(body).hexdigest()
        document_key = f"document-icd-{index:03d}"
        bodies[document_key] = body
        documents.append({
            "module_key": mapping.MODULE_KEY, "module_name": mapping.MODULE_NAME,
            "service_key": service_key, "service_name": service_key, "occurrence_id": f"occ-{index:03d}",
            "document_key": document_key, "document_type": "ICD", "source_row_number": index + 1,
            "reference_ordinal": 1, "physical_identity": f"confluence-page:{page_id}", "page_id": page_id,
            "status": "FETCHED", "blob_sha256": digest, "blob_relative_path": f"documents/blobs/{digest}.html",
            "size_bytes": len(body), "mime_type": "text/html", "title": f"ICD {page_id}",
            "source_version": "1", "retrieved_at": "", "error_class": "", "error_detail": "",
        })
    isds = []
    for index, service_key in enumerate(sorted(no_icd)):
        page_id = str(8000000000 + index)
        isds.append({
            **documents[0], "service_key": service_key, "document_type": "ISD",
            "page_id": page_id, "document_key": f"document-isd-{index}",
            "occurrence_id": f"isd-occ-{index}", "title": f"ISD {index}",
        })
    return services, documents, isds, bodies


def test_bounded_build_closes_every_icd_and_reconciles_flagged_duplicates(tmp_path: Path, monkeypatch) -> None:
    services, documents, isds, bodies = _fake_corpus()

    class FakeCatalog:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def list_modules(self):
            return [{"module_key": mapping.MODULE_KEY, "module_name": mapping.MODULE_NAME}]

        def list_services(self, _module):
            return services

        def list_documents(self, _module, document_type=None):
            return documents if document_type == "ICD" else isds

        def load_document(self, document_key):
            return {"status": "ok"}, bodies[document_key]

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

    assert first["counts"]["unique_icds"] == 149
    assert first["counts"]["mapped_unique_icds"] == 149
    assert first["counts"]["unresolved_icds"] == 0
    assert first["counts"]["main_icd_links"] == 152
    assert first["counts"]["flagged_input_entries"] == 22
    assert first["counts"]["flagged_distinct_services"] == 20
    assert first_hashes == second_hashes
    assert frozen.read_text() == "unchanged"
    summary = (output_root / "review_summary.md").read_text()
    assert "appears 3 times" in summary
    assert "149 unique ICDs mapped, 0 unresolved ICDs" in summary


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
