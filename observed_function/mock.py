"""Evidence-first, deterministic Task 015 Observed Function mock."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml

from semantic_inventory.full_inventory import _schema_shape


RULES_VERSION = "task015-observed-function-mock-v3"
OBSERVED_OUTPUT = Path("indexes/observed_function_sample.jsonl")
GAP_OUTPUT = Path("indexes/task015_upstream_gap_impact_register.jsonl")
REVIEW_OUTPUT = Path("indexes/task015_ambiguity_review_queue.jsonl")
MANIFEST_OUTPUT = Path("indexes/task015_mock_manifest.json")
CACHE_DIRECTORY = Path("indexes/cache/task015-observed-mock-v3")
V2_LEFT = "apic-identity:sha256:3165d30141993d77200c2630b10c29760e0e1c8f6520eb3368a12d6dd484657e"
V2_RIGHT = "apic-identity:sha256:6fa70f88ad990dcda279d38753d1e83806dc591c09b74619e945129c553f2aeb"

ACTION_MAP = {
    "get": "retrieve",
    "list": "list",
    "search": "search",
    "find": "retrieve",
    "retrieve": "retrieve",
    "enquire": "enquire",
    "enquiry": "enquire",
    "inquire": "enquire",
    "create": "create",
    "add": "create",
    "insert": "create",
    "submit": "submit",
    "send": "send",
    "push": "send",
    "update": "update",
    "patch": "update",
    "delete": "delete",
    "remove": "delete",
    "cancel": "cancel",
    "validate": "validate",
    "validates": "validate",
    "check": "validate",
    "activate": "activate",
    "deactivate": "deactivate",
    "issue": "issue",
    "extend": "extend",
}
TECHNICAL_TOKENS = {"jwt", "oauth", "token", "proxy", "health", "mock", "ratelimit", "schema", "keycloak", "security"}
GENERIC_TOKENS = {"api", "service", "operation", "request", "response", "rest", "v1", "v2", "qaas", "tip", "the", "to", "from", "of", "is", "used", "this"}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _json_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _stable_id(prefix: str, *values: Any) -> str:
    return f"{prefix}:sha256:{_json_hash(values)}"


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


def _words(value: str | None) -> list[str]:
    if not value:
        return []
    split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    return re.findall(r"[A-Za-z]+|[0-9]+", split.casefold())


def _schema_words(operation: dict[str, Any]) -> list[str]:
    refs = operation["request_summary"]["schema_references"] + operation["response_summary"]["schema_references"]
    words: list[str] = []
    for reference in refs:
        leaf = reference.rsplit("/", 1)[-1]
        words.extend(token for token in _words(leaf) if token not in {"rq", "rs", "message", "type", "request", "response"})
    return words


def _path_words(path: str) -> list[str]:
    return [token for token in _words(path) if token not in GENERIC_TOKENS and not token.isdigit()]


def _action_and_object(operation: dict[str, Any], api: dict[str, Any]) -> tuple[str | None, str | None, list[str]]:
    sources = [
        ("SOURCE_OPERATION_ID", operation.get("operation_id")),
        ("SOURCE_SUMMARY", operation.get("summary")),
        ("SOURCE_DESCRIPTION", operation.get("description")),
        ("SOURCE_PATH", operation.get("exact_path")),
        ("SOURCE_SCHEMA_REFERENCE", " ".join(_schema_words(operation))),
        ("CANONICAL_API_NAME", api.get("identity_name")),
    ]
    for evidence_type, text in sources:
        words = _words(text)
        for index, token in enumerate(words):
            if token in ACTION_MAP:
                object_words = [value for value in words[index + 1:] if value not in GENERIC_TOKENS][:8]
                if not object_words:
                    object_words = [value for value in words[:index] if value not in GENERIC_TOKENS][:8]
                return ACTION_MAP[token], " ".join(object_words) or None, [evidence_type]
    path_words = _path_words(operation["exact_path"])
    schema_words = _schema_words(operation)
    if path_words and (schema_words or operation["contract"]["parameters"]):
        action = {"GET": "retrieve", "POST": "process", "PUT": "update", "PATCH": "update", "DELETE": "delete"}.get(operation["method"])
        return action, " ".join(path_words[:8]), ["SOURCE_METHOD", "SOURCE_PATH", "SOURCE_SCHEMA_REFERENCE"]
    return None, None, []


def _compact_backend(operation: dict[str, Any]) -> dict[str, Any]:
    facts = [
        {
            "target_observation_id": value["target_observation_id"],
            "fact_taxonomy": value["fact_taxonomy"],
            "source_path": value["source_path"],
            "source_pointer": value["source_pointer"],
            "resolution_status": value["resolution_status"],
            "runtime_usage_proven": False,
        }
        for value in operation["configured_backend_facts"]
    ]
    candidates = operation["candidate_inherited_backend_context"]
    projection = [
        {
            "target_observation_id": value["target_observation_id"],
            "candidate_taxonomy": value["candidate_taxonomy"],
            "certainty": value["certainty"],
            "policy_context": value["policy_context"],
            "source_path": value["source_path"],
            "source_pointer": value["source_pointer"],
            "resolution_status": value["resolution_status"],
            "proven_operation_egress": False,
            "runtime_usage_proven": False,
        }
        for value in candidates[:5]
    ]
    return {
        "configured_operation_scoped_facts": facts,
        "candidate_inherited_context_count": len(candidates),
        "candidate_inherited_context_projection": projection,
        "candidate_projection_truncated": len(candidates) > len(projection),
        "all_candidate_context_sha256": _json_hash(candidates),
    }


def _contract_projection(operation: dict[str, Any]) -> dict[str, Any]:
    contract = operation["contract"]
    return {
        "parameters": contract["parameters"],
        "request": contract["request"],
        "responses": contract["responses"],
        "auth": contract["auth"],
        "exposure": contract["exposure"],
    }


def _action_signal(value: str | None) -> str | None:
    for word in _words(value):
        if word in ACTION_MAP:
            return ACTION_MAP[word]
    return None


def derive_observed_function(
    operation: dict[str, Any],
    api: dict[str, Any],
    categories: list[str],
) -> dict[str, Any]:
    action, object_phrase, evidence_types = _action_and_object(operation, api)
    evidence_types = set(evidence_types) | {"SOURCE_METHOD", "SOURCE_PATH"}
    for field, evidence_type in (("description", "SOURCE_DESCRIPTION"), ("summary", "SOURCE_SUMMARY"), ("operation_id", "SOURCE_OPERATION_ID")):
        if operation.get(field):
            evidence_types.add(evidence_type)
    if _schema_words(operation):
        evidence_types.add("SOURCE_SCHEMA_REFERENCE_AND_LOCAL_SHAPE")
    if operation["configured_backend_facts"]:
        evidence_types.add("CONFIGURED_OPERATION_SCOPED_BACKEND")
    if operation["candidate_inherited_backend_context"]:
        evidence_types.add("CANDIDATE_API_SHARED_BACKEND_CONTEXT")
    description_action = _action_signal(operation.get("description") or operation.get("summary"))
    operation_id_action = _action_signal(operation.get("operation_id"))
    contradictions = []
    if {description_action, operation_id_action} in ({"create", "retrieve"}, {"create", "delete"}, {"activate", "deactivate"}):
        contradictions.append({
            "type": "ACTION_SIGNAL_CONTRADICTION",
            "description_or_summary_action": description_action,
            "operation_id_action": operation_id_action,
        })
    meaningful_path = len(_path_words(operation["exact_path"])) >= 1 and operation["exact_path"] != "/"
    structural_signals = sum((meaningful_path, bool(_schema_words(operation)), bool(operation["contract"]["parameters"]), bool(operation["response_summary"]["response_status_codes"])))
    explicit = bool(operation.get("description") or operation.get("summary"))
    if contradictions:
        status, strength, reason = "AMBIGUOUS_NEEDS_REVIEW", "LOW", "Source operationId and descriptive text indicate materially different actions."
    elif explicit and action and object_phrase:
        status, strength, reason = "EXPLICITLY_DESCRIBED", "HIGH", "Explicit source description or summary corroborates the bounded action/object candidate and operation contract."
    elif action and object_phrase and (operation.get("operation_id") or structural_signals >= 2):
        status, strength, reason = "INFERRED_FROM_MULTIPLE_STRUCTURAL_SIGNALS", "MEDIUM", "Candidate wording is bounded to multiple source structural signals; it is not an architecture-approved function."
    elif action or object_phrase:
        status, strength, reason = "AMBIGUOUS_NEEDS_REVIEW", "LOW", "Only a limited lexical signal is available and cannot support a precise observed function."
    else:
        status, strength, reason = "INSUFFICIENT_EVIDENCE", "NONE", "Method/path and available contract evidence do not identify a defensible action and target."
    combined_words = set(_words(api.get("identity_name")) + _path_words(operation["exact_path"]) + _words(operation.get("operation_id")))
    nature = "TECHNICAL_OPERATION" if combined_words & TECHNICAL_TOKENS else "EVIDENCED_ACTION_APPEARING" if status == "EXPLICITLY_DESCRIBED" else "OPERATION_NATURE_UNDETERMINED"
    missing = [value["field"] for value in operation.get("missing_fields", [])]
    gap_refs = [f"task014-gap:missing-{field.casefold()}" for field in missing]
    if operation["candidate_inherited_backend_context"]:
        gap_refs.append("task014-gap:api-shared-backend-candidate-context")
    if "v2_pair" in categories:
        gap_refs.append("task014-gap:v2-schema-shape-difference")
    description = f"{action} {object_phrase}" if action and object_phrase else None
    return {
        "observed_function_id": _stable_id("observed-function", operation["semantic_operation_inventory_id"], RULES_VERSION),
        "record_layer": "PROVISIONAL_INTERPRETATION",
        "rules_version": RULES_VERSION,
        "canonical_api_id": operation["canonical_api_id"],
        "task014_operation_record_id": operation["semantic_operation_inventory_id"],
        "sample_categories": sorted(categories),
        "parent_api": {
            "identity_name": api.get("identity_name"),
            "identity_version": api.get("identity_version"),
            "operation_count": api["operation_count"],
            "protocol": api.get("protocol"),
        },
        "source_facts": {
            "method": operation["method"],
            "exact_path": operation["exact_path"],
            "operation_id": operation.get("operation_id"),
            "summary": operation.get("summary"),
            "description": operation.get("description"),
            "tags": operation.get("tags", []),
            "contract": _contract_projection(operation),
            "source_provenance": operation["source_provenance"],
            "source_variant_fingerprint": operation["source_variant_fingerprint"],
        },
        "backend_evidence": _compact_backend(operation),
        "candidate_observed_function": {
            "action_verb": action,
            "business_object_or_resource_phrase": object_phrase,
            "concise_description": description,
            "operation_nature": nature,
            "evidence_types": sorted(evidence_types),
        },
        "interpretation_status": status,
        "evidence_strength": strength,
        "certainty_reason": reason,
        "contradictory_signals": contradictions,
        "missing_information": sorted(missing),
        "upstream_gap_refs": sorted(set(gap_refs)),
        "reviewer_status": "PENDING_REVIEW",
        "runtime_usage_proven": False,
        "logical_function_asserted": False,
        "logical_api_asserted": False,
        "business_domain_asserted": False,
        "business_capability_asserted": False,
        "functional_duplication_asserted": False,
    }


def select_representative_operations(
    apis: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    api_by_id = {value["canonical_api_id"]: value for value in apis}
    by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        by_api[operation["canonical_api_id"]].append(operation)
    selected: dict[str, set[str]] = defaultdict(set)

    def add(category: str, values: Iterable[dict[str, Any]], count: int = 1) -> None:
        added = 0
        for value in sorted(values, key=lambda item: item["semantic_operation_inventory_id"]):
            operation_id = value["semantic_operation_inventory_id"]
            if category not in selected[operation_id]:
                selected[operation_id].add(category)
                added += 1
            if added == count:
                return
        raise ValueError(f"unable to satisfy sample category: {category}")

    add("v2_pair", by_api[V2_LEFT], len(by_api[V2_LEFT]))
    add("v2_pair", by_api[V2_RIGHT], len(by_api[V2_RIGHT]))
    add("explicit_description_and_operation_id", (value for value in operations if value.get("description") and value.get("operation_id")))
    add("missing_text_with_path_and_schema", (value for value in operations if not value.get("description") and not value.get("summary") and not value.get("operation_id") and value["exact_path"] != "/" and (_schema_words(value) or value["contract"]["parameters"])))
    add("ambiguous_generic_insufficient", (value for value in operations if not value.get("description") and not value.get("summary") and not value.get("operation_id") and value["exact_path"] == "/" and not _schema_words(value)))
    add("exact_operation_scoped_single_operation", (value for value in operations if value["configured_backend_facts"] and api_by_id[value["canonical_api_id"]]["operation_count"] == 1))
    add("exact_operation_scoped_multi_operation", (value for value in operations if value["configured_backend_facts"] and api_by_id[value["canonical_api_id"]]["operation_count"] > 1))
    add("conditional_multi_target_candidate_context", (value for value in operations if api_by_id[value["canonical_api_id"]]["identity_name"] == "osh" and any(item["policy_context"] == "CONDITIONAL_BRANCH" for item in value["candidate_inherited_backend_context"])), 2)
    add("contradictory_source_semantics", (value for value in operations if _action_signal(value.get("operation_id")) == "create" and _action_signal(value.get("description")) == "retrieve"))
    add("explicitly_technical_operation", (value for value in operations if "validate-jwt" in str(api_by_id[value["canonical_api_id"]].get("identity_name", "")).casefold()))

    overlap_pairs = [value for value in candidates if value["matching_request_schema_shape_sha256"] and value["matching_response_schema_shape_sha256"] and {value["left_canonical_api_id"], value["right_canonical_api_id"]} != {V2_LEFT, V2_RIGHT}][:2]
    if len(overlap_pairs) != 2:
        raise ValueError("unable to select two structural-overlap pairs")
    selected_candidate_ids = []
    for candidate in overlap_pairs:
        selected_candidate_ids.append(candidate["candidate_id"])
        shape = candidate["matching_method_path_shapes"][0]
        for side in (candidate["left_canonical_api_id"], candidate["right_canonical_api_id"]):
            matching = [value for value in by_api[side] if value["method"] == shape["method"] and value["contract"]["normalized_path_shape"] == shape["path_shape"]]
            add(f"structural_overlap_pair:{candidate['candidate_id']}", matching)

    operation_by_id = {value["semantic_operation_inventory_id"]: value for value in operations}
    selected_operations = [operation_by_id[value] for value in sorted(selected)]
    registry_api = next(value for value in apis if value["source_variant_classification"] == "REGISTRY_ONLY")
    no_path_api = next(value for value in apis if value["source_variants"] and value["operation_count"] == 0)
    return {
        "selected_operations": selected_operations,
        "categories_by_operation": {key: sorted(value) for key, value in sorted(selected.items())},
        "selected_structural_candidate_ids": sorted(selected_candidate_ids),
        "api_level_gap_representatives": [
            {"category": "registry_only_no_operations", "canonical_api_id": registry_api["canonical_api_id"], "identity_name": registry_api["identity_name"]},
            {"category": "source_backed_no_supported_path_items", "canonical_api_id": no_path_api["canonical_api_id"], "identity_name": no_path_api["identity_name"]},
        ],
    }


def _gap_record(
    gap_id: str,
    *,
    source_artifact: str,
    scope: str,
    api_ids: list[str],
    operation_ids: list[str],
    condition: str,
    downstream_effects: dict[str, str],
    severity: str,
    rationale: str,
    mitigation: str,
    role: str,
    trigger: str,
) -> dict[str, Any]:
    return {
        "gap_id": gap_id,
        "upstream_task": "TASK_014",
        "source_artifact": source_artifact,
        "scope": scope,
        "original_condition": condition,
        "affected_canonical_api_ids": sorted(set(api_ids)),
        "affected_operation_ids": sorted(set(operation_ids)),
        "impacted_record_count": len(set(operation_ids)) if operation_ids else len(set(api_ids)),
        "downstream_effects": downstream_effects,
        "severity": severity,
        "confidence": "HIGH",
        "rationale": rationale,
        "mitigation_or_retrieval_action": mitigation,
        "responsible_review_role": role,
        "recheck_trigger": trigger,
        "status": "CARRIED_FORWARD",
        "frozen_upstream_evidence_changed": False,
    }


def build_gap_register(apis: list[dict[str, Any]], operations: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    api_by_id = {value["canonical_api_id"]: value for value in apis}
    missing = lambda field: [value for value in operations if field in {item["field"] for item in value.get("missing_fields", [])}]
    shared = [value for value in operations if value["candidate_inherited_backend_context"]]
    registry = [value for value in apis if value["source_variant_classification"] == "REGISTRY_ONLY"]
    no_paths = [value for value in apis if value["source_variants"] and value["operation_count"] == 0]
    protocol_gaps = [value for value in apis if value.get("protocol") in {"graphql", "wsdl-to-rest"}]
    unresolved_api_ids = [value["canonical_api_id"] for value in apis if value["unresolved_product_location_occurrences"]]
    v2_ops = [value for value in operations if value["canonical_api_id"] in {V2_LEFT, V2_RIGHT}]
    body_without_shape = [value for value in operations if value["contract"]["request"]["body_present"] and not any(item.get("schema_shape_sha256") for item in value["contract"]["request"]["content"])]
    common_semantic_effect = {
        "015": "Reduces direct lexical evidence; use path/schema/backend only when multiple independent signals support a bounded interpretation.",
        "016": "May lower confidence when comparing or grouping observed functions.",
        "017": "May weaken technical-to-product/exposure explanations.",
        "018": "Must not be replaced by inferred domain labels.",
        "019": "Must not be replaced by inferred capability labels.",
    }
    records = []
    for field, gap_id in (("summary", "task014-gap:missing-summary"), ("description", "task014-gap:missing-description"), ("operationId", "task014-gap:missing-operationid")):
        values = missing(field)
        records.append(_gap_record(gap_id, source_artifact="indexes/semantic_operation_inventory.jsonl", scope="operation", api_ids=[value["canonical_api_id"] for value in values], operation_ids=[value["semantic_operation_inventory_id"] for value in values], condition=f"Task 014 source field {field} is absent or blank.", downstream_effects=common_semantic_effect, severity="NON_BLOCKING", rationale="Field absence alone does not block an observed function when independent structural evidence is adequate; affected operations still require evidence-strength evaluation.", mitigation="Use exact path, operationId/description alternatives, parameter and local schema shape evidence; queue the operation when signals remain vague.", role="Integration Architect", trigger="Source metadata enrichment or Task 015 reviewer decision"))
    records.extend([
        _gap_record("task014-gap:registry-only-no-operations", source_artifact="indexes/semantic_api_inventory.jsonl", scope="api", api_ids=[value["canonical_api_id"] for value in registry], operation_ids=[], condition="Accepted canonical identity has no accepted source API document and therefore no source-evidenced operation.", downstream_effects={task: "No operation/function evidence can be produced for these APIs until an authoritative source representation is recovered." for task in ("015", "016", "017", "018", "019")}, severity="DOWNSTREAM_BLOCKER", rationale="Creating operations or semantics would fabricate source evidence.", mitigation="Retrieve and validate an authoritative API representation without changing the frozen canonical identity.", role="Integration Architect", trigger="Accepted authoritative API source becomes available"),
        _gap_record("task014-gap:no-supported-path-items", source_artifact="indexes/semantic_api_inventory.jsonl", scope="api", api_ids=[value["canonical_api_id"] for value in no_paths], operation_ids=[], condition="Source-backed Swagger/OpenAPI document contains no supported explicit HTTP Path Item operation.", downstream_effects={task: "HTTP-operation-derived semantics are unavailable for these APIs; do not treat zero extracted operations as no business behavior." for task in ("015", "016", "017", "018", "019")}, severity="DOWNSTREAM_BLOCKER", rationale="Task 015 has no accepted operation anchor to interpret.", mitigation="Architect reviews source syntax/protocol and authorizes a protocol-specific parser or accepts the limitation.", role="Enterprise Architect", trigger="Protocol/parser decision or corrected source document"),
        _gap_record("task014-gap:native-protocol-semantics-not-extracted", source_artifact="tests/evidence/task-014/full-extraction/coverage_and_gaps.json", scope="protocol", api_ids=[value["canonical_api_id"] for value in protocol_gaps], operation_ids=[operation["semantic_operation_inventory_id"] for value in protocol_gaps for operation in operations if operation["canonical_api_id"] == value["canonical_api_id"]], condition="GraphQL and WSDL-to-REST documents have only wrapper HTTP Path Item inventory; native fields/WSDL operations were not parsed.", downstream_effects={"015": "Observed Functions are limited to wrapper HTTP operations.", "016": "Native-operation equivalence cannot be evaluated.", "017": "Protocol transformation detail remains incomplete.", "018": "Domain conclusions must not assume native-operation coverage.", "019": "Capability mapping must disclose wrapper-only evidence."}, severity="LOCAL_REVIEW_REQUIRED", rationale="Wrapper HTTP facts are valid but incomplete for native protocol semantics.", mitigation="Review wrapper semantics; separately authorize bounded native-protocol extraction if needed.", role="Enterprise Architect", trigger="Need for native GraphQL/WSDL semantic comparison"),
        _gap_record("task014-gap:unresolved-product-location", source_artifact="tests/evidence/task-007/unresolved_product_location_apis.jsonl", scope="relationship", api_ids=unresolved_api_ids, operation_ids=[], condition="113 Product-location occurrences remain unattached to accepted canonical APIs.", downstream_effects={"015": "Does not directly change operation action evidence.", "016": "May hide contextual evidence used to distinguish similar functions.", "017": "Directly limits product/exposure reconstruction.", "018": "May weaken contextual domain evidence.", "019": "May weaken capability ownership/context evidence."}, severity="LOCAL_REVIEW_REQUIRED", rationale="Candidate IDs are diagnostic only and cannot be promoted to relationships.", mitigation="Resolve using accepted URI/object identifiers and rerun dependent enrichment only after Phase 2 relationship approval.", role="Integration Architect", trigger="New authoritative Product-location identity evidence"),
        _gap_record("task014-gap:api-shared-backend-candidate-context", source_artifact="indexes/semantic_operation_inventory.jsonl", scope="operation", api_ids=[value["canonical_api_id"] for value in shared], operation_ids=[value["semantic_operation_inventory_id"] for value in shared], condition="API_SHARED backend configuration appears as candidate-only inherited context on operations.", downstream_effects={"015": "Backend context may corroborate but never establish an operation's action or runtime egress.", "016": "Shared backend is insufficient to merge observed functions.", "017": "Configured connectivity remains distinct from observed runtime integration.", "018": "Backend location must not become a domain label.", "019": "Backend target must not become a capability label."}, severity="LOCAL_REVIEW_REQUIRED", rationale="Operation attribution and runtime selection are unproven.", mitigation="Use exact operation-scoped configuration or runtime evidence when required; retain candidate certainty meanwhile.", role="Integration Architect", trigger="Exact operation-scoped configuration or accepted runtime evidence"),
        _gap_record("task014-gap:structural-overlap-candidates", source_artifact="indexes/semantic_structural_overlap_candidates.jsonl", scope="relationship", api_ids=[api for value in candidates for api in (value["left_canonical_api_id"], value["right_canonical_api_id"])], operation_ids=[], condition="60 cross-canonical pairs share multiple structural signals but are not confirmed duplicates.", downstream_effects={"015": "Compare observed wording and contradictions without unifying records.", "016": "Blocks confirmed Logical Function/API grouping for candidate pairs until semantic validation.", "017": "Shared backends do not establish common integration behavior.", "018": "No domain equality may be inferred.", "019": "No capability equality may be inferred."}, severity="DOWNSTREAM_BLOCKER", rationale="Task 016 grouping would be unsafe without semantic review of matching and differing contracts.", mitigation="Integration Architect validates observed functions and contract differences pair-by-pair.", role="Integration Architect", trigger="Task 015 observed-function approval for both sides and Task 016 review"),
        _gap_record("task014-gap:v2-schema-shape-difference", source_artifact="tests/evidence/task-014/full-extraction/v2_request_response_backend_comparison.json", scope="operation", api_ids=[V2_LEFT, V2_RIGHT], operation_ids=[value["semantic_operation_inventory_id"] for value in v2_ops], condition="The v2 pair has equal method/path and schema-ref labels but different deterministic request and response schema shapes; backend target path evidence is missing.", downstream_effects={"015": "Observed wording may overlap, but request/response distinctions and backend uncertainty must remain explicit.", "016": "Blocks any same-function or version-replacement conclusion without semantic/schema review.", "017": "Backend target ID overlap cannot prove equal runtime integration.", "018": "No shared domain conclusion follows from version naming.", "019": "No shared capability conclusion follows from structural overlap."}, severity="DOWNSTREAM_BLOCKER", rationale="Merging would erase evidenced contract differences.", mitigation="Review safe schema-shape differences and intended version semantics; obtain backend path/runtime evidence if required.", role="Enterprise Architect", trigger="Architect validation of v2 contract intent"),
        _gap_record("task014-gap:missing-request-schema-shape", source_artifact="indexes/semantic_operation_inventory.jsonl", scope="operation", api_ids=[value["canonical_api_id"] for value in body_without_shape], operation_ids=[value["semantic_operation_inventory_id"] for value in body_without_shape], condition="Request body is present but no deterministic local schema shape was available.", downstream_effects={"015": "Object/target interpretation cannot rely on request shape.", "016": "Request-contract similarity is not comparable.", "017": "Payload transformation evidence is incomplete.", "018": "No domain inference may fill the gap.", "019": "No capability inference may fill the gap."}, severity="LOCAL_REVIEW_REQUIRED", rationale="A body without a comparable schema weakens structural interpretation but other explicit text/path evidence may remain usable.", mitigation="Resolve safe local schema/reference or queue the operation for reviewer interpretation.", role="Integration Architect", trigger="Resolvable request schema or explicit source description"),
    ])
    for record in records:
        if record["gap_id"] == "task014-gap:unresolved-product-location":
            record["source_occurrence_count"] = 113
        elif record["gap_id"] == "task014-gap:structural-overlap-candidates":
            record["source_candidate_pair_count"] = len(candidates)
        elif record["gap_id"] == "task014-gap:native-protocol-semantics-not-extracted":
            record["affected_protocol_api_count"] = len(protocol_gaps)
    return sorted(records, key=lambda value: value["gap_id"])


def _cache_event(cache_path: Path, operation: dict[str, Any], categories: list[str]) -> tuple[str, dict[str, Any]]:
    fingerprint = _json_hash({"operation": operation, "categories": categories, "rules_version": RULES_VERSION})
    cached = None
    if cache_path.is_file():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cached = None
    if cached and cached.get("rules_version") == RULES_VERSION and cached.get("input_fingerprint") == fingerprint and isinstance(cached.get("record"), dict):
        return "HIT", cached["record"]
    if cached and cached.get("rules_version") != RULES_VERSION:
        event = "INVALIDATED_RULES_CHANGE"
    elif cached:
        event = "INVALIDATED_INPUT_CHANGE"
    else:
        event = "MISS"
    return event, {"input_fingerprint": fingerprint}


def _schema_differences(left: Any, right: Any, pointer: str = "", limit: int = 80) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    if type(left) is not type(right):
        return [{"pointer": pointer or "/", "left": type(left).__name__, "right": type(right).__name__, "difference": "TYPE_DIFFERENCE"}]
    if isinstance(left, dict):
        for key in sorted(set(left) | set(right)):
            child_pointer = f"{pointer}/{key}"
            if key not in left or key not in right:
                differences.append({"pointer": child_pointer, "left": "PRESENT" if key in left else "MISSING", "right": "PRESENT" if key in right else "MISSING", "difference": "PRESENCE_DIFFERENCE"})
            else:
                differences.extend(_schema_differences(left[key], right[key], child_pointer, limit - len(differences)))
            if len(differences) >= limit:
                break
    elif isinstance(left, list):
        if len(left) != len(right):
            differences.append({"pointer": pointer or "/", "left": len(left), "right": len(right), "difference": "LIST_LENGTH_DIFFERENCE"})
        for index, (left_value, right_value) in enumerate(zip(left, right)):
            differences.extend(_schema_differences(left_value, right_value, f"{pointer}/{index}", limit - len(differences)))
            if len(differences) >= limit:
                break
    elif left != right:
        differences.append({"pointer": pointer or "/", "left": left, "right": right, "difference": "VALUE_DIFFERENCE"})
    return differences[:limit]


def build_v2_safe_diff(root: Path) -> dict[str, Any]:
    paths = {
        "left": root / "staging/apis/_catalog/searchseasonalvisarequests_1.0.1.yaml",
        "right": root / "staging/apis/_catalog/searchseasonalvisarequests-v2_1.0.0.yaml",
    }
    documents = {side: yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.CSafeLoader) for side, path in paths.items()}
    operation = {side: document["paths"]["/searchseasvisareq"]["post"] for side, document in documents.items()}
    request_schema = {side: next(value["schema"] for value in value.get("parameters", []) if value.get("in") == "body") for side, value in operation.items()}
    response_schema = {side: value["responses"]["200"].get("schema") for side, value in operation.items()}
    request_shapes = {side: _schema_shape(schema, documents[side]) for side, schema in request_schema.items()}
    response_shapes = {side: _schema_shape(schema, documents[side]) for side, schema in response_schema.items()}
    return {
        "left_source": {"path": paths["left"].relative_to(root).as_posix(), "sha256": hashlib.sha256(paths["left"].read_bytes()).hexdigest()},
        "right_source": {"path": paths["right"].relative_to(root).as_posix(), "sha256": hashlib.sha256(paths["right"].read_bytes()).hexdigest()},
        "method": "POST",
        "path": "/searchseasvisareq",
        "request_shape_differences": _schema_differences(request_shapes["left"], request_shapes["right"]),
        "response_shape_differences": _schema_differences(response_shapes["left"], response_shapes["right"]),
        "safe_diff_limit": 80,
        "descriptions_examples_and_values_omitted": True,
        "semantic_equivalence_conclusion": "NOT_MADE_REQUIRES_VALIDATION",
    }


def build_mock(
    root: Path,
    *,
    observed_path: Path | None = None,
    gap_path: Path | None = None,
    review_path: Path | None = None,
    manifest_path: Path | None = None,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    observed_path = observed_path or root / OBSERVED_OUTPUT
    gap_path = gap_path or root / GAP_OUTPUT
    review_path = review_path or root / REVIEW_OUTPUT
    manifest_path = manifest_path or root / MANIFEST_OUTPUT
    cache_dir = cache_dir or root / CACHE_DIRECTORY
    apis = _load_jsonl(root / "indexes/semantic_api_inventory.jsonl")
    operations = _load_jsonl(root / "indexes/semantic_operation_inventory.jsonl")
    candidates = _load_jsonl(root / "indexes/semantic_structural_overlap_candidates.jsonl")
    api_by_id = {value["canonical_api_id"]: value for value in apis}
    selection = select_representative_operations(apis, operations, candidates)
    records = []
    events = Counter()
    for operation in selection["selected_operations"]:
        operation_id = operation["semantic_operation_inventory_id"]
        categories = selection["categories_by_operation"][operation_id]
        cache_path = cache_dir / f"{operation_id.rsplit(':', 1)[-1]}.json"
        event, cached_or_fingerprint = _cache_event(cache_path, operation, categories)
        if event == "HIT":
            record = cached_or_fingerprint
        else:
            record = derive_observed_function(operation, api_by_id[operation["canonical_api_id"]], categories)
            _atomic_json(cache_path, {"rules_version": RULES_VERSION, "input_fingerprint": cached_or_fingerprint["input_fingerprint"], "record": record})
        events[event] += 1
        records.append(record)
    records.sort(key=lambda value: value["observed_function_id"])
    gaps = build_gap_register(apis, operations, candidates)
    selected_candidate_ids = set(selection["selected_structural_candidate_ids"])
    review_queue = []
    for record in records:
        if record["interpretation_status"] in {"AMBIGUOUS_NEEDS_REVIEW", "INSUFFICIENT_EVIDENCE"} or record["contradictory_signals"]:
            review_queue.append({
                "review_item_id": _stable_id("task015-review", record["observed_function_id"]),
                "review_type": "OBSERVED_FUNCTION_INTERPRETATION",
                "observed_function_id": record["observed_function_id"],
                "canonical_api_id": record["canonical_api_id"],
                "operation_id": record["task014_operation_record_id"],
                "reason": record["certainty_reason"],
                "status": "PENDING_REVIEW",
                "responsible_role": "Integration Architect",
            })
    for candidate in candidates:
        if candidate["candidate_id"] in selected_candidate_ids:
            review_queue.append({
                "review_item_id": _stable_id("task015-review", candidate["candidate_id"]),
                "review_type": "STRUCTURAL_OVERLAP_SEMANTIC_VALIDATION",
                "candidate_id": candidate["candidate_id"],
                "left_canonical_api_id": candidate["left_canonical_api_id"],
                "right_canonical_api_id": candidate["right_canonical_api_id"],
                "reason": "Multiple structural signals justify comparison but do not prove functional duplication.",
                "status": "PENDING_REVIEW",
                "responsible_role": "Integration Architect",
            })
    _write_jsonl(observed_path, records)
    _write_jsonl(gap_path, gaps)
    _write_jsonl(review_path, sorted(review_queue, key=lambda value: value["review_item_id"]))
    coverage = {
        "selected_operation_count": len(records),
        "selected_canonical_api_count": len({value["canonical_api_id"] for value in records}),
        "interpretation_status_counts": dict(sorted(Counter(value["interpretation_status"] for value in records).items())),
        "evidence_strength_counts": dict(sorted(Counter(value["evidence_strength"] for value in records).items())),
        "configured_operation_scoped_sample_count": sum(bool(value["backend_evidence"]["configured_operation_scoped_facts"]) for value in records),
        "candidate_inherited_backend_sample_count": sum(bool(value["backend_evidence"]["candidate_inherited_context_count"]) for value in records),
        "review_queue_count": len(review_queue),
        "gap_register_count": len(gaps),
        "gap_severity_counts": dict(sorted(Counter(value["severity"] for value in gaps).items())),
        "model_use": "NONE_DETERMINISTIC_RULES_ONLY",
        "model_token_usage": 0,
        "estate_wide_task015_inference_performed": False,
        "functional_duplication_assertions": 0,
        "logical_api_assertions": 0,
        "domain_assertions": 0,
        "capability_assertions": 0,
        "registry_only_operations_fabricated": 0,
        "native_graphql_or_wsdl_operations_fabricated": 0,
    }
    outputs = {
        "observed_functions": {"path": observed_path.name, "sha256": hashlib.sha256(observed_path.read_bytes()).hexdigest(), "record_count": len(records)},
        "gap_register": {"path": gap_path.name, "sha256": hashlib.sha256(gap_path.read_bytes()).hexdigest(), "record_count": len(gaps)},
        "review_queue": {"path": review_path.name, "sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(), "record_count": len(review_queue)},
    }
    manifest = {"rules_version": RULES_VERSION, "cache_events": dict(sorted(events.items())), "coverage": coverage, "outputs": outputs, "selection": {key: value for key, value in selection.items() if key != "selected_operations"}, "v2_safe_schema_diff": build_v2_safe_diff(root)}
    _atomic_json(manifest_path, manifest)
    return {"records": records, "gaps": gaps, "review_queue": review_queue, "manifest": manifest}
