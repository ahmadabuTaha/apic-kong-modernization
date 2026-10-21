"""Normalize and consolidate the Task 019 Module -> Service -> ICD/ISD inventory.

This module deliberately performs no network access or semantic classification.
The accepted normalization behavior remains available for compatibility. The
Task 019-A CLI only consolidates the already-accepted Common baseline.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit


EXPECTED_COLUMNS = ["Module", "Module Codex(Sub Module)", "Service", "ICD", "ISD"]
PILOT_MODULE = "Common"
SCHEMA_VERSION = "capability-kg-015a-v1"
TASK019A_SCHEMA_VERSION = "phase6-task019a-consolidation-v1"
TASK019B_SCHEMA_VERSION = "phase6-task019b-all-modules-v1"
ACCEPTED_COUNTS = {
    "pilot_source_rows": 116,
    "services": 116,
    "accepted_reference_occurrences": 225,
}
BASELINE_INDEX_ROOT = Path("indexes/capability_kg/015a")
TASK019A_INDEX_ROOT = Path("indexes/phase6/task019/019a")
BASELINE_OUTPUT_ROOT = Path("outputs/capability_kg/015a")
TASK019A_OUTPUT_ROOT = Path("outputs/phase6/task019/019a")
TASK019B_INDEX_ROOT = Path("indexes/phase6/task019/019b")
TASK019B_OUTPUT_ROOT = Path("outputs/phase6/task019/019b")
CSV_FIELDS = {
    "modules.csv": ["module_key", "module_name", "source_row_count"],
    "services.csv": [
        "module_key", "service_key", "service_name", "source_row_references", "source_row_count"
    ],
    "documents.csv": [
        "document_key", "document_type", "reference_identifier", "source_kind", "sanitized_source_metadata"
    ],
    "service_document_edges.csv": [
        "module_key", "service_key", "document_key", "type", "source_row_number", "reference_ordinal"
    ],
    "source_rows.csv": [
        "source_file_sha256", "source_row_number", "module_key", "service_key", "raw_module",
        "raw_sub_module_audit_only", "raw_service", "raw_icd_cell", "raw_isd_cell",
    ],
    "exceptions.csv": [
        "source_row_number", "exception_type", "reason", "reference_type", "reference_ordinal",
        "original_reference_pointer",
    ],
}
MODULE_COVERAGE_FIELDS = [
    "module_key",
    "module_name",
    "source_row_count",
    "service_count",
    "icd_reference_occurrence_count",
    "isd_reference_occurrence_count",
    "total_reference_occurrence_count",
    "unique_document_count",
    "zero_document_service_count",
    "exception_count",
]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.strip().casefold()).strip("-")
    return value or "unnamed"


def _collision_keys(values: Iterable[str], prefix: str) -> tuple[dict[str, str], set[str]]:
    """Return stable keys and the display values involved in normalization collisions."""
    displays = sorted(set(values), key=lambda item: (item.casefold(), item))
    by_slug: dict[str, list[str]] = defaultdict(list)
    for display in displays:
        by_slug[_slug(display)].append(display)
    collisions = {display for group in by_slug.values() if len(group) > 1 for display in group}
    keys = {}
    for display in displays:
        base = _slug(display)
        suffix = f"-{_sha256(display.encode('utf-8'))[:10]}" if display in collisions else ""
        keys[display] = f"{prefix}-{base}{suffix}"
    return keys, collisions


def _reference_pointer(row_number: int, ref_type: str, ordinal: int, raw: str) -> str:
    digest = _sha256(raw.encode("utf-8"))[:16] if raw else "blank"
    return f"source_row:{row_number}:{ref_type}:{ordinal}:sha256:{digest}"


@dataclass(frozen=True)
class ParsedReference:
    canonical: str
    identifier: str
    source_kind: str
    metadata: str


def _parse_reference(raw: str) -> ParsedReference | None:
    value = raw.strip()
    if not value or any(character.isspace() for character in value):
        return None
    parsed = urlsplit(value)
    if parsed.scheme.casefold() in {"http", "https"} and parsed.netloc:
        try:
            port = parsed.port
        except ValueError:
            return None
        host = (parsed.hostname or "").casefold()
        if not host:
            return None
        netloc = host
        if port and not ((parsed.scheme.casefold() == "http" and port == 80) or
                         (parsed.scheme.casefold() == "https" and port == 443)):
            netloc = f"{host}:{port}"
        path = re.sub(r"/{2,}", "/", parsed.path or "/")
        canonical = urlunsplit((parsed.scheme.casefold(), netloc, path, parsed.query, ""))
        page_match = re.search(r"/pages/(\d+)(?:/|$)", path)
        if page_match:
            page_id = page_match.group(1)
            identifier = f"confluence_page_id:{page_id}"
            kind = "CONFLUENCE_PAGE"
            # Page titles and query strings can change without changing Confluence identity.
            canonical = f"confluence:{host}:page:{page_id}"
        else:
            identifier = f"url_sha256:{_sha256(canonical.encode('utf-8'))}"
            kind = "URL"
        metadata = f"scheme={parsed.scheme.casefold()};host_sha256={_sha256(host.encode('utf-8'))[:16]}"
        return ParsedReference(canonical, identifier, kind, metadata)
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}", value):
        return ParsedReference(
            value,
            f"reference_sha256:{_sha256(value.encode('utf-8'))}",
            "STABLE_REFERENCE",
            "syntax=opaque_identifier",
        )
    return None


def _csv_bytes(rows: list[dict[str, object]], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _read_source(source: Path, pilot_module: str | None) -> tuple[str, list[dict[str, str]]]:
    raw = source.read_bytes()
    source_hash = _sha256(raw)
    with io.StringIO(raw.decode("utf-8-sig"), newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"Unexpected columns: {reader.fieldnames!r}; expected {EXPECTED_COLUMNS!r}")
        rows = []
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"Row {row_number} has more fields than the header")
            if pilot_module is None or row["Module"] == pilot_module:
                rows.append({**row, "_source_row_number": str(row_number)})
    return source_hash, rows


def _normalize(source: Path, pilot_module: str | None = PILOT_MODULE) -> dict[str, object]:
    source_hash, raw_rows = _read_source(source, pilot_module)
    if pilot_module is not None and not raw_rows:
        raise ValueError(f"Pilot module {pilot_module!r} has no source rows")

    module_displays = [row["Module"] for row in raw_rows]
    module_keys, module_collisions = _collision_keys(module_displays, "module")
    service_values_by_module: dict[str, list[str]] = defaultdict(list)
    for row in raw_rows:
        service_values_by_module[row["Module"]].append(row["Service"].strip())
    service_keys: dict[tuple[str, str], str] = {}
    service_collisions: set[tuple[str, str]] = set()
    for module_name, services in service_values_by_module.items():
        scoped, collisions = _collision_keys(services, "service")
        module_key = module_keys[module_name]
        for service_name, service_key in scoped.items():
            service_keys[(module_name, service_name)] = f"{module_key}::{service_key}"
        service_collisions.update((module_name, value) for value in collisions)

    exceptions: list[dict[str, object]] = []
    module_counts = Counter(module_displays)
    service_rows: dict[tuple[str, str], list[int]] = defaultdict(list)
    source_rows: list[dict[str, object]] = []
    for row in raw_rows:
        row_number = int(row["_source_row_number"])
        module_name, service_name = row["Module"], row["Service"].strip()
        module_key = module_keys[module_name]
        service_key = service_keys[(module_name, service_name)]
        service_rows[(module_name, service_name)].append(row_number)
        source_rows.append({
            "source_file_sha256": source_hash,
            "source_row_number": row_number,
            "module_key": module_key,
            "service_key": service_key,
            "raw_module": row["Module"],
            "raw_sub_module_audit_only": row["Module Codex(Sub Module)"],
            "raw_service": row["Service"],
            "raw_icd_cell": row["ICD"],
            "raw_isd_cell": row["ISD"],
        })
        if module_name in module_collisions:
            exceptions.append({
                "source_row_number": row_number, "exception_type": "identity_collision",
                "reason": "distinct module labels share a normalized base; collision-safe keys retained",
                "reference_type": "MODULE", "reference_ordinal": "",
                "original_reference_pointer": f"source_row:{row_number}:Module",
            })
        if (module_name, service_name) in service_collisions:
            exceptions.append({
                "source_row_number": row_number, "exception_type": "identity_collision",
                "reason": "distinct service labels share a normalized base; collision-safe keys retained",
                "reference_type": "SERVICE", "reference_ordinal": "",
                "original_reference_pointer": f"source_row:{row_number}:Service",
            })

    modules = [
        {"module_key": module_keys[name], "module_name": name, "source_row_count": module_counts[name]}
        for name in sorted(module_counts, key=lambda item: module_keys[item])
    ]
    services = []
    for (module_name, service_name), row_numbers in service_rows.items():
        services.append({
            "module_key": module_keys[module_name],
            "service_key": service_keys[(module_name, service_name)],
            "service_name": service_name,
            "source_row_references": ";".join(str(value) for value in sorted(row_numbers)),
            "source_row_count": len(row_numbers),
        })

    documents_by_key: dict[str, dict[str, object]] = {}
    edges: list[dict[str, object]] = []
    seen_service_references: set[tuple[str, str, str]] = set()
    nonempty_before = rejected = 0
    for row in raw_rows:
        row_number = int(row["_source_row_number"])
        module_name, service_name = row["Module"], row["Service"].strip()
        service_key = service_keys[(module_name, service_name)]
        for ref_type in ("ICD", "ISD"):
            cell = row[ref_type]
            tokens = cell.split(";")
            for ordinal, token in enumerate(tokens, start=1):
                if not token.strip():
                    exceptions.append({
                        "source_row_number": row_number, "exception_type": "blank_reference",
                        "reason": "blank cell or empty semicolon-delimited reference token",
                        "reference_type": ref_type, "reference_ordinal": ordinal,
                        "original_reference_pointer": _reference_pointer(row_number, ref_type, ordinal, token),
                    })
                    continue
                nonempty_before += 1
                parsed = _parse_reference(token)
                if parsed is None:
                    rejected += 1
                    exceptions.append({
                        "source_row_number": row_number, "exception_type": "invalid_reference_format",
                        "reason": "reference is neither a valid HTTP(S) URL nor a stable opaque identifier",
                        "reference_type": ref_type, "reference_ordinal": ordinal,
                        "original_reference_pointer": _reference_pointer(row_number, ref_type, ordinal, token),
                    })
                    continue
                document_key = f"document-{ref_type.casefold()}-{_sha256(parsed.canonical.encode('utf-8'))[:20]}"
                documents_by_key.setdefault(document_key, {
                    "document_key": document_key,
                    "document_type": ref_type,
                    "reference_identifier": parsed.identifier,
                    "source_kind": parsed.source_kind,
                    "sanitized_source_metadata": parsed.metadata,
                })
                duplicate_key = (service_key, ref_type, document_key)
                if duplicate_key in seen_service_references:
                    exceptions.append({
                        "source_row_number": row_number, "exception_type": "duplicate_reference_occurrence",
                        "reason": "reference repeats for the same module-scoped service and document type; edge retained",
                        "reference_type": ref_type, "reference_ordinal": ordinal,
                        "original_reference_pointer": _reference_pointer(row_number, ref_type, ordinal, token),
                    })
                seen_service_references.add(duplicate_key)
                edges.append({
                    "module_key": module_keys[module_name], "service_key": service_key,
                    "document_key": document_key, "type": ref_type,
                    "source_row_number": row_number, "reference_ordinal": ordinal,
                })

    modules.sort(key=lambda row: str(row["module_key"]))
    services.sort(key=lambda row: (str(row["module_key"]), str(row["service_key"])))
    documents = sorted(documents_by_key.values(), key=lambda row: str(row["document_key"]))
    edges.sort(key=lambda row: (int(row["source_row_number"]), str(row["type"]), int(row["reference_ordinal"])))
    source_rows.sort(key=lambda row: int(row["source_row_number"]))
    exceptions.sort(key=lambda row: (
        int(row["source_row_number"]), str(row["exception_type"]), str(row["reference_type"]),
        int(row["reference_ordinal"]) if row["reference_ordinal"] != "" else 0,
    ))
    if nonempty_before != len(edges) + rejected:
        raise AssertionError("Reference occurrence reconciliation failed")
    tables = {
        "modules.csv": modules,
        "services.csv": services,
        "documents.csv": documents,
        "service_document_edges.csv": edges,
        "source_rows.csv": source_rows,
        "exceptions.csv": exceptions,
    }
    counts = {
        "pilot_source_rows": len(raw_rows),
        "modules": len(modules),
        "services": len(services),
        "documents": len(documents),
        "reference_occurrences_before_normalization": nonempty_before,
        "accepted_reference_occurrences": len(edges),
        "rejected_reference_occurrences": rejected,
        "exceptions": len(exceptions),
        "blank_reference": sum(row["exception_type"] == "blank_reference" for row in exceptions),
        "duplicate_reference_occurrence": sum(
            row["exception_type"] == "duplicate_reference_occurrence" for row in exceptions
        ),
        "invalid_reference_format": sum(
            row["exception_type"] == "invalid_reference_format" for row in exceptions
        ),
        "identity_collision": sum(row["exception_type"] == "identity_collision" for row in exceptions),
    }
    return {"source_hash": source_hash, "tables": tables, "counts": counts}


def _render_tables(normalized: dict[str, object]) -> dict[str, bytes]:
    tables = normalized["tables"]
    return {name: _csv_bytes(tables[name], fields) for name, fields in CSV_FIELDS.items()}


def build_common_inventory(
    repo_root: Path,
    source: Path | None = None,
    index_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, object]:
    repo_root = repo_root.resolve()
    source = (source or repo_root / "outputs/services_icd_isd_inventory.csv").resolve()
    index_dir = (index_dir or repo_root / "indexes/capability_kg/015a").resolve()
    output_dir = (output_dir or repo_root / "outputs/capability_kg/015a").resolve()
    first = _normalize(source, PILOT_MODULE)
    second = _normalize(source, PILOT_MODULE)
    rendered = _render_tables(first)
    deterministic = rendered == _render_tables(second) and first["counts"] == second["counts"]
    if not deterministic:
        raise AssertionError("Unchanged input did not produce deterministic normalized output")

    counts = first["counts"]
    services = first["tables"]["services.csv"]
    edges = first["tables"]["service_document_edges.csv"]
    sample = services[0] if services else None
    sample_counts = Counter(
        edge["type"] for edge in edges if sample and edge["service_key"] == sample["service_key"]
    )
    summary = (
        "# Capability-KG 015-A validation summary\n\n"
        f"- Scope: `{PILOT_MODULE}` module pilot only.\n"
        f"- Input SHA-256: `{first['source_hash']}`.\n"
        f"- Source rows: {counts['pilot_source_rows']}; services: {counts['services']}; "
        f"documents: {counts['documents']}.\n"
        f"- Nonempty reference occurrences: {counts['reference_occurrences_before_normalization']}; "
        f"accepted: {counts['accepted_reference_occurrences']}; rejected: {counts['rejected_reference_occurrences']}.\n"
        f"- Exceptions: {counts['exceptions']} (blank: {counts['blank_reference']}, "
        f"invalid: {counts['invalid_reference_format']}, duplicate occurrence: "
        f"{counts['duplicate_reference_occurrence']}, identity collision: {counts['identity_collision']}).\n"
        f"- Deterministic unchanged-input rerun: {'PASS' if deterministic else 'FAIL'}.\n"
        + (f"- Sample lookup: `{PILOT_MODULE}` -> `{sample['service_name']}` -> "
           f"ICD {sample_counts['ICD']}, ISD {sample_counts['ISD']}.\n" if sample else "")
        + "- Documents were not fetched. No capability, API, graph, ownership, or runtime inference was made.\n"
        "- Next step: ready for Enterprise Architect review at `EA_REVIEW_CAPKG_015A`.\n"
    ).encode("utf-8")
    output_hashes = {f"indexes/capability_kg/015a/{name}": _sha256(data) for name, data in rendered.items()}
    output_hashes["outputs/capability_kg/015a/validation_summary.md"] = _sha256(summary)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "task": "Capability-KG/015-A",
        "status": "EA_REVIEW_CAPKG_015A",
        "scope": {"pilot_module": PILOT_MODULE, "sub_module_used_for_identity_or_classification": False},
        "input": {
            "path": "outputs/services_icd_isd_inventory.csv",
            "sha256": first["source_hash"],
            "required_columns": EXPECTED_COLUMNS,
        },
        "counts": counts,
        "validations": {
            "deterministic_rerun": deterministic,
            "reference_reconciliation": counts["reference_occurrences_before_normalization"] ==
                counts["accepted_reference_occurrences"] + counts["rejected_reference_occurrences"],
            "documents_fetched": False,
            "network_required": False,
            "staging_scanned": False,
        },
        "outputs": output_hashes,
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    index_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in rendered.items():
        (index_dir / name).write_bytes(data)
    (output_dir / "validation_summary.md").write_bytes(summary)
    (output_dir / "manifest.json").write_bytes(manifest_bytes)
    return {**first, "manifest": manifest, "deterministic": deterministic}


def _common_projection(normalized: dict[str, object]) -> dict[str, list[dict[str, object]]]:
    tables = normalized["tables"]
    modules = [row for row in tables["modules.csv"] if row["module_name"] == PILOT_MODULE]
    if len(modules) != 1:
        raise ValueError(f"COMMON_BASELINE_REGRESSION: expected one Common module, found {len(modules)}")
    module_key = modules[0]["module_key"]
    services = [row for row in tables["services.csv"] if row["module_key"] == module_key]
    edges = [row for row in tables["service_document_edges.csv"] if row["module_key"] == module_key]
    source_rows = [row for row in tables["source_rows.csv"] if row["module_key"] == module_key]
    source_row_numbers = {int(row["source_row_number"]) for row in source_rows}
    exceptions = [
        row for row in tables["exceptions.csv"] if int(row["source_row_number"]) in source_row_numbers
    ]
    document_keys = {row["document_key"] for row in edges}
    documents = [row for row in tables["documents.csv"] if row["document_key"] in document_keys]
    return {
        "modules.csv": modules,
        "services.csv": services,
        "documents.csv": documents,
        "service_document_edges.csv": edges,
        "source_rows.csv": source_rows,
        "exceptions.csv": exceptions,
    }


def _validate_common_regression(normalized: dict[str, object], repo_root: Path) -> dict[str, object]:
    projection = _common_projection(normalized)
    baseline_manifest_path = repo_root / BASELINE_OUTPUT_ROOT / "manifest.json"
    baseline_manifest = json.loads(baseline_manifest_path.read_text(encoding="utf-8"))
    file_results = {}
    for name, fields in CSV_FIELDS.items():
        baseline_relative = BASELINE_INDEX_ROOT / name
        baseline_bytes = (repo_root / baseline_relative).read_bytes()
        expected_hash = baseline_manifest["outputs"].get(baseline_relative.as_posix())
        if _sha256(baseline_bytes) != expected_hash:
            raise ValueError(f"COMMON_BASELINE_REGRESSION: historical baseline hash changed for {name}")
        projected_bytes = _csv_bytes(projection[name], fields)
        if projected_bytes != baseline_bytes:
            raise ValueError(f"COMMON_BASELINE_REGRESSION: normalized mapping differs for {name}")
        file_results[name] = {
            "baseline_sha256": expected_hash,
            "projected_sha256": _sha256(projected_bytes),
            "byte_equal": True,
        }
    counts = {
        "source_rows": len(projection["source_rows.csv"]),
        "services": len(projection["services.csv"]),
        "reference_occurrences": len(projection["service_document_edges.csv"]),
    }
    expected_counts = {"source_rows": 116, "services": 116, "reference_occurrences": 225}
    if counts != expected_counts:
        raise ValueError(f"COMMON_BASELINE_REGRESSION: counts {counts!r} differ from {expected_counts!r}")
    return {"status": "PASS", "counts": counts, "files": file_results}


def _module_coverage(normalized: dict[str, object]) -> list[dict[str, object]]:
    tables = normalized["tables"]
    services_by_module: dict[str, list[dict[str, object]]] = defaultdict(list)
    edges_by_module: dict[str, list[dict[str, object]]] = defaultdict(list)
    module_by_source_row = {
        int(row["source_row_number"]): row["module_key"] for row in tables["source_rows.csv"]
    }
    exceptions_by_module: Counter[str] = Counter()
    for row in tables["services.csv"]:
        services_by_module[str(row["module_key"])].append(row)
    for row in tables["service_document_edges.csv"]:
        edges_by_module[str(row["module_key"])].append(row)
    for row in tables["exceptions.csv"]:
        exceptions_by_module[module_by_source_row[int(row["source_row_number"])]] += 1

    coverage = []
    for module in tables["modules.csv"]:
        module_key = str(module["module_key"])
        services = services_by_module[module_key]
        edges = edges_by_module[module_key]
        services_with_documents = {str(row["service_key"]) for row in edges}
        type_counts = Counter(str(row["type"]) for row in edges)
        coverage.append({
            "module_key": module_key,
            "module_name": module["module_name"],
            "source_row_count": module["source_row_count"],
            "service_count": len(services),
            "icd_reference_occurrence_count": type_counts["ICD"],
            "isd_reference_occurrence_count": type_counts["ISD"],
            "total_reference_occurrence_count": len(edges),
            "unique_document_count": len({str(row["document_key"]) for row in edges}),
            "zero_document_service_count": sum(
                str(service["service_key"]) not in services_with_documents for service in services
            ),
            "exception_count": exceptions_by_module[module_key],
        })
    return sorted(coverage, key=lambda row: str(row["module_key"]))


def build_all_modules_inventory(
    repo_root: Path,
    source: Path | None = None,
    index_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, object]:
    """Normalize every source row and literal Module for Task 019-B."""
    repo_root = repo_root.resolve()
    source = (source or repo_root / "outputs/services_icd_isd_inventory.csv").resolve()
    index_dir = (index_dir or repo_root / TASK019B_INDEX_ROOT).resolve()
    output_dir = (output_dir or repo_root / TASK019B_OUTPUT_ROOT).resolve()
    normalized = _normalize(source, pilot_module=None)
    rendered = _render_tables(normalized)
    coverage = _module_coverage(normalized)
    rendered["module_coverage.csv"] = _csv_bytes(coverage, MODULE_COVERAGE_FIELDS)
    common_regression = _validate_common_regression(normalized, repo_root)

    tables = normalized["tables"]
    edges = tables["service_document_edges.csv"]
    edge_types = Counter(str(row["type"]) for row in edges)
    services_with_documents = {str(row["service_key"]) for row in edges}
    exception_types = Counter(str(row["exception_type"]) for row in tables["exceptions.csv"])
    counts = {
        "source_data_rows": len(tables["source_rows.csv"]),
        "processed_source_rows": len(tables["source_rows.csv"]),
        "modules": len(tables["modules.csv"]),
        "services": len(tables["services.csv"]),
        "documents": len(tables["documents.csv"]),
        "source_reference_occurrences": normalized["counts"]["reference_occurrences_before_normalization"],
        "accepted_reference_occurrences": normalized["counts"]["accepted_reference_occurrences"],
        "rejected_reference_occurrences": normalized["counts"]["rejected_reference_occurrences"],
        "icd_reference_occurrences": edge_types["ICD"],
        "isd_reference_occurrences": edge_types["ISD"],
        "zero_document_services": sum(
            str(row["service_key"]) not in services_with_documents for row in tables["services.csv"]
        ),
        "exceptions": len(tables["exceptions.csv"]),
        "blank_reference": exception_types["blank_reference"],
        "invalid_reference_format": exception_types["invalid_reference_format"],
        "duplicate_reference_occurrence": exception_types["duplicate_reference_occurrence"],
        "identity_collision": exception_types["identity_collision"],
    }
    reference_closure = (
        counts["source_reference_occurrences"] ==
        counts["accepted_reference_occurrences"] + counts["rejected_reference_occurrences"]
    )
    module_coverage_closure = (
        sum(int(row["source_row_count"]) for row in coverage) == counts["processed_source_rows"] and
        sum(int(row["service_count"]) for row in coverage) == counts["services"] and
        sum(int(row["total_reference_occurrence_count"]) for row in coverage) ==
        counts["accepted_reference_occurrences"]
    )
    if not reference_closure or not module_coverage_closure:
        raise AssertionError("Task 019-B coverage reconciliation failed")

    summary = (
        "# Phase 6 Task 019-B validation summary\n\n"
        "- Scope: all literal Modules and all source rows; Sub Module excluded from the working model.\n"
        f"- Input SHA-256: `{normalized['source_hash']}`.\n"
        f"- Coverage: {counts['processed_source_rows']}/{counts['source_data_rows']} rows; "
        f"{counts['modules']} modules; {counts['services']} module-scoped services.\n"
        f"- References: {counts['icd_reference_occurrences']} ICD + "
        f"{counts['isd_reference_occurrences']} ISD = {counts['source_reference_occurrences']} source occurrences; "
        f"{counts['accepted_reference_occurrences']} accepted + "
        f"{counts['rejected_reference_occurrences']} rejected.\n"
        f"- Documents: {counts['documents']} unique typed identities; "
        f"zero-document services: {counts['zero_document_services']}.\n"
        f"- Exceptions: {counts['exceptions']} (blank {counts['blank_reference']}; "
        f"invalid {counts['invalid_reference_format']}; duplicate occurrence "
        f"{counts['duplicate_reference_occurrence']}; identity collision {counts['identity_collision']}).\n"
        "- Common regression: PASS; 116 source rows, 116 services, 225 occurrences, "
        "and all six normalized CSV projections byte-match the frozen baseline.\n"
        "- Per-module coverage: `indexes/phase6/task019/019b/module_coverage.csv`.\n"
        "- No documents were fetched and no semantic, API, graph, runtime, or product inference was made.\n"
        "- Next gate: `EA_REVIEW_TASK019B`.\n"
    ).encode("utf-8")
    output_hashes = {
        (TASK019B_INDEX_ROOT / name).as_posix(): _sha256(content) for name, content in rendered.items()
    }
    output_hashes[(TASK019B_OUTPUT_ROOT / "validation_summary.md").as_posix()] = _sha256(summary)
    manifest = {
        "schema_version": TASK019B_SCHEMA_VERSION,
        "parser_schema_version": SCHEMA_VERSION,
        "task": "Phase 6 / Task 019-B",
        "status": "EA_REVIEW_TASK019B",
        "scope": {
            "all_modules": True,
            "pilot_filter": None,
            "sub_module_used_for_identity_or_grouping": False,
        },
        "input": {
            "path": "outputs/services_icd_isd_inventory.csv",
            "sha256": normalized["source_hash"],
            "committed": False,
            "required_columns": EXPECTED_COLUMNS,
            "parse_count": 1,
        },
        "counts": counts,
        "exception_counts": dict(sorted(exception_types.items())),
        "common_regression": common_regression,
        "module_coverage_index": (TASK019B_INDEX_ROOT / "module_coverage.csv").as_posix(),
        "validations": {
            "full_row_coverage": counts["processed_source_rows"] == counts["source_data_rows"],
            "all_literal_modules_represented": True,
            "reference_closure": reference_closure,
            "module_coverage_closure": module_coverage_closure,
            "common_baseline_regression": True,
            "deterministic_sorting": True,
            "documents_fetched": False,
            "network_required": False,
            "semantic_work_performed": False,
            "staging_scanned": False,
        },
        "outputs": output_hashes,
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    index_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in rendered.items():
        (index_dir / name).write_bytes(content)
    (output_dir / "validation_summary.md").write_bytes(summary)
    (output_dir / "manifest.json").write_bytes(manifest_bytes)
    return {**normalized, "coverage": coverage, "manifest": manifest, "summary": summary}


def consolidate_accepted_baseline(
    repo_root: Path,
    index_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, object]:
    """Validate and byte-copy the accepted 015-A baseline into Task 019-A.

    This function never invokes the CSV normalization/parser. The private input
    is read only to verify its accepted SHA-256 and is never copied.
    """
    repo_root = repo_root.resolve()
    index_dir = (index_dir or repo_root / TASK019A_INDEX_ROOT).resolve()
    output_dir = (output_dir or repo_root / TASK019A_OUTPUT_ROOT).resolve()
    baseline_manifest_path = repo_root / BASELINE_OUTPUT_ROOT / "manifest.json"
    baseline_manifest_bytes = baseline_manifest_path.read_bytes()
    baseline_manifest = json.loads(baseline_manifest_bytes.decode("utf-8"))
    baseline_counts = baseline_manifest.get("counts", {})
    for key, expected in ACCEPTED_COUNTS.items():
        if baseline_counts.get(key) != expected:
            raise ValueError(
                f"REVIEW_REQUIRED_MIGRATION_MISMATCH: accepted {key}={expected}, "
                f"baseline has {baseline_counts.get(key)!r}"
            )

    source_relative = Path(baseline_manifest["input"]["path"])
    source_path = repo_root / source_relative
    if not source_path.is_file():
        raise FileNotFoundError(f"BLOCKED_INPUT_NOT_AVAILABLE: {source_relative.as_posix()}")
    source_hash = _sha256(source_path.read_bytes())
    if source_hash != baseline_manifest["input"]["sha256"]:
        raise ValueError("REVIEW_REQUIRED_MIGRATION_MISMATCH: private input hash changed")

    for relative, recorded_hash in baseline_manifest["outputs"].items():
        historical_path = repo_root / relative
        if not historical_path.is_file() or _sha256(historical_path.read_bytes()) != recorded_hash:
            raise ValueError(
                f"REVIEW_REQUIRED_MIGRATION_MISMATCH: accepted historical output changed: {relative}"
            )

    baseline_files: dict[str, bytes] = {}
    mappings: dict[str, dict[str, object]] = {}
    for name in CSV_FIELDS:
        old_relative = BASELINE_INDEX_ROOT / name
        old_path = repo_root / old_relative
        content = old_path.read_bytes()
        content_hash = _sha256(content)
        recorded_hash = baseline_manifest["outputs"].get(old_relative.as_posix())
        if recorded_hash != content_hash:
            raise ValueError(
                f"REVIEW_REQUIRED_MIGRATION_MISMATCH: {old_relative.as_posix()} hash differs from baseline"
            )
        with io.StringIO(content.decode("utf-8"), newline="") as stream:
            row_count = sum(1 for _ in csv.DictReader(stream))
        baseline_files[name] = content
        mappings[name] = {
            "old_path": old_relative.as_posix(),
            "new_path": (TASK019A_INDEX_ROOT / name).as_posix(),
            "sha256": content_hash,
            "row_count": row_count,
            "byte_equal": True,
            "semantic_equal": True,
        }

    summary = (
        "# Phase 6 Task 019-A validation summary\n\n"
        "- Scope: workspace consolidation and accepted Common baseline equivalence only.\n"
        f"- Source baseline: `Capability-KG/015-A`; private input SHA-256: `{source_hash}`.\n"
        f"- Accepted counts: {baseline_counts['pilot_source_rows']} rows; "
        f"{baseline_counts['services']} services; "
        f"{baseline_counts['accepted_reference_occurrences']} reference occurrences.\n"
        "- Migration validation: PASS; all six canonical CSV indexes are byte- and semantic-equal.\n"
        "- Ownership: 019-A consolidation; 019-B document acquisition; 019-C persistent cache; "
        "019-D ICD semantics; 019-E ISD contracts; 019-F canonical resolution; "
        "019-G capability API/scheduler mapping; 019-H knowledge graph; "
        "019-I queries and validation; 019-J module rollout.\n"
        "- Roadmap entries are ownership notes only and are not authorization to implement later tasks.\n"
        "- No document fetch, semantic extraction, graph work, API mapping, or network access occurred.\n"
        "- Next gate: `EA_REVIEW_TASK019A`.\n"
    ).encode("utf-8")
    manifest = {
        "schema_version": TASK019A_SCHEMA_VERSION,
        "task": "Phase 6 / Task 019-A",
        "status": "EA_REVIEW_TASK019A",
        "source_baseline": "Capability-KG/015-A",
        "source": {
            "private_input_path": source_relative.as_posix(),
            "private_input_sha256": source_hash,
            "private_input_committed": False,
            "baseline_manifest_path": (BASELINE_OUTPUT_ROOT / "manifest.json").as_posix(),
            "baseline_manifest_sha256": _sha256(baseline_manifest_bytes),
        },
        "path_mapping": {
            "code_old": "capability_kg/inventory_normalization.py",
            "code_new": "business_capability_kg/inventory_normalization.py",
            "indexes_old": BASELINE_INDEX_ROOT.as_posix(),
            "indexes_new": TASK019A_INDEX_ROOT.as_posix(),
            "outputs_old": BASELINE_OUTPUT_ROOT.as_posix(),
            "outputs_new": TASK019A_OUTPUT_ROOT.as_posix(),
        },
        "counts": baseline_counts,
        "files": mappings,
        "validations": {
            "all_file_hashes_match_accepted_baseline": True,
            "all_files_byte_equal": True,
            "all_files_semantic_equal": True,
            "accepted_counts_unchanged": True,
            "private_input_hash_matches": True,
            "historical_manifest_outputs_verified": True,
            "normalizer_rerun": False,
            "network_required": False,
            "documents_fetched": False,
            "semantic_work_performed": False,
            "staging_scanned": False,
        },
        "outputs": {
            **{mapping["new_path"]: mapping["sha256"] for mapping in mappings.values()},
            (TASK019A_OUTPUT_ROOT / "validation_summary.md").as_posix(): _sha256(summary),
        },
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")

    index_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in baseline_files.items():
        destination = index_dir / name
        destination.write_bytes(content)
        if destination.read_bytes() != content:
            raise ValueError(f"REVIEW_REQUIRED_MIGRATION_MISMATCH: copy verification failed for {name}")
    (output_dir / "validation_summary.md").write_bytes(summary)
    (output_dir / "manifest.json").write_bytes(manifest_bytes)
    return {"manifest": manifest, "manifest_bytes": manifest_bytes, "summary": summary}


def legacy_main() -> None:
    parser = argparse.ArgumentParser(description="Normalize the Capability-KG 015-A Common-module pilot")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--input", type=Path)
    parser.add_argument("--index-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    result = build_common_inventory(args.root, args.input, args.index_dir, args.output_dir)
    print(json.dumps(result["manifest"]["counts"], indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Consolidate the accepted 015-A baseline into Phase 6 Task 019-A")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--index-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    result = consolidate_accepted_baseline(args.root, args.index_dir, args.output_dir)
    print(json.dumps(result["manifest"]["counts"], indent=2, sort_keys=True))
