"""Persistent, metadata-first retrieval catalog for Phase 6 / Task 019-D.

This module indexes the accepted Task 019-B/019-C artifacts without acquiring,
copying, parsing, or interpreting source documents. Blob bytes are opened only
during a cold integrity build or an explicit selected-document read.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "phase6-task019d-retrieval-v1"
IMPLEMENTATION_VERSION = "document-cache-v1"
INDEX_ROOT = Path("indexes/phase6/task019/019d")
OUTPUT_ROOT = Path("outputs/phase6/task019/019d")
CATALOG_NAME = "retrieval_catalog.sqlite3"
MANIFEST_NAME = "manifest.json"
BASELINE_019B_INDEX = Path("indexes/phase6/task019/019b")
BASELINE_019B_MANIFEST = Path("outputs/phase6/task019/019b/manifest.json")
BASELINE_019C_INDEX = Path("indexes/phase6/task019/019c")
BASELINE_019C_OUTPUT = Path("outputs/phase6/task019/019c")
BASELINE_019C_MANIFEST = BASELINE_019C_OUTPUT / "acquisition_manifest.json"
EXPECTED = {
    "modules": 32,
    "services": 952,
    "occurrences": 1941,
    "ICD": 988,
    "ISD": 953,
    "fetched": 1940,
    "failed": 1,
    "physical_identities": 1940,
    "blobs": 1932,
    "content_bytes": 193802986,
}


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _require_hash(path: Path, expected_hash: str, expected_size: int | None = None) -> None:
    if not path.is_file():
        raise ValueError(f"MISSING_BASELINE_ARTIFACT: {path}")
    if expected_size is not None and path.stat().st_size != expected_size:
        raise ValueError(f"BASELINE_SIZE_MISMATCH: {path}")
    if _sha256_file(path) != expected_hash:
        raise ValueError(f"BASELINE_HASH_MISMATCH: {path}")


def _validated_sources(root: Path) -> dict[str, Any]:
    manifest_b_path = root / BASELINE_019B_MANIFEST
    manifest_c_path = root / BASELINE_019C_MANIFEST
    manifest_b_bytes = manifest_b_path.read_bytes()
    manifest_c_bytes = manifest_c_path.read_bytes()
    manifest_b = json.loads(manifest_b_bytes)
    manifest_c = json.loads(manifest_c_bytes)
    manifest_b_sha = _sha256_bytes(manifest_b_bytes)
    if manifest_c.get("baseline_manifest_sha256") != manifest_b_sha:
        raise ValueError("TASK019B_019C_MANIFEST_LINK_MISMATCH")

    counts_b = manifest_b["counts"]
    counts_c = manifest_c["counts"]
    actual = {
        "modules": counts_b["modules"],
        "services": counts_b["services"],
        "occurrences": counts_b["accepted_reference_occurrences"],
        "ICD": counts_b["icd_reference_occurrences"],
        "ISD": counts_b["isd_reference_occurrences"],
        "fetched": counts_c["fetched"],
        "failed": counts_c["failed"],
        "blobs": manifest_c["storage"]["unique_physical_file_count"],
        "content_bytes": manifest_c["storage"]["size_bytes"],
    }
    for key in ("modules", "services", "occurrences", "ICD", "ISD", "fetched", "failed", "blobs", "content_bytes"):
        if actual[key] != EXPECTED[key]:
            raise ValueError(f"TASK019_BASELINE_COUNT_MISMATCH: {key}={actual[key]}")
    if counts_c["blocked"] or counts_c["pending"]:
        raise ValueError("TASK019C_BASELINE_HAS_UNRESOLVED_OCCURRENCES")

    source_files: dict[str, dict[str, Any]] = {}
    for name in ("modules.csv", "services.csv"):
        relative = (BASELINE_019B_INDEX / name).as_posix()
        path = root / relative
        expected_hash = manifest_b["outputs"][relative]
        _require_hash(path, expected_hash)
        source_files[relative] = {"sha256": expected_hash, "size_bytes": path.stat().st_size}
    for name, evidence in sorted(manifest_c["indexes"].items()):
        relative = (BASELINE_019C_INDEX / name).as_posix()
        path = root / relative
        _require_hash(path, evidence["sha256"], int(evidence["size_bytes"]))
        source_files[relative] = {
            "sha256": evidence["sha256"], "size_bytes": int(evidence["size_bytes"])
        }
    signature_payload = {
        "schema_version": SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "task019b_manifest_sha256": manifest_b_sha,
        "task019c_manifest_sha256": _sha256_bytes(manifest_c_bytes),
        "source_files": source_files,
    }
    return {
        "manifest_b": manifest_b,
        "manifest_c": manifest_c,
        "source_files": source_files,
        "signature_payload": signature_payload,
        "source_signature": _sha256_bytes(_json_bytes(signature_payload)),
    }


def _safe_blob_path(root: Path, relative: str) -> Path:
    content_root = (root / BASELINE_019C_OUTPUT).resolve()
    blob_root = (content_root / "documents/blobs").resolve()
    candidate = (content_root / relative).resolve()
    if not candidate.is_relative_to(blob_root):
        raise ValueError(f"UNSAFE_BLOB_PATH: {relative}")
    return candidate


def _catalog_valid(catalog_path: Path, manifest_path: Path, output_root: Path, source_signature: str) -> bool:
    if not catalog_path.is_file() or not manifest_path.is_file():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["schema_version"] != SCHEMA_VERSION:
            return False
        if manifest["source_signature"] != source_signature:
            return False
        catalog = manifest["catalog"]
        if catalog_path.stat().st_size != int(catalog["size_bytes"]):
            return False
        if _sha256_file(catalog_path) != catalog["sha256"]:
            return False
        for name, evidence in manifest["support_files"].items():
            path = output_root / name
            if path.stat().st_size != int(evidence["size_bytes"]):
                return False
            if _sha256_file(path) != evidence["sha256"]:
                return False
        with sqlite3.connect(f"file:{catalog_path}?mode=ro", uri=True) as connection:
            meta = dict(connection.execute("SELECT key, value FROM catalog_meta"))
        return meta.get("schema_version") == SCHEMA_VERSION and meta.get("source_signature") == source_signature
    except (KeyError, OSError, ValueError, sqlite3.Error, json.JSONDecodeError):
        return False


def _create_catalog(
    path: Path,
    source_signature: str,
    modules: list[dict[str, str]],
    services: list[dict[str, str]],
    occurrences: list[dict[str, str]],
    blobs: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.unlink(missing_ok=True)
    connection = sqlite3.connect(temporary)
    try:
        connection.executescript(
            """
            PRAGMA page_size=4096;
            PRAGMA journal_mode=OFF;
            PRAGMA synchronous=OFF;
            PRAGMA auto_vacuum=NONE;
            CREATE TABLE catalog_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
            CREATE TABLE modules (
                module_key TEXT PRIMARY KEY, module_name TEXT NOT NULL, source_row_count INTEGER NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE services (
                service_key TEXT PRIMARY KEY, module_key TEXT NOT NULL, service_name TEXT NOT NULL,
                source_row_references TEXT NOT NULL, source_row_count INTEGER NOT NULL,
                FOREIGN KEY(module_key) REFERENCES modules(module_key)
            ) WITHOUT ROWID;
            CREATE TABLE blobs (
                blob_sha256 TEXT PRIMARY KEY, blob_relative_path TEXT NOT NULL,
                size_bytes INTEGER NOT NULL, mime_type TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE TABLE occurrences (
                occurrence_id TEXT PRIMARY KEY, module_key TEXT NOT NULL, service_key TEXT NOT NULL,
                document_key TEXT NOT NULL, document_type TEXT NOT NULL,
                source_row_number INTEGER NOT NULL, reference_ordinal INTEGER NOT NULL,
                physical_identity TEXT NOT NULL, page_id TEXT NOT NULL, status TEXT NOT NULL,
                blob_sha256 TEXT NOT NULL, blob_relative_path TEXT NOT NULL, size_bytes INTEGER NOT NULL,
                mime_type TEXT NOT NULL, title TEXT NOT NULL, source_version TEXT NOT NULL,
                retrieved_at TEXT NOT NULL, error_class TEXT NOT NULL, error_detail TEXT NOT NULL,
                FOREIGN KEY(module_key) REFERENCES modules(module_key),
                FOREIGN KEY(service_key) REFERENCES services(service_key)
            ) WITHOUT ROWID;
            CREATE INDEX occurrence_module_idx ON occurrences(module_key, service_key, document_type, source_row_number, reference_ordinal, occurrence_id);
            CREATE INDEX occurrence_document_idx ON occurrences(document_key, occurrence_id);
            CREATE INDEX occurrence_physical_idx ON occurrences(physical_identity, occurrence_id);
            CREATE INDEX occurrence_page_idx ON occurrences(page_id, occurrence_id);
            """
        )
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executemany(
            "INSERT INTO catalog_meta VALUES (?, ?)",
            sorted({
                "implementation_version": IMPLEMENTATION_VERSION,
                "schema_version": SCHEMA_VERSION,
                "source_signature": source_signature,
            }.items()),
        )
        connection.executemany(
            "INSERT INTO modules VALUES (?, ?, ?)",
            [
                (row["module_key"], row["module_name"], int(row["source_row_count"]))
                for row in sorted(modules, key=lambda item: item["module_key"])
            ],
        )
        connection.executemany(
            "INSERT INTO services VALUES (?, ?, ?, ?, ?)",
            [
                (
                    row["service_key"], row["module_key"], row["service_name"],
                    row["source_row_references"], int(row["source_row_count"]),
                )
                for row in sorted(services, key=lambda item: item["service_key"])
            ],
        )
        connection.executemany(
            "INSERT INTO blobs VALUES (?, ?, ?, ?)",
            [
                (row["blob_sha256"], row["blob_relative_path"], row["size_bytes"], row["mime_type"])
                for row in sorted(blobs, key=lambda item: item["blob_sha256"])
            ],
        )
        fields = (
            "occurrence_id", "module_key", "service_key", "document_key", "document_type",
            "source_row_number", "reference_ordinal", "physical_identity", "page_id", "status",
            "blob_sha256", "blob_relative_path", "size_bytes", "mime_type", "title",
            "source_version", "retrieved_at", "error_class", "error_detail",
        )
        connection.executemany(
            f"INSERT INTO occurrences VALUES ({','.join('?' for _ in fields)})",
            [
                tuple(
                    int(row[field]) if field in {"source_row_number", "reference_ordinal", "size_bytes"}
                    else row[field]
                    for field in fields
                )
                for row in sorted(occurrences, key=lambda item: item["occurrence_id"])
            ],
        )
        connection.commit()
        connection.execute("VACUUM")
        connection.close()
        os.replace(temporary, path)
    except Exception:
        connection.close()
        temporary.unlink(missing_ok=True)
        raise


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


class DocumentCatalog:
    """Read-only catalog with explicit, verified blob loading."""

    def __init__(self, root: Path, catalog_path: Path | None = None) -> None:
        self.root = root.resolve()
        self.catalog_path = (catalog_path or self.root / INDEX_ROOT / CATALOG_NAME).resolve()
        self.connection = sqlite3.connect(f"file:{self.catalog_path}?mode=ro", uri=True)
        self.connection.row_factory = sqlite3.Row
        self.blob_body_reads = 0

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "DocumentCatalog":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _module_key(self, identity: str) -> str:
        rows = self.connection.execute(
            "SELECT module_key FROM modules WHERE module_key=? OR module_name=? ORDER BY module_key",
            (identity, identity),
        ).fetchall()
        if len(rows) != 1:
            raise KeyError(f"module_not_found_or_ambiguous: {identity}")
        return str(rows[0]["module_key"])

    def _service_key(self, module_key: str, identity: str) -> str:
        rows = self.connection.execute(
            "SELECT service_key FROM services WHERE module_key=? AND (service_key=? OR service_name=?) ORDER BY service_key",
            (module_key, identity, identity),
        ).fetchall()
        if len(rows) != 1:
            raise KeyError(f"service_not_found_or_ambiguous: {identity}")
        return str(rows[0]["service_key"])

    def list_modules(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT m.module_key, m.module_name,
                   (SELECT COUNT(*) FROM services s WHERE s.module_key=m.module_key) AS service_count,
                   (SELECT COUNT(*) FROM occurrences o WHERE o.module_key=m.module_key) AS occurrence_count
            FROM modules m ORDER BY m.module_key
            """
        ).fetchall()
        return [_row_dict(row) for row in rows]

    def list_services(self, module: str) -> list[dict[str, Any]]:
        module_key = self._module_key(module)
        rows = self.connection.execute(
            """
            SELECT s.module_key, s.service_key, s.service_name,
                   COUNT(o.occurrence_id) AS occurrence_count
            FROM services s LEFT JOIN occurrences o ON o.service_key=s.service_key
            WHERE s.module_key=? GROUP BY s.service_key ORDER BY s.service_key
            """,
            (module_key,),
        ).fetchall()
        return [_row_dict(row) for row in rows]

    def list_documents(
        self, module: str, service: str | None = None, document_type: str | None = None
    ) -> list[dict[str, Any]]:
        module_key = self._module_key(module)
        clauses, values = ["o.module_key=?"], [module_key]
        if service is not None:
            clauses.append("o.service_key=?")
            values.append(self._service_key(module_key, service))
        if document_type is not None:
            normalized = document_type.upper()
            if normalized not in {"ICD", "ISD"}:
                raise ValueError("document_type must be ICD or ISD")
            clauses.append("o.document_type=?")
            values.append(normalized)
        rows = self.connection.execute(
            f"""
            SELECT o.*, m.module_name, s.service_name
            FROM occurrences o JOIN modules m ON m.module_key=o.module_key
            JOIN services s ON s.service_key=o.service_key
            WHERE {' AND '.join(clauses)}
            ORDER BY o.service_key, o.source_row_number, o.document_type,
                     o.reference_ordinal, o.occurrence_id
            """,
            values,
        ).fetchall()
        return [_row_dict(row) for row in rows]

    def document_info(self, document_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT o.*, m.module_name, s.service_name
            FROM occurrences o JOIN modules m ON m.module_key=o.module_key
            JOIN services s ON s.service_key=o.service_key
            WHERE o.document_key=? OR o.occurrence_id=? OR o.physical_identity=? OR o.page_id=?
            ORDER BY o.module_key, o.service_key, o.source_row_number,
                     o.document_type, o.reference_ordinal, o.occurrence_id
            """,
            (document_id, document_id, document_id, document_id),
        ).fetchall()
        return [_row_dict(row) for row in rows]

    def load_document(self, document_id: str) -> tuple[dict[str, Any], bytes | None]:
        records = self.document_info(document_id)
        if not records:
            return {"status": "document_not_found", "document_id": document_id}, None
        identities = {(row["physical_identity"], row["blob_sha256"]) for row in records}
        if len(identities) != 1:
            return {"status": "ambiguous_document_id", "document_id": document_id, "matches": len(records)}, None
        record = records[0]
        if record["status"] != "FETCHED":
            status = "acquisition_failed_404" if record["error_class"] == "NOT_FOUND" else "acquisition_failed"
            return {"status": status, "document_id": document_id, "metadata": record}, None
        try:
            path = _safe_blob_path(self.root, record["blob_relative_path"])
        except ValueError:
            return {"status": "unsafe_blob_path", "document_id": document_id, "metadata": record}, None
        if not path.is_file():
            return {"status": "missing_blob", "document_id": document_id, "metadata": record}, None
        self.blob_body_reads += 1
        content = path.read_bytes()
        if len(content) != int(record["size_bytes"]) or _sha256_bytes(content) != record["blob_sha256"]:
            return {"status": "corrupt_blob", "document_id": document_id, "metadata": record}, None
        return {"status": "ok", "document_id": document_id, "metadata": record}, content

    def write_document(self, document_id: str, destination: Path) -> dict[str, Any]:
        destination = destination.resolve()
        if destination.is_relative_to(self.root):
            return {"status": "unsafe_output_path", "document_id": document_id}
        if destination.exists():
            return {"status": "output_exists", "document_id": document_id}
        result, content = self.load_document(document_id)
        if content is None:
            return result
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return {
            "status": "written", "document_id": document_id,
            "output_path": str(destination), "size_bytes": len(content),
            "sha256": _sha256_bytes(content),
        }


def _build_support_outputs(
    root: Path, output_root: Path, catalog_path: Path, counts: dict[str, Any],
    source_signature: str, catalog_sha: str, catalog_size: int,
) -> dict[str, bytes]:
    with DocumentCatalog(root, catalog_path) as catalog:
        modules = catalog.list_modules()
        sample_module = modules[0]
        services = catalog.list_services(sample_module["module_key"])
        sample_service = services[0]
        documents = catalog.list_documents(sample_module["module_key"], sample_service["service_key"])
        known_404 = catalog.document_info("4939350056")
        examples = {
            "metadata_only_blob_body_reads": catalog.blob_body_reads,
            "module": sample_module,
            "service": sample_service,
            "documents": documents[:3],
            "known_404": known_404,
        }
    summary = (
        "# Phase 6 Task 019-D retrieval catalog validation\n\n"
        f"- Closure: {counts['modules']} modules, {counts['services']} services, "
        f"{counts['occurrences']} occurrences ({counts['ICD']} ICD; {counts['ISD']} ISD).\n"
        f"- Status: {counts['fetched']} fetched; {counts['failed']} failed; "
        f"{counts['pending']} pending; {counts['blocked']} blocked.\n"
        f"- Physical content: {counts['blobs']} validated blobs and "
        f"{counts['content_bytes']} existing bytes, referenced in place and not copied.\n"
        f"- Catalog: `{INDEX_ROOT / CATALOG_NAME}`, {catalog_size} bytes, SHA-256 `{catalog_sha}`.\n"
        f"- Source signature: `{source_signature}`. Cold build: MISS / rebuild / "
        f"{counts['blobs']} integrity reads. Immediate warm validation: HIT / 0 blob-body reads.\n"
        "- Metadata-only sample lookups read zero document bodies; examples are in `lookup_examples.json`.\n"
        "- Explicit selected-document reads verify path containment, file existence, byte length and SHA-256.\n"
        "- Known page `4939350056` returns `acquisition_failed_404`; no empty blob represents it.\n"
        "- Automated validation command: `.venv/bin/pytest -q tests/business_capability_kg/test_document_cache.py`.\n"
        "- No acquisition network call, staging scan, semantic parsing, text extraction or content duplication occurred.\n"
    ).encode("utf-8")
    return {"lookup_examples.json": _json_bytes(examples), "validation_summary.md": summary}


def build_catalog(
    root: Path,
    index_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Build or reuse the persistent catalog and return cache telemetry."""
    root = root.resolve()
    index_root = (index_root or root / INDEX_ROOT).resolve()
    output_root = (output_root or root / OUTPUT_ROOT).resolve()
    catalog_path = index_root / CATALOG_NAME
    manifest_path = output_root / MANIFEST_NAME
    sources = _validated_sources(root)
    if _catalog_valid(catalog_path, manifest_path, output_root, sources["source_signature"]):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {"cache_status": "HIT", "blob_body_reads": 0, "manifest": manifest}

    modules = _read_csv(root / BASELINE_019B_INDEX / "modules.csv")
    services = _read_csv(root / BASELINE_019B_INDEX / "services.csv")
    occurrences = _read_csv(root / BASELINE_019C_INDEX / "document_acquisition.csv")
    if len(modules) != EXPECTED["modules"] or len(services) != EXPECTED["services"]:
        raise ValueError("TASK019D_MODULE_SERVICE_CLOSURE_MISMATCH")
    if len(occurrences) != EXPECTED["occurrences"]:
        raise ValueError("TASK019D_OCCURRENCE_CLOSURE_MISMATCH")
    types = Counter(row["document_type"] for row in occurrences)
    statuses = Counter(row["status"] for row in occurrences)
    physical = {row["physical_identity"] for row in occurrences}
    if types != Counter({"ICD": EXPECTED["ICD"], "ISD": EXPECTED["ISD"]}):
        raise ValueError("TASK019D_DOCUMENT_TYPE_CLOSURE_MISMATCH")
    if statuses != Counter({"FETCHED": EXPECTED["fetched"], "FAILED": EXPECTED["failed"]}):
        raise ValueError("TASK019D_STATUS_CLOSURE_MISMATCH")
    if len(physical) != EXPECTED["physical_identities"]:
        raise ValueError("TASK019D_PHYSICAL_IDENTITY_CLOSURE_MISMATCH")

    module_keys = {row["module_key"] for row in modules}
    service_keys = {row["service_key"] for row in services}
    if any(row["module_key"] not in module_keys or row["service_key"] not in service_keys for row in occurrences):
        raise ValueError("TASK019D_FOREIGN_KEY_CLOSURE_MISMATCH")
    blobs_by_hash: dict[str, dict[str, Any]] = {}
    for row in occurrences:
        if row["status"] != "FETCHED":
            continue
        candidate = {
            "blob_sha256": row["blob_sha256"],
            "blob_relative_path": row["blob_relative_path"],
            "size_bytes": int(row["size_bytes"]),
            "mime_type": row["mime_type"],
        }
        previous = blobs_by_hash.setdefault(row["blob_sha256"], candidate)
        if previous != candidate:
            raise ValueError(f"TASK019D_BLOB_METADATA_CONFLICT: {row['blob_sha256']}")
    if len(blobs_by_hash) != EXPECTED["blobs"]:
        raise ValueError("TASK019D_BLOB_CLOSURE_MISMATCH")
    if sum(item["size_bytes"] for item in blobs_by_hash.values()) != EXPECTED["content_bytes"]:
        raise ValueError("TASK019D_CONTENT_SIZE_CLOSURE_MISMATCH")

    for digest, blob in sorted(blobs_by_hash.items()):
        path = _safe_blob_path(root, blob["blob_relative_path"])
        if not path.is_file():
            raise ValueError(f"MISSING_BLOB: {digest}")
        if path.stat().st_size != blob["size_bytes"] or _sha256_file(path) != digest:
            raise ValueError(f"CORRUPT_BLOB: {digest}")

    _create_catalog(
        catalog_path, sources["source_signature"], modules, services, occurrences,
        list(blobs_by_hash.values()),
    )
    catalog_sha, catalog_size = _sha256_file(catalog_path), catalog_path.stat().st_size
    counts = {
        "modules": len(modules), "services": len(services), "occurrences": len(occurrences),
        "ICD": types["ICD"], "ISD": types["ISD"], "fetched": statuses["FETCHED"],
        "failed": statuses["FAILED"], "pending": statuses["PENDING"], "blocked": statuses["BLOCKED"],
        "physical_identities": len(physical), "blobs": len(blobs_by_hash),
        "content_bytes": sum(item["size_bytes"] for item in blobs_by_hash.values()),
    }
    support = _build_support_outputs(
        root, output_root, catalog_path, counts, sources["source_signature"], catalog_sha, catalog_size
    )
    for name, content in support.items():
        _atomic_write(output_root / name, content)
    support_evidence = {
        name: {"sha256": _sha256_bytes(content), "size_bytes": len(content)}
        for name, content in sorted(support.items())
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "task": "Phase 6 / Task 019-D",
        "status": "EA_REVIEW_TASK019D",
        "source_signature": sources["source_signature"],
        "sources": sources["signature_payload"],
        "counts": counts,
        "catalog": {
            "path": (INDEX_ROOT / CATALOG_NAME).as_posix(),
            "sha256": catalog_sha,
            "size_bytes": catalog_size,
            "contains_document_bodies": False,
        },
        "support_files": support_evidence,
        "cache_validation": {
            "cold_status": "MISS", "cold_blob_body_reads": len(blobs_by_hash),
            "immediate_warm_status": "HIT", "warm_blob_body_reads": 0,
        },
        "validations": {
            "all_blob_hashes_and_sizes_verified": True,
            "metadata_queries_open_document_bodies": False,
            "known_404_indexed": any(row["page_id"] == "4939350056" for row in occurrences),
            "network_used": False, "staging_scanned": False,
            "semantic_processing_performed": False, "document_bodies_copied": False,
        },
    }
    _atomic_write(manifest_path, _json_bytes(manifest))
    if not _catalog_valid(catalog_path, manifest_path, output_root, sources["source_signature"]):
        raise ValueError("TASK019D_IMMEDIATE_WARM_VALIDATION_FAILED")
    return {"cache_status": "MISS", "blob_body_reads": len(blobs_by_hash), "manifest": manifest}


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 019-D local document retrieval catalog")
    parser.add_argument("command", choices=(
        "build", "list-modules", "list-services", "list-documents", "document-info", "read-document"
    ))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--index-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--module")
    parser.add_argument("--service")
    parser.add_argument("--type", choices=("ICD", "ISD"))
    parser.add_argument("--id")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    build = build_catalog(args.root, args.index_root, args.output_root)
    if args.command == "build":
        _print_json({
            "cache_status": build["cache_status"], "blob_body_reads": build["blob_body_reads"],
            "counts": build["manifest"]["counts"], "catalog": build["manifest"]["catalog"],
        })
        return
    catalog_path = (args.index_root or args.root / INDEX_ROOT) / CATALOG_NAME
    with DocumentCatalog(args.root, catalog_path) as catalog:
        if args.command == "list-modules":
            result = catalog.list_modules()
        elif args.command == "list-services":
            if not args.module:
                parser.error("list-services requires --module")
            result = catalog.list_services(args.module)
        elif args.command == "list-documents":
            if not args.module:
                parser.error("list-documents requires --module")
            result = catalog.list_documents(args.module, args.service, args.type)
        elif args.command == "document-info":
            if not args.id:
                parser.error("document-info requires --id")
            result = catalog.document_info(args.id)
        else:
            if not args.id or args.out is None:
                parser.error("read-document requires --id and --out; content is never printed")
            result = catalog.write_document(args.id, args.out)
        _print_json(result)


if __name__ == "__main__":
    main()
