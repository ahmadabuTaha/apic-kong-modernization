"""Deterministic, safe evidence projections for Task 014 architecture review."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml


HTTP_METHODS = {"delete", "get", "head", "options", "patch", "post", "put", "trace"}
SENSITIVE_KEY = re.compile(r"password|passwd|secret|token|credential|api[-_]?key", re.I)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def _refs(value: Any) -> list[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str):
                found.add(child)
            else:
                found.update(_refs(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_refs(child))
    return sorted(found)


def _policy_shapes(value: Any, pointer: str = "") -> list[str]:
    """Return policy/key shapes, never target values or other scalar content."""
    shapes: list[str] = []
    if isinstance(value, dict):
        for key in sorted(value):
            child = value[key]
            child_pointer = f"{pointer}/{key}"
            if key in {"invoke", "proxy", "operation-switch", "switch", "map", "gatewayscript"}:
                shapes.append(child_pointer)
            if SENSITIVE_KEY.search(key) or key in {"target-url", "url"}:
                continue
            shapes.extend(_policy_shapes(child, child_pointer))
    elif isinstance(value, list):
        for child in value:
            shapes.extend(_policy_shapes(child, f"{pointer}/*"))
    return sorted(set(shapes))


def document_signature(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"expected mapping document: {path}")
    operations: list[dict[str, Any]] = []
    for api_path, path_item in sorted((document.get("paths") or {}).items()):
        if not isinstance(path_item, dict):
            continue
        shared_parameters = path_item.get("parameters", [])
        for method, operation in sorted(path_item.items()):
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            parameters = []
            for scope, values in (("PATH", shared_parameters), ("OPERATION", operation.get("parameters", []))):
                if not isinstance(values, list):
                    continue
                for item in values:
                    if not isinstance(item, dict):
                        continue
                    parameters.append({
                        "scope": scope,
                        "name": item.get("name") if isinstance(item.get("name"), str) else None,
                        "in": item.get("in") if isinstance(item.get("in"), str) else None,
                        "required": item.get("required") if isinstance(item.get("required"), bool) else None,
                        "ref": item.get("$ref") if isinstance(item.get("$ref"), str) else None,
                        "schema_refs": _refs(item.get("schema")),
                    })
            responses = operation.get("responses") if isinstance(operation.get("responses"), dict) else {}
            operations.append({
                "method": method.lower(),
                "path": api_path,
                "path_shape": re.sub(r"\{[^}]+\}", "{parameter}", api_path),
                "parameters": parameters,
                "request_schema_refs": _refs(operation.get("requestBody")) + _refs(operation.get("parameters")),
                "response_statuses": sorted(str(value) for value in responses),
                "response_schema_refs": _refs(responses),
            })
    structural = {
        "format": "OPENAPI_3" if str(document.get("openapi", "")).startswith("3") else "SWAGGER_2" if str(document.get("swagger", "")) == "2.0" else "OTHER",
        "operations": operations,
        "assembly_policy_shapes": _policy_shapes(document.get("x-ibm-configuration", {}), "/x-ibm-configuration"),
    }
    descriptive = {
        "api_description_present": bool((document.get("info") or {}).get("description")),
        "operation_description_presence": [
            bool(operation.get("description"))
            for path_item in (document.get("paths") or {}).values() if isinstance(path_item, dict)
            for method, operation in sorted(path_item.items())
            if method.lower() in HTTP_METHODS and isinstance(operation, dict)
        ],
    }
    return {
        "source_path": path.as_posix(),
        "source_sha256": _sha(path),
        "structural_fingerprint_sha256": _hash_json(structural),
        "descriptive_presence_fingerprint_sha256": _hash_json(descriptive),
        "operation_count": len(operations),
        "operation_anchors": [{"method": value["method"], "path": value["path"]} for value in operations],
        "structural": structural,
    }


def build_variant_profile(root: Path) -> dict[str, Any]:
    identities = json.loads((root / "indexes/apic_identity_resolution.json").read_text(encoding="utf-8"))["canonical_identity_records"]
    extracted = {item["extracted_record_id"]: item for item in _load_jsonl(root / "indexes/extracted_records.jsonl")}
    groups = []
    for identity in identities:
        if identity.get("canonical_object_type") != "api_artifact":
            continue
        occurrences = []
        for evidence in identity.get("source_evidence", []):
            source = evidence.get("source_relative_path", "")
            if evidence.get("source_object_pointer") != "" or not source.endswith((".yaml", ".yml")):
                continue
            record = extracted.get(evidence.get("extracted_record_id"), {})
            occurrences.append({
                "occurrence_id": evidence.get("extracted_record_id"),
                "source_path": source,
                "source_sha256": record.get("source_sha256"),
                "role": "AUTHORITATIVE_API_ARTIFACT" if evidence.get("extracted_record_id") in identity.get("authoritative_artifact_occurrence_ids", []) else "PRODUCT_LOCATION_REPRESENTATION",
            })
        if len(occurrences) > 1:
            groups.append((identity, sorted(occurrences, key=lambda value: (value["source_path"], value["occurrence_id"]))))
    distribution = Counter(len(values) for _, values in groups)
    differing = [(identity, values) for identity, values in groups if len({value["source_sha256"] for value in values}) > 1]
    exact = [(identity, values) for identity, values in groups if len({value["source_sha256"] for value in values}) == 1]
    samples: list[dict[str, Any]] = []
    if exact:
        identity, values = exact[0]
        samples.append({
            "canonical_api_id": identity["canonical_identity_record_id"],
            "api_name": identity.get("name"),
            "classification": "BYTE_IDENTICAL_DUPLICATE_REPRESENTATIONS",
            "occurrences": values,
            "targeted_parse_performed": False,
        })
    for identity, values in differing:
        signatures = [document_signature(root / value["source_path"]) for value in values]
        structural = {value["structural_fingerprint_sha256"] for value in signatures}
        samples.append({
            "canonical_api_id": identity["canonical_identity_record_id"],
            "api_name": identity.get("name"),
            "classification": "SEMANTICALLY_EQUIVALENT_STRUCTURAL_VARIANTS" if len(structural) == 1 else "CONFLICT_REQUIRES_ARCHITECTURE_REVIEW",
            "occurrences": values,
            "targeted_parse_performed": True,
            "variant_signatures": [
                {
                    "source_path": occurrence["source_path"],
                    **{key: signature[key] for key in ("source_sha256", "structural_fingerprint_sha256", "descriptive_presence_fingerprint_sha256", "operation_count", "operation_anchors")},
                }
                for occurrence, signature in zip(values, signatures, strict=True)
            ],
        })
    return {
        "summary": {
            "canonical_api_groups_with_multiple_root_yaml_representations": len(groups),
            "representation_count_distribution": {str(key): distribution[key] for key in sorted(distribution)},
            "groups_all_representations_same_sha256": len(exact),
            "groups_with_multiple_sha256_values": len(differing),
            "groups_with_multiple_authoritative_api_artifacts": sum(sum(value["role"] == "AUTHORITATIVE_API_ARTIFACT" for value in values) > 1 for _, values in groups),
            "estate_wide_structural_comparison_performed": False,
            "targeted_groups_structurally_compared": len(differing),
        },
        "samples": samples,
    }


def backend_case(root: Path, canonical_api_id: str, case: str) -> dict[str, Any]:
    identities = json.loads((root / "indexes/apic_identity_resolution.json").read_text(encoding="utf-8"))["canonical_identity_records"]
    identity = next(value for value in identities if value["canonical_identity_record_id"] == canonical_api_id)
    observations = [value for value in _load_jsonl(root / "indexes/backend_target_resolution.jsonl") if value["canonical_api_id"] == canonical_api_id]
    source = next((value["source_relative_path"] for value in identity.get("source_evidence", []) if value["source_relative_path"].startswith("staging/apis/") and value.get("source_object_pointer") == "" and value["source_relative_path"].endswith((".yaml", ".yml"))), None)
    operation_count = document_signature(root / source)["operation_count"] if source else 0
    scopes = sorted({value["scope_classification"] for value in observations})
    evidence = [{
        "task011_observation_id": value["target_observation_id"],
        "accepted_fact_scope": value["scope_classification"],
        "fact_taxonomy": "EVIDENCED_OPERATION_SCOPED" if value["scope_classification"] == "OPERATION_SCOPED" else "CONFIGURED_API_SHARED",
        "operation_anchors": value.get("operation_scope") or [],
        "source_path": value["source_path"],
        "source_pointer": value["source_pointer"],
        "resolution_status": value["resolution_status"],
        "target_observation_id": value["target_observation_id"],
        "target_path_suffix_or_template": value.get("target_path_suffix_or_template"),
        "policy_context": "OPERATION_SWITCH_CASE" if "/operation-switch/" in value["source_pointer"] else "CONDITIONAL_BRANCH" if "/switch/" in value["source_pointer"] else "ASSEMBLY_SEQUENCE",
    } for value in observations]
    candidates = []
    if "API_SHARED" in scopes:
        candidates.append({
            "candidate_taxonomy": "CANDIDATE_INHERITED_CONTEXT",
            "operation_anchors": document_signature(root / source)["operation_anchors"] if source else [],
            "certainty": "CANDIDATE_ONLY",
            "limit": "Configuration context only; not observed or proven operation egress.",
        })
    return {
        "case": case,
        "case_status": "EVIDENCED",
        "canonical_api_id": canonical_api_id,
        "api_name": identity.get("name"),
        "operation_count": operation_count,
        "accepted_scope_facts": scopes,
        "backend_target_count": len({value["target_observation_id"] for value in observations}),
        "evidence": evidence,
        "candidate_architectural_associations": candidates,
        "runtime_usage_proven": False,
    }


def compare_cross_canonical_pair(root: Path, left_id: str, right_id: str, backend_target_id: str) -> dict[str, Any]:
    identities = json.loads((root / "indexes/apic_identity_resolution.json").read_text(encoding="utf-8"))["canonical_identity_records"]
    by_id = {value["canonical_identity_record_id"]: value for value in identities}
    def source(identity: dict[str, Any]) -> str:
        return sorted(value["source_relative_path"] for value in identity["source_evidence"] if value["source_relative_path"].startswith("staging/apis/") and value.get("source_object_pointer") == "" and value["source_relative_path"].endswith((".yaml", ".yml")))[0]
    sides = []
    signatures = []
    for api_id in (left_id, right_id):
        identity = by_id[api_id]
        source_path = source(identity)
        signature = document_signature(root / source_path)
        signatures.append(signature)
        sides.append({"canonical_api_id": api_id, "api_name": identity.get("name"), "source_path": source_path, "source_sha256": signature["source_sha256"], "operation_count": signature["operation_count"]})
    operation_sets = [{(value["method"], value["path_shape"]) for value in signature["structural"]["operations"]} for signature in signatures]
    ref_sets = [{ref for value in signature["structural"]["operations"] for ref in value["request_schema_refs"] + value["response_schema_refs"]} for signature in signatures]
    union = operation_sets[0] | operation_sets[1]
    return {
        "status": "POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION",
        "apis": sides,
        "matching_signals": {
            "shared_backend_target_id": backend_target_id,
            "method_path_shape_intersection": [{"method": method, "path_shape": path} for method, path in sorted(operation_sets[0] & operation_sets[1])],
            "method_path_shape_jaccard": round(len(operation_sets[0] & operation_sets[1]) / len(union), 6) if union else 0,
            "schema_reference_intersection": sorted(ref_sets[0] & ref_sets[1]),
        },
        "differing_signals": {
            "left_only_method_path_shapes": sorted([list(value) for value in operation_sets[0] - operation_sets[1]]),
            "right_only_method_path_shapes": sorted([list(value) for value in operation_sets[1] - operation_sets[0]]),
        },
        "limitations": ["Shared backend does not prove duplication.", "Structural similarity does not establish business-semantic equivalence.", "No runtime traffic evidence was evaluated."],
    }
