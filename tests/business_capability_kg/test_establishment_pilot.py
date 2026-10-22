import hashlib
import json
from pathlib import Path

import business_capability_kg.establishment_pilot as pilot
from business_capability_kg.icd_capability_extraction import parse_document


def test_function_extraction_requires_full_wording_and_preserves_exact_pointer() -> None:
    parsed = parse_document(b"""
        <h1>Approve Establishment</h1>
        <h2>Purpose</h2>
        <p>This service is used to approve an establishment request.</p>
        <p>This service is used to reject an establishment request when ownership evidence is missing.</p>
        <table><tr><td>This service is used to validate establishment eligibility.</td></tr></table>
    """)
    functions = pilot.extract_business_functions(parsed)
    assert [row["action"] for row in functions] == ["approve", "reject", "validate"]
    assert functions[1]["conditions_rules"] == "when ownership evidence is missing"
    assert all(row["block_id"].startswith("b") for row in functions)
    assert all(row["char_end"] > row["char_start"] for row in functions)


def test_headings_names_and_technical_sections_are_not_functions() -> None:
    parsed = parse_document(b"""
        <h1>Open Establishment</h1>
        <p>Establishment details are available.</p>
        <h2>API Endpoints</h2>
        <p>This service is used to send an HTTP request to an API endpoint.</p>
    """)
    assert pilot.extract_business_functions(parsed) == []


def test_repeated_sources_are_retained_but_semantic_identity_is_stable() -> None:
    parsed = parse_document(b"""
        <h2>Purpose</h2>
        <p>This service is used to open an establishment using a commercial registration.</p>
        <h2>Scope</h2>
        <p>This service is used to open an establishment using a commercial registration.</p>
    """)
    rows = pilot.extract_business_functions(parsed)
    assert len(rows) == 2
    assert rows[0]["normalized_label"] == rows[1]["normalized_label"]
    assert rows[0]["block_id"] != rows[1]["block_id"]


def test_explicit_compound_actions_become_distinct_business_functions() -> None:
    parsed = parse_document(
        b"<h2>Purpose</h2><p>This service is used to approve or reject a government agent request.</p>"
    )
    rows = pilot.extract_business_functions(parsed)
    assert [(row["action"], row["business_object"]) for row in rows] == [
        ("approve", "government agent request"), ("reject", "government agent request")
    ]


def test_grouping_occurs_from_functions_and_ambiguous_function_is_unmatched() -> None:
    activity = {
        "candidate_label": "Change establishment activity", "business_object": "establishment activity",
        "purpose_outcome": "", "conditions_rules": "", "source_phrases": ["change activity"],
    }
    ambiguous = {
        "candidate_label": "Calculate fees", "business_object": "fees",
        "purpose_outcome": "", "conditions_rules": "", "source_phrases": ["calculate fees"],
    }
    matches = pilot._group_matches(activity)
    assert any(rule["label"] == "Establishment Activity Management" for rule, _ in matches)
    assert pilot._group_matches(ambiguous) == []


def test_parse_cache_cold_warm_and_invalidation(tmp_path: Path, monkeypatch) -> None:
    body = b"<h2>Purpose</h2><p>This service is used to open an establishment file.</p>"
    digest = hashlib.sha256(body).hexdigest()
    document = {
        "document_key": "doc-1", "blob_sha256": digest, "mime_type": "text/html",
        "size_bytes": len(body),
    }

    class Catalog:
        reads = 0

        def load_document(self, _document_key):
            self.reads += 1
            return {"status": "ok"}, body

    catalog = Catalog()
    telemetry = pilot.Counter()
    first = pilot._parse_cached(catalog, document, tmp_path, telemetry)
    second = pilot._parse_cached(catalog, document, tmp_path, telemetry)
    assert first[0] == second[0]
    assert catalog.reads == 1
    assert telemetry["cache_misses"] == 1 and telemetry["cache_hits"] == 1
    monkeypatch.setattr(pilot, "EXTRACTOR_VERSION", "changed")
    pilot._parse_cached(catalog, document, tmp_path, telemetry)
    assert catalog.reads == 2


def test_end_to_end_scope_integrity_dedupe_and_no_sub_capabilities(tmp_path: Path, monkeypatch) -> None:
    services = [
        {
            "module_key": pilot.MODULE_KEY, "service_key": f"service-{index:03d}",
            "service_name": f"Service {index:03d}", "occurrence_count": 1,
        }
        for index in range(142)
    ]
    suspected = list(pilot.SUSPECTED_PAGE_IDS)
    documents = []
    bodies = {}
    for index in range(149):
        page_id = suspected[index] if index < 5 else str(7000000000 + index)
        # Two blocks in each document exercise repeated-source retention and
        # within-Module semantic deduplication.
        body = (
            f"<h2>Purpose</h2><p>This service is used to open establishment record {index}.</p>"
            f"<h2>Scope</h2><p>This service is used to open establishment record {index}.</p>"
            "<p>Supporting business context is deliberately long enough to distinguish this source from the known placeholder representation.</p>"
        ).encode()
        digest = hashlib.sha256(body).hexdigest()
        key = f"doc-{index:03d}"
        bodies[key] = body
        documents.append({
            "module_key": pilot.MODULE_KEY, "module_name": pilot.MODULE_NAME,
            "service_key": f"service-{index % 139:03d}", "service_name": f"Service {index % 139:03d}",
            "occurrence_id": f"occ-{index:03d}", "document_key": key, "document_type": "ICD",
            "source_row_number": index + 1, "reference_ordinal": 1,
            "physical_identity": f"page:{page_id}", "page_id": page_id, "status": "FETCHED",
            "blob_sha256": digest, "blob_relative_path": f"documents/blobs/{digest}.html",
            "size_bytes": len(body), "mime_type": "text/html", "title": f"ICD {index}",
            "source_version": "1", "retrieved_at": "", "error_class": "", "error_detail": "",
        })
    isds = [{**documents[0], "document_type": "ISD", "document_key": "isd-1", "occurrence_id": "isd-occ-1"}]

    class FakeCatalog:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def list_modules(self):
            return [{"module_key": pilot.MODULE_KEY, "module_name": pilot.MODULE_NAME, "service_count": 142, "occurrence_count": 150}]

        def list_services(self, _module):
            return services

        def list_documents(self, _module, document_type=None):
            return documents if document_type == "ICD" else isds

        def load_document(self, document_key):
            return {"status": "ok"}, bodies[document_key]

    investigation = {
        page_id: {
            "page_id": page_id, "classification": "RECOVERED_SOURCE_BODY", "retrieval_status": "SUCCESS",
            "original_size_bytes": "198", "original_sha256": pilot.PLACEHOLDER_SHA256,
            "effective_sha256": documents[index]["blob_sha256"], "diagnostic": "PLACEHOLDER_BODY_REPLACED",
        }
        for index, page_id in enumerate(suspected)
    }
    monkeypatch.setattr(pilot, "DocumentCatalog", FakeCatalog)
    monkeypatch.setattr(pilot, "_validated_recovery", lambda _root: {
        "manifest_sha256": "m", "catalog_sha256": "c", "investigated_sha256": "i",
        "catalog_path": tmp_path / "catalog", "investigated": investigation,
    })
    index_root, output_root = tmp_path / "indexes", tmp_path / "outputs"
    frozen = tmp_path / "frozen.marker"
    frozen.write_text("unchanged")
    cold = pilot.build_establishment_pilot(tmp_path, index_root, output_root)
    cold_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in index_root.glob("*.csv")
    }
    warm = pilot.build_establishment_pilot(tmp_path, index_root, output_root)
    warm_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in index_root.glob("*.csv")
    }

    assert cold["manifest"]["counts"]["icd_occurrences"] == 149
    assert cold["manifest"]["counts"]["business_functions"] == 149
    assert cold["manifest"]["counts"]["function_evidence"] == 298
    assert cold["manifest"]["validations"]["all_five_recovered_and_validated"]
    assert cold["manifest"]["cache_telemetry"]["cache_misses"] == 149
    assert warm["manifest"]["cache_telemetry"]["cache_hits"] == 149
    assert cold_hashes == warm_hashes
    assert frozen.read_text() == "unchanged"
    assert not list(index_root.glob("*sub_capabilit*"))
    assert not list(output_root.glob("*sub_capabilit*"))
    assert json.loads((output_root / "pilot_manifest.json").read_text())["status"] == "EA_REVIEW_019E_R1"
