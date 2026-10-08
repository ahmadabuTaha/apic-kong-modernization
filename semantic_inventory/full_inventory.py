"""Task 014 Gate B full semantic inventory with deterministic incremental cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml

from semantic_preflight.preflight import _policy_shapes

from .inventory import (
    HTTP_METHODS,
    _backend_summary,
    _collect_refs,
    _document_format,
    _escape,
    _hash_file,
    _load_jsonl,
    _relationship_connections,
    _safe_text,
    _stable_id,
    extract_api_inventory,
)


EXTRACTOR_VERSION = "task014-full-inventory-v3"
CACHE_SCHEMA_VERSION = 1
API_OUTPUT = Path("indexes/semantic_api_inventory.jsonl")
OPERATION_OUTPUT = Path("indexes/semantic_operation_inventory.jsonl")
CANDIDATE_OUTPUT = Path("indexes/semantic_structural_overlap_candidates.jsonl")
MANIFEST_OUTPUT = Path("indexes/semantic_cache_manifest.json")
CACHE_DIRECTORY = Path("indexes/cache/task014-semantic-v2")


def _json_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, path)


def _write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text("".join(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for value in values), encoding="utf-8")
    os.replace(temporary, path)


def cache_decision(
    cached: dict[str, Any] | None,
    *,
    source_fingerprint: str,
    dependency_fingerprint: str,
    extractor_version: str = EXTRACTOR_VERSION,
) -> str:
    if cached is None:
        return "MISS"
    if cached.get("cache_schema_version") != CACHE_SCHEMA_VERSION or cached.get("extractor_version") != extractor_version:
        return "INVALIDATED_EXTRACTOR_CHANGE"
    if cached.get("source_fingerprint") != source_fingerprint:
        return "INVALIDATED_SOURCE_CHANGE"
    if cached.get("dependency_fingerprint") != dependency_fingerprint:
        return "INVALIDATED_DEPENDENCY_CHANGE"
    if not isinstance(cached.get("api_record"), dict) or not isinstance(cached.get("operation_records"), list):
        return "INVALIDATED_PARTIAL_CACHE"
    return "HIT"


def _schema_shape(schema: Any, document: dict[str, Any], seen: frozenset[str] = frozenset()) -> Any:
    if not isinstance(schema, dict):
        return None
    reference = schema.get("$ref")
    if isinstance(reference, str) and reference.startswith("#/"):
        if reference in seen:
            return {"cycle_ref": reference}
        target: Any = document
        try:
            for token in reference[2:].split("/"):
                target = target[token.replace("~1", "/").replace("~0", "~")]
        except (KeyError, TypeError):
            return {"unresolved_local_ref": reference}
        return {"local_ref": reference, "resolved": _schema_shape(target, document, seen | {reference})}
    result: dict[str, Any] = {}
    for key in ("type", "format", "nullable", "required", "enum", "allOf", "oneOf", "anyOf", "items", "additionalProperties"):
        if key in schema:
            value = schema[key]
            if key in {"allOf", "oneOf", "anyOf"} and isinstance(value, list):
                result[key] = [_schema_shape(item, document, seen) for item in value]
            elif key in {"items", "additionalProperties"} and isinstance(value, dict):
                result[key] = _schema_shape(value, document, seen)
            elif key == "enum" and isinstance(value, list):
                result[key] = {"value_count": len(value), "types": sorted({type(item).__name__ for item in value})}
            else:
                result[key] = value
    properties = schema.get("properties")
    if isinstance(properties, dict):
        result["properties"] = {name: _schema_shape(value, document, seen) for name, value in sorted(properties.items())}
    return result


def _schema_signature(schema: Any, document: dict[str, Any]) -> str | None:
    shape = _schema_shape(schema, document)
    return _json_hash(shape) if shape is not None else None


def _content_contract(content: Any, document: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(content, dict):
        return []
    return [
        {
            "content_type": content_type,
            "schema_refs": _collect_refs(media),
            "schema_shape_sha256": _schema_signature(media.get("schema"), document) if isinstance(media, dict) else None,
        }
        for content_type, media in sorted(content.items())
    ]


def operation_contract(document: dict[str, Any], path: str, method: str) -> dict[str, Any]:
    path_item = (document.get("paths") or {}).get(path, {})
    operation = path_item.get(method.lower(), {}) if isinstance(path_item, dict) else {}
    parameters: list[dict[str, Any]] = []
    body_contracts: list[dict[str, Any]] = []
    for scope, values in (("PATH_SHARED", path_item.get("parameters", [])), ("OPERATION", operation.get("parameters", []))):
        if not isinstance(values, list):
            continue
        for item in values:
            if not isinstance(item, dict):
                continue
            schema = item.get("schema")
            parameters.append({
                "scope": scope,
                "name": item.get("name") if isinstance(item.get("name"), str) else None,
                "location": item.get("in") if isinstance(item.get("in"), str) else None,
                "required": item.get("required") if isinstance(item.get("required"), bool) else None,
                "type": item.get("type") if isinstance(item.get("type"), str) else schema.get("type") if isinstance(schema, dict) and isinstance(schema.get("type"), str) else None,
                "schema_refs": _collect_refs(schema),
                "schema_shape_sha256": _schema_signature(schema, document),
            })
            if item.get("in") == "body":
                body_contracts.extend(
                    {
                        "content_type": value,
                        "schema_refs": _collect_refs(schema),
                        "schema_shape_sha256": _schema_signature(schema, document),
                    }
                    for value in (
                        operation.get("consumes")
                        or document.get("consumes")
                        or ["UNDECLARED"]
                    )
                )
    request_body = operation.get("requestBody")
    if isinstance(request_body, dict):
        body_contracts.extend(_content_contract(request_body.get("content"), document))
    responses = operation.get("responses") if isinstance(operation.get("responses"), dict) else {}
    response_contracts = []
    for status, response in sorted(responses.items(), key=lambda item: str(item[0])):
        if not isinstance(response, dict):
            response_contracts.append({"status": str(status), "content": [], "schema_refs": [], "schema_shape_sha256": None})
            continue
        content = _content_contract(response.get("content"), document)
        swagger_schema = response.get("schema")
        if not content and isinstance(swagger_schema, dict):
            content = [{"content_type": value, "schema_refs": _collect_refs(swagger_schema), "schema_shape_sha256": _schema_signature(swagger_schema, document)} for value in (operation.get("produces") or document.get("produces") or ["UNDECLARED"])]
        response_contracts.append({"status": str(status), "content": content, "schema_refs": _collect_refs(response), "schema_shape_sha256": _schema_signature(swagger_schema, document)})
    security = operation.get("security", document.get("security"))
    security_schemes = document.get("securityDefinitions") or (document.get("components") or {}).get("securitySchemes") or {}
    return {
        "method": method.upper(),
        "exact_path": path,
        "normalized_path_shape": re.sub(r"\{[^}]+\}", "{parameter}", path),
        "parameters": parameters,
        "request": {"body_present": bool(body_contracts), "content": body_contracts},
        "responses": response_contracts,
        "auth": {
            "security_requirement_present": security is not None,
            "security_scheme_types": sorted({value.get("type") for value in security_schemes.values() if isinstance(value, dict) and isinstance(value.get("type"), str)}),
        },
        "exposure": {
            "schemes": sorted(value for value in document.get("schemes", []) if isinstance(value, str)),
            "base_path_present": isinstance(document.get("basePath"), str),
            "servers_present": isinstance(document.get("servers"), list) and bool(document.get("servers")),
        },
    }


def _root_representations(identity: dict[str, Any], extracted: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    values = []
    for evidence in identity.get("source_evidence", []):
        path = evidence.get("source_relative_path", "")
        if evidence.get("source_object_pointer") != "" or not path.endswith((".yaml", ".yml")):
            continue
        record = extracted.get(evidence.get("extracted_record_id"), {})
        values.append({
            "occurrence_id": evidence.get("extracted_record_id"),
            "source_path": path,
            "source_sha256": record.get("source_sha256"),
            "source_role": "AUTHORITATIVE_API_ARTIFACT" if evidence.get("extracted_record_id") in identity.get("authoritative_artifact_occurrence_ids", []) else "PRODUCT_LOCATION_REPRESENTATION",
        })
    return sorted(values, key=lambda value: (value["source_path"], value["occurrence_id"]))


def _structural_fingerprint(document: dict[str, Any]) -> str:
    operations = []
    for path, item in sorted((document.get("paths") or {}).items()):
        if not isinstance(item, dict):
            continue
        for method in sorted(item):
            if method.lower() in HTTP_METHODS and isinstance(item[method], dict):
                operations.append(operation_contract(document, path, method))
    return _json_hash({"format": _document_format(document)[0], "operations": operations, "assembly_policy_shapes": _policy_shapes(document.get("x-ibm-configuration", {}), "/x-ibm-configuration")})


def _source_fingerprint(representations: list[dict[str, Any]]) -> str:
    return _json_hash([{"occurrence_id": value["occurrence_id"], "source_path": value["source_path"], "source_sha256": value["source_sha256"], "source_role": value["source_role"]} for value in representations])


def _dependency_fingerprint(backend: list[dict[str, Any]], relationships: list[dict[str, Any]], unresolved: list[dict[str, Any]]) -> str:
    return _json_hash({"backend": backend, "relationships": relationships, "unresolved": unresolved})


def _enrich_backend(api: dict[str, Any], operations: list[dict[str, Any]]) -> None:
    shared = api.pop("api_shared_backend_evidence", [])
    api["configured_backend_facts"] = [
        {**value, "fact_taxonomy": "CONFIGURED_API_SHARED", "runtime_usage_proven": False}
        for value in shared
    ]
    api["operation_scoped_backend_facts"] = [
        {"target_observation_id": value, "fact_taxonomy": "EVIDENCED_OPERATION_SCOPED", "runtime_usage_proven": False}
        for value in api.pop("operation_scoped_backend_observation_refs", [])
    ]
    api["routing_state"] = "UNRESOLVED_ROUTING" if not api["configured_backend_facts"] and not api["operation_scoped_backend_facts"] else "CONFIGURATION_EVIDENCE_PRESENT"
    for operation in operations:
        scoped = operation.pop("operation_scoped_backend_evidence", [])
        operation["configured_backend_facts"] = [{**value, "fact_taxonomy": "EVIDENCED_OPERATION_SCOPED", "runtime_usage_proven": False} for value in scoped]
        old_context = operation.pop("api_shared_backend_context")
        operation["candidate_inherited_backend_context"] = [
            {
                "target_observation_id": value["target_observation_id"],
                "candidate_taxonomy": "CANDIDATE_INHERITED_CONTEXT",
                "certainty": "CANDIDATE_ONLY",
                "source_path": value["source_path"],
                "source_pointer": value["source_pointer"],
                "configuration_scope": value["scope_classification"],
                "resolution_status": value["resolution_status"],
                "safe_target_path_or_template": value.get("safe_target_path_or_template"),
                "policy_context": "CONDITIONAL_BRANCH" if "/switch/" in value["source_pointer"] else "ASSEMBLY_SEQUENCE",
                "operation_anchor": {"method": operation["method"], "path": operation["exact_path"]},
                "proven_operation_egress": False,
                "runtime_usage_proven": False,
            }
            for value in shared
        ]
        operation["legacy_api_shared_context_status"] = old_context["status"]


def _build_payload(
    root: Path,
    identity: dict[str, Any],
    representations: list[dict[str, Any]],
    backend: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    unresolved: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    if not representations:
        api, operations = extract_api_inventory(identity, None, source_path=None, source_sha256=None, backend_observations=backend, relationships=relationships, unresolved_product_occurrences=unresolved, sample_categories=[])
        _enrich_backend(api, operations)
        api["source_variants"] = []
        api["source_variant_classification"] = "REGISTRY_ONLY"
        return api, operations, "REGISTRY_ONLY"
    unique_by_sha: dict[str, dict[str, Any]] = {}
    for value in representations:
        unique_by_sha.setdefault(value["source_sha256"], value)
    parsed: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    for sha, representation in sorted(unique_by_sha.items()):
        document = yaml.load((root / representation["source_path"]).read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
        document = document if isinstance(document, dict) else {}
        parsed.append((representation, document, _structural_fingerprint(document)))
    fingerprints = sorted({value[2] for value in parsed})
    if len(unique_by_sha) == 1:
        classification = "BYTE_IDENTICAL_REPRESENTATIONS" if len(representations) > 1 else "SINGLE_REPRESENTATION"
    elif len(fingerprints) == 1:
        classification = "SEMANTICALLY_EQUIVALENT_STRUCTURAL_VARIANTS"
    else:
        classification = "CONFLICT_REQUIRES_ARCHITECTURE_REVIEW"
    authoritative_paths = {value["source_path"] for value in representations if value["source_role"] == "AUTHORITATIVE_API_ARTIFACT"}
    primary = next((value for value in parsed if value[0]["source_path"] in authoritative_paths), parsed[0])
    selected = [primary] if classification != "CONFLICT_REQUIRES_ARCHITECTURE_REVIEW" else [next(value for value in parsed if value[2] == fingerprint) for fingerprint in fingerprints]
    all_operations: list[dict[str, Any]] = []
    api: dict[str, Any] | None = None
    for representation, document, fingerprint in selected:
        current_api, operations = extract_api_inventory(identity, document, source_path=representation["source_path"], source_sha256=representation["source_sha256"], backend_observations=backend, relationships=relationships, unresolved_product_occurrences=unresolved, sample_categories=[])
        for operation in operations:
            legacy = operation["semantic_operation_inventory_id"]
            operation["legacy_semantic_operation_inventory_id_v1"] = legacy
            operation["source_variant_fingerprint"] = fingerprint
            operation["semantic_operation_inventory_id"] = _stable_id("semantic-operation-v2", identity["canonical_identity_record_id"], fingerprint, operation["method"], operation["exact_path"])
            operation["contract"] = operation_contract(document, operation["exact_path"], operation["method"])
            operation["source_variant_provenance"] = [value for value in representations if any(item[2] == fingerprint and item[0]["source_sha256"] == value["source_sha256"] for item in parsed)]
        _enrich_backend(current_api, operations)
        api = api or current_api
        all_operations.extend(operations)
    assert api is not None
    api["operation_record_ids"] = sorted(value["semantic_operation_inventory_id"] for value in all_operations)
    api["operation_count"] = len(all_operations)
    api["source_variants"] = [
        {**value, "structural_fingerprint_sha256": next(item[2] for item in parsed if item[0]["source_sha256"] == value["source_sha256"])}
        for value in representations
    ]
    api["source_variant_classification"] = classification
    api["semantic_payload_count"] = len(selected)
    status = "UNSUPPORTED_FORMAT" if api["parser_coverage_status"] == "UNSUPPORTED_DOCUMENT_FORMAT" else "EXTRACTED"
    return api, all_operations, status


def _safe_unresolved(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "extracted_record_id": item["extracted_record_id"],
        "source_relative_path": item["source_relative_path"],
        "source_object_pointer": item["source_object_pointer"],
        "task_006_resolution_outcome": item["task_006_resolution_outcome"],
        "attachment_status": "PRESERVED_UNRESOLVED_NOT_ATTACHED",
        "candidate_link_is_diagnostic_only": True,
    }


def _candidate_records(
    operations: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    api_names: dict[str, str | None],
    limit: int = 100,
) -> list[dict[str, Any]]:
    by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        by_api[operation["canonical_api_id"]].append(operation)
    target_apis: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        target_apis[edge["target_canonical_identity_record_id"]].add(edge["source_canonical_identity_record_id"])
    scored = []
    seen: set[tuple[str, str]] = set()
    for target, api_ids in sorted(target_apis.items()):
        values = sorted(api_id for api_id in api_ids if api_id in by_api)
        for index, left in enumerate(values):
            for right in values[index + 1:]:
                if api_names.get(left) == api_names.get(right):
                    continue
                pair = (left, right)
                if pair in seen:
                    continue
                seen.add(pair)
                left_ops, right_ops = by_api[left], by_api[right]
                left_shapes = {(value["method"], value["contract"]["normalized_path_shape"]) for value in left_ops}
                right_shapes = {(value["method"], value["contract"]["normalized_path_shape"]) for value in right_ops}
                shape_match = left_shapes & right_shapes
                left_req = {item["schema_shape_sha256"] for value in left_ops for item in value["contract"]["request"]["content"] if item["schema_shape_sha256"]}
                right_req = {item["schema_shape_sha256"] for value in right_ops for item in value["contract"]["request"]["content"] if item["schema_shape_sha256"]}
                left_resp = {item["schema_shape_sha256"] for value in left_ops for response in value["contract"]["responses"] for item in response["content"] if item["schema_shape_sha256"]}
                right_resp = {item["schema_shape_sha256"] for value in right_ops for response in value["contract"]["responses"] for item in response["content"] if item["schema_shape_sha256"]}
                signals = int(bool(shape_match)) + int(bool(left_req & right_req)) + int(bool(left_resp & right_resp)) + 1
                if signals < 2 or not shape_match:
                    continue
                score = (signals, len(shape_match), -abs(len(left_ops) - len(right_ops)), left, right)
                scored.append((score, {
                    "candidate_id": _stable_id("structural-overlap-candidate", left, right),
                    "left_canonical_api_id": left,
                    "right_canonical_api_id": right,
                    "left_api_name": api_names.get(left),
                    "right_api_name": api_names.get(right),
                    "status": "POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION",
                    "blocking_basis": "SHARED_BACKEND_TARGET_PLUS_OPERATION_CONTRACT_SIGNALS",
                    "shared_backend_target_ids": [target],
                    "matching_method_path_shapes": [{"method": method, "path_shape": path} for method, path in sorted(shape_match)],
                    "matching_request_schema_shape_sha256": sorted(left_req & right_req),
                    "matching_response_schema_shape_sha256": sorted(left_resp & right_resp),
                    "differing_method_path_shapes": {
                        "left_only": [{"method": method, "path_shape": path} for method, path in sorted(left_shapes - right_shapes)],
                        "right_only": [{"method": method, "path_shape": path} for method, path in sorted(right_shapes - left_shapes)],
                    },
                    "differing_request_schema_shape_sha256": {
                        "left_only": sorted(left_req - right_req),
                        "right_only": sorted(right_req - left_req),
                    },
                    "differing_response_schema_shape_sha256": {
                        "left_only": sorted(left_resp - right_resp),
                        "right_only": sorted(right_resp - left_resp),
                    },
                    "source_provenance": {
                        "left": left_ops[0]["source_provenance"],
                        "right": right_ops[0]["source_provenance"],
                    },
                    "runtime_or_functional_duplication_proven": False,
                    "limitations": [
                        "Shared backend does not prove common operation egress.",
                        "Structural overlap does not prove functional duplication.",
                    ],
                }))
    required_pair = {
        "apic-identity:sha256:3165d30141993d77200c2630b10c29760e0e1c8f6520eb3368a12d6dd484657e",
        "apic-identity:sha256:6fa70f88ad990dcda279d38753d1e83806dc591c09b74619e945129c553f2aeb",
    }
    ordered = sorted(scored, key=lambda item: item[0], reverse=True)
    required = next((value for _, value in ordered if {value["left_canonical_api_id"], value["right_canonical_api_id"]} == required_pair), None)
    selected = [value for _, value in ordered[:limit]]
    if required is not None and required not in selected:
        selected[-1:] = [required]
    return sorted(selected, key=lambda value: value["candidate_id"])


def build_full_inventory(
    root: Path,
    *,
    api_path: Path | None = None,
    operation_path: Path | None = None,
    candidate_path: Path | None = None,
    manifest_path: Path | None = None,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    api_path = api_path or root / API_OUTPUT
    operation_path = operation_path or root / OPERATION_OUTPUT
    candidate_path = candidate_path or root / CANDIDATE_OUTPUT
    manifest_path = manifest_path or root / MANIFEST_OUTPUT
    cache_dir = cache_dir or root / CACHE_DIRECTORY
    phase2 = json.loads((root / "indexes/apic_identity_resolution.json").read_text(encoding="utf-8"))
    identities = sorted((value for value in phase2["canonical_identity_records"] if value["canonical_object_type"] == "api_artifact"), key=lambda value: value["canonical_identity_record_id"])
    extracted = {value["extracted_record_id"]: value for value in _load_jsonl(root / "indexes/extracted_records.jsonl")}
    backend_by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for value in _load_jsonl(root / "indexes/backend_target_resolution.jsonl"):
        backend_by_api[value["canonical_api_id"]].append(value)
    relationships = _load_jsonl(root / "indexes/relationship_index.jsonl")
    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    product_plan_by_plan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for value in relationships:
        if value["relationship_type"] in {"product_contains_api", "plan_entitles_api"}:
            incoming[value["target_canonical_identity_record_id"]].append(value)
        elif value["relationship_type"] == "product_contains_plan":
            product_plan_by_plan[value["target_canonical_identity_record_id"]].append(value)
    unresolved_rows = _load_jsonl(root / "tests/evidence/task-007/unresolved_product_location_apis.jsonl")
    unresolved_by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for value in unresolved_rows:
        safe = _safe_unresolved(value)
        for candidate in value.get("candidate_canonical_identity_record_ids", []):
            unresolved_by_api[candidate].append(safe)
    api_records: list[dict[str, Any]] = []
    operation_records: list[dict[str, Any]] = []
    events = Counter()
    for identity in identities:
        api_id = identity["canonical_identity_record_id"]
        representations = _root_representations(identity, extracted)
        relevant_relationships = list(incoming[api_id])
        for relation in incoming[api_id]:
            if relation["relationship_type"] == "plan_entitles_api":
                relevant_relationships.extend(product_plan_by_plan[relation["source_canonical_identity_record_id"]])
        relevant_relationships.sort(key=lambda value: value["relationship_id"])
        backend = sorted(backend_by_api[api_id], key=lambda value: value["target_observation_id"])
        unresolved = sorted(unresolved_by_api[api_id], key=lambda value: value["extracted_record_id"])
        source_fp = _source_fingerprint(representations)
        dependency_fp = _dependency_fingerprint(backend, relevant_relationships, unresolved)
        cache_path = cache_dir / f"{api_id.rsplit(':', 1)[-1]}.json"
        cached = None
        if cache_path.is_file():
            try:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                cached = {}
        event = cache_decision(cached, source_fingerprint=source_fp, dependency_fingerprint=dependency_fp)
        if event == "HIT":
            api, operations = cached["api_record"], cached["operation_records"]
            payload_status = cached.get("payload_status", "EXTRACTED")
        else:
            api, operations, payload_status = _build_payload(root, identity, representations, backend, relevant_relationships, unresolved)
            _atomic_json(cache_path, {
                "cache_schema_version": CACHE_SCHEMA_VERSION,
                "extractor_version": EXTRACTOR_VERSION,
                "source_fingerprint": source_fp,
                "dependency_fingerprint": dependency_fp,
                "payload_status": payload_status,
                "api_record": api,
                "operation_records": operations,
            })
        if payload_status in {"REGISTRY_ONLY", "UNSUPPORTED_FORMAT"}:
            events[payload_status] += 1
        else:
            events[event] += 1
        api_records.append(api)
        operation_records.extend(operations)
    api_records.sort(key=lambda value: value["canonical_api_id"])
    operation_records.sort(key=lambda value: value["semantic_operation_inventory_id"])
    operation_ids = [value["semantic_operation_inventory_id"] for value in operation_records]
    if len(operation_ids) != len(set(operation_ids)):
        raise ValueError("duplicate semantic operation inventory IDs")
    candidates = _candidate_records(
        operation_records,
        _load_jsonl(root / "indexes/codegraph_dependency_edges.jsonl"),
        {value["canonical_api_id"]: value.get("identity_name") for value in api_records},
    )
    _write_jsonl(api_path, api_records)
    _write_jsonl(operation_path, operation_records)
    _write_jsonl(candidate_path, candidates)
    coverage = {
        "accepted_canonical_api_count": len(identities),
        "api_inventory_record_count": len(api_records),
        "source_backed_api_count": sum(bool(value["source_variants"]) for value in api_records),
        "registry_only_api_count": sum(value["source_variant_classification"] == "REGISTRY_ONLY" for value in api_records),
        "operation_inventory_record_count": len(operation_records),
        "unique_operation_id_count": len(set(operation_ids)),
        "document_format_counts": dict(sorted(Counter(value.get("document_format") or "NO_DOCUMENT" for value in api_records).items())),
        "protocol_counts": dict(sorted(Counter(value.get("protocol") or "NO_PROTOCOL_OR_REGISTRY_ONLY" for value in api_records).items())),
        "parser_coverage_status_counts": dict(sorted(Counter(value["parser_coverage_status"] for value in api_records).items())),
        "source_variant_classification_counts": dict(sorted(Counter(value["source_variant_classification"] for value in api_records).items())),
        "unresolved_product_location_occurrence_count": len(unresolved_rows),
        "unresolved_attached_as_relationship_count": 0,
        "structural_overlap_candidate_count": len(candidates),
    }
    def display_path(path: Path) -> str:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            return path.name

    outputs = {
        "api_inventory": {"path": display_path(api_path), "sha256": _hash_file(api_path), "record_count": len(api_records)},
        "operation_inventory": {"path": display_path(operation_path), "sha256": _hash_file(operation_path), "record_count": len(operation_records)},
        "structural_overlap_candidates": {"path": display_path(candidate_path), "sha256": _hash_file(candidate_path), "record_count": len(candidates)},
    }
    manifest = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "cache_events": dict(sorted(events.items())),
        "coverage": coverage,
        "outputs": outputs,
    }
    _atomic_json(manifest_path, manifest)
    return {"api_records": api_records, "operation_records": operation_records, "candidates": candidates, "manifest": manifest}


def compare_candidate_pair(result: dict[str, Any], left_id: str, right_id: str) -> dict[str, Any]:
    apis = {value["canonical_api_id"]: value for value in result["api_records"]}
    operations: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for value in result["operation_records"]:
        operations[value["canonical_api_id"]].append(value)
    def dimension(left: Any, right: Any) -> dict[str, Any]:
        if left in (None, [], {}) or right in (None, [], {}):
            state = "MISSING_EVIDENCE" if left in (None, [], {}) and right in (None, [], {}) else "NOT_COMPARABLE"
        else:
            state = "EQUAL" if left == right else "DIFFERENT"
        return {"state": state, "left": left, "right": right}
    left_api, right_api = apis[left_id], apis[right_id]
    left_ops, right_ops = operations[left_id], operations[right_id]
    candidate = next(
        (
            value
            for value in result.get("candidates", [])
            if {value["left_canonical_api_id"], value["right_canonical_api_id"]}
            == {left_id, right_id}
        ),
        None,
    )
    pairs = []
    for left in left_ops:
        for right in right_ops:
            if left["method"] == right["method"] and left["contract"]["normalized_path_shape"] == right["contract"]["normalized_path_shape"]:
                pairs.append({
                    "operation_anchor": {"method": left["method"], "left_path": left["exact_path"], "right_path": right["exact_path"]},
                    "method_path": dimension(
                        {"method": left["method"], "path": left["exact_path"], "normalized_shape": left["contract"]["normalized_path_shape"]},
                        {"method": right["method"], "path": right["exact_path"], "normalized_shape": right["contract"]["normalized_path_shape"]},
                    ),
                    "parameters": dimension(left["contract"]["parameters"], right["contract"]["parameters"]),
                    "request_contract": dimension(left["contract"]["request"], right["contract"]["request"]),
                    "response_contract": dimension(left["contract"]["responses"], right["contract"]["responses"]),
                    "auth": dimension(left["contract"]["auth"], right["contract"]["auth"]),
                    "exposure": dimension(left["contract"]["exposure"], right["contract"]["exposure"]),
                    "backend_target_ids": dimension(
                        candidate["shared_backend_target_ids"] if candidate else [],
                        candidate["shared_backend_target_ids"] if candidate else [],
                    ),
                    "backend_target_paths": dimension(
                        sorted(value["safe_target_path_or_template"] for value in left["candidate_inherited_backend_context"] if value.get("safe_target_path_or_template")),
                        sorted(value["safe_target_path_or_template"] for value in right["candidate_inherited_backend_context"] if value.get("safe_target_path_or_template")),
                    ),
                    "backend_configuration": dimension(
                        {
                            "facts": left["configured_backend_facts"],
                            "candidates": left["candidate_inherited_backend_context"],
                        },
                        {
                            "facts": right["configured_backend_facts"],
                            "candidates": right["candidate_inherited_backend_context"],
                        },
                    ),
                })
    return {
        "status": "POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION",
        "left": {"canonical_api_id": left_id, "name": left_api["identity_name"], "version": left_api["identity_version"], "source_variants": left_api["source_variants"]},
        "right": {"canonical_api_id": right_id, "name": right_api["identity_name"], "version": right_api["identity_version"], "source_variants": right_api["source_variants"]},
        "version": dimension(left_api["identity_version"], right_api["identity_version"]),
        "operation_comparisons": pairs,
        "limitations": ["Configuration evidence does not prove runtime egress.", "Structural equality does not prove functional duplication.", "Different canonical APIs remain distinct."],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    result = build_full_inventory(args.root)
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
