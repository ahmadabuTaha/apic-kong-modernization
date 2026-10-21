import csv
import hashlib
import json
from pathlib import Path

import pytest

import business_capability_kg.document_cache as cache


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _fixture(root: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    monkeypatch.setattr(cache, "EXPECTED", {
        "modules": 2, "services": 3, "occurrences": 5, "ICD": 3, "ISD": 2,
        "fetched": 4, "failed": 1, "physical_identities": 4, "blobs": 3,
        "content_bytes": 18,
    })
    b_index = root / cache.BASELINE_019B_INDEX
    c_index = root / cache.BASELINE_019C_INDEX
    c_output = root / cache.BASELINE_019C_OUTPUT
    modules = [
        {"module_key": "module-a", "module_name": "A", "source_row_count": 2},
        {"module_key": "module-b", "module_name": "B", "source_row_count": 1},
    ]
    services = [
        {"module_key": "module-a", "service_key": "module-a::service-same", "service_name": "Same", "source_row_references": "2", "source_row_count": 1},
        {"module_key": "module-a", "service_key": "module-a::service-multi", "service_name": "Multi", "source_row_references": "3", "source_row_count": 1},
        {"module_key": "module-b", "service_key": "module-b::service-same", "service_name": "Same", "source_row_references": "4", "source_row_count": 1},
    ]
    _write_csv(b_index / "modules.csv", list(modules[0]), modules)
    _write_csv(b_index / "services.csv", list(services[0]), services)
    contents = {"a": b"alpha", "shared": b"shared", "c": b"charlie"}
    blobs = {}
    for name, content in contents.items():
        digest = hashlib.sha256(content).hexdigest()
        relative = f"documents/blobs/{digest}.html"
        path = c_output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        blobs[name] = (digest, relative, len(content))
    fields = [
        "occurrence_id", "module_key", "service_key", "document_key", "document_type",
        "source_row_number", "reference_ordinal", "physical_identity", "page_id", "status",
        "attempt_count", "blob_sha256", "blob_relative_path", "size_bytes", "mime_type", "title",
        "source_version", "retrieved_at", "version_changed", "error_class", "error_detail",
    ]
    def occurrence(
        oid: str, module: str, service: str, doc: str, dtype: str, row: int, ordinal: int,
        physical: str, blob: str | None, page: str,
    ) -> dict[str, object]:
        digest, relative, size = blobs[blob] if blob else ("", "", 0)
        return {
            "occurrence_id": oid, "module_key": module, "service_key": service,
            "document_key": doc, "document_type": dtype, "source_row_number": row,
            "reference_ordinal": ordinal, "physical_identity": physical, "page_id": page,
            "status": "FETCHED" if blob else "FAILED", "attempt_count": 1,
            "blob_sha256": digest, "blob_relative_path": relative, "size_bytes": size,
            "mime_type": "text/html" if blob else "", "title": f"title-{oid}" if blob else "",
            "source_version": "1" if blob else "", "retrieved_at": "2026-01-01T00:00:00Z" if blob else "",
            "version_changed": "false", "error_class": "" if blob else "NOT_FOUND",
            "error_detail": "" if blob else "404 Not Found",
        }
    rows = [
        occurrence("occ-1", "module-a", "module-a::service-same", "doc-a", "ICD", 2, 1, "page:1", "a", "1"),
        occurrence("occ-2", "module-a", "module-a::service-multi", "doc-shared-a", "ICD", 3, 1, "page:2", "shared", "2"),
        occurrence("occ-3", "module-a", "module-a::service-multi", "doc-c", "ISD", 3, 2, "page:3", "c", "3"),
        occurrence("occ-4", "module-b", "module-b::service-same", "doc-shared-b", "ISD", 4, 1, "page:2", "shared", "2"),
        occurrence("occ-5", "module-b", "module-b::service-same", "doc-missing", "ICD", 4, 2, "page:4939350056", None, "4939350056"),
    ]
    _write_csv(c_index / "document_acquisition.csv", fields, rows)
    _write_csv(c_index / "failures.csv", ["occurrence_id"], [{"occurrence_id": "occ-5"}])
    _write_csv(c_index / "module_document_coverage.csv", ["module_key"], [{"module_key": "module-a"}, {"module_key": "module-b"}])

    b_manifest_path = root / cache.BASELINE_019B_MANIFEST
    b_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for name in ("modules.csv", "services.csv"):
        relative = (cache.BASELINE_019B_INDEX / name).as_posix()
        outputs[relative] = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    b_manifest = {
        "counts": {
            "modules": 2, "services": 3, "accepted_reference_occurrences": 5,
            "icd_reference_occurrences": 3, "isd_reference_occurrences": 2,
        },
        "outputs": outputs,
    }
    b_manifest_path.write_bytes(cache._json_bytes(b_manifest))
    c_manifest_path = root / cache.BASELINE_019C_MANIFEST
    c_indexes = {}
    for name in ("document_acquisition.csv", "failures.csv", "module_document_coverage.csv"):
        path = c_index / name
        c_indexes[name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size_bytes": path.stat().st_size}
    c_manifest = {
        "baseline_manifest_sha256": hashlib.sha256(b_manifest_path.read_bytes()).hexdigest(),
        "counts": {"fetched": 4, "failed": 1, "blocked": 0, "pending": 0},
        "storage": {"unique_physical_file_count": 3, "size_bytes": 18},
        "indexes": c_indexes,
    }
    c_manifest_path.write_bytes(cache._json_bytes(c_manifest))
    return {name: values[0] for name, values in blobs.items()}


def test_cold_warm_metadata_coverage_order_and_module_separation(tmp_path: Path, monkeypatch) -> None:
    _fixture(tmp_path, monkeypatch)
    indexes, outputs = tmp_path / "cache-index", tmp_path / "cache-output"
    cold = cache.build_catalog(tmp_path, indexes, outputs)
    warm = cache.build_catalog(tmp_path, indexes, outputs)
    assert cold["cache_status"] == "MISS" and cold["blob_body_reads"] == 3
    assert warm["cache_status"] == "HIT" and warm["blob_body_reads"] == 0
    assert cold["manifest"]["counts"]["occurrences"] == 5
    with cache.DocumentCatalog(tmp_path, indexes / cache.CATALOG_NAME) as catalog:
        assert len(catalog.list_modules()) == 2
        assert len(catalog.list_services("module-a")) == 2
        a = catalog.list_documents("module-a", "Same")
        b = catalog.list_documents("module-b", "Same")
        assert [row["occurrence_id"] for row in a] == ["occ-1"]
        assert [row["occurrence_id"] for row in b] == ["occ-5", "occ-4"]
        multi = catalog.list_documents("module-a", "Multi")
        assert [(row["document_type"], row["reference_ordinal"]) for row in multi] == [("ICD", 1), ("ISD", 2)]
        assert catalog.blob_body_reads == 0


def test_shared_blob_read_on_demand_and_known_404(tmp_path: Path, monkeypatch) -> None:
    digests = _fixture(tmp_path, monkeypatch)
    indexes, outputs = tmp_path / "cache-index", tmp_path / "cache-output"
    cache.build_catalog(tmp_path, indexes, outputs)
    with cache.DocumentCatalog(tmp_path, indexes / cache.CATALOG_NAME) as catalog:
        assert catalog.document_info("page:2")[0]["blob_sha256"] == digests["shared"]
        assert len(catalog.document_info("page:2")) == 2
        ok, content = catalog.load_document("doc-shared-b")
        assert ok["status"] == "ok" and content == b"shared"
        missing, content = catalog.load_document("4939350056")
        assert missing["status"] == "acquisition_failed_404" and content is None
        assert catalog.blob_body_reads == 1


def test_missing_and_corrupt_blob_are_precise(tmp_path: Path, monkeypatch) -> None:
    _fixture(tmp_path, monkeypatch)
    indexes, outputs = tmp_path / "cache-index", tmp_path / "cache-output"
    cache.build_catalog(tmp_path, indexes, outputs)
    with cache.DocumentCatalog(tmp_path, indexes / cache.CATALOG_NAME) as catalog:
        record = catalog.document_info("doc-a")[0]
        blob = tmp_path / cache.BASELINE_019C_OUTPUT / record["blob_relative_path"]
        original = blob.read_bytes()
        blob.unlink()
        assert catalog.load_document("doc-a")[0]["status"] == "missing_blob"
        blob.write_bytes(original + b"changed")
        assert catalog.load_document("doc-a")[0]["status"] == "corrupt_blob"


def test_source_change_invalidates_catalog_and_rebuilds(tmp_path: Path, monkeypatch) -> None:
    _fixture(tmp_path, monkeypatch)
    indexes, outputs = tmp_path / "cache-index", tmp_path / "cache-output"
    first = cache.build_catalog(tmp_path, indexes, outputs)
    acquisition = tmp_path / cache.BASELINE_019C_INDEX / "document_acquisition.csv"
    text = acquisition.read_text()
    acquisition.write_text(text.replace("title-occ-1", "changed-title"))
    manifest_path = tmp_path / cache.BASELINE_019C_MANIFEST
    manifest = json.loads(manifest_path.read_text())
    manifest["indexes"]["document_acquisition.csv"] = {
        "sha256": hashlib.sha256(acquisition.read_bytes()).hexdigest(),
        "size_bytes": acquisition.stat().st_size,
    }
    manifest_path.write_bytes(cache._json_bytes(manifest))
    second = cache.build_catalog(tmp_path, indexes, outputs)
    assert first["manifest"]["source_signature"] != second["manifest"]["source_signature"]
    assert second["cache_status"] == "MISS"
    with cache.DocumentCatalog(tmp_path, indexes / cache.CATALOG_NAME) as catalog:
        assert catalog.document_info("doc-a")[0]["title"] == "changed-title"


def test_unchanged_cold_rebuild_is_byte_identical(tmp_path: Path, monkeypatch) -> None:
    _fixture(tmp_path, monkeypatch)
    indexes, outputs = tmp_path / "cache-index", tmp_path / "cache-output"
    cache.build_catalog(tmp_path, indexes, outputs)
    first_catalog = (indexes / cache.CATALOG_NAME).read_bytes()
    first_support = {path.name: path.read_bytes() for path in outputs.iterdir()}
    (indexes / cache.CATALOG_NAME).unlink()
    for path in outputs.iterdir():
        path.unlink()
    cache.build_catalog(tmp_path, indexes, outputs)
    assert (indexes / cache.CATALOG_NAME).read_bytes() == first_catalog
    assert {path.name: path.read_bytes() for path in outputs.iterdir()} == first_support


def test_write_requires_explicit_safe_new_destination(tmp_path: Path, monkeypatch) -> None:
    _fixture(tmp_path, monkeypatch)
    indexes, outputs = tmp_path / "cache-index", tmp_path / "cache-output"
    cache.build_catalog(tmp_path, indexes, outputs)
    with cache.DocumentCatalog(tmp_path, indexes / cache.CATALOG_NAME) as catalog:
        destination = tmp_path.parent / f"{tmp_path.name}-selected/document.html"
        result = catalog.write_document("doc-a", destination)
        assert result["status"] == "written" and destination.read_bytes() == b"alpha"
        assert catalog.write_document("doc-a", destination)["status"] == "output_exists"
        frozen = tmp_path / cache.BASELINE_019C_OUTPUT / "should-not-write.html"
        assert catalog.write_document("doc-a", frozen)["status"] == "unsafe_output_path"
