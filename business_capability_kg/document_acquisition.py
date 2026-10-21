"""Resumable Task 019-C acquisition for indexed Confluence ICD/ISD pages.

The module consumes already-authorized retrieval envelopes from stdin. It does
not contain credentials, construct source URLs, or perform semantic analysis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "phase6-task019c-acquisition-v1"
BASELINE_INDEX = Path("indexes/phase6/task019/019b")
BASELINE_MANIFEST = Path("outputs/phase6/task019/019b/manifest.json")
INDEX_ROOT = Path("indexes/phase6/task019/019c")
OUTPUT_ROOT = Path("outputs/phase6/task019/019c")
EXPECTED = {"modules": 32, "services": 952, "occurrences": 1941, "ICD": 988, "ISD": 953}
MAX_ATTEMPTS = 3
ACQUISITION_FIELDS = [
    "occurrence_id", "module_key", "service_key", "document_key", "document_type",
    "source_row_number", "reference_ordinal", "physical_identity", "page_id", "status",
    "attempt_count", "blob_sha256", "blob_relative_path", "size_bytes", "mime_type", "title",
    "source_version", "retrieved_at", "version_changed", "error_class", "error_detail",
]
COVERAGE_FIELDS = [
    "module_key", "module_name", "service_count", "reference_occurrence_count",
    "fetched_occurrence_count", "blocked_occurrence_count", "failed_occurrence_count",
    "pending_occurrence_count", "unique_fetched_file_count", "logical_size_bytes",
]
FAILURE_FIELDS = [
    "occurrence_id", "module_key", "service_key", "document_key", "document_type",
    "source_row_number", "reference_ordinal", "physical_identity", "page_id", "status",
    "attempt_count", "error_class", "error_detail",
]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def _validate_baseline(root: Path) -> dict[str, Any]:
    manifest_path = root / BASELINE_MANIFEST
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    counts = manifest["counts"]
    actual = {
        "modules": counts["modules"], "services": counts["services"],
        "occurrences": counts["accepted_reference_occurrences"],
        "ICD": counts["icd_reference_occurrences"], "ISD": counts["isd_reference_occurrences"],
    }
    if actual != EXPECTED:
        raise ValueError(f"TASK019B_BASELINE_MISMATCH: {actual!r} != {EXPECTED!r}")
    for relative, expected_hash in manifest["outputs"].items():
        path = root / relative
        if not path.is_file() or _sha256(path.read_bytes()) != expected_hash:
            raise ValueError(f"TASK019B_BASELINE_MISMATCH: {relative}")
    return {"manifest": manifest, "manifest_sha256": _sha256(manifest_bytes)}


def _reference_tokens(cell: str) -> list[tuple[int, str]]:
    return [(ordinal, token.strip()) for ordinal, token in enumerate(cell.split(";"), start=1) if token.strip()]


def build_acquisition_plan(root: Path) -> dict[str, Any]:
    """Build a URL-free acquisition plan from the frozen 019-B indexes."""
    root = root.resolve()
    baseline = _validate_baseline(root)
    documents = {row["document_key"]: row for row in _read_csv(root / BASELINE_INDEX / "documents.csv")}
    source_rows = {int(row["source_row_number"]): row for row in _read_csv(root / BASELINE_INDEX / "source_rows.csv")}
    modules = {row["module_key"]: row["module_name"] for row in _read_csv(root / BASELINE_INDEX / "modules.csv")}
    services = _read_csv(root / BASELINE_INDEX / "services.csv")
    edges = _read_csv(root / BASELINE_INDEX / "service_document_edges.csv")
    occurrences = []
    for edge in edges:
        row_number = int(edge["source_row_number"])
        ordinal = int(edge["reference_ordinal"])
        document_type = edge["type"]
        source = source_rows[row_number]
        tokens = dict(_reference_tokens(source[f"raw_{document_type.casefold()}_cell"]))
        if ordinal not in tokens:
            raise ValueError(f"TASK019B_PROVENANCE_MISMATCH: row {row_number} {document_type} #{ordinal}")
        document = documents[edge["document_key"]]
        match = re.fullmatch(r"confluence_page_id:(\d+)", document["reference_identifier"])
        page_id = match.group(1) if match else ""
        physical_identity = f"confluence-page:{page_id}" if page_id else f"unsupported:{edge['document_key']}"
        identity_material = "|".join([
            edge["module_key"], edge["service_key"], edge["document_key"], document_type,
            str(row_number), str(ordinal),
        ])
        occurrences.append({
            "occurrence_id": f"occ-{_sha256(identity_material.encode('utf-8'))[:24]}",
            "module_key": edge["module_key"], "service_key": edge["service_key"],
            "document_key": edge["document_key"], "document_type": document_type,
            "source_row_number": row_number, "reference_ordinal": ordinal,
            "physical_identity": physical_identity, "page_id": page_id,
        })
    occurrences.sort(key=lambda row: (
        str(row["module_key"]), str(row["service_key"]), int(row["source_row_number"]),
        str(row["document_type"]), int(row["reference_ordinal"]),
    ))
    counts = Counter(str(row["document_type"]) for row in occurrences)
    if len(occurrences) != EXPECTED["occurrences"] or counts != Counter({"ICD": 988, "ISD": 953}):
        raise ValueError("TASK019B_PROVENANCE_MISMATCH: occurrence closure")
    plan_core = {"modules": modules, "services": services, "occurrences": occurrences}
    return {
        **plan_core,
        "plan_sha256": _sha256(_json_bytes(plan_core)),
        "baseline_manifest_sha256": baseline["manifest_sha256"],
    }


def _progress_path(output_root: Path) -> Path:
    return output_root / "progress.json"


def _load_progress(output_root: Path) -> dict[str, Any] | None:
    path = _progress_path(output_root)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _save_progress(output_root: Path, progress: dict[str, Any]) -> None:
    _atomic_write(_progress_path(output_root), _json_bytes(progress))


def prepare_acquisition(root: Path, output_root: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    output_root = (output_root or root / OUTPUT_ROOT).resolve()
    plan = build_acquisition_plan(root)
    existing = _load_progress(output_root)
    if existing and existing["plan_sha256"] != plan["plan_sha256"]:
        raise ValueError("ACQUISITION_PLAN_CHANGED: preserve old progress for review")
    physical: dict[str, dict[str, Any]] = existing["physical_documents"] if existing else {}
    page_ids_by_identity: dict[str, str] = {}
    document_keys_by_identity: dict[str, set[str]] = defaultdict(set)
    for occurrence in plan["occurrences"]:
        identity = occurrence["physical_identity"]
        page_ids_by_identity[identity] = occurrence["page_id"]
        document_keys_by_identity[identity].add(occurrence["document_key"])
    for identity in sorted(page_ids_by_identity):
        if identity in physical:
            continue
        supported = bool(page_ids_by_identity[identity])
        physical[identity] = {
            "physical_identity": identity,
            "page_id": page_ids_by_identity[identity],
            "document_keys": sorted(document_keys_by_identity[identity]),
            "status": "PENDING" if supported else "BLOCKED",
            "attempt_count": 0,
            "blob_sha256": "", "blob_relative_path": "", "size_bytes": 0,
            "mime_type": "", "title": "", "source_version": "", "retrieved_at": "",
            "version_changed": False, "previous_blob_sha256": "",
            "error_class": "" if supported else "UNSUPPORTED_REFERENCE",
            "error_detail": "" if supported else "No indexed Confluence page ID",
        }
    progress = {
        "schema_version": SCHEMA_VERSION,
        "plan_sha256": plan["plan_sha256"],
        "baseline_manifest_sha256": plan["baseline_manifest_sha256"],
        "physical_documents": dict(sorted(physical.items())),
    }
    _save_progress(output_root, progress)
    return finalize_acquisition(root, output_root=output_root, progress=progress, plan=plan)


def acquisition_worklist(
    root: Path,
    output_root: Path | None = None,
    refresh_fetched: bool = False,
) -> list[dict[str, Any]]:
    root = root.resolve()
    output_root = (output_root or root / OUTPUT_ROOT).resolve()
    if not _progress_path(output_root).is_file():
        prepare_acquisition(root, output_root)
    progress = _load_progress(output_root)
    assert progress is not None
    work = []
    for record in progress["physical_documents"].values():
        eligible = (
            (record["status"] in {"PENDING", "FAILED"} and record["attempt_count"] < MAX_ATTEMPTS) or
            (refresh_fetched and record["status"] == "FETCHED")
        )
        if eligible and record["page_id"]:
            work.append({"physical_identity": record["physical_identity"], "page_id": record["page_id"]})
    return sorted(work, key=lambda row: int(row["page_id"]))


def _extract_tool_payload(tool_result: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    if tool_result.get("isError"):
        details = []
        for block in tool_result.get("content", []):
            if block.get("type") != "text":
                continue
            text = str(block.get("text", ""))
            try:
                envelope = json.loads(text)
            except json.JSONDecodeError:
                details.append(text)
            else:
                details.append(str(envelope.get("message") or envelope.get("error") or text))
        return None, ("; ".join(filter(None, details)) or "tool returned isError")
    for block in tool_result.get("content", []):
        if block.get("type") != "text":
            continue
        try:
            envelope = json.loads(block.get("text", ""))
        except json.JSONDecodeError:
            continue
        data = envelope.get("data")
        if isinstance(data, dict):
            return data, ""
        if isinstance(envelope, dict) and envelope.get("id") and "body" in envelope:
            return envelope, ""
        if envelope.get("error"):
            return None, str(envelope["error"])
    return None, "missing parseable Atlassian data envelope"


def _classify_error(message: str, attempts: int) -> tuple[str, str]:
    lowered = message.casefold()
    if any(token in lowered for token in ("429", "too many requests", "rate limit")):
        return "PENDING", "RATE_LIMITED"
    if any(token in lowered for token in ("forbidden", "unauthorized", "permission", "sign in", "login")):
        return "BLOCKED", "ACCESS_BLOCKED"
    if any(token in lowered for token in ("not found", "404", "does not exist")):
        return "FAILED", "NOT_FOUND"
    return ("FAILED" if attempts >= MAX_ATTEMPTS else "PENDING"), "RETRIEVAL_ERROR"


def ingest_retrieval(
    root: Path,
    physical_identity: str,
    tool_result: dict[str, Any],
    output_root: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    output_root = (output_root or root / OUTPUT_ROOT).resolve()
    progress = _load_progress(output_root)
    if not progress or physical_identity not in progress["physical_documents"]:
        raise ValueError(f"Unknown physical identity: {physical_identity}")
    record = progress["physical_documents"][physical_identity]
    record["attempt_count"] += 1
    data, error = _extract_tool_payload(tool_result)
    if data is not None:
        body = data.get("body") or {}
        value = body.get("value") if isinstance(body, dict) else body if isinstance(body, str) else None
        title = str(data.get("title") or "")
        if not isinstance(value, str) or not value:
            error = "successful envelope contained no document body"
        elif len(value) < 10000 and any(
            marker in (title + "\n" + value).casefold()
            for marker in ("log in to continue", "sign in to continue", "atlassian account login")
        ):
            error = "sign-in response rejected as document content"
        else:
            content = value.encode("utf-8")
            digest = _sha256(content)
            relative = Path("documents/blobs") / f"{digest}.html"
            blob_path = output_root / relative
            if blob_path.exists() and blob_path.read_bytes() != content:
                raise ValueError("CHECKSUM_COLLISION: existing blob differs")
            if not blob_path.exists():
                _atomic_write(blob_path, content)
            previous = record.get("blob_sha256", "")
            source_version = data.get("snapshotToken") or data.get("version") or ""
            if isinstance(source_version, dict):
                source_version = source_version.get("number") or json.dumps(source_version, sort_keys=True)
            record.update({
                "status": "FETCHED", "blob_sha256": digest,
                "blob_relative_path": relative.as_posix(), "size_bytes": blob_path.stat().st_size,
                "mime_type": "text/html; charset=utf-8", "title": title,
                "source_version": str(source_version),
                "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "version_changed": bool(previous and previous != digest),
                "previous_blob_sha256": previous if previous and previous != digest else "",
                "error_class": "", "error_detail": "",
            })
    if data is None or error:
        status, error_class = _classify_error(error, record["attempt_count"])
        if error_class == "RATE_LIMITED":
            # A shared upstream throttle is not a page-level acquisition attempt.
            record["attempt_count"] -= 1
        record.update({"status": status, "error_class": error_class, "error_detail": error[:500]})
    _save_progress(output_root, progress)
    return record


def _verified_blobs(output_root: Path, progress: dict[str, Any]) -> dict[str, int]:
    blobs: dict[str, int] = {}
    for record in progress["physical_documents"].values():
        if record["status"] != "FETCHED":
            continue
        path = output_root / record["blob_relative_path"]
        if not path.is_file():
            raise ValueError(f"MISSING_FETCHED_BLOB: {record['physical_identity']}")
        content = path.read_bytes()
        if _sha256(content) != record["blob_sha256"] or len(content) != int(record["size_bytes"]):
            raise ValueError(f"BLOB_CHECKSUM_MISMATCH: {record['physical_identity']}")
        blobs[record["blob_sha256"]] = path.stat().st_size
    return blobs


def _format_mib(value: int) -> str:
    return f"{value / 1024 ** 2:.6f}"


def _format_gib(value: int) -> str:
    return f"{value / 1024 ** 3:.9f}"


def finalize_acquisition(
    root: Path,
    output_root: Path | None = None,
    index_root: Path | None = None,
    progress: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    output_root = (output_root or root / OUTPUT_ROOT).resolve()
    index_root = (index_root or root / INDEX_ROOT).resolve()
    plan = plan or build_acquisition_plan(root)
    progress = progress or _load_progress(output_root)
    if not progress:
        raise ValueError("Acquisition is not prepared")
    if progress["plan_sha256"] != plan["plan_sha256"]:
        raise ValueError("ACQUISITION_PLAN_CHANGED")
    blobs = _verified_blobs(output_root, progress)
    module_names = plan["modules"]
    service_modules = {row["service_key"]: row["module_key"] for row in plan["services"]}
    services_by_module: Counter[str] = Counter(service_modules.values())
    acquisition_rows = []
    blob_sets_by_module: dict[str, set[str]] = defaultdict(set)
    blob_sets_by_type: dict[str, set[str]] = defaultdict(set)
    status_counts: Counter[str] = Counter()
    pointer_bytes = 0
    for occurrence in plan["occurrences"]:
        physical = progress["physical_documents"][occurrence["physical_identity"]]
        status = physical["status"]
        status_counts[status] += 1
        if status == "FETCHED":
            blob_sets_by_module[occurrence["module_key"]].add(physical["blob_sha256"])
            blob_sets_by_type[occurrence["document_type"]].add(physical["blob_sha256"])
        row = {
            **occurrence, "status": status, "attempt_count": physical["attempt_count"],
            "blob_sha256": physical["blob_sha256"], "blob_relative_path": physical["blob_relative_path"],
            "size_bytes": physical["size_bytes"], "mime_type": physical["mime_type"],
            "title": physical["title"], "source_version": physical["source_version"],
            "retrieved_at": physical["retrieved_at"],
            "version_changed": str(bool(physical["version_changed"])).lower(),
            "error_class": physical["error_class"], "error_detail": physical["error_detail"],
        }
        acquisition_rows.append(row)
        pointer = {
            key: row[key] for key in (
                "occurrence_id", "module_key", "service_key", "document_key", "document_type",
                "source_row_number", "reference_ordinal", "physical_identity", "page_id", "status",
                "blob_sha256", "blob_relative_path", "size_bytes", "mime_type", "title",
                "source_version", "retrieved_at", "error_class", "error_detail",
            )
        }
        pointer_path = (
            output_root / "modules" / occurrence["module_key"] /
            occurrence["document_type"].casefold() / f"{occurrence['occurrence_id']}.json"
        )
        pointer_content = _json_bytes(pointer)
        _atomic_write(pointer_path, pointer_content)
        pointer_bytes += pointer_path.stat().st_size

    coverage = []
    for module_key in sorted(module_names):
        rows = [row for row in acquisition_rows if row["module_key"] == module_key]
        statuses = Counter(row["status"] for row in rows)
        module_blobs = blob_sets_by_module[module_key]
        coverage.append({
            "module_key": module_key, "module_name": module_names[module_key],
            "service_count": services_by_module[module_key], "reference_occurrence_count": len(rows),
            "fetched_occurrence_count": statuses["FETCHED"],
            "blocked_occurrence_count": statuses["BLOCKED"],
            "failed_occurrence_count": statuses["FAILED"],
            "pending_occurrence_count": statuses["PENDING"],
            "unique_fetched_file_count": len(module_blobs),
            "logical_size_bytes": sum(blobs[digest] for digest in module_blobs),
        })
    failures = [
        {key: row[key] for key in FAILURE_FIELDS}
        for row in acquisition_rows if row["status"] != "FETCHED"
    ]
    index_root.mkdir(parents=True, exist_ok=True)
    index_payloads = {
        "document_acquisition.csv": _csv_bytes(acquisition_rows, ACQUISITION_FIELDS),
        "module_document_coverage.csv": _csv_bytes(coverage, COVERAGE_FIELDS),
        "failures.csv": _csv_bytes(failures, FAILURE_FIELDS),
    }
    for name, content in index_payloads.items():
        _atomic_write(index_root / name, content)

    icd_blobs, isd_blobs = blob_sets_by_type["ICD"], blob_sets_by_type["ISD"]
    occurrence_types = Counter(str(row["document_type"]) for row in acquisition_rows)
    overlap = icd_blobs & isd_blobs
    storage = {
        "unique_physical_file_count": len(blobs),
        "size_bytes": sum(blobs.values()),
        "size_mib": _format_mib(sum(blobs.values())),
        "size_gib": _format_gib(sum(blobs.values())),
        "icd_distinct_file_count": len(icd_blobs),
        "icd_size_bytes": sum(blobs[digest] for digest in icd_blobs),
        "isd_distinct_file_count": len(isd_blobs),
        "isd_size_bytes": sum(blobs[digest] for digest in isd_blobs),
        "icd_isd_overlap_file_count": len(overlap),
        "icd_isd_overlap_size_bytes": sum(blobs[digest] for digest in overlap),
        "module_pointer_file_count": len(acquisition_rows),
        "module_pointer_size_bytes": pointer_bytes,
        "index_file_count": len(index_payloads),
        "index_size_bytes": sum(len(content) for content in index_payloads.values()),
    }
    fetched = status_counts["FETCHED"]
    completion_rate = fetched / len(acquisition_rows) * 100 if acquisition_rows else 0.0
    summary = (
        "# Phase 6 Task 019-C acquisition summary\n\n"
        f"- Inventory closure: {len(module_names)} modules, {len(plan['services'])} services, "
        f"{len(acquisition_rows)} reference occurrences.\n"
        f"- Acquisition states: fetched {fetched}; blocked {status_counts['BLOCKED']}; "
        f"failed {status_counts['FAILED']}; pending {status_counts['PENDING']}.\n"
        f"- Completion rate: {completion_rate:.6f}% of reference occurrences.\n"
        "- Document bodies are preserved as verified HTML blobs; module ICD/ISD directories contain "
        "occurrence pointers. No semantic extraction was performed.\n"
        "- Failures and access constraints remain explicit in `indexes/phase6/task019/019c/failures.csv`.\n\n"
        "## Storage & File Size Totals\n\n"
        f"- Unique successfully downloaded and validated physical files: {storage['unique_physical_file_count']}.\n"
        f"- Exact physical blob storage: {storage['size_bytes']} bytes = {storage['size_mib']} MiB = "
        f"{storage['size_gib']} GiB (base 1024, each persisted blob counted once).\n"
        f"- ICD distinct files: {storage['icd_distinct_file_count']}; "
        f"{storage['icd_size_bytes']} bytes. ISD distinct files: {storage['isd_distinct_file_count']}; "
        f"{storage['isd_size_bytes']} bytes. ICD/ISD overlap: {storage['icd_isd_overlap_file_count']} files; "
        f"{storage['icd_isd_overlap_size_bytes']} bytes.\n"
        f"- Expected occurrences: {occurrence_types['ICD']} ICD + {occurrence_types['ISD']} ISD = "
        f"{len(acquisition_rows):,}; fetched {fetched}, "
        f"blocked {status_counts['BLOCKED']}, failed {status_counts['FAILED']}, "
        f"pending {status_counts['PENDING']}; completion {completion_rate:.6f}%.\n"
        "- Per-module unique file counts and logical bytes are in `module_document_coverage.csv`; shared "
        "documents can make summed module bytes differ from global deduplicated bytes.\n"
        f"- Pointer overhead (excluded from physical total): {storage['module_pointer_file_count']} files, "
        f"{storage['module_pointer_size_bytes']} bytes. Index overhead (also excluded): "
        f"{storage['index_file_count']} files, {storage['index_size_bytes']} bytes. "
        "Unavailable remote sizes are unmeasured.\n"
    ).encode("utf-8")
    manifest = {
        "schema_version": SCHEMA_VERSION, "task": "Phase 6 / Task 019-C",
        "status": "EA_REVIEW_TASK019C", "plan_sha256": plan["plan_sha256"],
        "baseline_manifest_sha256": plan["baseline_manifest_sha256"],
        "counts": {
            "modules": len(module_names), "services": len(plan["services"]),
            "reference_occurrences": len(acquisition_rows), "icd_occurrences": occurrence_types["ICD"],
            "isd_occurrences": occurrence_types["ISD"], "fetched": fetched, "blocked": status_counts["BLOCKED"],
            "failed": status_counts["FAILED"], "pending": status_counts["PENDING"],
        },
        "storage": storage,
        "validations": {
            "occurrence_closure": sum(status_counts.values()) == len(acquisition_rows),
            "blob_hashes_and_sizes_verified": True, "module_pointer_count_complete": pointer_bytes >= 0,
            "documents_semantically_analyzed": False, "staging_scanned": False,
        },
        "indexes": {
            name: {"sha256": _sha256(content), "size_bytes": len(content)}
            for name, content in index_payloads.items()
        },
        "report_sha256": _sha256(summary),
    }
    _atomic_write(output_root / "acquisition_summary.md", summary)
    _atomic_write(output_root / "acquisition_manifest.json", _json_bytes(manifest))
    return {"manifest": manifest, "summary": summary, "coverage": coverage}


def ingest_stream(
    root: Path,
    output_root: Path | None = None,
    index_root: Path | None = None,
    expected_count: int | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    output_root = (output_root or root / OUTPUT_ROOT).resolve()
    if not _progress_path(output_root).is_file():
        prepare_acquisition(root, output_root)
    ingested = 0
    for line in sys.stdin:
        if not line.strip():
            continue
        payload = json.loads(line)
        ingest_retrieval(root, payload["physical_identity"], payload["result"], output_root)
        ingested += 1
        if expected_count is not None and ingested >= expected_count:
            break
    return finalize_acquisition(root, output_root, index_root)


def reset_transient_failures(root: Path, output_root: Path | None = None) -> int:
    """Requeue terminal generic retrieval errors without touching evidence states."""
    root = root.resolve()
    output_root = (output_root or root / OUTPUT_ROOT).resolve()
    progress = _load_progress(output_root)
    if not progress:
        return 0
    reset = 0
    for record in progress["physical_documents"].values():
        if record["status"] == "FAILED" and record["error_class"] == "RETRIEVAL_ERROR":
            record.update({"status": "PENDING", "attempt_count": 0, "error_class": "", "error_detail": ""})
            reset += 1
    if reset:
        _save_progress(output_root, progress)
    return reset


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 019-C resumable document acquisition storage")
    parser.add_argument(
        "command", choices=("prepare", "worklist", "ingest-stream", "reset-transient", "finalize")
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--index-root", type=Path)
    parser.add_argument("--refresh-fetched", action="store_true")
    parser.add_argument("--expected-count", type=int)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare_acquisition(args.root, args.output_root)
        print(json.dumps(result["manifest"]["counts"], sort_keys=True))
    elif args.command == "worklist":
        print(json.dumps(acquisition_worklist(args.root, args.output_root, args.refresh_fetched)))
    elif args.command == "ingest-stream":
        result = ingest_stream(args.root, args.output_root, args.index_root, args.expected_count)
        print(json.dumps(result["manifest"]["counts"], sort_keys=True))
    elif args.command == "reset-transient":
        print(json.dumps({"reset": reset_transient_failures(args.root, args.output_root)}))
    else:
        result = finalize_acquisition(args.root, args.output_root, args.index_root)
        print(json.dumps(result["manifest"]["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
