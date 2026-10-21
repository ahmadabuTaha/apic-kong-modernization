import hashlib
import json
from pathlib import Path

import business_capability_kg.document_acquisition as acquisition


ROOT = Path(__file__).resolve().parents[2]


def _small_plan() -> dict:
    occurrences = [
        {
            "occurrence_id": "occ-1", "module_key": "module-a", "service_key": "service-a",
            "document_key": "document-icd-1", "document_type": "ICD", "source_row_number": 2,
            "reference_ordinal": 1, "physical_identity": "confluence-page:101", "page_id": "101",
        },
        {
            "occurrence_id": "occ-2", "module_key": "module-b", "service_key": "service-b",
            "document_key": "document-isd-1", "document_type": "ISD", "source_row_number": 3,
            "reference_ordinal": 1, "physical_identity": "confluence-page:101", "page_id": "101",
        },
        {
            "occurrence_id": "occ-3", "module_key": "module-b", "service_key": "service-b",
            "document_key": "unsupported", "document_type": "ISD", "source_row_number": 3,
            "reference_ordinal": 2, "physical_identity": "unsupported:unsupported", "page_id": "",
        },
    ]
    core = {
        "modules": {"module-a": "A", "module-b": "B"},
        "services": [
            {"module_key": "module-a", "service_key": "service-a"},
            {"module_key": "module-b", "service_key": "service-b"},
        ],
        "occurrences": occurrences,
    }
    return {
        **core,
        "plan_sha256": acquisition._sha256(acquisition._json_bytes(core)),
        "baseline_manifest_sha256": "baseline-hash",
    }


def _success(body: str = "<h1>ICD</h1><p>complete source</p>") -> dict:
    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "data": {
                    "id": "101", "type": "page", "title": "Document title", "status": "current",
                    "spaceId": "42", "snapshotToken": "v:7",
                    "body": {"format": "html", "value": body},
                }
            }),
        }]
    }


def test_real_plan_reconciles_frozen_inventory_without_urls() -> None:
    plan = acquisition.build_acquisition_plan(ROOT)
    assert len(plan["modules"]) == 32
    assert len(plan["services"]) == 952
    assert len(plan["occurrences"]) == 1941
    assert sum(row["document_type"] == "ICD" for row in plan["occurrences"]) == 988
    assert sum(row["document_type"] == "ISD" for row in plan["occurrences"]) == 953
    rendered = json.dumps(plan)
    assert "https://" not in rendered and "http://" not in rendered
    assert all(row["page_id"].isdigit() for row in plan["occurrences"])


def test_prepare_preserves_every_occurrence_as_pending_pointer(tmp_path: Path) -> None:
    output, indexes = tmp_path / "output", tmp_path / "indexes"
    acquisition.prepare_acquisition(ROOT, output)
    result = acquisition.finalize_acquisition(ROOT, output, indexes)
    counts = result["manifest"]["counts"]
    assert counts == {
        "modules": 32, "services": 952, "reference_occurrences": 1941,
        "icd_occurrences": 988, "isd_occurrences": 953,
        "fetched": 0, "blocked": 0, "failed": 0, "pending": 1941,
    }
    assert len(list((output / "modules").glob("*/icd/*.json"))) == 988
    assert len(list((output / "modules").glob("*/isd/*.json"))) == 953
    assert result["manifest"]["storage"]["size_bytes"] == 0
    summary = result["summary"].decode("utf-8")
    assert summary.rstrip().splitlines()[-1].endswith("Unavailable remote sizes are unmeasured.")
    assert summary.count("## Storage & File Size Totals") == 1


def test_fetched_blob_dedup_overlap_sizes_and_module_logical_bytes(tmp_path: Path, monkeypatch) -> None:
    plan = _small_plan()
    monkeypatch.setattr(acquisition, "build_acquisition_plan", lambda root: plan)
    output, indexes = tmp_path / "output", tmp_path / "indexes"
    acquisition.prepare_acquisition(ROOT, output)
    record = acquisition.ingest_retrieval(ROOT, "confluence-page:101", _success(), output)
    result = acquisition.finalize_acquisition(ROOT, output, indexes)
    content = "<h1>ICD</h1><p>complete source</p>".encode()
    digest = hashlib.sha256(content).hexdigest()
    blob = output / "documents/blobs" / f"{digest}.html"
    assert record["status"] == "FETCHED"
    assert blob.read_bytes() == content
    storage = result["manifest"]["storage"]
    assert storage["unique_physical_file_count"] == 1
    assert storage["size_bytes"] == len(content) == blob.stat().st_size
    assert storage["icd_distinct_file_count"] == storage["isd_distinct_file_count"] == 1
    assert storage["icd_isd_overlap_file_count"] == 1
    assert storage["icd_isd_overlap_size_bytes"] == len(content)
    coverage = {row["module_key"]: row for row in result["coverage"]}
    assert coverage["module-a"]["logical_size_bytes"] == len(content)
    assert coverage["module-b"]["logical_size_bytes"] == len(content)
    assert result["manifest"]["counts"] == {
        "modules": 2, "services": 2, "reference_occurrences": 3,
        "icd_occurrences": 1, "isd_occurrences": 2,
        "fetched": 2, "blocked": 1, "failed": 0, "pending": 0,
    }


def test_resume_skips_fetched_and_detects_changed_content(tmp_path: Path, monkeypatch) -> None:
    plan = _small_plan()
    monkeypatch.setattr(acquisition, "build_acquisition_plan", lambda root: plan)
    output = tmp_path / "output"
    acquisition.prepare_acquisition(ROOT, output)
    first = acquisition.ingest_retrieval(ROOT, "confluence-page:101", _success("<p>one</p>"), output)
    assert acquisition.acquisition_worklist(ROOT, output) == []
    refresh = acquisition.acquisition_worklist(ROOT, output, refresh_fetched=True)
    assert refresh == [{"physical_identity": "confluence-page:101", "page_id": "101"}]
    second = acquisition.ingest_retrieval(ROOT, "confluence-page:101", _success("<p>two</p>"), output)
    assert first["blob_sha256"] != second["blob_sha256"]
    assert second["version_changed"] is True
    assert second["previous_blob_sha256"] == first["blob_sha256"]


def test_access_and_transient_errors_remain_explicit(tmp_path: Path, monkeypatch) -> None:
    plan = _small_plan()
    monkeypatch.setattr(acquisition, "build_acquisition_plan", lambda root: plan)
    output = tmp_path / "output"
    acquisition.prepare_acquisition(ROOT, output)
    blocked = acquisition.ingest_retrieval(
        ROOT, "confluence-page:101",
        {"content": [{"type": "text", "text": json.dumps({"error": "403 forbidden"})}]}, output,
    )
    assert blocked["status"] == "BLOCKED" and blocked["error_class"] == "ACCESS_BLOCKED"
    assert acquisition.acquisition_worklist(ROOT, output) == []


def test_rate_limit_preserves_retry_budget_and_error_detail(tmp_path: Path, monkeypatch) -> None:
    plan = _small_plan()
    monkeypatch.setattr(acquisition, "build_acquisition_plan", lambda root: plan)
    output = tmp_path / "output"
    acquisition.prepare_acquisition(ROOT, output)
    throttled = acquisition.ingest_retrieval(
        ROOT, "confluence-page:101",
        {
            "isError": True,
            "content": [{"type": "text", "text": json.dumps({"message": "HTTP 429 Too Many Requests"})}],
        },
        output,
    )
    assert throttled["status"] == "PENDING"
    assert throttled["error_class"] == "RATE_LIMITED"
    assert throttled["attempt_count"] == 0
    assert "429" in throttled["error_detail"]
    assert acquisition.acquisition_worklist(ROOT, output) == [
        {"physical_identity": "confluence-page:101", "page_id": "101"}
    ]


def test_direct_atlassian_page_envelope_is_accepted(tmp_path: Path, monkeypatch) -> None:
    plan = _small_plan()
    monkeypatch.setattr(acquisition, "build_acquisition_plan", lambda root: plan)
    output = tmp_path / "output"
    acquisition.prepare_acquisition(ROOT, output)
    body = "<h1>Direct connector content</h1>"
    direct = {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "id": "101", "type": "page", "title": "Direct page",
                "version": {"number": 41}, "body": body,
                "webUrl": "https://private.example.invalid/wiki/pages/101",
            }),
        }]
    }
    record = acquisition.ingest_retrieval(ROOT, "confluence-page:101", direct, output)
    assert record["status"] == "FETCHED"
    assert record["source_version"] == "41"
    assert (output / record["blob_relative_path"]).read_text() == body
    assert "private.example.invalid" not in json.dumps(record)


def test_unchanged_finalize_is_byte_stable_and_storage_matches_filesystem(tmp_path: Path, monkeypatch) -> None:
    plan = _small_plan()
    monkeypatch.setattr(acquisition, "build_acquisition_plan", lambda root: plan)
    output, indexes = tmp_path / "output", tmp_path / "indexes"
    acquisition.prepare_acquisition(ROOT, output)
    acquisition.ingest_retrieval(ROOT, "confluence-page:101", _success(), output)
    acquisition.finalize_acquisition(ROOT, output, indexes)
    before_indexes = {path.name: path.read_bytes() for path in indexes.iterdir()}
    before_reports = {
        path.name: path.read_bytes() for path in output.iterdir()
        if path.is_file() and path.name != "progress.json"
    }
    result = acquisition.finalize_acquisition(ROOT, output, indexes)
    assert before_indexes == {path.name: path.read_bytes() for path in indexes.iterdir()}
    assert before_reports == {
        path.name: path.read_bytes() for path in output.iterdir()
        if path.is_file() and path.name != "progress.json"
    }
    measured = sum(path.stat().st_size for path in (output / "documents/blobs").iterdir())
    assert result["manifest"]["storage"]["size_bytes"] == measured
    measured_indexes = sum(path.stat().st_size for path in indexes.iterdir())
    assert result["manifest"]["storage"]["index_file_count"] == 3
    assert result["manifest"]["storage"]["index_size_bytes"] == measured_indexes
