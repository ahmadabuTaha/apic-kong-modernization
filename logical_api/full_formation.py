"""Evidence-led provisional Logical API formation for Task 017."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from logical_api.expanded_validation import _jsonl
from logical_api.mock import _member
from logical_function.full_inventory import _relationship_context


RULES_VERSION = "task017-full-logical-api-formation-v1"
MAX_API_MEMBER_COUNT = 10
OUTPUTS = {
    "operation_disposition": Path("indexes/task017_full_operation_disposition.jsonl"),
    "proposals": Path("indexes/task017_full_logical_api_proposals.jsonl"),
    "operation_intents": Path("indexes/task017_full_logical_operation_intents.jsonl"),
    "review_queue": Path("indexes/task017_full_review_queue.jsonl"),
    "diagnostics": Path("indexes/task017_full_formation_diagnostics.jsonl"),
    "manifest": Path("indexes/task017_full_manifest.json"),
}

GENERIC_RESOURCE_TOKENS = {
    "api", "apis", "data", "details", "entity", "information", "item", "items",
    "object", "process", "record", "records", "request", "requests", "resource",
    "resources", "response", "service", "services", "uri", "value", "values",
}
GENERIC_ACTIONS = {"", "process", "query", "unknown", "unresolved"}
ACTION_WORDS = {
    "activate", "add", "approve", "assign", "cancel", "close", "create", "delete",
    "disable", "enable", "generate", "issue", "list", "open", "reject", "remove",
    "retrieve", "search", "submit", "update", "validate",
}


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def _stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}:sha256:{_hash(parts)}"


def _write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        "".join(
            json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
            for value in values
        ),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _fingerprint(path: Path, root: Path, count: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }
    if count is not None:
        result["record_count"] = count
    return result


def _normalized_phrase(value: str | None) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (value or "").lower()))


def _resource_tokens(value: str | None) -> set[str]:
    return {
        token
        for token in _normalized_phrase(value).split()
        if token not in GENERIC_RESOURCE_TOKENS and not token.isdigit()
    }


def _static_path_segments(path: str) -> set[str]:
    result = set()
    for part in path.strip("/").split("/"):
        if not part or (part.startswith("{") and part.endswith("}")):
            continue
        tokens = _resource_tokens(part.replace("-", " ").replace("_", " "))
        if tokens:
            result.add(" ".join(sorted(tokens)))
    return result


def _member_citations(member: dict[str, Any]) -> list[str]:
    provenance = member["source_provenance"]
    return [
        f"{provenance['source_path']}#{provenance['source_pointer']}",
        member["task015_observed_function_id"],
        *member["task016_comparison_refs"],
        *member["task016_refinement_refs"],
    ]


def _exposure_citations(members: list[dict[str, Any]]) -> list[str]:
    refs = set()
    for member in members:
        exposure = member.get("relationship_exposure_context", {})
        refs.update(exposure.get("accepted_product_relationship_ids", []))
        refs.update(exposure.get("accepted_plan_relationship_ids", []))
        refs.update(exposure.get("subscription_relationship_ids", []))
    return sorted(refs) or sorted({ref for member in members for ref in _member_citations(member)})


def _supported_actions(member: dict[str, Any]) -> list[str]:
    actions = member.get("supported_actions", [])
    if not actions and member.get("observed_action"):
        actions = [member["observed_action"]]
    return sorted(
        {
            str(action).strip().lower()
            for action in actions
            if str(action).strip().lower() not in GENERIC_ACTIONS
        }
    )


def _api_assessment(members: list[dict[str, Any]]) -> tuple[str, dict[str, Any], str, str, str]:
    object_phrases = [_normalized_phrase(member.get("observed_object")) for member in members]
    object_tokens = [_resource_tokens(member.get("observed_object")) for member in members]
    actions = [_supported_actions(member) for member in members]
    path_tokens = [_static_path_segments(member["exact_path"]) for member in members]
    shared_path_signals = set.intersection(*path_tokens) if path_tokens else set()
    same_object = bool(object_phrases) and len(set(object_phrases)) == 1 and bool(object_tokens[0])
    explicit_descriptions = all(
        member.get("interpretation_status") == "EXPLICITLY_DESCRIBED" for member in members
    )
    actions_evidenced = all(actions)
    distinct_actions = len({action for values in actions for action in values}) > 1
    concrete_path_family = bool(shared_path_signals)
    disjoint_objects = bool(object_tokens) and all(
        object_tokens[index].isdisjoint(object_tokens[other])
        for index in range(len(object_tokens))
        for other in range(index + 1, len(object_tokens))
    )
    contradiction = any(
        member.get("semantic_support") in {"CONTRADICTED", "CONFLICTING"}
        or member.get("interpretation_status") == "AMBIGUOUS_NEEDS_REVIEW"
        for member in members
    )

    criteria = {
        "R1": {
            "status": "SUPPORTED" if same_object and explicit_descriptions else "NOT_EVIDENCED",
            "rationale": (
                "All members have the same explicit non-generic resource phrase."
                if same_object and explicit_descriptions
                else "A corroborated, non-generic common resource phrase is not present for every member."
            ),
            "evidence_refs": sorted({ref for member in members for ref in _member_citations(member)}),
        },
        "R2": {
            "status": (
                "SUPPORTED"
                if same_object and actions_evidenced and distinct_actions and concrete_path_family and explicit_descriptions and not contradiction
                else "CONTRADICTED"
                if not same_object and not concrete_path_family and len({tuple(sorted(tokens)) for tokens in object_tokens}) > 1
                else "NOT_EVIDENCED"
            ),
            "rationale": (
                "Distinct documented actions share a direct, non-generic resource path family."
                if same_object and actions_evidenced and distinct_actions and concrete_path_family and explicit_descriptions and not contradiction
                else "Member evidence is mixed or lacks direct action/resource-path cohesion."
            ),
            "evidence_refs": sorted({ref for member in members for ref in _member_citations(member)}),
        },
        "R3": {
            "status": "NOT_EVIDENCED",
            "rationale": "Accepted Product/Plan context is exposure evidence only; a common owner, consumer, authorization boundary, or entitlement intent is not established.",
            "evidence_refs": _exposure_citations(members),
        },
        "R4": {
            "status": "SUPPORTED",
            "rationale": "Each source operation retains exact method/path, API version, request/response schema fingerprints, statuses, and security requirements; compatibility is not inferred.",
            "evidence_refs": sorted({ref for member in members for ref in _member_citations(member)}),
        },
        "R5": {
            "status": "SUPPORTED" if all(
                member.get("backend_context", {}).get("certainty") == "CONFIGURED_OPERATION_SCOPED"
                for member in members
            ) else "NOT_EVIDENCED",
            "rationale": (
                "Operation-scoped configured backend evidence is recorded, without asserting execution."
                if all(member.get("backend_context", {}).get("certainty") == "CONFIGURED_OPERATION_SCOPED" for member in members)
                else "API-shared candidates or missing operation-level evidence do not establish backend behavior or runtime egress."
            ),
            "evidence_refs": sorted({ref for member in members for ref in _member_citations(member)}),
        },
        "R6": {
            "status": "SUPPORTED",
            "rationale": "The proposal records a non-formation alternative and retains distinct actions and source contracts; no pairwise/transitive equivalence is asserted.",
            "evidence_refs": sorted({ref for member in members for ref in _member_citations(member)}),
        },
        "R7": {
            "status": "SUPPORTED",
            "rationale": "Canonical API, Task 014 operation, Task 015 observed-function, Task 016 candidate references, and source fingerprint/pointer are retained per member.",
            "evidence_refs": sorted({ref for member in members for ref in _member_citations(member)}),
        },
    }

    r1_r2_supported = criteria["R1"]["status"] == "SUPPORTED" and criteria["R2"]["status"] == "SUPPORTED"
    if r1_r2_supported and criteria["R7"]["status"] == "SUPPORTED":
        sufficiency = "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY"
        decision_basis = "R1+R2+R7: same explicit resource, distinct actions, and direct resource-path family."
    elif (
        criteria["R2"]["status"] == "CONTRADICTED"
        and explicit_descriptions
        and disjoint_objects
    ):
        sufficiency = "SUPPORTED_SEPARATE"
        decision_basis = "Available object/path evidence supports keeping these operations separate."
    elif any(object_tokens) or any(actions):
        sufficiency = "PARTIAL"
        decision_basis = "Some resource or action signals exist, but direct cohesive-boundary evidence is incomplete."
    else:
        sufficiency = "INSUFFICIENT"
        decision_basis = "Resource and action evidence is insufficient to propose a conceptual boundary."

    positive = (
        "A single current APIC API exposes the listed operations; the proposal keeps APIC identity and operation contracts intact."
        if sufficiency != "INSUFFICIENT"
        else "Only the current APIC grouping is observed; no conceptual business boundary is asserted."
    )
    counter = (
        "The same canonical API is not proof of one business boundary; retain separate operation intents, contract variants, and exposure context."
    )
    alternative = (
        "Keep each source operation as a separate conceptual boundary until lifecycle, ownership, or consumer evidence supports a cohesive grouping."
    )
    return sufficiency, criteria, decision_basis, positive, f"{counter} Alternative: {alternative}"


def _contract_summary(member: dict[str, Any]) -> dict[str, Any]:
    request = member.get("request_contract", {})
    return {
        "request_schema_refs": sorted(
            {ref for item in request.get("content", []) for ref in item.get("schema_refs", [])}
        ),
        "request_schema_shape_sha256": sorted(
            {item["schema_shape_sha256"] for item in request.get("content", []) if item.get("schema_shape_sha256")}
        ),
        "response_statuses": sorted(
            {item["status"] for item in member.get("response_contract", []) if item.get("status")}
        ),
        "response_schema_shape_sha256": sorted(
            {
                item["schema_shape_sha256"]
                for item in member.get("response_contract", [])
                if item.get("schema_shape_sha256")
            }
        ),
        "security_requirement_present": member.get("security_context", {}).get("security_requirement_present"),
        "security_scheme_types": sorted(member.get("security_context", {}).get("security_scheme_types", [])),
    }


def _member_criteria(
    member: dict[str, Any], group_criteria: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    ref = f"{member['source_provenance']['source_path']}#{member['source_provenance']['source_pointer']}"
    exposure = member.get("relationship_exposure_context", {})
    exposure_refs = sorted(
        set(exposure.get("accepted_product_relationship_ids", []))
        | set(exposure.get("accepted_plan_relationship_ids", []))
        | set(exposure.get("subscription_relationship_ids", []))
    )
    resource_tokens = _resource_tokens(member.get("observed_object"))
    resource_supported = bool(resource_tokens) and member.get("interpretation_status") == "EXPLICITLY_DESCRIBED"
    return {
        "R1": {
            "status": "SUPPORTED" if resource_supported else "NOT_EVIDENCED",
            "rationale": "Member has an explicit non-generic resource phrase." if resource_supported else "Member resource phrase is missing, generic, or not explicitly described.",
            "evidence_refs": [ref],
        },
        "R2": {
            "status": group_criteria["R2"]["status"] if group_criteria["R2"]["status"] == "SUPPORTED" else "NOT_EVIDENCED",
            "rationale": "Member action and direct path-family evidence contribute to the group criterion." if group_criteria["R2"]["status"] == "SUPPORTED" else "The member-to-boundary cohesion link is not sufficiently evidenced.",
            "evidence_refs": [ref],
        },
        "R3": {
            "status": "NOT_EVIDENCED",
            "rationale": "Accepted Product/Plan/Subscription associations are preserved as exposure context, not as proof of a consumer, owner, authorization boundary, or entitlement intent.",
            "evidence_refs": exposure_refs or [ref],
        },
        "R4": {
            "status": "SUPPORTED",
            "rationale": "Exact method/path, version, contract fingerprints, and security context are retained.",
            "evidence_refs": [ref],
        },
        "R5": {
            "status": "SUPPORTED" if member.get("backend_context", {}).get("certainty") == "CONFIGURED_OPERATION_SCOPED" else "NOT_EVIDENCED",
            "rationale": "Operation-scoped configuration is recorded without implying execution." if member.get("backend_context", {}).get("certainty") == "CONFIGURED_OPERATION_SCOPED" else "No operation-scoped semantic or runtime evidence is established.",
            "evidence_refs": [ref],
        },
        "R6": {
            "status": "SUPPORTED",
            "rationale": "Distinct action and source-contract evidence is retained; source operation identity is not collapsed.",
            "evidence_refs": [ref],
        },
        "R7": {
            "status": "SUPPORTED",
            "rationale": "Canonical API, Task 014/015 identity, Task 016 links, and source fingerprint/pointer are retained.",
            "evidence_refs": [
                member["task014_operation_id"],
                member["task015_observed_function_id"],
                *member["task016_comparison_refs"],
                *member["task016_refinement_refs"],
                ref,
                member["source_provenance"]["source_sha256"],
            ],
        },
    }


def _sample_safe_member(member: dict[str, Any], disposition: dict[str, Any]) -> dict[str, Any]:
    provenance = member["source_provenance"]
    exposure = member.get("product_plan_subscription_context", {})
    return {
        "api_name": member["api_name"],
        "api_version": member.get("api_version"),
        "canonical_api_id": member["canonical_api_id"],
        "task014_operation_id": member["task014_operation_id"],
        "task015_observed_function_id": member["task015_observed_function_id"],
        "task016_comparison_refs": member.get("task016_comparison_refs", []),
        "task016_refinement_refs": member.get("task016_refinement_refs", []),
        "method": member["method"],
        "exact_path": member["exact_path"],
        "supported_actions": member.get("supported_actions", []),
        "observed_object": member.get("observed_object"),
        "interpretation_status": member.get("interpretation_status"),
        "contract": _contract_summary(member),
        "source_provenance": {
            "source_path": provenance["source_path"],
            "source_pointer": provenance["source_pointer"],
            "source_sha256": provenance["source_sha256"],
        },
        "accepted_product_count": len(exposure.get("accepted_product_ids", [])),
        "accepted_plan_count": len(exposure.get("accepted_plan_ids", [])),
        "accepted_product_ids": exposure.get("accepted_product_ids", []),
        "accepted_plan_ids": exposure.get("accepted_plan_ids", []),
        "accepted_product_relationship_ids": exposure.get("accepted_product_relationship_ids", []),
        "accepted_plan_relationship_ids": exposure.get("accepted_plan_relationship_ids", []),
        "subscription_evidence_state": exposure.get("subscription_evidence_state", "NOT_EVIDENCED"),
        "subscription_join_count": exposure.get("subscription_join_count", 0),
        "subscription_relationship_ids": exposure.get("subscription_relationship_ids", []),
        "product_is_logical_api": False,
        "runtime_activity_proven": False,
        "primary_disposition": disposition["primary_disposition"],
    }


def _cache_fingerprints(root: Path, inputs: dict[str, Path]) -> dict[str, Any]:
    fingerprints = {}
    for name, path in inputs.items():
        fingerprints[name] = _fingerprint(path, root)
    return fingerprints


def build_full_formation(root: Path) -> dict[str, Any]:
    root = root.resolve()
    inputs = {
        "apis": root / "indexes/semantic_api_inventory.jsonl",
        "operations": root / "indexes/semantic_operation_inventory.jsonl",
        "observed_functions": root / "indexes/observed_function_inventory.jsonl",
        "task015_api_gaps": root / "indexes/task015_api_level_gap_records.jsonl",
        "task016_operation_catalog": root / "indexes/task016_full_operation_catalog.jsonl",
        "task016_comparisons": root / "indexes/task016_full_candidate_pairs.jsonl",
        "task016_refinements": root / "indexes/task016_semantic_refinement_pairs.jsonl",
        "task016_manifest": root / "indexes/task016_full_manifest.json",
        "task017_expanded_register": root / "indexes/task017_expanded_validation_register.jsonl",
        "task017_expanded_manifest": root / "indexes/task017_expanded_validation_manifest.json",
        "relationships": root / "indexes/relationship_index.jsonl",
        "backend_resolution": root / "indexes/backend_target_resolution.jsonl",
        "codegraph_dependency_edges": root / "indexes/codegraph_dependency_edges.jsonl",
        "implementation": Path(__file__).resolve(),
    }
    if any(not path.exists() for path in inputs.values()):
        missing = [str(path.relative_to(root)) for path in inputs.values() if not path.exists()]
        raise FileNotFoundError(f"Required frozen Task 014-017 indexes are missing: {missing}")

    api_rows = _jsonl(inputs["apis"])
    operation_rows = _jsonl(inputs["operations"])
    observed_rows = _jsonl(inputs["observed_functions"])
    catalog_rows = _jsonl(inputs["task016_operation_catalog"])
    comparison_rows = _jsonl(inputs["task016_comparisons"])
    refinement_rows = _jsonl(inputs["task016_refinements"])
    gap_rows = _jsonl(inputs["task015_api_gaps"])
    sample_rows = _jsonl(inputs["task017_expanded_register"])
    resolution_rows = _jsonl(inputs["backend_resolution"])
    dependency_edges = _jsonl(inputs["codegraph_dependency_edges"])
    relationship_rows = _jsonl(inputs["relationships"])

    operation_by_id = {row["semantic_operation_inventory_id"]: row for row in operation_rows}
    observed_by_operation = {row["task014_operation_record_id"]: row for row in observed_rows}
    api_by_id = {row["canonical_api_id"]: row for row in api_rows}
    exposure_by_api = _relationship_context(api_rows, relationship_rows)
    catalog_by_id = {row["task014_operation_id"]: row for row in catalog_rows}
    resolution = {row["target_observation_id"]: row for row in resolution_rows}
    graph: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in dependency_edges:
        graph[edge["source_canonical_identity_record_id"]].append(edge)

    if len(api_rows) != 2036 or len(operation_rows) != 2414 or len(observed_rows) != 2414:
        raise ValueError("Frozen Task 014/015 operation or API counts do not match accepted baseline.")
    if len(operation_by_id) != len(operation_rows) or len(observed_by_operation) != len(observed_rows):
        raise ValueError("Duplicate Task 014 or Task 015 operation IDs detected.")
    if set(operation_by_id) != set(observed_by_operation):
        raise ValueError("Task 014/015 operation reconciliation is not one-to-one.")
    if set(operation_by_id) != set(catalog_by_id):
        raise ValueError("Task 016 operation catalog does not reconcile to Task 014 operations.")

    comparisons_by_operation: dict[str, list[str]] = defaultdict(list)
    comparison_by_id = {row["comparison_id"]: row for row in comparison_rows}
    for row in comparison_rows:
        for side in ("left", "right"):
            operation_id = row[side]["task014_operation_id"]
            comparisons_by_operation[operation_id].append(row["comparison_id"])
    refinements_by_operation: dict[str, list[str]] = defaultdict(list)
    refinement_by_comparison: dict[str, dict[str, Any]] = {}
    for row in refinement_rows:
        refinement_by_comparison[row["prior_comparison_id"]] = row
        for side in ("left", "right"):
            refinements_by_operation[row[side]["task014_operation_id"]].append(row["refinement_id"])

    api_members: dict[str, list[dict[str, Any]]] = defaultdict(list)
    members_by_operation: dict[str, dict[str, Any]] = {}
    for operation_id, operation in operation_by_id.items():
        observed = observed_by_operation[operation_id]
        api = api_by_id[operation["canonical_api_id"]]
        if observed["canonical_api_id"] != operation["canonical_api_id"]:
            raise ValueError(f"Task 015 canonical API mismatch for {operation_id}")
        member = _member(operation_id, operation_by_id, observed_by_operation, api_by_id, resolution, graph)
        context = exposure_by_api[operation["canonical_api_id"]]
        member["relationship_exposure_context"] = {
            "subscription_evidence_state": context["subscription_evidence_state"],
            "accepted_product_ids": context["accepted_product_ids"],
            "accepted_plan_ids": context["accepted_plan_ids"],
            "accepted_product_relationship_ids": context["accepted_product_relationship_ids"],
            "accepted_plan_relationship_ids": context["accepted_plan_relationship_ids"],
            "subscription_join_count": context["subscription_join_count"],
            "subscription_relationship_ids": sorted(
                {
                    join["subscription_relationship_id"]
                    for join in context["subscription_join_relationships"]
                }
            ),
            "operation_consumption_proven": False,
            "runtime_activity_proven": False,
            "consumer_identifiers_omitted": True,
        }
        member["task016_comparison_refs"] = sorted(set(comparisons_by_operation[operation_id]))
        member["task016_refinement_refs"] = sorted(set(refinements_by_operation[operation_id]))
        member["task016_candidate_refs"] = [
            {
                "comparison_id": comparison_id,
                "candidate_logical_function_id": comparison_by_id[comparison_id][
                    "candidate_logical_function_id"
                ],
                "refinement_id": refinement_by_comparison.get(comparison_id, {}).get("refinement_id"),
                "functional_equivalence_approved": False,
            }
            for comparison_id in sorted(set(comparisons_by_operation[operation_id]))
        ]
        members_by_operation[operation_id] = member
        api_members[operation["canonical_api_id"]].append(member)

    for values in api_members.values():
        values.sort(key=lambda value: (value["exact_path"], value["method"], value["task014_operation_id"]))

    proposals: list[dict[str, Any]] = []
    skipped_groups: list[dict[str, Any]] = []
    proposal_by_api: dict[str, dict[str, Any]] = {}
    for api_id, members in sorted(api_members.items()):
        if len(members) == 1:
            continue
        api = api_by_id[api_id]
        if len(members) > MAX_API_MEMBER_COUNT:
            skipped_groups.append(
                {
                    "canonical_api_id": api_id,
                    "api_name": api.get("identity_name"),
                    "operation_count": len(members),
                    "maximum_member_cap": MAX_API_MEMBER_COUNT,
                    "reason": "OVERSIZED_CANONICAL_API_GROUP_SKIPPED_FOR_MANUAL_SCOPE_REVIEW",
                    "member_operation_ids": [member["task014_operation_id"] for member in members],
                }
            )
            continue
        sufficiency, criteria, basis, positive, counter = _api_assessment(members)
        proposal_id = _stable_id(
            "logical-api-boundary-proposal",
            api_id,
            [member["task014_operation_id"] for member in members],
            RULES_VERSION,
        )
        proposal = {
            "logical_api_proposal_id": proposal_id,
            "boundary_label": f"{api.get('identity_name', 'unlabelled API')} — current-API operation family proposal",
            "proposal_scope": "WITHIN_ONE_CURRENT_CANONICAL_APIC_API",
            "canonical_api_id": api_id,
            "current_api_name": api.get("identity_name"),
            "current_api_version": api.get("api_version"),
            "member_operation_ids": [member["task014_operation_id"] for member in members],
            "direct_member_assertions": [
                {
                    "task014_operation_id": member["task014_operation_id"],
                    "task015_observed_function_id": member["task015_observed_function_id"],
                    "task016_comparison_refs": member["task016_comparison_refs"],
                    "task016_refinement_refs": member["task016_refinement_refs"],
                    "source_provenance": member["source_provenance"],
                    "membership_assertion": (
                        "PROVISIONAL_BOUNDARY_MEMBER"
                        if sufficiency == "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY"
                        else "PARTIAL_BOUNDARY_MEMBER"
                        if sufficiency == "PARTIAL"
                        else "NOT_ASSERTED"
                    ),
                    "criteria": _member_criteria(member, criteria),
                    "relationship_exposure_context": member["relationship_exposure_context"],
                    "contract": _contract_summary(member),
                    "resource": member.get("observed_object"),
                    "actions": _supported_actions(member),
                }
                for member in members
            ],
            "candidate_rubric": criteria,
            "evidence_for": [positive, basis],
            "strongest_counterevidence": [counter],
            "alternative_boundary": "Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.",
            "task016_functional_candidate_refs": sorted(
                {
                    ref
                    for member in members
                    for ref in member["task016_comparison_refs"]
                }
            ),
            "product_plan_subscription_context": {
                "accepted_associations_retained_in_members": True,
                "common_consumer_or_entitlement_inferred": False,
                "product_is_logical_api": False,
            },
            "three_result_axes": {
                "technical_validation": "PASS",
                "evidence_sufficiency": sufficiency,
                "architect_acceptance": "PENDING",
            },
            "functional_equivalence_approved": False,
            "transitive_equivalence_inferred": False,
            "domain_assignment": None,
            "capability_assignment": None,
            "kong_topology": None,
            "production_usage_inferred": False,
            "retirement_decision": None,
        }
        proposals.append(proposal)
        proposal_by_api[api_id] = proposal

    proposals.sort(key=lambda value: value["logical_api_proposal_id"])
    proposal_by_id = {value["logical_api_proposal_id"]: value for value in proposals}
    case_by_operation: dict[str, list[dict[str, Any]]] = defaultdict(list)
    sample_action_overrides: dict[str, set[str]] = defaultdict(set)
    for sample in sample_rows:
        for member in sample["members"]:
            operation_id = member["task014_operation_id"]
            case_by_operation[operation_id].append(sample)
            sample_action_overrides[operation_id].update(member.get("supported_actions", []))

    operation_dispositions: list[dict[str, Any]] = []
    for operation_id, operation in sorted(operation_by_id.items()):
        member = members_by_operation[operation_id]
        api_id = operation["canonical_api_id"]
        proposal = proposal_by_api.get(api_id)
        api_size = len(api_members[api_id])
        if proposal:
            sufficiency = proposal["three_result_axes"]["evidence_sufficiency"]
            disposition = {
                "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY": "PROVISIONAL_BOUNDARY_MEMBER",
                "PARTIAL": "PARTIAL_BOUNDARY_MEMBER",
                "SUPPORTED_SEPARATE": "SEPARATE_BOUNDARY",
                "INSUFFICIENT": "UNFORMED_INSUFFICIENT",
            }[sufficiency]
            reason = proposal["evidence_for"][1]
            proposal_ids = [proposal["logical_api_proposal_id"]]
        elif api_size == 1:
            disposition = "SINGLETON_UNFORMED"
            sufficiency = "INSUFFICIENT"
            reason = "One supported source operation is visible; no conceptual multi-operation boundary is asserted."
            proposal_ids = []
        else:
            disposition = "UNFORMED_INSUFFICIENT"
            sufficiency = "INSUFFICIENT"
            reason = "Oversized canonical API group was not formed as a boundary proposal; operations remain visible."
            proposal_ids = []
        operation_dispositions.append(
            {
                "task014_operation_id": operation_id,
                "task015_observed_function_id": member["task015_observed_function_id"],
                "canonical_api_id": api_id,
                "current_api_name": member["api_name"],
                "current_api_version": member["api_version"],
                "method": member["method"],
                "exact_path": member["exact_path"],
                "primary_disposition": disposition,
                "evidence_sufficiency": sufficiency,
                "reason": reason,
                "logical_api_proposal_ids": proposal_ids,
                "competing_boundary_proposal_ids": [],
                "task016_comparison_refs": member["task016_comparison_refs"],
                "task016_refinement_refs": member["task016_refinement_refs"],
                "task016_candidate_refs": member["task016_candidate_refs"],
                "relationship_exposure_context": member["relationship_exposure_context"],
                "sample_regression_case_ids": sorted(case["expanded_case_id"] for case in case_by_operation[operation_id]),
                "source_provenance": member["source_provenance"],
                "source_variant_fingerprint": member.get("source_variant_fingerprint"),
            }
        )
    disposition_by_operation = {row["task014_operation_id"]: row for row in operation_dispositions}

    operation_intents: list[dict[str, Any]] = []
    for operation_id, member in sorted(members_by_operation.items()):
        actions = sample_action_overrides.get(operation_id) or set(_supported_actions(member))
        provenance = member["source_provenance"]
        for action in sorted(actions) if actions else ["UNRESOLVED"]:
            if operation_id in sample_action_overrides:
                origin = "TASK017_EXPANDED_SAMPLE_SUPPORTED_ACTION"
            elif action == "UNRESOLVED":
                origin = "NO_SUPPORTED_ACTION_SIGNAL"
            else:
                origin = "TASK015_PROVISIONAL_OBSERVED_FUNCTION"
            operation_intents.append(
                {
                    "logical_operation_intent_id": _stable_id(
                        "logical-operation-intent", operation_id, action, RULES_VERSION
                    ),
                    "source_task014_operation_id": operation_id,
                    "task015_observed_function_id": member["task015_observed_function_id"],
                    "action_intent": action,
                    "resource_phrase": member.get("observed_object"),
                    "intent_evidence_status": origin,
                    "sample_case_ids": sorted(case["expanded_case_id"] for case in case_by_operation[operation_id]),
                    "source_pointer": f"{provenance['source_path']}#{provenance['source_pointer']}",
                    "source_sha256": provenance["source_sha256"],
                    "distinct_source_operation_preserved": True,
                    "architect_approved": False,
                }
            )

    api_gaps_by_status = Counter(row["status"] for row in gap_rows)
    task016_unpaired = {
        row["task014_operation_id"]
        for row in catalog_rows
        if not row.get("candidate_membership_ids")
    }
    if len(task016_unpaired) != 1481:
        raise ValueError(f"Expected 1,481 Task 016 unpaired operations, found {len(task016_unpaired)}")
    if len(gap_rows) != 44 or api_gaps_by_status != {
        "REGISTRY_ONLY_NO_OPERATIONS": 36,
        "NO_SUPPORTED_HTTP_PATHS": 5,
        "UNSUPPORTED_PROTOCOL": 3,
    }:
        raise ValueError("Task 015 API-level gap records do not match the accepted baseline.")

    diagnostics: list[dict[str, Any]] = []
    for group in skipped_groups:
        diagnostics.append(
            {
                "diagnostic_type": "OVERSIZED_CANONICAL_API_GROUP_SKIPPED",
                **group,
            }
        )
    candidate_fanout = Counter()
    for member in members_by_operation.values():
        candidate_fanout[member["task014_operation_id"]] = len(member["task016_comparison_refs"])
    diagnostics.extend(
        [
            {
                "diagnostic_type": "BOUNDED_CANDIDATE_GENERATION",
                "all_pairs_search_performed": False,
                "task016_comparison_count": len(comparison_rows),
                "task016_refinement_count": len(refinement_rows),
                "task016_unpaired_operation_count": len(task016_unpaired),
                "maximum_task016_comparison_refs_per_operation": max(candidate_fanout.values(), default=0),
                "per_operation_candidate_cap_inherited": 20,
                "canonical_api_member_cap": MAX_API_MEMBER_COUNT,
                "cross_canonical_api_logical_proposals_created": 0,
                "functional_equivalence_hypotheses_used_as_approved_membership": False,
                "uncovered_business_signals": "Not computed as absence evidence; all source operations remain in the ledger.",
            },
            {
                "diagnostic_type": "API_LEVEL_GAP_COVERAGE",
                "gap_record_count": len(gap_rows),
                "status_counts": dict(sorted(api_gaps_by_status.items())),
                "records_with_zero_supported_http_operations": sum(
                    row["accepted_http_operation_count"] == 0 for row in gap_rows
                ),
                "unsupported_protocol_records_with_accepted_http_operations": sum(
                    row["status"] == "UNSUPPORTED_PROTOCOL" and row["accepted_http_operation_count"] > 0
                    for row in gap_rows
                ),
                "fabricated_http_operation_count": 0,
            },
        ]
    )
    diagnostics.sort(key=lambda value: (value["diagnostic_type"], value.get("api_name", "")))

    evidence_dir = root / "tests/evidence/task-017/full-extraction"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    reviewable_examples: list[dict[str, Any]] = []
    for sample in sorted(sample_rows, key=lambda value: value["expanded_case_id"]):
        reviewable_examples.append(
            {
                "example_type": "FROZEN_TASK017_REGRESSION_CASE",
                "example_id": sample["expanded_case_id"],
                "label": sample["candidate_boundary_label"],
                "frozen_sample_evidence_sufficiency": sample["result_axes"]["evidence_sufficiency"],
                "architect_acceptance": "PENDING",
                "candidate_rubric": sample["candidate_rubric"],
                "evidence_for": sample["evidence_for"],
                "evidence_against": sample["evidence_against"],
                "alternative_boundary": sample["alternative_boundary"],
                "members": [
                    _sample_safe_member(
                        member,
                        disposition_by_operation[member["task014_operation_id"]],
                    )
                    for member in sample["members"]
                ],
                "full_estate_reassessment": (
                    "PRIMARY_WITHIN_API_PROPOSAL"
                    if len({member["canonical_api_id"] for member in sample["members"]}) == 1
                    and sample["members"][0]["canonical_api_id"] in proposal_by_api
                    else "CROSS_API_NOT_FORMED_OR_NO_MATCHING_PROPOSAL"
                ),
                "functional_equivalence_approved": False,
                "production_usage_inferred": False,
            }
        )

    regression_api_ids = {
        member["canonical_api_id"]
        for sample in sample_rows
        for member in sample["members"]
    }
    added_proposals = 0
    example_proposals = sorted(
        proposals,
        key=lambda value: (
            0 if value["three_result_axes"]["evidence_sufficiency"] == "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY" else 1,
            value["current_api_name"] or "",
            value["logical_api_proposal_id"],
        ),
    )
    for proposal in example_proposals:
        if added_proposals == 4:
            break
        if proposal["canonical_api_id"] in regression_api_ids:
            continue
        if proposal["three_result_axes"]["evidence_sufficiency"] not in {
            "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY",
            "PARTIAL",
        }:
            continue
        proposal_members = [
            members_by_operation[operation_id]
            for operation_id in proposal["member_operation_ids"]
        ]
        reviewable_examples.append(
            {
                "example_type": "FULL_ESTATE_CANONICAL_API_PROPOSAL",
                "example_id": proposal["logical_api_proposal_id"],
                "label": proposal["boundary_label"],
                "evidence_sufficiency": proposal["three_result_axes"]["evidence_sufficiency"],
                "architect_acceptance": "PENDING",
                "candidate_rubric": proposal["candidate_rubric"],
                "evidence_for": proposal["evidence_for"],
                "evidence_against": proposal["strongest_counterevidence"],
                "alternative_boundary": proposal["alternative_boundary"],
                "members": [
                    _sample_safe_member(
                        member,
                        disposition_by_operation[member["task014_operation_id"]],
                    )
                    for member in proposal_members
                ],
                "functional_equivalence_approved": False,
                "production_usage_inferred": False,
            }
        )
        added_proposals += 1
    if not 30 <= len(reviewable_examples) <= 50:
        raise ValueError(f"Reviewable examples must contain 30-50 records; got {len(reviewable_examples)}")

    regression_rows: list[dict[str, Any]] = []
    for sample in sorted(sample_rows, key=lambda value: value["expanded_case_id"]):
        sample_api_ids = {member["canonical_api_id"] for member in sample["members"]}
        comparable = len(sample_api_ids) == 1 and next(iter(sample_api_ids)) in proposal_by_api
        proposal = proposal_by_api.get(next(iter(sample_api_ids))) if comparable else None
        current_sufficiency = (
            proposal["three_result_axes"]["evidence_sufficiency"] if proposal else "NOT_REASSESSED"
        )
        original_status = sample["result_axes"]["evidence_sufficiency"]
        if not comparable:
            change_state = "NOT_COMPARABLE_OR_NO_PRIMARY_PROPOSAL"
            rationale = (
                "The frozen sample spans canonical APIs or the full pass skipped an oversized group; "
                "the sample verdict remains preserved and is not silently converted into primary membership."
            )
        elif current_sufficiency == original_status:
            change_state = "UNCHANGED"
            rationale = "The current within-API assessment has the same evidence-sufficiency result as the frozen sample."
        else:
            change_state = "STATUS_DIFFERENCE_REQUIRES_REVIEW"
            rationale = (
                "The complete current-API family was assessed rather than only the sampled subset. "
                f"Full-estate counterevidence: {proposal['strongest_counterevidence'][0]} "
                "Preserve both statuses pending architectural review."
            )
        regression_rows.append(
            {
                "expanded_case_id": sample["expanded_case_id"],
                "label": sample["candidate_boundary_label"],
                "frozen_sample_sufficiency": original_status,
                "full_estate_primary_sufficiency": current_sufficiency,
                "full_estate_proposal_id": proposal["logical_api_proposal_id"] if proposal else None,
                "change_state": change_state,
                "rationale": rationale,
                "member_operation_ids": sorted(
                    member["task014_operation_id"] for member in sample["members"]
                ),
                "architect_acceptance": "PENDING",
            }
        )

    sample_regression_by_label = {
        value["candidate_boundary_label"]: value for value in sample_rows
    }
    sc_request = sample_regression_by_label.get("SC Request Workflow")
    if not sc_request:
        raise ValueError("The frozen SC Request regression case is missing.")
    sc_operations = {
        member["task014_operation_id"]: member["supported_actions"]
        for member in sc_request["members"]
    }
    if (
        len(sc_operations) != 2
        or sorted(action for actions in sc_operations.values() for action in actions)
        != ["approve", "cancel", "reject"]
        or sc_request["result_axes"]["evidence_sufficiency"] != "PARTIAL"
    ):
        raise ValueError("SC Request must retain two source operations, three intents, and PARTIAL evidence.")

    status_counts = Counter(value["three_result_axes"]["evidence_sufficiency"] for value in proposals)
    disposition_counts = Counter(value["primary_disposition"] for value in operation_dispositions)
    sample_outcome_counts = Counter(value["change_state"] for value in regression_rows)
    api_count_distribution = Counter(len(value) for value in api_members.values())
    gap_api_inventory = [
        {
            "api_gap_record_id": row["api_gap_record_id"],
            "canonical_api_id": row["canonical_api_id"],
            "status": row["status"],
            "accepted_http_operation_count": row["accepted_http_operation_count"],
            "source_sha256": (
                row["source_provenance"]["source_sha256"] if row.get("source_provenance") else None
            ),
            "source_pointer": (
                f"{row['source_provenance']['source_path']}#{row['source_provenance']['source_pointer']}"
                if row.get("source_provenance")
                else None
            ),
            "source_provenance_status": (
                "PRESENT" if row.get("source_provenance") else "NOT_EVIDENCED_IN_ACCEPTED_GAP_RECORD"
            ),
            "fabricated_operation_count": 0,
        }
        for row in sorted(gap_rows, key=lambda value: value["api_gap_record_id"])
    ]

    coverage = {
        "scope": "TASK017_FULL_PROVISIONAL_LOGICAL_API_FORMATION",
        "task014_supported_http_operations_expected": 2414,
        "task014_supported_http_operations_accounted": len(operation_dispositions),
        "task014_operation_unique_count": len({row["task014_operation_id"] for row in operation_dispositions}),
        "task015_observed_function_rows": len(observed_rows),
        "task015_one_to_one_reconciliation": len(operation_by_id) == len(observed_by_operation) == 2414,
        "task016_previous_unpaired_operations_expected": 1481,
        "task016_previous_unpaired_operations_retained": sum(
            row["task014_operation_id"] in task016_unpaired for row in operation_dispositions
        ),
        "api_inventory_count": len(api_rows),
        "canonical_api_operation_size_distribution": {
            str(key): value for key, value in sorted(api_count_distribution.items())
        },
        "primary_disposition_counts": dict(sorted(disposition_counts.items())),
        "proposal_evidence_sufficiency_counts": dict(sorted(status_counts.items())),
        "proposal_count": len(proposals),
        "operations_with_primary_proposal": sum(bool(row["logical_api_proposal_ids"]) for row in operation_dispositions),
        "operations_with_competing_primary_proposals": 0,
        "cross_api_functional_candidate_links_retained": sum(bool(row["task016_comparison_refs"]) for row in operation_dispositions),
        "task015_api_level_gap_record_count": len(gap_api_inventory),
        "task015_api_level_gap_status_counts": dict(sorted(api_gaps_by_status.items())),
        "api_level_gap_inventory": gap_api_inventory,
        "registry_only_no_operations": api_gaps_by_status["REGISTRY_ONLY_NO_OPERATIONS"],
        "source_backed_no_supported_http_paths": api_gaps_by_status["NO_SUPPORTED_HTTP_PATHS"],
        "unsupported_protocol_records": api_gaps_by_status["UNSUPPORTED_PROTOCOL"],
        "fabricated_http_operation_count": 0,
        "transitive_equivalence_inferred": False,
        "functional_equivalence_approved": False,
        "product_as_logical_api_inferred": False,
        "production_usage_inferred": False,
        "architect_acceptance_count": 0,
        "task017_expanded_sample_case_count": len(sample_rows),
        "task017_expanded_sample_crosscheck_outcomes": dict(sorted(sample_outcome_counts.items())),
        "sc_request": {
            "source_operation_count": len(sc_operations),
            "logical_action_intents": sorted(action for actions in sc_operations.values() for action in actions),
            "frozen_sufficiency": sc_request["result_axes"]["evidence_sufficiency"],
            "architect_acceptance": "PENDING",
            "cross_api_primary_boundary_formed": False,
        },
    }
    coverage_path = evidence_dir / "estate_coverage_and_disposition.json"
    _write_json(coverage_path, coverage)
    _write_jsonl(evidence_dir / "reviewable_boundary_examples.jsonl", reviewable_examples)
    _write_jsonl(evidence_dir / "case_regression_crosscheck.jsonl", regression_rows)

    review_queue = []
    reason_counts = Counter()
    for proposal in proposals:
        sufficiency = proposal["three_result_axes"]["evidence_sufficiency"]
        reason = (
            "RESOURCE_ACTION_PATH_COHESION_SUPPORTED_BUT_ARCHITECTURE_PENDING"
            if sufficiency == "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY"
            else "PARTIAL_DIRECT_COHESION_OR_CONSUMER_BACKEND_GAPS"
            if sufficiency == "PARTIAL"
            else "INSUFFICIENT_OR_CONTRADICTED_RESOURCE_ACTION_EVIDENCE"
        )
        priority = "HIGH" if sufficiency in {"PARTIAL", "SUPPORTED_SEPARATE"} else "MEDIUM" if sufficiency == "INSUFFICIENT" else "LOW"
        reason_counts[reason] += 1
        review_queue.append(
            {
                "review_item_id": _stable_id("task017-full-review", proposal["logical_api_proposal_id"]),
                "priority": priority,
                "canonical_api_id": proposal["canonical_api_id"],
                "current_api_name": proposal["current_api_name"],
                "logical_api_proposal_id": proposal["logical_api_proposal_id"],
                "evidence_sufficiency": sufficiency,
                "architect_acceptance": "PENDING",
                "primary_failure_or_decision_reason": reason,
                "specific_question": proposal["strongest_counterevidence"][0],
                "member_count": len(proposal["member_operation_ids"]),
            }
        )
    for group in skipped_groups:
        reason = "OVERSIZED_GROUP_REQUIRES_BOUNDED_SUBFAMILY_REVIEW"
        reason_counts[reason] += 1
        review_queue.append(
            {
                "review_item_id": _stable_id("task017-full-review-oversized", group["canonical_api_id"]),
                "priority": "HIGH",
                "canonical_api_id": group["canonical_api_id"],
                "current_api_name": group["api_name"],
                "logical_api_proposal_id": None,
                "evidence_sufficiency": "INSUFFICIENT",
                "architect_acceptance": "PENDING",
                "primary_failure_or_decision_reason": reason,
                "specific_question": "Which directly evidenced resource/workflow subfamilies, if any, should be assessed separately?",
                "member_count": group["operation_count"],
            }
        )
    for gap in gap_api_inventory:
        if gap["status"] in {"REGISTRY_ONLY_NO_OPERATIONS", "NO_SUPPORTED_HTTP_PATHS"}:
            reason = gap["status"]
            reason_counts[reason] += 1
            review_queue.append(
                {
                    "review_item_id": _stable_id("task017-full-review-gap", gap["api_gap_record_id"]),
                    "priority": "LOW",
                    "canonical_api_id": gap["canonical_api_id"],
                    "current_api_name": None,
                    "logical_api_proposal_id": None,
                    "evidence_sufficiency": "INSUFFICIENT",
                    "architect_acceptance": "PENDING",
                    "primary_failure_or_decision_reason": reason,
                    "specific_question": "Does authoritative API evidence exist beyond the current accepted HTTP operation inventory?",
                    "member_count": 0,
                }
            )
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    review_queue.sort(
        key=lambda value: (
            priority_order[value["priority"]],
            value["primary_failure_or_decision_reason"],
            value["current_api_name"] or "",
            value["review_item_id"],
        )
    )

    _write_jsonl(root / OUTPUTS["operation_disposition"], operation_dispositions)
    _write_jsonl(root / OUTPUTS["proposals"], proposals)
    _write_jsonl(root / OUTPUTS["operation_intents"], operation_intents)
    _write_jsonl(root / OUTPUTS["review_queue"], review_queue)
    _write_jsonl(root / OUTPUTS["diagnostics"], diagnostics)

    input_fingerprints = _cache_fingerprints(root, inputs)
    expanded_manifest = json.loads(inputs["task017_expanded_manifest"].read_text(encoding="utf-8"))
    if expanded_manifest["outputs"]["register"]["sha256"] != input_fingerprints["task017_expanded_register"]["sha256"]:
        raise ValueError("Task 017 expanded-sample cache fingerprint mismatch.")
    task016_manifest = json.loads(inputs["task016_manifest"].read_text(encoding="utf-8"))
    expected_pairs = task016_manifest["outputs"]["candidate_pairs"]["sha256"]
    if expected_pairs != input_fingerprints["task016_comparisons"]["sha256"]:
        raise ValueError("Task 016 candidate cache fingerprint mismatch.")
    expected_relationships = task016_manifest["inputs"]["relationships"]["sha256"]
    if expected_relationships != input_fingerprints["relationships"]["sha256"]:
        raise ValueError("Task 016 relationship cache fingerprint mismatch.")

    manifest = {
        "rules_version": RULES_VERSION,
        "scope": "FULL_ESTATE_PROVISIONAL_LOGICAL_API_FORMATION",
        "frozen_inputs_modified": False,
        "staging_read": False,
        "staging_modified": False,
        "all_pairs_search_performed": False,
        "maximum_canonical_api_candidate_member_count": MAX_API_MEMBER_COUNT,
        "architect_acceptance_count": 0,
        "full_catalog_fit_as_provisional_task018_input": "CONDITIONALLY_FIT_AFTER_ENTERPRISE_ARCHITECT_REVIEW",
        "outputs": {},
        "summary": {
            "operation_count": len(operation_dispositions),
            "unique_task014_operation_count": len({row["task014_operation_id"] for row in operation_dispositions}),
            "task015_observed_function_count": len(observed_rows),
            "canonical_api_count": len(api_rows),
            "proposal_count": len(proposals),
            "proposal_evidence_sufficiency_counts": dict(sorted(status_counts.items())),
            "primary_disposition_counts": dict(sorted(disposition_counts.items())),
            "task016_unpaired_operation_count": len(task016_unpaired),
            "task016_comparison_count": len(comparison_rows),
            "task016_refinement_count": len(refinement_rows),
            "task017_expanded_regression_case_count": len(sample_rows),
            "reviewable_example_count": len(reviewable_examples),
            "api_level_gap_counts": dict(sorted(api_gaps_by_status.items())),
            "oversized_candidate_group_count": len(skipped_groups),
            "review_queue_count": len(review_queue),
            "review_reason_counts": dict(sorted(reason_counts.items())),
            "sample_regression_crosscheck_counts": dict(sorted(sample_outcome_counts.items())),
        },
        "inputs": input_fingerprints,
        "output_paths": {key: value.as_posix() for key, value in OUTPUTS.items()},
        "evidence_paths": [
            "tests/evidence/task-017/full-extraction/estate_coverage_and_disposition.json",
            "tests/evidence/task-017/full-extraction/reviewable_boundary_examples.jsonl",
            "tests/evidence/task-017/full-extraction/case_regression_crosscheck.jsonl",
        ],
    }
    for name, path in OUTPUTS.items():
        if name == "manifest":
            continue
        output_path = root / path
        line_count = sum(1 for _ in output_path.open(encoding="utf-8"))
        manifest["outputs"][name] = _fingerprint(output_path, root, line_count)
    manifest["outputs"]["estate_coverage_and_disposition"] = _fingerprint(coverage_path, root)
    manifest["outputs"]["reviewable_boundary_examples"] = _fingerprint(
        evidence_dir / "reviewable_boundary_examples.jsonl", root, len(reviewable_examples)
    )
    manifest["outputs"]["case_regression_crosscheck"] = _fingerprint(
        evidence_dir / "case_regression_crosscheck.jsonl", root, len(regression_rows)
    )
    existing_manifest_path = root / OUTPUTS["manifest"]
    if existing_manifest_path.exists():
        existing_manifest = json.loads(existing_manifest_path.read_text(encoding="utf-8"))
        committed_evidence = existing_manifest.get("outputs", {}).get("committed_evidence", {})
        if committed_evidence and all(
            (root / details["path"]).exists()
            and hashlib.sha256((root / details["path"]).read_bytes()).hexdigest() == details["sha256"]
            for details in committed_evidence.values()
        ):
            manifest["outputs"]["committed_evidence"] = committed_evidence
            if "technical_validation" in existing_manifest:
                manifest["technical_validation"] = existing_manifest["technical_validation"]
    _write_json(root / OUTPUTS["manifest"], manifest)

    return {
        "manifest": manifest,
        "coverage": coverage,
        "proposals": proposals,
        "operation_dispositions": operation_dispositions,
        "operation_intents": operation_intents,
        "review_queue": review_queue,
        "diagnostics": diagnostics,
        "reviewable_examples": reviewable_examples,
        "regression_rows": regression_rows,
    }
