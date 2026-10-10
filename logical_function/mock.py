"""Evidence-first deterministic Task 016 Logical Function normalization mock."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import yaml

from observed_function.mock import _schema_differences
from semantic_inventory.full_inventory import _schema_shape


MOCK_RULES_VERSION = "task016-logical-function-mock-v2"
COMPARISON_OUTPUT = Path("indexes/task016_mock_candidate_comparisons.jsonl")
REVIEW_OUTPUT = Path("indexes/task016_mock_review_queue.jsonl")
MANIFEST_OUTPUT = Path("indexes/task016_mock_manifest.json")

V2_LEFT = "apic-identity:sha256:3165d30141993d77200c2630b10c29760e0e1c8f6520eb3368a12d6dd484657e"
V2_RIGHT = "apic-identity:sha256:6fa70f88ad990dcda279d38753d1e83806dc591c09b74619e945129c553f2aeb"


SELECTION_SPECS = (
    {
        "selection_key": "seasonal_visa_v2_contract_change",
        "kind": "STRUCTURAL_CANDIDATE",
        "left_name": "searchseasonalvisarequests",
        "right_name": "searchseasonalvisarequests-v2",
        "method": "POST",
        "path_shape": "/searchseasvisareq",
        "status": "POSSIBLE_SAME_LOGICAL_FUNCTION",
        "categories": ["V2_REQUIRED", "IDENTICAL_PROVISIONAL_WORDING_SCHEMA_DIFFERENCE", "VERSION_DIFFERENCE"],
    },
    {
        "selection_key": "employment_enquiry_different_names",
        "kind": "STRUCTURAL_CANDIDATE",
        "left_name": "mcsemploymentstatusenquiry_querycenter",
        "right_name": "mcsemploymentstatusenquiry",
        "method": "POST",
        "path_shape": "/employmentstatusenquiry",
        "status": "POSSIBLE_SAME_LOGICAL_FUNCTION",
        "categories": ["DIFFERENT_NAMES", "SHARED_BACKEND_AND_WORDING", "SCHEMA_DIFFERENCE"],
    },
    {
        "selection_key": "contributor_income_different_names",
        "kind": "STRUCTURAL_CANDIDATE",
        "left_name": "gosi-getgosicontributorsalary",
        "right_name": "gosi-getcontributorsalary",
        "method": "GET",
        "path_shape": "/contributor/{parameter}/income",
        "status": "POSSIBLE_SAME_LOGICAL_FUNCTION",
        "categories": ["DIFFERENT_NAMES", "SIMILAR_ACTION_OBJECT", "SCHEMA_DIFFERENCE"],
    },
    {
        "selection_key": "proposal_contract_multi_operation",
        "kind": "STRUCTURAL_CANDIDATE",
        "left_name": "proposals",
        "right_name": "ajeer-bulk-contracts",
        "method": "GET",
        "path_shape": "/{parameter}",
        "status": "POSSIBLE_SAME_LOGICAL_FUNCTION",
        "categories": ["ONE_TO_MANY_CONTEXT", "MULTI_OPERATION_APIS", "INFERRED_INTERPRETATION"],
    },
    {
        "selection_key": "appointment_action_conflict",
        "kind": "STRUCTURAL_CANDIDATE",
        "left_name": "updateappointmentstatustip",
        "right_name": "updateappointmentstatus",
        "method": "POST",
        "path_shape": "/updateappoinstatus",
        "status": "REVIEW_REQUIRED_CONFLICTING_SIGNALS",
        "categories": ["SAME_BACKEND_DIFFERING_ACTION_OR_PAYLOAD", "FALSE_POSITIVE_PREVENTION"],
    },
    {
        "selection_key": "farming_establishment_action_conflict",
        "kind": "STRUCTURAL_CANDIDATE",
        "left_name": "openfarmingestablishmentfiletip",
        "right_name": "openfarmingestablishmentfile",
        "method": "POST",
        "path_shape": "/openfarmingestfile",
        "status": "REVIEW_REQUIRED_CONFLICTING_SIGNALS",
        "categories": ["SAME_PATH_BACKEND_CONFLICTING_WORDING", "FALSE_POSITIVE_PREVENTION"],
    },
    {
        "selection_key": "ambiguous_ticket_lookup",
        "kind": "STRUCTURAL_CANDIDATE",
        "left_name": "noor-api-for-testing-19dec2022",
        "right_name": "noor-api-for-testing",
        "method": "POST",
        "path_shape": "/GetTicketByEstablishmentID",
        "status": "REVIEW_REQUIRED_CONFLICTING_SIGNALS",
        "categories": ["TASK015_AMBIGUOUS", "SCHEMA_DIFFERENCE", "SANDBOX_TEST_CONTEXT"],
    },
    {
        "selection_key": "root_get_missing_evidence",
        "kind": "STRUCTURAL_CANDIDATE",
        "left_name": "p2htip_testapi2",
        "right_name": "p2htip_testapi_ratelimit_dynamicvalue",
        "method": "GET",
        "path_shape": "/",
        "status": "NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE",
        "categories": ["TASK015_INSUFFICIENT", "MISSING_SUMMARY_DESCRIPTION", "TECHNICAL_TEST_CONTEXT"],
    },
    {
        "selection_key": "technical_health_vs_token",
        "kind": "INDEXED_NEGATIVE_CONTROL",
        "left_name": "qks-systemhealthcheck",
        "right_name": "qaas_generatekeycloakoken",
        "left_method": "GET",
        "left_path": "/qksHealthCheck",
        "right_method": "POST",
        "right_path": "/keycloak/token",
        "status": "CLEARLY_DIFFERENT_SUPPORTED",
        "categories": ["TECHNICAL_SECURITY", "NEGATIVE_CONTROL", "DIFFERENT_ACTION_OBJECT_CONTRACT"],
    },
    {
        "selection_key": "payment_token_generate_vs_delete",
        "kind": "INDEXED_NEGATIVE_CONTROL",
        "left_name": "generatepaymentcardtoken",
        "right_name": "deletepaymentcardtoken",
        "left_method": "POST",
        "left_path": "/generatepaymentcardtoken",
        "right_method": "POST",
        "right_path": "/deletepaymentcardtoken",
        "status": "CLEARLY_DIFFERENT_SUPPORTED",
        "categories": ["TECHNICAL_SECURITY", "NEGATIVE_CONTROL", "SAME_OBJECT_DIFFERENT_ACTION"],
    },
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}:sha256:{_hash(parts)}"


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, path)


def _write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text("".join(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n" for value in values), encoding="utf-8")
    os.replace(temporary, path)


def _fingerprint(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


def _output_fingerprint(path: Path, root: Path, record_count: int) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name
    return {
        "path": relative,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "record_count": record_count,
    }


def _candidate_lookup(candidates: list[dict[str, Any]], left: str, right: str) -> dict[str, Any]:
    matches = [value for value in candidates if {value["left_api_name"], value["right_api_name"]} == {left, right}]
    if len(matches) != 1:
        raise ValueError(f"expected one structural candidate for {left} <> {right}, found {len(matches)}")
    return matches[0]


def _api_lookup(apis: list[dict[str, Any]], name: str, candidate_api_ids: set[str] | None = None) -> dict[str, Any]:
    matches = [value for value in apis if value["identity_name"] == name and (candidate_api_ids is None or value["canonical_api_id"] in candidate_api_ids)]
    if len(matches) != 1:
        raise ValueError(f"expected one API for {name}, found {len(matches)}")
    return matches[0]


def _operation_by_shape(values: list[dict[str, Any]], method: str, path_shape: str) -> dict[str, Any]:
    matches = [value for value in values if value["method"] == method and value["contract"]["normalized_path_shape"] == path_shape]
    if len(matches) != 1:
        raise ValueError(f"expected one {method} {path_shape} operation, found {len(matches)}")
    return matches[0]


def _operation_by_exact(values: list[dict[str, Any]], method: str, path: str) -> dict[str, Any]:
    matches = [value for value in values if value["method"] == method and value["exact_path"] == path]
    if len(matches) != 1:
        raise ValueError(f"expected one {method} {path} operation, found {len(matches)}")
    return matches[0]


def select_pairs(
    apis: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_api: dict[str, list[dict[str, Any]]] = {}
    for operation in operations:
        by_api.setdefault(operation["canonical_api_id"], []).append(operation)
    selected = []
    for spec in SELECTION_SPECS:
        candidate = None
        candidate_api_ids = None
        if spec["kind"] == "STRUCTURAL_CANDIDATE":
            candidate = _candidate_lookup(candidates, spec["left_name"], spec["right_name"])
            candidate_api_ids = {candidate["left_canonical_api_id"], candidate["right_canonical_api_id"]}
        left_api = _api_lookup(apis, spec["left_name"], candidate_api_ids)
        right_api = _api_lookup(apis, spec["right_name"], candidate_api_ids)
        if spec["kind"] == "STRUCTURAL_CANDIDATE":
            left_operation = _operation_by_shape(by_api[left_api["canonical_api_id"]], spec["method"], spec["path_shape"])
            right_operation = _operation_by_shape(by_api[right_api["canonical_api_id"]], spec["method"], spec["path_shape"])
        else:
            left_operation = _operation_by_exact(by_api[left_api["canonical_api_id"]], spec["left_method"], spec["left_path"])
            right_operation = _operation_by_exact(by_api[right_api["canonical_api_id"]], spec["right_method"], spec["right_path"])
        selected.append({"spec": spec, "candidate": candidate, "left_api": left_api, "right_api": right_api, "left_operation": left_operation, "right_operation": right_operation})
    return selected


def _document_and_operation(root: Path, operation: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    source = root / operation["source_provenance"]["source_path"]
    document = yaml.load(source.read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
    payload = document["paths"][operation["exact_path"]][operation["method"].lower()]
    return document, payload


def _request_shapes(document: dict[str, Any], operation: dict[str, Any]) -> list[Any]:
    shapes = []
    for parameter in operation.get("parameters", []):
        if isinstance(parameter, dict) and parameter.get("in") == "body" and isinstance(parameter.get("schema"), dict):
            shapes.append(_schema_shape(parameter["schema"], document))
    request_body = operation.get("requestBody")
    if isinstance(request_body, dict):
        for media in (request_body.get("content") or {}).values():
            if isinstance(media, dict) and isinstance(media.get("schema"), dict):
                shapes.append(_schema_shape(media["schema"], document))
    return shapes


def _response_shapes(document: dict[str, Any], operation: dict[str, Any]) -> list[dict[str, Any]]:
    shapes = []
    for status, response in sorted((operation.get("responses") or {}).items(), key=lambda item: str(item[0])):
        if not isinstance(response, dict):
            continue
        schemas = []
        if isinstance(response.get("schema"), dict):
            schemas.append(_schema_shape(response["schema"], document))
        for media in (response.get("content") or {}).values():
            if isinstance(media, dict) and isinstance(media.get("schema"), dict):
                schemas.append(_schema_shape(media["schema"], document))
        shapes.append({"status": str(status), "schemas": schemas})
    return shapes


def _policy_evidence(document: dict[str, Any]) -> dict[str, Any]:
    root = (document.get("x-ibm-configuration") or {}).get("assembly") or {}
    found: list[dict[str, str]] = []
    transformations = {"map", "gatewayscript", "xslt", "set-variable", "parse", "json-to-xml", "xml-to-json"}

    def visit(value: Any, pointer: str) -> None:
        if isinstance(value, dict):
            for key, child in sorted(value.items()):
                child_pointer = f"{pointer}/{key}"
                if key in transformations:
                    found.append({"policy": key, "source_pointer": child_pointer})
                visit(child, child_pointer)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{pointer}/{index}")

    visit(root, "/x-ibm-configuration/assembly")
    return {
        "transformation_policy_count": len(found),
        "transformation_policies": found,
        "configuration_scope": "API_ASSEMBLY_CONTEXT_NOT_PROVEN_OPERATION_EXECUTION",
        "runtime_execution_proven": False,
        "raw_policy_values_omitted": True,
    }


def _side_projection(api: dict[str, Any], operation: dict[str, Any], observed: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    configured = operation["configured_backend_facts"]
    candidates = operation["candidate_inherited_backend_context"]
    return {
        "canonical_api_id": api["canonical_api_id"],
        "api_name": api["identity_name"],
        "api_version": api.get("identity_version"),
        "api_operation_count": api["operation_count"],
        "task014_operation_id": operation["semantic_operation_inventory_id"],
        "task015_observed_function_id": observed["observed_function_id"],
        "source_provenance": operation["source_provenance"],
        "source_variant_fingerprint": operation["source_variant_fingerprint"],
        "method": operation["method"],
        "exact_path": operation["exact_path"],
        "normalized_path_shape": operation["contract"]["normalized_path_shape"],
        "operation_selector": operation.get("operation_selector"),
        "provisional_action_object": observed["candidate_observed_function"],
        "task015_interpretation_status": observed["interpretation_status"],
        "task015_evidence_strength": observed["evidence_strength"],
        "task015_reviewer_status": observed["reviewer_status"],
        "parameters": operation["contract"]["parameters"],
        "request_contract": operation["contract"]["request"],
        "response_contract": operation["contract"]["responses"],
        "auth": operation["contract"]["auth"],
        "exposure": operation["contract"]["exposure"],
        "backend_evidence": {
            "configured_operation_scoped_target_observation_ids": sorted(value["target_observation_id"] for value in configured),
            "candidate_api_shared_target_observation_ids": sorted(value["target_observation_id"] for value in candidates),
            "configured_operation_scoped_count": len(configured),
            "candidate_api_shared_count": len(candidates),
            "candidate_certainty": "CANDIDATE_ONLY" if candidates else None,
            "runtime_usage_proven": False,
            "operation_egress_proven": False,
        },
        "operation_routing_scope": (
            "EVIDENCED_OPERATION_SCOPED_BACKEND"
            if configured
            else "API_SHARED_CANDIDATE_CONTEXT"
            if candidates
            else "NO_BACKEND_ROUTING_EVIDENCE"
        ),
        "assembly_transformation_evidence": policy,
        "missing_information": observed["missing_information"],
    }


def _evidence(
    left: dict[str, Any],
    right: dict[str, Any],
    candidate: dict[str, Any] | None,
    left_request_shape_present: bool,
    right_request_shape_present: bool,
    left_response_shape_present: bool,
    right_response_shape_present: bool,
    request_differences: list[dict[str, Any]],
    response_differences: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    positive = []
    negative = []

    def item(kind: str, fact: str, left_value: Any, right_value: Any) -> dict[str, Any]:
        return {"evidence_type": kind, "fact": fact, "left": left_value, "right": right_value}

    if left["method"] == right["method"]:
        positive.append(item("HTTP_METHOD", "equal", left["method"], right["method"]))
    else:
        negative.append(item("HTTP_METHOD", "different", left["method"], right["method"]))
    if left["normalized_path_shape"] == right["normalized_path_shape"]:
        positive.append(item("NORMALIZED_PATH", "equal", left["normalized_path_shape"], right["normalized_path_shape"]))
    else:
        negative.append(item("NORMALIZED_PATH", "different", left["normalized_path_shape"], right["normalized_path_shape"]))
    left_phrase = left["provisional_action_object"]["concise_description"]
    right_phrase = right["provisional_action_object"]["concise_description"]
    if left_phrase and left_phrase == right_phrase:
        positive.append(item("PROVISIONAL_ACTION_OBJECT", "equal_but_not_human_approved", left_phrase, right_phrase))
    elif left_phrase or right_phrase:
        negative.append(item("PROVISIONAL_ACTION_OBJECT", "different_or_incomplete", left_phrase, right_phrase))
    if candidate and candidate["shared_backend_target_ids"]:
        positive.append(item("CONFIGURED_BACKEND_BLOCK", "shared_target_identity_candidate_context_only", candidate["shared_backend_target_ids"], candidate["shared_backend_target_ids"]))
    if not left_request_shape_present or not right_request_shape_present:
        negative.append(item("ACTUAL_SAFE_REQUEST_SHAPE", "schema_not_available", left_request_shape_present, right_request_shape_present))
    elif request_differences:
        negative.append(item("ACTUAL_SAFE_REQUEST_SHAPE", "different", len(request_differences), len(request_differences)))
    else:
        positive.append(item("ACTUAL_SAFE_REQUEST_SHAPE", "no_difference_detected", 0, 0))
    if not left_response_shape_present or not right_response_shape_present:
        negative.append(item("ACTUAL_SAFE_RESPONSE_SHAPE", "schema_not_available", left_response_shape_present, right_response_shape_present))
    elif response_differences:
        negative.append(item("ACTUAL_SAFE_RESPONSE_SHAPE", "different", len(response_differences), len(response_differences)))
    else:
        positive.append(item("ACTUAL_SAFE_RESPONSE_SHAPE", "no_difference_detected", 0, 0))
    if left["auth"] != right["auth"]:
        negative.append(item("AUTH", "different", left["auth"], right["auth"]))
    if left["exposure"] != right["exposure"]:
        negative.append(item("EXPOSURE", "different", left["exposure"], right["exposure"]))
    if left["api_version"] != right["api_version"]:
        negative.append(item("API_VERSION", "different_not_precedence", left["api_version"], right["api_version"]))
    return positive, negative


def _limitations(spec: dict[str, Any], left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    values = [
        "STAGING_EXPORT_DOES_NOT_PROVE_PRODUCTION_DEPLOYMENT_OR_USAGE",
        "CONFIGURED_BACKEND_DOES_NOT_PROVE_RUNTIME_EGRESS",
        "TASK015_WORDING_IS_PROVISIONAL_AUTOMATED_INTERPRETATION",
        "DISTINCT_CANONICAL_APIS_AND_OPERATION_IDS_REMAIN_DISTINCT",
        "NO_DUPLICATE_REPLACEMENT_OR_RETIREMENT_DECISION_AUTHORIZED",
    ]
    if left["missing_information"] or right["missing_information"]:
        values.append("METADATA_ABSENT")
    if spec["status"] == "NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE":
        values.extend(["SOURCE_EVIDENCE_NOT_AVAILABLE", "SEMANTIC_VALIDATION_PENDING"])
    if spec["status"] == "REVIEW_REQUIRED_CONFLICTING_SIGNALS":
        values.append("AUTOMATED_INTERPRETATION_LIMIT")
    return sorted(set(values))


def build_mock(
    root: Path,
    *,
    comparison_path: Path | None = None,
    review_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    comparison_path = comparison_path or root / COMPARISON_OUTPUT
    review_path = review_path or root / REVIEW_OUTPUT
    manifest_path = manifest_path or root / MANIFEST_OUTPUT
    input_paths = {
        "api_inventory": root / "indexes/semantic_api_inventory.jsonl",
        "operation_inventory": root / "indexes/semantic_operation_inventory.jsonl",
        "structural_candidates": root / "indexes/semantic_structural_overlap_candidates.jsonl",
        "observed_functions": root / "indexes/observed_function_inventory.jsonl",
        "task015_gap_register": root / "indexes/task015_full_gap_impact_register.jsonl",
    }
    apis = _load_jsonl(input_paths["api_inventory"])
    operations = _load_jsonl(input_paths["operation_inventory"])
    candidates = _load_jsonl(input_paths["structural_candidates"])
    observed = {value["task014_operation_record_id"]: value for value in _load_jsonl(input_paths["observed_functions"])}
    selections = select_pairs(apis, operations, candidates)
    comparisons = []
    source_paths: set[Path] = set()
    for selection in selections:
        spec = selection["spec"]
        left_operation = selection["left_operation"]
        right_operation = selection["right_operation"]
        left_document, left_payload = _document_and_operation(root, left_operation)
        right_document, right_payload = _document_and_operation(root, right_operation)
        source_paths.update({root / left_operation["source_provenance"]["source_path"], root / right_operation["source_provenance"]["source_path"]})
        left_request = _request_shapes(left_document, left_payload)
        right_request = _request_shapes(right_document, right_payload)
        left_response = _response_shapes(left_document, left_payload)
        right_response = _response_shapes(right_document, right_payload)
        request_differences = _schema_differences(left_request, right_request, limit=120)
        response_differences = _schema_differences(left_response, right_response, limit=120)
        left = _side_projection(selection["left_api"], left_operation, observed[left_operation["semantic_operation_inventory_id"]], _policy_evidence(left_document))
        right = _side_projection(selection["right_api"], right_operation, observed[right_operation["semantic_operation_inventory_id"]], _policy_evidence(right_document))
        positive, negative = _evidence(
            left,
            right,
            selection["candidate"],
            bool(left_request),
            bool(right_request),
            any(value["schemas"] for value in left_response),
            any(value["schemas"] for value in right_response),
            request_differences,
            response_differences,
        )
        comparison_id = _stable_id("logical-function-comparison", left["task014_operation_id"], right["task014_operation_id"], MOCK_RULES_VERSION)
        candidate_proposal_id = _stable_id("logical-function-candidate", comparison_id)
        comparisons.append({
            "comparison_id": comparison_id,
            "candidate_logical_function_proposal_id": candidate_proposal_id,
            "rules_version": MOCK_RULES_VERSION,
            "selection_key": spec["selection_key"],
            "sample_categories": sorted(spec["categories"]),
            "selection_basis": spec["kind"],
            "structural_candidate_id": selection["candidate"]["candidate_id"] if selection["candidate"] else None,
            "left": left,
            "right": right,
            "actual_safe_schema_comparison": {
                "request_shape_differences": request_differences,
                "response_shape_differences": response_differences,
                "difference_limit_per_direction": 120,
                "descriptions_examples_and_values_omitted": True,
                "source_documents_read": [left["source_provenance"], right["source_provenance"]],
            },
            "positive_evidence": positive,
            "negative_evidence": negative,
            "comparison_status": spec["status"],
            "status_is_proposal_not_approval": True,
            "certainty_reason": {
                "POSSIBLE_SAME_LOGICAL_FUNCTION": "Multiple independent similarities justify semantic review, while recorded differences prevent approval or substitution.",
                "CLEARLY_DIFFERENT_SUPPORTED": "Explicit action/path/contract evidence supports treating these operations as different in this mock.",
                "NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE": "Available source metadata and contract structure do not identify a defensible function comparison.",
                "REVIEW_REQUIRED_CONFLICTING_SIGNALS": "Positive structural signals conflict with action wording, schema, or automated interpretation evidence.",
            }[spec["status"]],
            "limitations": _limitations(spec, left, right),
            "false_positive_risks": ["shared_backend_or_path_may_reflect_facade_or_routing_reuse", "provisional_wording_may_hide_contract_or_action_differences"],
            "false_negative_risks": ["path_rewrite_or_middleware_may_hide_related_functions", "schema_aliases_or_versioned_adapters_may_preserve_business_intent"],
            "reviewer_status": "PENDING_REVIEW",
            "canonical_apis_merged": False,
            "operations_collapsed": False,
            "confirmed_duplicate": False,
            "safe_replacement_asserted": False,
            "runtime_equivalence_asserted": False,
            "logical_api_asserted": False,
        })
    comparisons.sort(key=lambda value: value["comparison_id"])
    review_queue = [{
        "review_item_id": _stable_id("task016-review", value["comparison_id"]),
        "comparison_id": value["comparison_id"],
        "candidate_logical_function_proposal_id": value["candidate_logical_function_proposal_id"],
        "comparison_status": value["comparison_status"],
        "selection_key": value["selection_key"],
        "specific_evidence_request": "Validate the proposed action/object and material contract differences; provide a named source document only if the indexed evidence is insufficient.",
        "candidate_follow_up_source": "CONFLUENCE_POTENTIAL_UNVERIFIED" if value["comparison_status"] in {"NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE", "REVIEW_REQUIRED_CONFLICTING_SIGNALS"} else None,
        "responsible_role": "Integration Architect",
        "status": "PENDING_REVIEW",
    } for value in comparisons]
    _write_jsonl(comparison_path, comparisons)
    _write_jsonl(review_path, review_queue)
    inputs = {name: _fingerprint(path, root) for name, path in input_paths.items()}
    inputs["targeted_source_documents"] = [_fingerprint(path, root) for path in sorted(source_paths)]
    outputs = {
        "comparisons": _output_fingerprint(comparison_path, root, len(comparisons)),
        "review_queue": _output_fingerprint(review_path, root, len(review_queue)),
    }
    manifest = {
        "rules_version": MOCK_RULES_VERSION,
        "sample_pair_count": len(comparisons),
        "status_distribution": dict(sorted(Counter(value["comparison_status"] for value in comparisons).items())),
        "category_distribution": dict(sorted(Counter(category for value in comparisons for category in value["sample_categories"]).items())),
        "review_queue_count": len(review_queue),
        "structural_candidate_pair_count": sum(value["selection_basis"] == "STRUCTURAL_CANDIDATE" for value in comparisons),
        "indexed_negative_control_count": sum(value["selection_basis"] == "INDEXED_NEGATIVE_CONTROL" for value in comparisons),
        "full_estate_grouping_performed": False,
        "model_use": "NONE_DETERMINISTIC_RULES_ONLY",
        "model_token_usage": 0,
        "confluence_retrieved": False,
        "inputs": inputs,
        "outputs": outputs,
    }
    _atomic_json(manifest_path, manifest)
    return {"comparisons": comparisons, "review_queue": review_queue, "manifest": manifest}
