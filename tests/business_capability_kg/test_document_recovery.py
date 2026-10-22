import json
from pathlib import Path

import business_capability_kg.document_recovery as recovery
from business_capability_kg.icd_capability_extraction import extract_functions, parse_document


def _tool_result(data: dict) -> dict:
    return {"content": [{"type": "text", "text": json.dumps({"data": data})}]}


def test_html_and_adf_source_representations_are_preserved() -> None:
    html, html_type, html_suffix = recovery._body_bytes({"body": {"value": "<p>business</p>"}})
    assert html == b"<p>business</p>"
    assert html_type == "text/html; charset=utf-8" and html_suffix == ".html"

    adf = {
        "version": 1, "type": "doc", "content": [
            {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Purpose"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "This service is used to approve contracts."}]},
        ],
    }
    content, mime_type, suffix = recovery._body_bytes({"body": adf})
    assert mime_type == "application/vnd.atlassian.document+json" and suffix == ".adf.json"
    parsed = parse_document(content, mime_type)
    assert parsed["parse_status"] == "PARSED"
    assert [row["kind"] for row in parsed["blocks"]] == ["heading", "paragraph"]
    assert extract_functions(parsed)[0]["sub_label"] == "Approve Contracts"


def test_child_classification_uses_title_and_content_not_parent_assumption() -> None:
    scheduler = {
        "title": "UpdateStatus-Scheduler",
        "body": {"value": "<h1>UpdateStatus - ICD</h1><p>Document Control</p>"},
    }
    ignored = {
        "title": "Ignore this document - To be deleted",
        "body": {"value": "<h1>Old ICD</h1>"},
    }
    unrelated = {"title": "Navigation", "body": {"value": "<p>Child links</p>"}}
    assert recovery._classify_child(scheduler, "ICD")[0] == "VALID_ICD_CHILD"
    assert recovery._classify_child(ignored, "ICD")[0] == "EXCLUDED_SUPERSEDED"
    assert recovery._classify_child(unrelated, "ICD")[0] == "UNRESOLVED_CHILD_TYPE"


def test_snapshot_reader_accepts_authorized_envelope_and_descendants(tmp_path: Path) -> None:
    page = {"id": "101", "title": "Example ICD", "body": {"value": "<p>content</p>"}}
    (tmp_path / "101.json").write_text(json.dumps(_tool_result(page)))
    descendants = [{"id": "102", "title": "Child ICD", "parentId": "101"}]
    direct_list = {"content": [{"type": "text", "text": json.dumps({"results": descendants})}]}
    (tmp_path / "101-descendants.json").write_text(json.dumps(direct_list))
    assert recovery._snapshot_data(tmp_path, "101")["title"] == "Example ICD"
    assert recovery._descendants(tmp_path, "101")[0]["id"] == "102"


def test_recovery_scope_and_wps_override_are_explicit() -> None:
    assert len(recovery.DIRECT_ICD_PAGES) == 8
    assert len(recovery.PARENT_GROUPS) == 5
    wps = recovery.PARENT_GROUPS[0]
    assert wps["name"] == "WPS"
    assert wps["override_module"] == "module-wage-protection"
    assert wps["override_service"] == "module-wage-protection::service-wps"
