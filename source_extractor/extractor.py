"""Phase 1 deterministic source-occurrence extractor.

The extractor preserves evidence needed by later identity resolution. It does
not merge occurrences, resolve references, or emit graph relationships.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ElementTree
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import yaml


EXTRACTED = "EXTRACTED"
EXTRACTION_PARTIAL = "EXTRACTION_PARTIAL"
EXTRACTION_FAILED = "EXTRACTION_FAILED"

REQUIRED_FIELD_MISSING = "required_field_missing"
UNSUPPORTED_OBJECT_SHAPE = "unsupported_object_shape"
SOURCE_ARTIFACT_MALFORMED = "source_artifact_malformed"
FIELD_TYPE_MISMATCH = "field_type_mismatch"

APPROVED_OBJECT_TYPES = {
    "api_artifact",
    "product",
    "plan",
    "consumer_org",
    "application",
    "credential",
    "subscription",
    "catalog_config",
    "catalog_property",
}

REASON_ORDER = {
    REQUIRED_FIELD_MISSING: 0,
    UNSUPPORTED_OBJECT_SHAPE: 1,
    SOURCE_ARTIFACT_MALFORMED: 2,
    FIELD_TYPE_MISMATCH: 3,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_path(source_root: Path, path: Path) -> str:
    return (Path(source_root.name) / path.relative_to(source_root)).as_posix()


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _record_id(candidate: str | None, source_path: str, pointer: str) -> str:
    identity = json.dumps(
        [candidate, source_path, pointer],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"extracted-record:sha256:{hashlib.sha256(identity).hexdigest()}"


def _schema_family(data: Any, path: Path) -> str:
    if path.suffix.lower() == ".wsdl":
        return "OTHER"
    if isinstance(data, dict):
        if "swagger" in data or "openapi" in data:
            return "OPENAPI_DOCUMENT"
        if "product" in data:
            return "APIC_PRODUCT"
        if "api_version" in data and "type" in data:
            return "APIC_RESOURCE"
        if {"results", "total_results"}.issubset(data):
            return "APIC_COLLECTION"
        return "JSON_OBJECT" if path.suffix.lower() == ".json" else "YAML_OBJECT"
    if isinstance(data, list):
        return "JSON_ARRAY" if path.suffix.lower() == ".json" else "YAML_ARRAY"
    if data is None:
        return "JSON_EMPTY" if path.suffix.lower() == ".json" else "YAML_EMPTY"
    return "JSON_SCALAR" if path.suffix.lower() == ".json" else "YAML_SCALAR"


def _load_phase_zero_families(output_root: Path) -> dict[str, str]:
    index = output_root / "indexes/file_index.jsonl"
    if not index.is_file():
        return {}
    families: dict[str, str] = {}
    try:
        for line in index.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            source_path = item.get("source_path")
            family = item.get("schema_family")
            if isinstance(source_path, str) and isinstance(family, str):
                families[source_path] = family
    except (OSError, json.JSONDecodeError):
        return {}
    return families


def _string(
    value: Any,
    reasons: set[str],
    *,
    required: bool = False,
) -> str | None:
    if value is None:
        if required:
            reasons.add(REQUIRED_FIELD_MISSING)
        return None
    if not isinstance(value, str):
        reasons.add(FIELD_TYPE_MISMATCH)
        return None
    if required and not value:
        reasons.add(REQUIRED_FIELD_MISSING)
        return None
    return value


def _string_list(value: Any, reasons: set[str]) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        reasons.add(FIELD_TYPE_MISMATCH)
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            result.append(item)
        else:
            reasons.add(FIELD_TYPE_MISMATCH)
    return result


def _status(reasons: set[str], *, failed: bool = False) -> str:
    if failed:
        return EXTRACTION_FAILED
    return EXTRACTION_PARTIAL if reasons else EXTRACTED


def _base_record(
    *,
    candidate: str | None,
    source_path: str,
    source_sha256: str,
    schema_family: str,
    pointer: str,
    status: str = EXTRACTED,
    reasons: Iterable[str] = (),
) -> dict[str, Any]:
    if candidate is not None and candidate not in APPROVED_OBJECT_TYPES:
        raise ValueError(f"unapproved canonical object type: {candidate}")
    failure_reasons = sorted(set(reasons), key=REASON_ORDER.__getitem__)
    return {
        "extracted_record_id": _record_id(candidate, source_path, pointer),
        "canonical_object_type_candidate": candidate,
        "extraction_status": status,
        "failure_reasons": failure_reasons,
        "source_relative_path": source_path,
        "source_sha256": source_sha256,
        "source_schema_family": schema_family,
        "source_object_pointer": pointer,
        "apic_object_id": None,
        "apic_object_url": None,
        "name": None,
        "title": None,
        "version": None,
        "org_url": None,
        "catalog_url": None,
    }


def _object_record(
    item: dict[str, Any],
    *,
    candidate: str,
    source_path: str,
    source_sha256: str,
    schema_family: str,
    pointer: str,
    required: tuple[str, ...] = (),
) -> tuple[dict[str, Any], set[str]]:
    reasons: set[str] = set()
    values = {
        "apic_object_id": _string(item.get("id"), reasons, required="id" in required),
        "apic_object_url": _string(item.get("url"), reasons, required="url" in required),
        "name": _string(item.get("name"), reasons, required="name" in required),
        "title": _string(item.get("title"), reasons),
        "version": _string(item.get("version"), reasons, required="version" in required),
        "org_url": _string(item.get("org_url"), reasons),
        "catalog_url": _string(item.get("catalog_url"), reasons),
    }
    record = _base_record(
        candidate=candidate,
        source_path=source_path,
        source_sha256=source_sha256,
        schema_family=schema_family,
        pointer=pointer,
        status=_status(reasons),
        reasons=reasons,
    )
    record.update(values)
    observed_type = _string(item.get("type"), reasons)
    if observed_type is not None:
        record["observed_type"] = observed_type
    record["extraction_status"] = _status(reasons)
    record["failure_reasons"] = sorted(reasons, key=REASON_ORDER.__getitem__)
    return record, reasons


def _unsupported_record(
    *,
    source_path: str,
    source_sha256: str,
    schema_family: str,
    pointer: str,
    malformed: bool = False,
) -> dict[str, Any]:
    reason = SOURCE_ARTIFACT_MALFORMED if malformed else UNSUPPORTED_OBJECT_SHAPE
    return _base_record(
        candidate=None,
        source_path=source_path,
        source_sha256=source_sha256,
        schema_family=schema_family,
        pointer=pointer,
        status=EXTRACTION_FAILED,
        reasons=(reason,),
    )


def _map_product_ref(raw_ref: str, project_root: Path) -> str | None:
    if raw_ref.count("/staging/") != 1:
        return None
    suffix = raw_ref.split("/staging/", 1)[1]
    mapped = (Path("staging") / suffix).as_posix()
    if any(part in {"", ".", ".."} for part in Path(mapped).parts):
        return None
    return mapped if (project_root / mapped).is_file() else None


def _api_document_record(
    data: dict[str, Any],
    *,
    source_path: str,
    source_sha256: str,
    schema_family: str,
) -> dict[str, Any]:
    reasons: set[str] = set()
    info = data.get("info")
    if not isinstance(info, dict):
        reasons.add(REQUIRED_FIELD_MISSING if info is None else FIELD_TYPE_MISMATCH)
        info = {}
    name = _string(info.get("x-ibm-name"), reasons, required=True)
    title = _string(info.get("title"), reasons)
    version = _string(info.get("version"), reasons, required=True)
    record = _base_record(
        candidate="api_artifact",
        source_path=source_path,
        source_sha256=source_sha256,
        schema_family=schema_family,
        pointer="",
        status=_status(reasons),
        reasons=reasons,
    )
    record.update({"name": name, "title": title, "version": version})
    return record


def _product_document_records(
    data: dict[str, Any],
    *,
    source_path: str,
    source_sha256: str,
    schema_family: str,
    project_root: Path,
) -> list[dict[str, Any]]:
    reasons: set[str] = set()
    info = data.get("info")
    if not isinstance(info, dict):
        reasons.add(REQUIRED_FIELD_MISSING if info is None else FIELD_TYPE_MISMATCH)
        info = {}
    name = _string(info.get("name"), reasons, required=True)
    title = _string(info.get("title"), reasons)
    version = _string(info.get("version"), reasons, required=True)

    api_references: list[dict[str, str | None]] = []
    apis = data.get("apis")
    if apis is None:
        apis = {}
    elif not isinstance(apis, dict):
        reasons.add(FIELD_TYPE_MISMATCH)
        apis = {}
    for api_key in sorted(apis):
        entry = apis[api_key]
        if not isinstance(api_key, str) or not isinstance(entry, dict):
            reasons.add(FIELD_TYPE_MISMATCH)
            continue
        raw_ref = _string(entry.get("$ref"), reasons, required=True)
        api_references.append(
            {
                "api_key": api_key,
                "raw_ref": raw_ref,
                "mapped_source_relative_path": (
                    _map_product_ref(raw_ref, project_root) if raw_ref is not None else None
                ),
            }
        )

    product = _base_record(
        candidate="product",
        source_path=source_path,
        source_sha256=source_sha256,
        schema_family=schema_family,
        pointer="",
        status=_status(reasons),
        reasons=reasons,
    )
    product.update(
        {
            "name": name,
            "title": title,
            "version": version,
            "api_references": api_references,
        }
    )

    records = [product]
    plans = data.get("plans")
    if plans is None:
        plans = {}
    elif not isinstance(plans, dict):
        reasons.add(FIELD_TYPE_MISMATCH)
        plans = {}
        product["extraction_status"] = _status(reasons)
        product["failure_reasons"] = sorted(reasons, key=REASON_ORDER.__getitem__)
    for plan_key in sorted(plans):
        plan_value = plans[plan_key]
        pointer = f"/plans/{_pointer_token(str(plan_key))}"
        if not isinstance(plan_key, str) or not isinstance(plan_value, dict):
            records.append(
                _unsupported_record(
                    source_path=source_path,
                    source_sha256=source_sha256,
                    schema_family=schema_family,
                    pointer=pointer,
                )
            )
            continue
        plan_reasons: set[str] = set()
        plan_apis = plan_value.get("apis")
        if plan_apis is None:
            plan_apis = {}
        elif not isinstance(plan_apis, dict):
            plan_reasons.add(FIELD_TYPE_MISMATCH)
            plan_apis = {}
        plan = _base_record(
            candidate="plan",
            source_path=source_path,
            source_sha256=source_sha256,
            schema_family=schema_family,
            pointer=pointer,
            status=_status(plan_reasons),
            reasons=plan_reasons,
        )
        plan.update(
            {
                "name": plan_key,
                "title": _string(plan_value.get("title"), plan_reasons),
                "parent_extracted_record_id": product["extracted_record_id"],
                "plan_key": plan_key,
                "api_keys": sorted(key for key in plan_apis if isinstance(key, str)),
            }
        )
        if len(plan["api_keys"]) != len(plan_apis):
            plan_reasons.add(FIELD_TYPE_MISMATCH)
        plan["extraction_status"] = _status(plan_reasons)
        plan["failure_reasons"] = sorted(plan_reasons, key=REASON_ORDER.__getitem__)
        records.append(plan)
    return records


def _summary_plan_records(
    plans: Any,
    *,
    source_path: str,
    source_sha256: str,
    schema_family: str,
    pointer: str,
    parent_id: str,
) -> list[dict[str, Any]]:
    if plans is None:
        return []
    if not isinstance(plans, list):
        return []
    records: list[dict[str, Any]] = []
    for index, value in enumerate(plans):
        plan_pointer = f"{pointer}/plans/{index}"
        if not isinstance(value, dict):
            records.append(
                _unsupported_record(
                    source_path=source_path,
                    source_sha256=source_sha256,
                    schema_family=schema_family,
                    pointer=plan_pointer,
                )
            )
            continue
        reasons: set[str] = set()
        name = _string(value.get("name"), reasons, required=True)
        api_references: list[dict[str, str | None]] = []
        api_items = value.get("apis")
        if api_items is None:
            api_items = []
        elif not isinstance(api_items, list):
            reasons.add(FIELD_TYPE_MISMATCH)
            api_items = []
        for api in api_items:
            if not isinstance(api, dict):
                reasons.add(FIELD_TYPE_MISMATCH)
                continue
            api_references.append(
                {
                    "apic_object_id": _string(api.get("id"), reasons),
                    "apic_object_url": _string(api.get("url"), reasons),
                    "name": _string(api.get("name"), reasons),
                    "version": _string(api.get("version"), reasons),
                }
            )
        record = _base_record(
            candidate="plan",
            source_path=source_path,
            source_sha256=source_sha256,
            schema_family=schema_family,
            pointer=plan_pointer,
            status=_status(reasons),
            reasons=reasons,
        )
        record.update(
            {
                "name": name,
                "title": _string(value.get("title"), reasons),
                "parent_extracted_record_id": parent_id,
                "plan_key": name,
                "api_references": api_references,
            }
        )
        record["extraction_status"] = _status(reasons)
        record["failure_reasons"] = sorted(reasons, key=REASON_ORDER.__getitem__)
        records.append(record)
    return records


def _collection_item_records(
    item: Any,
    *,
    source_path: str,
    source_sha256: str,
    schema_family: str,
    pointer: str,
    source_category: str,
) -> list[dict[str, Any]]:
    if not isinstance(item, dict):
        return [
            _unsupported_record(
                source_path=source_path,
                source_sha256=source_sha256,
                schema_family=schema_family,
                pointer=pointer,
            )
        ]

    observed_type = item.get("type")
    candidate = {
        "api": "api_artifact",
        "product": "product",
        "consumer_org": "consumer_org",
        "app": "application",
        "credential": "credential",
        "subscription": "subscription",
    }.get(observed_type)
    if candidate is None and source_category == "config" and observed_type != "member":
        candidate = "catalog_property"
    if candidate is None:
        return [
            _unsupported_record(
                source_path=source_path,
                source_sha256=source_sha256,
                schema_family=schema_family,
                pointer=pointer,
            )
        ]

    required = {
        "api_artifact": ("id", "url", "name", "version"),
        "product": ("id", "url", "name", "version"),
        "consumer_org": ("id", "url", "name"),
        "application": ("id", "url", "name"),
        "credential": ("id", "url", "name"),
        "subscription": ("id", "url", "name"),
        "catalog_property": (),
    }[candidate]
    record, reasons = _object_record(
        item,
        candidate=candidate,
        source_path=source_path,
        source_sha256=source_sha256,
        schema_family=schema_family,
        pointer=pointer,
        required=required,
    )

    if candidate == "product":
        record["api_urls"] = _string_list(item.get("api_urls"), reasons)
    elif candidate == "application":
        record["consumer_org_url"] = _string(
            item.get("consumer_org_url"), reasons, required=True
        )
        record["app_credential_urls"] = _string_list(
            item.get("app_credential_urls"), reasons
        )
        record["lifecycle_state"] = _string(item.get("lifecycle_state"), reasons)
        record["state"] = _string(item.get("state"), reasons)
    elif candidate == "credential":
        record["app_url"] = _string(item.get("app_url"), reasons, required=True)
        record["consumer_org_url"] = _string(
            item.get("consumer_org_url"), reasons, required=True
        )
        record["client_id_present"] = "client_id" in item
        record["client_secret_present"] = "client_secret" in item
        record["hashed_secret_present"] = "client_secret_hashed" in item
    elif candidate == "subscription":
        record["app_url"] = _string(item.get("app_url"), reasons, required=True)
        record["consumer_org_url"] = _string(
            item.get("consumer_org_url"), reasons, required=True
        )
        record["product_url"] = _string(
            item.get("product_url"), reasons, required=True
        )
        record["plan"] = _string(item.get("plan"), reasons, required=True)
        record["state"] = _string(item.get("state"), reasons)
    elif candidate == "consumer_org":
        record["state"] = _string(item.get("state"), reasons)

    record["extraction_status"] = _status(reasons)
    record["failure_reasons"] = sorted(reasons, key=REASON_ORDER.__getitem__)
    records = [record]
    if candidate == "product":
        records.extend(
            _summary_plan_records(
                item.get("plans"),
                source_path=source_path,
                source_sha256=source_sha256,
                schema_family=schema_family,
                pointer=pointer,
                parent_id=record["extracted_record_id"],
            )
        )
        if item.get("plans") is not None and not isinstance(item.get("plans"), list):
            reasons.add(FIELD_TYPE_MISMATCH)
            record["extraction_status"] = _status(reasons)
            record["failure_reasons"] = sorted(reasons, key=REASON_ORDER.__getitem__)
    return records


def _resource_record(
    data: dict[str, Any],
    *,
    source_path: str,
    source_sha256: str,
    schema_family: str,
) -> list[dict[str, Any]]:
    observed_type = data.get("type")
    if observed_type == "consumer_org":
        record, reasons = _object_record(
            data,
            candidate="consumer_org",
            source_path=source_path,
            source_sha256=source_sha256,
            schema_family=schema_family,
            pointer="",
            required=("id", "url", "name"),
        )
        record["state"] = _string(data.get("state"), reasons)
    elif observed_type in {"catalog", "catalog_setting"}:
        record, reasons = _object_record(
            data,
            candidate="catalog_config",
            source_path=source_path,
            source_sha256=source_sha256,
            schema_family=schema_family,
            pointer="",
        )
    else:
        return [
            _unsupported_record(
                source_path=source_path,
                source_sha256=source_sha256,
                schema_family=schema_family,
                pointer="",
            )
        ]
    record["extraction_status"] = _status(reasons)
    record["failure_reasons"] = sorted(reasons, key=REASON_ORDER.__getitem__)
    return [record]


def _wsdl_record(
    path: Path,
    *,
    source_path: str,
    source_sha256: str,
    schema_family: str,
) -> dict[str, Any]:
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError):
        return _unsupported_record(
            source_path=source_path,
            source_sha256=source_sha256,
            schema_family=schema_family,
            pointer="",
            malformed=True,
        )
    reasons: set[str] = set()
    local_name = root.tag.rsplit("}", 1)[-1]
    if local_name != "definitions":
        reasons.add(UNSUPPORTED_OBJECT_SHAPE)
        return _base_record(
            candidate=None,
            source_path=source_path,
            source_sha256=source_sha256,
            schema_family=schema_family,
            pointer="",
            status=EXTRACTION_FAILED,
            reasons=reasons,
        )
    record = _base_record(
        candidate=None,
        source_path=source_path,
        source_sha256=source_sha256,
        schema_family=schema_family,
        pointer="",
    )
    record["definitions_name"] = _string(root.attrib.get("name"), reasons)
    record["target_namespace"] = _string(root.attrib.get("targetNamespace"), reasons)
    record["extraction_status"] = _status(reasons)
    record["failure_reasons"] = sorted(reasons, key=REASON_ORDER.__getitem__)
    return record


def _parse_structured(path: Path) -> tuple[Any, bool]:
    try:
        text = path.read_text(encoding="utf-8-sig")
        if path.suffix.lower() == ".json":
            return json.loads(text), True
        documents = list(yaml.safe_load_all(text))
        return (documents[0] if len(documents) == 1 else documents), True
    except (UnicodeDecodeError, OSError, json.JSONDecodeError, yaml.YAMLError):
        return None, False


def _extract_file(
    path: Path,
    *,
    source_root: Path,
    project_root: Path,
    phase_zero_families: dict[str, str],
) -> list[dict[str, Any]]:
    source_path = _source_path(source_root, path)
    source_sha256 = _sha256(path)
    suffix = path.suffix.lower()
    if suffix == ".wsdl":
        family = phase_zero_families.get(source_path, "OTHER")
        return [
            _wsdl_record(
                path,
                source_path=source_path,
                source_sha256=source_sha256,
                schema_family=family,
            )
        ]
    if suffix not in {".json", ".yaml", ".yml"}:
        return [
            _unsupported_record(
                source_path=source_path,
                source_sha256=source_sha256,
                schema_family=phase_zero_families.get(source_path, "OTHER"),
                pointer="",
            )
        ]

    data, parsed = _parse_structured(path)
    detected_family = _schema_family(data, path) if parsed else "UNDETERMINED"
    family = phase_zero_families.get(source_path, detected_family)
    if not parsed:
        return [
            _unsupported_record(
                source_path=source_path,
                source_sha256=source_sha256,
                schema_family=family,
                pointer="",
                malformed=True,
            )
        ]
    if isinstance(data, dict) and ("swagger" in data or "openapi" in data):
        return [
            _api_document_record(
                data,
                source_path=source_path,
                source_sha256=source_sha256,
                schema_family=family,
            )
        ]
    if isinstance(data, dict) and "product" in data:
        return _product_document_records(
            data,
            source_path=source_path,
            source_sha256=source_sha256,
            schema_family=family,
            project_root=project_root,
        )
    if isinstance(data, dict) and "api_version" in data and "type" in data:
        return _resource_record(
            data,
            source_path=source_path,
            source_sha256=source_sha256,
            schema_family=family,
        )

    source_category = path.relative_to(source_root).parts[0]
    if isinstance(data, dict) and "results" in data:
        results = data.get("results")
        if not isinstance(results, list):
            return [
                _base_record(
                    candidate=None,
                    source_path=source_path,
                    source_sha256=source_sha256,
                    schema_family=family,
                    pointer="",
                    status=EXTRACTION_FAILED,
                    reasons=(FIELD_TYPE_MISMATCH,),
                )
            ]
        records: list[dict[str, Any]] = []
        for index, item in enumerate(results):
            records.extend(
                _collection_item_records(
                    item,
                    source_path=source_path,
                    source_sha256=source_sha256,
                    schema_family=family,
                    pointer=f"/results/{index}",
                    source_category=source_category,
                )
            )
        return records
    if isinstance(data, list) and source_category == "config":
        records = []
        for index, item in enumerate(data):
            records.extend(
                _collection_item_records(
                    item,
                    source_path=source_path,
                    source_sha256=source_sha256,
                    schema_family=family,
                    pointer=f"/{index}",
                    source_category=source_category,
                )
            )
        return records
    return [
        _unsupported_record(
            source_path=source_path,
            source_sha256=source_sha256,
            schema_family=family,
            pointer="",
        )
    ]


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for record in records:
            output.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")


def _ensure_output_is_outside_source(source_root: Path, output_root: Path) -> None:
    source = source_root.resolve()
    output = output_root.resolve()
    if output == source or source in output.parents:
        raise ValueError("output root must not be inside the immutable source directory")


def extract_repository(
    source_root: Path,
    output_root: Path,
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Extract deterministic Phase 1 source-occurrence evidence."""
    source_root = Path(source_root)
    output_root = Path(output_root)
    project_root = Path(project_root) if project_root is not None else source_root.parent
    if not source_root.is_dir():
        raise ValueError(f"source directory does not exist: {source_root}")
    _ensure_output_is_outside_source(source_root, output_root)

    phase_zero_families = _load_phase_zero_families(output_root)
    paths = sorted(
        (path for path in source_root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(source_root).as_posix(),
    )
    records: list[dict[str, Any]] = []
    for path in paths:
        records.extend(
            _extract_file(
                path,
                source_root=source_root,
                project_root=project_root,
                phase_zero_families=phase_zero_families,
            )
        )
    records.sort(
        key=lambda item: (
            item["source_relative_path"],
            item["source_object_pointer"],
            item["canonical_object_type_candidate"] or "",
            item["extracted_record_id"],
        )
    )
    index_path = output_root / "indexes/extracted_records.jsonl"
    _write_jsonl(index_path, records)

    type_counts = Counter(
        record["canonical_object_type_candidate"] for record in records
    )
    status_counts = Counter(record["extraction_status"] for record in records)
    return {
        "index_path": index_path.relative_to(output_root).as_posix(),
        "total_occurrences": len(records),
        "occurrences_by_canonical_object_type_candidate": {
            (key if key is not None else "null"): type_counts[key]
            for key in sorted(type_counts, key=lambda value: value or "")
        },
        "occurrences_by_extraction_status": dict(sorted(status_counts.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("staging"))
    parser.add_argument("--output-root", type=Path, default=Path("."))
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    summary = extract_repository(
        args.source,
        args.output_root,
        project_root=args.project_root,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0
