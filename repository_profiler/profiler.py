"""Phase 0 deterministic repository profiler.

Project phase naming:

* Phase 0: Repository Profiling
* Phase 1: Object Extraction & Normalization
* Phase 2: URI / Identifier Resolution
* Phase 3: Relationship Reconstruction

Only file metadata and structural schema markers are emitted. Source document
contents, including credential values, are never copied to generated reports.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml


PARSE_OK = "PARSE_OK"
PARSE_FAILED = "PARSE_FAILED"
NOT_APPLICABLE = "NOT_APPLICABLE"
NOT_EVALUATED = "NOT_EVALUATED"
SUPPORTED_SCHEMA = "SUPPORTED_SCHEMA"
UNSUPPORTED_SCHEMA = "UNSUPPORTED_SCHEMA"
EXACT_FILE_DUPLICATE = "EXACT_FILE_DUPLICATE"
NOT_EXACT_FILE_DUPLICATE = "NOT_EXACT_FILE_DUPLICATE"

SUPPORTED_OPENAPI_RE = re.compile(r"^3\.(?:0|1)(?:\.\d+)?$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _format_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return "YAML"
    if suffix == ".json":
        return "JSON"
    return "OTHER"


def _parse(path: Path, detected_format: str) -> tuple[Any, str, dict[str, Any] | None]:
    if detected_format == "OTHER":
        return None, NOT_APPLICABLE, None

    try:
        text = path.read_text(encoding="utf-8-sig")
        if detected_format == "JSON":
            return json.loads(text), PARSE_OK, None
        documents = list(yaml.safe_load_all(text))
        parsed: Any = documents[0] if len(documents) == 1 else documents
        return parsed, PARSE_OK, None
    except json.JSONDecodeError as error:
        return None, PARSE_FAILED, {
            "failure_reason": "parse_failed_invalid_json",
            "line": error.lineno,
            "column": error.colno,
        }
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        details: dict[str, Any] = {"failure_reason": "parse_failed_invalid_yaml"}
        if mark is not None:
            details.update({"line": mark.line + 1, "column": mark.column + 1})
        return None, PARSE_FAILED, details
    except (UnicodeDecodeError, OSError):
        reason = (
            "parse_failed_invalid_json"
            if detected_format == "JSON"
            else "parse_failed_invalid_yaml"
        )
        return None, PARSE_FAILED, {"failure_reason": reason}


def _version_result(family: str, version: Any, supported: bool) -> dict[str, Any]:
    result = {
        "schema_family": family,
        "schema_version": str(version),
        "schema_support_status": SUPPORTED_SCHEMA if supported else UNSUPPORTED_SCHEMA,
        "schema_failure_reason": None,
    }
    if not supported:
        result["schema_failure_reason"] = "unsupported_schema_version"
    return result


def _detect_schema(data: Any, detected_format: str, parse_status: str) -> dict[str, Any]:
    if parse_status == PARSE_FAILED:
        return {
            "schema_family": "UNDETERMINED",
            "schema_version": None,
            "schema_support_status": NOT_EVALUATED,
            "schema_failure_reason": None,
        }
    if detected_format == "OTHER":
        return {
            "schema_family": "OTHER",
            "schema_version": None,
            "schema_support_status": UNSUPPORTED_SCHEMA,
            "schema_failure_reason": "unsupported_file_format",
        }

    if isinstance(data, dict):
        if "swagger" in data:
            version = data["swagger"]
            return _version_result("OPENAPI_DOCUMENT", version, str(version) == "2.0")
        if "openapi" in data:
            version = data["openapi"]
            return _version_result(
                "OPENAPI_DOCUMENT",
                version,
                bool(SUPPORTED_OPENAPI_RE.fullmatch(str(version))),
            )
        if "product" in data:
            version = data["product"]
            return _version_result("APIC_PRODUCT", version, str(version) == "1.0.0")
        if "api_version" in data and "type" in data:
            version = data["api_version"]
            return _version_result("APIC_RESOURCE", version, str(version) == "2.0.0")
        if {"results", "total_results"}.issubset(data):
            return _supported_unversioned("APIC_COLLECTION")
        return _supported_unversioned(f"{detected_format}_OBJECT")

    if isinstance(data, list):
        return _supported_unversioned(f"{detected_format}_ARRAY")
    if data is None:
        return _supported_unversioned(f"{detected_format}_EMPTY")
    return _supported_unversioned(f"{detected_format}_SCALAR")


def _supported_unversioned(family: str) -> dict[str, Any]:
    return {
        "schema_family": family,
        "schema_version": None,
        "schema_support_status": SUPPORTED_SCHEMA,
        "schema_failure_reason": None,
    }


def _source_details(source_root: Path, path: Path) -> tuple[str, str, str]:
    relative_inside = path.relative_to(source_root)
    source_path = (Path(source_root.name) / relative_inside).as_posix()
    parts = relative_inside.parts
    source_category = parts[0] if len(parts) > 1 else "_root"
    source_folder = (Path(source_root.name) / relative_inside.parent).as_posix()
    return source_path, source_category, source_folder


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for value in values:
            output.write(json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n")


def _ensure_output_is_outside_source(source_root: Path, output_root: Path) -> None:
    source = source_root.resolve()
    output = output_root.resolve()
    if output == source or source in output.parents:
        raise ValueError("output root must not be inside the immutable source directory")


def profile_repository(source_root: Path, output_root: Path) -> dict[str, Any]:
    """Profile every file under ``source_root`` and write Phase 0 artifacts."""
    source_root = Path(source_root)
    output_root = Path(output_root)
    if not source_root.is_dir():
        raise ValueError(f"source directory does not exist: {source_root}")
    _ensure_output_is_outside_source(source_root, output_root)

    paths = sorted(
        (path for path in source_root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(source_root).as_posix(),
    )
    records: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []
    hashes: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for path in paths:
        source_path, source_category, source_folder = _source_details(source_root, path)
        detected_format = _format_for(path)
        data, parse_status, parse_error = _parse(path, detected_format)
        schema = _detect_schema(data, detected_format, parse_status)
        digest = _sha256(path)
        record = {
            "source_path": source_path,
            "relative_source_path": source_path,
            "source_category": source_category,
            "source_folder": source_folder,
            "file_extension": path.suffix.lower(),
            "file_size_bytes": path.stat().st_size,
            "sha256": digest,
            "detected_format": detected_format,
            "parse_status": parse_status,
            "parse_failure_reason": parse_error["failure_reason"] if parse_error else None,
            **schema,
            "exact_duplicate_group": None,
            "duplicate_status": NOT_EXACT_FILE_DUPLICATE,
            "duplicate_failure_reason": None,
        }
        records.append(record)
        hashes[digest].append(record)
        if parse_error:
            parse_errors.append({"source_path": source_path, **parse_error})

    duplicate_records: list[dict[str, Any]] = []
    duplicate_groups = [
        (digest, members)
        for digest, members in hashes.items()
        if len(members) > 1
    ]
    for digest, members in sorted(duplicate_groups):
        group = f"sha256:{digest}"
        for member in members:
            member["exact_duplicate_group"] = group
            member["duplicate_status"] = EXACT_FILE_DUPLICATE
            member["duplicate_failure_reason"] = "duplicate_due_to_identical_hash"
            duplicate_records.append(
                {
                    "exact_duplicate_group": group,
                    "sha256": digest,
                    "source_path": member["source_path"],
                    "status": EXACT_FILE_DUPLICATE,
                    "failure_reason": "duplicate_due_to_identical_hash",
                }
            )

    duplicate_records.sort(key=lambda item: (item["exact_duplicate_group"], item["source_path"]))
    category_counts = Counter(record["source_category"] for record in records)
    extension_counts = Counter(record["file_extension"] or "[no extension]" for record in records)
    format_counts = Counter(record["detected_format"] for record in records)
    family_counts = Counter(record["schema_family"] for record in records)
    family_support_counts: dict[str, Counter[str]] = defaultdict(Counter)
    family_versions: dict[str, set[str]] = defaultdict(set)
    for record in records:
        family_support_counts[record["schema_family"]][record["schema_support_status"]] += 1
        if record["schema_version"] is not None:
            family_versions[record["schema_family"]].add(record["schema_version"])

    schema_families = {
        "schema_families": [
            {
                "schema_family": family,
                "file_count": family_counts[family],
                "schema_versions": sorted(family_versions[family]),
                "support_status_counts": dict(sorted(family_support_counts[family].items())),
            }
            for family in sorted(family_counts)
        ]
    }
    profile = {
        "total_files": len(records),
        "files_by_source_category": dict(sorted(category_counts.items())),
        "files_by_extension": dict(sorted(extension_counts.items())),
        "yaml_count": format_counts["YAML"],
        "json_count": format_counts["JSON"],
        "other_count": format_counts["OTHER"],
        "successfully_parsed_count": sum(r["parse_status"] == PARSE_OK for r in records),
        "parse_failure_count": sum(r["parse_status"] == PARSE_FAILED for r in records),
        "schema_families_detected": dict(sorted(family_counts.items())),
        "unsupported_schema_count": sum(
            r["schema_support_status"] == UNSUPPORTED_SCHEMA for r in records
        ),
        "exact_duplicate_file_count": len(duplicate_records),
        "exact_duplicate_group_count": len(duplicate_groups),
    }

    _write_jsonl(output_root / "indexes/file_index.jsonl", records)
    _write_json(output_root / "outputs/repository_profile/repository_profile.json", profile)
    _write_jsonl(output_root / "outputs/parse_errors/parse_errors.jsonl", parse_errors)
    _write_jsonl(
        output_root / "outputs/duplicates/exact_duplicate_files.jsonl",
        duplicate_records,
    )
    _write_json(output_root / "outputs/schema_families/schema_families.json", schema_families)
    return profile


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("staging"))
    parser.add_argument("--output-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    profile = profile_repository(args.source, args.output_root)
    print(json.dumps(profile, indent=2, sort_keys=True))
    return 0
