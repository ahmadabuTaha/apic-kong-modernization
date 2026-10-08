"""Build a small deterministic semantic API/operation inventory sample."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml


API_SAMPLE_PATH = Path("indexes/semantic_api_inventory_sample.jsonl")
OPERATION_SAMPLE_PATH = Path("indexes/semantic_operation_inventory_sample.jsonl")
HTTP_METHODS = ("delete", "get", "head", "options", "patch", "post", "put", "trace")
URL_PATTERN = re.compile(r"https?://[^\s<>'\"]+", re.IGNORECASE)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(password|passwd|client[_-]?secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s,;]+"
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for value in values
        ),
        encoding="utf-8",
    )


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_id(prefix: str, *parts: object) -> str:
    payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{prefix}:sha256:{hashlib.sha256(payload.encode()).hexdigest()}"


def _escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _safe_text(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    result = URL_PATTERN.sub("[URL_REDACTED]", value.strip())
    result = SECRET_ASSIGNMENT_PATTERN.sub(lambda match: f"{match.group(1)}=[REDACTED]", result)
    return result


def _accepted_api_source(identity: dict[str, Any]) -> dict[str, Any] | None:
    candidates = sorted(
        (
            item
            for item in identity.get("source_evidence", [])
            if item.get("source_relative_path", "").startswith("staging/apis/")
            and item.get("source_relative_path", "").endswith((".yaml", ".yml"))
            and item.get("source_object_pointer", "") == ""
        ),
        key=lambda item: (
            item["source_relative_path"], item.get("extracted_record_id", "")
        ),
    )
    return candidates[0] if candidates else None


def _collect_refs(value: Any) -> list[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str):
                refs.add(child)
            else:
                refs.update(_collect_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_collect_refs(child))
    return sorted(refs)


def _parameter_summary(path_item: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any]:
    values = []
    for source_scope, parameters in (
        ("PATH_SHARED", path_item.get("parameters", [])),
        ("OPERATION", operation.get("parameters", [])),
    ):
        if not isinstance(parameters, list):
            continue
        for item in parameters:
            if isinstance(item, dict) and isinstance(item.get("$ref"), str):
                values.append(
                    {
                        "source_scope": source_scope,
                        "reference": item["$ref"],
                        "name": None,
                        "location": None,
                        "required": None,
                    }
                )
            elif isinstance(item, dict):
                values.append(
                    {
                        "source_scope": source_scope,
                        "reference": None,
                        "name": _safe_text(item.get("name")),
                        "location": item.get("in"),
                        "required": item.get("required")
                        if isinstance(item.get("required"), bool)
                        else None,
                    }
                )
    return {
        "parameter_count": len(values),
        "parameters": values,
        "schema_references": sorted(
            set(_collect_refs(path_item.get("parameters", [])))
            | set(_collect_refs(operation.get("parameters", [])))
        ),
    }


def _request_summary(operation: dict[str, Any]) -> dict[str, Any]:
    request_body = operation.get("requestBody")
    body_parameters = [
        item
        for item in operation.get("parameters", [])
        if isinstance(item, dict) and item.get("in") == "body"
    ] if isinstance(operation.get("parameters", []), list) else []
    content_types = sorted(
        request_body.get("content", {})
        if isinstance(request_body, dict)
        and isinstance(request_body.get("content"), dict)
        else []
    )
    refs = sorted(
        set(_collect_refs(request_body)) | set(_collect_refs(body_parameters))
    )
    return {
        "request_body_evidenced": isinstance(request_body, dict) or bool(body_parameters),
        "required": request_body.get("required")
        if isinstance(request_body, dict)
        and isinstance(request_body.get("required"), bool)
        else None,
        "content_types": content_types,
        "schema_references": refs,
    }


def _response_summary(operation: dict[str, Any]) -> dict[str, Any]:
    responses = operation.get("responses")
    if not isinstance(responses, dict):
        return {
            "response_status_codes": [],
            "content_types": [],
            "schema_references": [],
            "status": "MISSING_RESPONSES",
        }
    content_types: set[str] = set()
    for response in responses.values():
        if isinstance(response, dict) and isinstance(response.get("content"), dict):
            content_types.update(response["content"])
    return {
        "response_status_codes": sorted(str(value) for value in responses),
        "content_types": sorted(content_types),
        "schema_references": _collect_refs(responses),
        "status": "EXPLICIT_RESPONSES",
    }


def _document_format(document: dict[str, Any]) -> tuple[str, str]:
    if str(document.get("swagger", "")) == "2.0":
        return "SWAGGER_2", "SUPPORTED_PATH_OPERATIONS"
    if isinstance(document.get("openapi"), str) and document["openapi"].startswith("3."):
        return "OPENAPI_3", "SUPPORTED_PATH_OPERATIONS"
    return "UNSUPPORTED_OR_UNDECLARED", "UNSUPPORTED_DOCUMENT_FORMAT"


def _backend_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_observation_id": item["target_observation_id"],
        "scope_classification": item["scope_classification"],
        "operation_scope": item.get("operation_scope") or [],
        "target_classification": item["target_classification"],
        "resolution_status": item["resolution_status"],
        "resolution_reason": item["resolution_reason"],
        "symbolic_property_tokens": sorted(
            token
            for token in item.get("symbolic_property_tokens", [])
            if token not in item.get("runtime_parameter_tokens", [])
        ),
        "runtime_parameter_tokens": sorted(item.get("runtime_parameter_tokens", [])),
        "source_path": item["source_path"],
        "source_pointer": item["source_pointer"],
        "source_sha256": item["source_sha256"],
        "safe_target_path_or_template": item.get("target_path_suffix_or_template"),
        "raw_endpoint_host_omitted": True,
    }


def _relationship_connections(
    api_id: str, relationships: list[dict[str, Any]]
) -> dict[str, Any]:
    products = sorted(
        (
            {
                "product_canonical_id": item["source_canonical_identity_record_id"],
                "relationship_id": item["relationship_id"],
                "evidence_state": item["evidence_state"],
            }
            for item in relationships
            if item["relationship_type"] == "product_contains_api"
            and item["target_canonical_identity_record_id"] == api_id
        ),
        key=lambda item: item["relationship_id"],
    )
    plans = sorted(
        (
            {
                "plan_canonical_id": item["source_canonical_identity_record_id"],
                "relationship_id": item["relationship_id"],
                "evidence_state": item["evidence_state"],
            }
            for item in relationships
            if item["relationship_type"] == "plan_entitles_api"
            and item["target_canonical_identity_record_id"] == api_id
        ),
        key=lambda item: item["relationship_id"],
    )
    plan_ids = {item["plan_canonical_id"] for item in plans}
    plan_products = sorted(
        (
            {
                "product_canonical_id": item["source_canonical_identity_record_id"],
                "plan_canonical_id": item["target_canonical_identity_record_id"],
                "relationship_id": item["relationship_id"],
                "evidence_state": item["evidence_state"],
            }
            for item in relationships
            if item["relationship_type"] == "product_contains_plan"
            and item["target_canonical_identity_record_id"] in plan_ids
        ),
        key=lambda item: item["relationship_id"],
    )
    return {
        "product_contains_api": products,
        "plan_entitles_api": plans,
        "product_contains_plan_for_entitled_plans": plan_products,
        "connection_status": "EXPLICIT_ACCEPTED_RELATIONSHIPS"
        if products or plans
        else "NO_ACCEPTED_PRODUCT_PLAN_RELATIONSHIP_IN_INDEX",
    }


def extract_api_inventory(
    identity: dict[str, Any],
    document: dict[str, Any] | None,
    *,
    source_path: str | None,
    source_sha256: str | None,
    backend_observations: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    unresolved_product_occurrences: list[dict[str, Any]],
    sample_categories: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Extract factual API and operation records for one accepted identity."""

    api_id = identity["canonical_identity_record_id"]
    api_shared = [
        _backend_summary(item)
        for item in backend_observations
        if item["scope_classification"] == "API_SHARED"
    ]
    operation_scoped = [
        item
        for item in backend_observations
        if item["scope_classification"] == "OPERATION_SCOPED"
    ]
    if document is None:
        api_record = {
            "semantic_api_inventory_id": _stable_id("semantic-api-inventory", api_id),
            "record_layer": "EXTRACTED_FACT",
            "canonical_api_id": api_id,
            "sample_categories": sorted(sample_categories),
            "identity_name": identity.get("name"),
            "identity_title": identity.get("title"),
            "identity_version": identity.get("version"),
            "api_title": None,
            "api_description": None,
            "api_version": None,
            "protocol": None,
            "descriptive_tags": [],
            "document_format": None,
            "parser_coverage_status": "REGISTRY_ONLY_NO_ACCEPTED_API_YAML",
            "accepted_source": None,
            "source_representation_status": "REGISTRY_ONLY",
            "operation_record_ids": [],
            "operation_count": 0,
            "api_shared_backend_evidence": api_shared,
            "operation_scoped_backend_observation_refs": [
                item["target_observation_id"] for item in operation_scoped
            ],
            "as_is_product_plan_connections": _relationship_connections(
                api_id, relationships
            ),
            "unresolved_product_location_occurrences": unresolved_product_occurrences,
            "missing_fields": [
                {"field": field, "reason": "no_accepted_api_yaml_representation"}
                for field in (
                    "api_title",
                    "api_description",
                    "api_version",
                    "protocol",
                    "operations",
                )
            ],
            "evidence_confidence": "HIGH_FOR_ABSENCE_OF_ACCEPTED_YAML",
            "future_hypotheses": [],
            "architectural_judgments": [],
        }
        return api_record, []

    document_format, parser_status = _document_format(document)
    info = document.get("info") if isinstance(document.get("info"), dict) else {}
    x_ibm = (
        document.get("x-ibm-configuration")
        if isinstance(document.get("x-ibm-configuration"), dict)
        else {}
    )
    paths = document.get("paths") if isinstance(document.get("paths"), dict) else {}
    operations: list[dict[str, Any]] = []
    if parser_status == "SUPPORTED_PATH_OPERATIONS":
        for exact_path, path_item in sorted(paths.items(), key=lambda item: str(item[0])):
            if not isinstance(path_item, dict):
                continue
            for raw_method, operation in sorted(path_item.items(), key=lambda item: str(item[0])):
                method = str(raw_method).casefold()
                if method not in HTTP_METHODS or not isinstance(operation, dict):
                    continue
                pointer = f"/paths/{_escape(str(exact_path))}/{_escape(str(raw_method))}"
                operation_id = _stable_id(
                    "semantic-operation",
                    api_id,
                    source_path,
                    pointer,
                    method.upper(),
                    exact_path,
                )
                matching_backend = []
                for observation in operation_scoped:
                    for scope in observation.get("operation_scope") or []:
                        if (
                            str(scope.get("verb", "")).casefold() == method
                            and scope.get("path") == exact_path
                        ):
                            matching_backend.append(_backend_summary(observation))
                            break
                missing = []
                for field in ("operationId", "summary", "description"):
                    if _safe_text(operation.get(field)) is None:
                        missing.append(
                            {"field": field, "reason": "field_absent_or_blank_in_source"}
                        )
                operations.append(
                    {
                        "semantic_operation_inventory_id": operation_id,
                        "record_layer": "EXTRACTED_FACT",
                        "canonical_api_id": api_id,
                        "method": method.upper(),
                        "exact_path": exact_path,
                        "operation_selector": None,
                        "operation_id": _safe_text(operation.get("operationId")),
                        "summary": _safe_text(operation.get("summary")),
                        "description": _safe_text(operation.get("description")),
                        "tags": sorted(
                            {
                                value
                                for value in operation.get("tags", [])
                                if isinstance(value, str) and value.strip()
                            }
                        )
                        if isinstance(operation.get("tags"), list)
                        else [],
                        "parameter_summary": _parameter_summary(path_item, operation),
                        "request_summary": _request_summary(operation),
                        "response_summary": _response_summary(operation),
                        "operation_scoped_backend_evidence": sorted(
                            matching_backend,
                            key=lambda item: item["target_observation_id"],
                        ),
                        "api_shared_backend_context": {
                            "status": "API_LEVEL_ONLY_NOT_PROVEN_OPERATION_EGRESS"
                            if api_shared
                            else "NO_API_SHARED_BACKEND_OBSERVATION",
                            "target_observation_ids": [
                                item["target_observation_id"] for item in api_shared
                            ],
                        },
                        "source_provenance": {
                            "source_path": source_path,
                            "source_pointer": pointer,
                            "source_sha256": source_sha256,
                            "source_type": document_format,
                        },
                        "missing_fields": missing,
                        "evidence_confidence": "HIGH_EXPLICIT_SOURCE_STRUCTURE",
                        "future_hypotheses": [],
                        "architectural_judgments": [],
                    }
                )
    operation_ids = [item["semantic_operation_inventory_id"] for item in operations]
    api_missing = []
    for field, value in (
        ("api_title", _safe_text(info.get("title"))),
        ("api_description", _safe_text(info.get("description"))),
        ("api_version", _safe_text(info.get("version"))),
        ("protocol", _safe_text(x_ibm.get("type"))),
    ):
        if value is None:
            api_missing.append(
                {"field": field, "reason": "field_absent_or_blank_in_source"}
            )
    if not operations:
        api_missing.append(
            {
                "field": "operations",
                "reason": "no_supported_explicit_path_operations"
                if parser_status == "SUPPORTED_PATH_OPERATIONS"
                else "unsupported_document_format",
            }
        )
    source_occurrence_ids = sorted(
        item["extracted_record_id"]
        for item in identity.get("source_evidence", [])
        if item.get("source_relative_path") == source_path
    )
    api_record = {
        "semantic_api_inventory_id": _stable_id("semantic-api-inventory", api_id),
        "record_layer": "EXTRACTED_FACT",
        "canonical_api_id": api_id,
        "sample_categories": sorted(sample_categories),
        "identity_name": identity.get("name"),
        "identity_title": identity.get("title"),
        "identity_version": identity.get("version"),
        "api_title": _safe_text(info.get("title")),
        "api_description": _safe_text(info.get("description")),
        "api_version": _safe_text(info.get("version")),
        "protocol": _safe_text(x_ibm.get("type")),
        "descriptive_tags": sorted(
            {
                value
                for value in document.get("tags", [])
                if isinstance(value, str) and value.strip()
            }
        )
        if isinstance(document.get("tags"), list)
        else [],
        "document_format": document_format,
        "parser_coverage_status": parser_status,
        "accepted_source": {
            "source_path": source_path,
            "source_pointer": "",
            "source_sha256": source_sha256,
            "source_occurrence_ids": source_occurrence_ids,
            "authoritative_occurrence_ids": sorted(
                identity.get("authoritative_artifact_occurrence_ids", [])
            ),
            "contributing_occurrence_ids": sorted(
                identity.get("contributing_extracted_record_ids", [])
            ),
        },
        "source_representation_status": "ACCEPTED_AUTHORITATIVE_YAML",
        "operation_record_ids": operation_ids,
        "operation_count": len(operations),
        "api_shared_backend_evidence": sorted(
            api_shared, key=lambda item: item["target_observation_id"]
        ),
        "operation_scoped_backend_observation_refs": sorted(
            item["target_observation_id"] for item in operation_scoped
        ),
        "as_is_product_plan_connections": _relationship_connections(
            api_id, relationships
        ),
        "unresolved_product_location_occurrences": unresolved_product_occurrences,
        "missing_fields": api_missing,
        "evidence_confidence": "HIGH_EXPLICIT_SOURCE_STRUCTURE",
        "future_hypotheses": [],
        "architectural_judgments": [],
    }
    return api_record, operations


def _operation_count(root: Path, identity: dict[str, Any]) -> tuple[int, str | None]:
    source = _accepted_api_source(identity)
    if source is None:
        return 0, None
    path = root / source["source_relative_path"]
    document = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
    if not isinstance(document, dict):
        return 0, source["source_relative_path"]
    paths = document.get("paths") if isinstance(document.get("paths"), dict) else {}
    count = sum(
        1
        for item in paths.values()
        if isinstance(item, dict)
        for method, value in item.items()
        if str(method).casefold() in HTTP_METHODS and isinstance(value, dict)
    )
    return count, source["source_relative_path"]


def _select_sample(
    root: Path,
    identities: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    backend: list[dict[str, Any]],
    dependency_edges: list[dict[str, Any]],
    unresolved_rows: list[dict[str, Any]],
) -> tuple[dict[str, list[str]], list[str]]:
    api_by_id = {
        item["canonical_identity_record_id"]: item
        for item in identities
        if item["canonical_object_type"] == "api_artifact"
    }
    targeted_reads: list[str] = []
    operation_candidates = sorted(
        {
            item["canonical_api_id"]
            for item in backend
            if item["scope_classification"] == "OPERATION_SCOPED"
        }
    )
    operation_scoped = operation_candidates[0]
    multi_operation = None
    for api_id in operation_candidates:
        count, source = _operation_count(root, api_by_id[api_id])
        if source:
            targeted_reads.append(source)
        if count > 1:
            multi_operation = api_id
            break
    if multi_operation is None:
        raise ValueError("no deterministic multi-operation sample in operation-scoped candidates")

    api_shared_candidates = sorted(
        {
            item["canonical_api_id"]
            for item in backend
            if item["scope_classification"] == "API_SHARED"
            and item["canonical_api_id"] in api_by_id
            and _accepted_api_source(api_by_id[item["canonical_api_id"]]) is not None
        }
    )
    single_operation = None
    for api_id in api_shared_candidates:
        count, source = _operation_count(root, api_by_id[api_id])
        if source:
            targeted_reads.append(source)
        if count == 1:
            single_operation = api_id
            break
    if single_operation is None:
        raise ValueError("no deterministic single-operation API sample")

    product_apis = {
        item["target_canonical_identity_record_id"]
        for item in relationships
        if item["relationship_type"] == "product_contains_api"
    }
    plan_apis = {
        item["target_canonical_identity_record_id"]
        for item in relationships
        if item["relationship_type"] == "plan_entitles_api"
    }
    product_plan = min(product_apis & plan_apis)
    registry_only = min(
        api_id
        for api_id, identity in api_by_id.items()
        if _accepted_api_source(identity) is None
    )
    edge_counts = Counter(
        item["source_canonical_identity_record_id"] for item in dependency_edges
    )
    multiple_targets = min(api_id for api_id, count in edge_counts.items() if count > 1)
    unresolved_candidates = sorted(
        {
            api_id
            for item in unresolved_rows
            for api_id in item.get("candidate_canonical_identity_record_ids", [])
            if api_id in api_by_id
        }
    )
    unresolved_product = unresolved_candidates[0]
    api_shared = api_shared_candidates[0]
    categories = {
        "explicit_multi_operation_rest_api": [multi_operation],
        "single_operation_api": [single_operation],
        "missing_or_unresolved_operation_metadata": [registry_only],
        "api_shared_backend_scope": [api_shared],
        "operation_scoped_backend_evidence": [operation_scoped],
        "as_is_product_and_plan_relationship": [product_plan],
        "registry_only_canonical_api": [registry_only],
        "multiple_backend_targets": [multiple_targets],
        "unresolved_product_location_occurrence": [unresolved_product],
    }
    return categories, sorted(set(targeted_reads))


def build_representative_sample(root: Path) -> dict[str, Any]:
    phase2 = json.loads((root / "indexes/apic_identity_resolution.json").read_text())
    identities = phase2["canonical_identity_records"]
    relationships = _load_jsonl(root / "indexes/relationship_index.jsonl")
    backend = _load_jsonl(root / "indexes/backend_target_resolution.jsonl")
    dependency_edges = _load_jsonl(root / "indexes/codegraph_dependency_edges.jsonl")
    unresolved_rows = _load_jsonl(
        root / "tests/evidence/task-007/unresolved_product_location_apis.jsonl"
    )
    categories, selection_reads = _select_sample(
        root, identities, relationships, backend, dependency_edges, unresolved_rows
    )
    selected_ids = sorted(
        {api_id for values in categories.values() for api_id in values}
    )
    categories_by_api: dict[str, list[str]] = defaultdict(list)
    for category, api_ids in categories.items():
        for api_id in api_ids:
            categories_by_api[api_id].append(category)
    api_by_id = {
        item["canonical_identity_record_id"]: item for item in identities
    }
    backend_by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in backend:
        backend_by_api[item["canonical_api_id"]].append(item)
    unresolved_by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in unresolved_rows:
        for api_id in item.get("candidate_canonical_identity_record_ids", []):
            unresolved_by_api[api_id].append(
                {
                    "extracted_record_id": item["extracted_record_id"],
                    "source_relative_path": item["source_relative_path"],
                    "source_object_pointer": item["source_object_pointer"],
                    "task_006_resolution_outcome": item[
                        "task_006_resolution_outcome"
                    ],
                    "attachment_status": "PRESERVED_UNRESOLVED_NOT_ATTACHED",
                    "candidate_link_is_diagnostic_only": True,
                }
            )

    api_records: list[dict[str, Any]] = []
    operation_records: list[dict[str, Any]] = []
    parsed_sources: list[str] = []
    for api_id in selected_ids:
        identity = api_by_id[api_id]
        source = _accepted_api_source(identity)
        document = None
        source_path = None
        source_sha = None
        if source is not None:
            source_path = source["source_relative_path"]
            absolute = root / source_path
            source_sha = _hash_file(absolute)
            loaded = yaml.load(absolute.read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
            document = loaded if isinstance(loaded, dict) else {}
            parsed_sources.append(source_path)
        api_record, operations = extract_api_inventory(
            identity,
            document,
            source_path=source_path,
            source_sha256=source_sha,
            backend_observations=backend_by_api[api_id],
            relationships=relationships,
            unresolved_product_occurrences=sorted(
                unresolved_by_api[api_id], key=lambda item: item["extracted_record_id"]
            ),
            sample_categories=categories_by_api[api_id],
        )
        api_records.append(api_record)
        operation_records.extend(operations)
    api_records.sort(key=lambda item: item["canonical_api_id"])
    operation_records.sort(
        key=lambda item: item["semantic_operation_inventory_id"]
    )
    if len({item["semantic_operation_inventory_id"] for item in operation_records}) != len(operation_records):
        raise ValueError("duplicate semantic operation inventory ID")
    return {
        "api_records": api_records,
        "operation_records": operation_records,
        "selection": {
            "selection_algorithm_version": "task-014-representative-selection-v1",
            "selection_basis": "lowest stable canonical API ID satisfying each compact-index-derived criterion",
            "categories": categories,
            "selected_canonical_api_ids": selected_ids,
            "selected_api_count": len(selected_ids),
            "targeted_sources_read_for_selection": selection_reads,
            "targeted_sources_parsed_for_inventory": sorted(set(parsed_sources)),
            "estate_wide_source_scan_performed": False,
        },
        "coverage": {
            "sample_api_count": len(api_records),
            "sample_operation_count": len(operation_records),
            "registry_only_sample_count": sum(
                item["source_representation_status"] == "REGISTRY_ONLY"
                for item in api_records
            ),
            "source_backed_sample_count": sum(
                item["source_representation_status"]
                == "ACCEPTED_AUTHORITATIVE_YAML"
                for item in api_records
            ),
            "apis_with_api_shared_backend_evidence": sum(
                bool(item["api_shared_backend_evidence"]) for item in api_records
            ),
            "apis_with_operation_scoped_backend_evidence": sum(
                bool(item["operation_scoped_backend_observation_refs"])
                for item in api_records
            ),
            "operations_with_operation_scoped_backend_evidence": sum(
                bool(item["operation_scoped_backend_evidence"])
                for item in operation_records
            ),
            "operations_with_missing_description": sum(
                item["description"] is None for item in operation_records
            ),
            "sampled_unresolved_product_location_occurrences": sum(
                len(item["unresolved_product_location_occurrences"])
                for item in api_records
            ),
            "estate_unresolved_product_location_occurrences_preserved": 113,
            "unresolved_product_location_occurrences_attached_as_relationships": 0,
            "parser_format_counts": dict(
                sorted(Counter(item["document_format"] or "NO_DOCUMENT" for item in api_records).items())
            ),
            "parser_coverage_status_counts": dict(
                sorted(Counter(item["parser_coverage_status"] for item in api_records).items())
            ),
            "operation_record_ids_unique": True,
            "semantic_function_inference_performed": False,
            "logical_api_formation_performed": False,
            "domain_or_capability_tagging_performed": False,
        },
    }


def write_representative_sample(
    root: Path,
    *,
    api_path: Path | None = None,
    operation_path: Path | None = None,
) -> dict[str, Any]:
    result = build_representative_sample(root)
    api_path = api_path or root / API_SAMPLE_PATH
    operation_path = operation_path or root / OPERATION_SAMPLE_PATH
    _write_jsonl(api_path, result["api_records"])
    _write_jsonl(operation_path, result["operation_records"])
    result["outputs"] = {
        "api": {
            "path": str(api_path),
            "sha256": _hash_file(api_path),
            "record_count": len(result["api_records"]),
        },
        "operation": {
            "path": str(operation_path),
            "sha256": _hash_file(operation_path),
            "record_count": len(result["operation_records"]),
        },
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    result = write_representative_sample(args.root.resolve())
    printable = {
        "selection": result["selection"],
        "coverage": result["coverage"],
        "outputs": result["outputs"],
    }
    print(json.dumps(printable, ensure_ascii=False, indent=2, sort_keys=True))
    return 0
