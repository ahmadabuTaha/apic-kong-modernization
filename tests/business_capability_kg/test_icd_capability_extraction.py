import json
from pathlib import Path

import business_capability_kg.icd_capability_extraction as extraction


def test_structured_html_parses_headings_mixed_content_tables_and_offsets() -> None:
    content = b"""
    <h1>Introduction</h1><h2>Purpose</h2>
    <p>This service is used to approve or reject external contracts.</p>
    <ul><li>The service allows the user to validate contract eligibility.</li></ul>
    <table><tr><th>Rule</th><th>Meaning</th></tr>
    <tr><td>This service is used to calculate contract fees.</td><td>Business rule</td></tr></table>
    """
    parsed = extraction.parse_html(content)
    functions = extraction.extract_functions(parsed)
    assert parsed["parse_status"] == "PARSED"
    assert [row["kind"] for row in parsed["blocks"]] == [
        "heading", "heading", "paragraph", "list_item", "table_row", "table_row"
    ]
    assert all(row["char_end"] > row["char_start"] for row in parsed["blocks"])
    labels = {row["sub_label"] for row in functions}
    assert "Approve Or Reject External Contracts" in labels
    assert "Validate Contract Eligibility" in labels
    assert "Calculate Contract Fees" in labels


def test_low_evidence_and_technical_sections_refuse_candidates() -> None:
    content = b"""
    <h2>Service Endpoints</h2><p>This service is used to send JSON request to API endpoint.</p>
    <h2>Notes</h2><p>Contract information is available in the system.</p>
    """
    parsed = extraction.parse_html(content)
    assert extraction.extract_functions(parsed) == []

    auth = extraction.parse_html(
        b"<h2>Purpose</h2><p>This service is used to get OAuth bearer token for service authentication.</p>"
    )
    assert extraction.extract_functions(auth) == []


def test_malformed_utf8_is_explicit() -> None:
    parsed = extraction.parse_html(b"<p>\xff</p>")
    assert parsed["parse_status"] == "MALFORMED"
    assert parsed["gap_reason"].startswith("utf8_decode_error")


def test_multi_capability_and_evidence_redaction() -> None:
    content = b"""
    <h2>Purpose</h2>
    <p>This service is used to create visa requests. This service is used to validate worker eligibility.</p>
    <p>This service is used to retrieve details from https://private.invalid/path.</p>
    """
    parsed = extraction.parse_html(content)
    functions = extraction.extract_functions(parsed)
    assert len(functions) == 3
    assert len({row["sub_label"] for row in functions}) == 3
    assert all("private.invalid" not in row["source_wording"] for row in functions)


def test_cross_module_queue_observes_exact_labels_without_merging() -> None:
    subs = [
        {"module_key": "module-a", "sub_capability_id": "sub-a", "normalized_label": "approve contract", "evidence_count": 2},
        {"module_key": "module-b", "sub_capability_id": "sub-b", "normalized_label": "approve contract", "evidence_count": 1},
        {"module_key": "module-c", "sub_capability_id": "sub-c", "normalized_label": "issue visa", "evidence_count": 1},
    ]
    rows = extraction._cross_module_candidates(subs)
    assert len(rows) == 1
    assert rows[0]["status"] == "EA_COMPARISON_REQUIRED_NO_MERGE"
    assert rows[0]["module_a"] == "module-a" and rows[0]["module_b"] == "module-b"


def test_parser_cache_hit_and_version_invalidation(tmp_path: Path, monkeypatch) -> None:
    body = b"<h2>Purpose</h2><p>This service is used to create contract requests.</p>"
    digest = extraction._sha256_bytes(body)
    document = {"document_key": "doc-1", "blob_sha256": digest}

    class Catalog:
        def __init__(self) -> None:
            self.reads = 0

        def load_document(self, document_id: str):
            self.reads += 1
            return {"status": "ok"}, body

    catalog = Catalog()
    telemetry = extraction.Counter()
    first = extraction._parsed_document(catalog, document, tmp_path, telemetry)
    second = extraction._parsed_document(catalog, document, tmp_path, telemetry)
    assert first == second and catalog.reads == 1
    assert telemetry["parse_misses"] == 1 and telemetry["parse_hits"] == 1
    monkeypatch.setattr(extraction, "RULES_VERSION", "changed-rules")
    extraction._parsed_document(catalog, document, tmp_path, telemetry)
    assert catalog.reads == 2 and telemetry["parse_misses"] == 2


def test_module_checkpoint_requires_signature_and_model_hash(tmp_path: Path) -> None:
    model = tmp_path / "module_capability_model.json"
    manifest = tmp_path / "module_completion_manifest.json"
    model.write_bytes(extraction._json_bytes({"module": "a"}))
    manifest.write_bytes(extraction._json_bytes({
        "schema_version": extraction.SCHEMA_VERSION,
        "source_signature": "source-a",
        "model_sha256": extraction._sha256_file(model),
        "completion_status": "MODULE_COMPLETE_WITH_GAPS",
    }))
    assert extraction._module_checkpoint_valid(tmp_path, "source-a")
    assert not extraction._module_checkpoint_valid(tmp_path, "source-b")
    model.write_text("changed")
    assert not extraction._module_checkpoint_valid(tmp_path, "source-a")


def test_review_record_for_no_icd_service_is_stable() -> None:
    first = extraction._review("module-a", "NO_ICD_REFERENCE", "gap", "service-a")
    second = extraction._review("module-a", "NO_ICD_REFERENCE", "gap", "service-a")
    assert first == second
    assert first["status"] == "EA_REVIEW_REQUIRED"


def test_module_build_reuses_shared_icd_and_accounts_for_no_icd(tmp_path: Path) -> None:
    body = b"<h2>Purpose</h2><p>This service is used to approve contract requests.</p>"
    digest = extraction._sha256_bytes(body)
    module = {"module_key": "module-a", "module_name": "Module A"}
    services = [
        {"module_key": "module-a", "service_key": key, "service_name": key, "occurrence_count": count}
        for key, count in (("service-a", 1), ("service-b", 1), ("service-no-icd", 0))
    ]
    documents = [
        {
            "module_key": "module-a", "service_key": service, "occurrence_id": f"occ-{index}",
            "document_key": f"doc-{index}", "physical_identity": "page-1", "blob_sha256": digest,
            "source_version": "v1", "size_bytes": len(body), "status": "FETCHED",
            "source_row_number": index, "reference_ordinal": 1,
        }
        for index, service in enumerate(("service-a", "service-b"), start=1)
    ]

    class Catalog:
        def __init__(self) -> None:
            self.reads = 0

        def load_document(self, document_id: str):
            self.reads += 1
            return {"status": "ok"}, body

    catalog = Catalog()
    built = extraction._build_module(
        module, services, documents, catalog, tmp_path, "source-signature", extraction.Counter()
    )
    model = built["model"]
    assert catalog.reads == 1
    assert [row["cache_status"] for row in model["icd_parse_status"]] == ["MISS", "MODULE_REUSE"]
    assert len(model["sub_capabilities"]) == 1
    assert model["sub_capabilities"][0]["service_count"] == 2
    assert len(model["capability_service_icd_edges"]) == 2
    assert model["main_capabilities"][0]["sub_capability_count"] == 1
    assert {row["issue_type"] for row in model["review_queue"]} == {"NO_ICD_REFERENCE"}
    assert built["completion"]["completion_status"] == "MODULE_COMPLETE_WITH_GAPS"
