"""Deterministic, bounded Task 017 logical-API formation mock.

This consumes frozen Task 014--016 indexes.  It deliberately does not scan the
estate, infer transitive equivalence, or read raw staging documents.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from logical_function.refinement import _backend_projection, _semantic_evidence


RULES_VERSION = "task017-representative-logical-api-mock-v1"
CASE_OUTPUT = Path("indexes/task017_mock_logical_api_candidates.jsonl")
QUEUE_OUTPUT = Path("indexes/task017_mock_review_queue.jsonl")
MANIFEST_OUTPUT = Path("indexes/task017_mock_manifest.json")


PAIR_CASES = (
    ("training-disclosure-workflow", "Establishment Training Disclosure", "submitestablishmenttrainingsdisclosure", "updateestablishmenttrainingsdisclosure", "COHESIVE_LOGICAL_API_CANDIDATE", ["Same evidenced training-disclosure object with distinct submit and update actions."], ["Distinct actions are not functionally equivalent and must remain separate logical operations."]),
    ("seasonal-visa-search-variants", "Seasonal Visa Request Search", "searchseasonalvisarequests", "searchseasonalvisarequests-v2", "PARTIAL_OR_VARIANT_BOUNDARY_REVIEW", ["Task 016 records a possible same behavior hypothesis across versioned exposures."], ["Material request/response differences and consumer/product context must be reviewed before choosing a boundary."]),
    ("employment-status-enquiry", "Employment Status Enquiry", "mcsemploymentstatusenquiry_querycenter", "mcsemploymentstatusenquiry", "INSUFFICIENT_EVIDENCE_TO_FORM", ["Names and provisional objects suggest a possible enquiry boundary."], ["Task 016 semantic evidence and backend-operation semantics are insufficient."]),
    ("visa-cancellation-naming-variant", "Visa Cancellation", "updateworkerdata", "cancelvisa", "PARTIAL_OR_VARIANT_BOUNDARY_REVIEW", ["Task 016 found a possible same-behavior hypothesis despite different API names and paths."], ["Naming divergence and exposure/contract context prevent collapse or substitution."]),
    ("appointment-status-shared-path-control", "Appointment Status Workflow", "updateappointmentstatustip", "updateappointmentstatus", "INSUFFICIENT_EVIDENCE_TO_FORM", ["The compared operations share structural and routing signals."], ["Task 016 found conflicting action semantics; a shared path, schema, or backend is not cohesion proof."]),
    ("wps-wrapper-structural-control", "WPS Certificate Retrieval", "findwpscertificatesapiwrapper", "ajeerfindwpscertificateapiwrapper", "INSUFFICIENT_EVIDENCE_TO_FORM", ["The wrappers share an object token and structurally equal compared shapes."], ["Only one side has a documented action; generic wrapper and backend similarity cannot establish a boundary."]),
    ("ambiguous-root-test-control", "Unidentified Root Test Operations", "p2htip_testapi2", "p2htip_testapi_ratelimit_dynamicvalue", "INSUFFICIENT_EVIDENCE_TO_FORM", [], ["Root test endpoints lack sufficient business resource and behavioral evidence."]),
)


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _id(prefix: str, *parts: Any) -> str:
    return f"{prefix}:sha256:{_hash(parts)}"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, path)


def _write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text("".join(json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n" for v in values), encoding="utf-8")
    os.replace(temporary, path)


def _fingerprint(path: Path, root: Path, count: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    if count is not None:
        value["record_count"] = count
    return value


def _member(operation_id: str, operations: dict[str, dict[str, Any]], observed: dict[str, dict[str, Any]], apis: dict[str, dict[str, Any]], resolution: dict[str, dict[str, Any]], graph: dict[str, list[dict[str, Any]]], pair_ref: dict[str, Any] | None = None) -> dict[str, Any]:
    operation = operations[operation_id]
    observation = observed[operation_id]
    api = apis[operation["canonical_api_id"]]
    semantic = _semantic_evidence(observation, operation)
    context = api["as_is_product_plan_connections"]
    return {
        "canonical_api_id": operation["canonical_api_id"],
        "api_name": observation["parent_api"].get("identity_name"),
        "api_version": api.get("api_version"),
        "task014_operation_id": operation_id,
        "task015_observed_function_id": observation["observed_function_id"],
        "task016_comparison_refs": [pair_ref["prior_comparison_id"]] if pair_ref else [],
        "task016_refinement_refs": [pair_ref["refinement_id"]] if pair_ref else [],
        "method": operation["method"],
        "exact_path": operation["exact_path"],
        "normalized_path": operation["contract"]["normalized_path_shape"],
        "source_provenance": operation["source_provenance"],
        "source_variant_fingerprint": observation["source_facts"]["source_variant_fingerprint"],
        "observed_action": semantic["task015_provisional_action"],
        "observed_object": semantic["task015_provisional_object"],
        "supported_actions": semantic["supported_action_categories"],
        "semantic_support": semantic["action_support"],
        "interpretation_status": semantic["task015_interpretation_status"],
        "request_contract": operation["contract"]["request"],
        "response_contract": operation["contract"]["responses"],
        "security_context": operation["contract"]["auth"],
        "exposure_context": operation["contract"]["exposure"],
        "backend_context": _backend_projection(operation, resolution, graph),
        "as_is_product_plan_context": context,
        "product_is_logical_api": False,
        "operation_consumption_proven": False,
        "runtime_activity_proven": False,
    }


def _logical_operations(case_id: str, members: list[dict[str, Any]], overrides: dict[str, list[str]] | None = None) -> list[dict[str, Any]]:
    values = []
    for member in members:
        actions = (overrides or {}).get(member["task014_operation_id"], member["supported_actions"] or ([member["observed_action"]] if member["observed_action"] else []))
        if not actions:
            actions = ["UNRESOLVED"]
        for action in actions:
            values.append({
                "logical_operation_id": _id("logical-operation-proposal", case_id, member["task014_operation_id"], action),
                "action": action,
                "object_or_intent": member["observed_object"] or "UNRESOLVED",
                "source_member_operation_id": member["task014_operation_id"],
                "distinct_operation_preserved": True,
                "architect_approved": False,
            })
    return sorted(values, key=lambda v: v["logical_operation_id"])


def _case(key: str, label: str, members: list[dict[str, Any]], status: str, positive: list[str], negative: list[str], *, pair: dict[str, Any] | None = None, action_overrides: dict[str, list[str]] | None = None, alternatives: list[str] | None = None) -> dict[str, Any]:
    member_ids = sorted(v["task014_operation_id"] for v in members)
    case_id = _id("logical-api-boundary-case", key, member_ids, RULES_VERSION)
    formation_asserted = status in {"COHESIVE_LOGICAL_API_CANDIDATE", "PARTIAL_OR_VARIANT_BOUNDARY_REVIEW"}
    return {
        "boundary_case_id": case_id,
        "logical_api_candidate_id": _id("logical-api-proposal", key, member_ids),
        "provisional_business_neutral_label": label,
        "rules_version": RULES_VERSION,
        "disposition": status,
        "proposal_status": "REVIEW_REQUIRED",
        "formation_asserted": formation_asserted,
        "candidate_members": members,
        "membership_graph": [{
            "membership_assertion_id": _id("logical-api-membership-proposal", case_id, v["task014_operation_id"]),
            "logical_api_candidate_id": _id("logical-api-proposal", key, member_ids),
            "member_operation_id": v["task014_operation_id"],
            "assertion_status": "PROVISIONAL" if formation_asserted else "NOT_ASSERTED_NONFORMATION_CASE",
        } for v in members],
        "intended_logical_operations": _logical_operations(case_id, members, action_overrides),
        "logical_api_cohesion": {"relation_type": "LOGICAL_API_COHESION", "positive_evidence": positive, "reasons_not_to_group": negative, "status": status},
        "functional_equivalence": {
            "relation_type": "FUNCTIONAL_EQUIVALENCE_CANDIDATE",
            "task016_comparison_id": pair["prior_comparison_id"] if pair else None,
            "task016_refinement_id": pair["refinement_id"] if pair else None,
            "task016_refinement_verdict": pair["refinement_verdict"] if pair else "NOT_A_TASK016_PAIR",
            "equivalence_approved": False,
            "member_ids_collapsed": False,
        },
        "contract_compatibility": pair["contract_compatibility_context"] if pair else "MEMBER_CONTRACTS_PRESERVED_NOT_REDUCED_TO_EQUIVALENCE",
        "boundary_alternatives": alternatives or ["Keep each current canonical API as a separate exposure boundary pending review."],
        "transitive_equivalence_inferred": False,
        "unresolved_members_contaminate_group_certainty": False,
        "migration_safety": "NOT_ASSESSED_OR_AUTHORIZED",
        "domain_assignment": None,
        "capability_assignment": None,
        "kong_topology": None,
        "retirement_decision": None,
        "runtime_usage_inferred": False,
        "architect_approval": "PENDING",
    }


def build_mock(root: Path, *, case_path: Path | None = None, queue_path: Path | None = None, manifest_path: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    case_path = case_path or root / CASE_OUTPUT
    queue_path = queue_path or root / QUEUE_OUTPUT
    manifest_path = manifest_path or root / MANIFEST_OUTPUT
    inputs = {
        "apis": root / "indexes/semantic_api_inventory.jsonl",
        "operations": root / "indexes/semantic_operation_inventory.jsonl",
        "observed": root / "indexes/observed_function_inventory.jsonl",
        "task016_pairs": root / "indexes/task016_semantic_refinement_pairs.jsonl",
        "task016_focused": root / "indexes/task016_semantic_refinement_focused_cases.jsonl",
        "backend_resolution": root / "indexes/backend_target_resolution.jsonl",
        "codegraph_dependency_edges": root / "indexes/codegraph_dependency_edges.jsonl",
        "implementation": Path(__file__).resolve(),
    }
    api_values = _jsonl(inputs["apis"])
    operation_values = _jsonl(inputs["operations"])
    observed_values = _jsonl(inputs["observed"])
    refined = _jsonl(inputs["task016_pairs"])
    focused = _jsonl(inputs["task016_focused"])
    if len(api_values) != 2036 or len(operation_values) != 2414 or len(refined) != 1170:
        raise ValueError("Frozen Task 014--016 inventory reconciliation mismatch")
    operations = {v["semantic_operation_inventory_id"]: v for v in operation_values}
    observed = {v["task014_operation_record_id"]: v for v in observed_values}
    apis = {v["canonical_api_id"]: v for v in api_values}
    resolution = {v["target_observation_id"]: v for v in _jsonl(inputs["backend_resolution"])}
    graph: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in _jsonl(inputs["codegraph_dependency_edges"]):
        graph[edge["source_canonical_identity_record_id"]].append(edge)
    pair_lookup = {tuple(sorted((v["left"]["api_name"], v["right"]["api_name"]))): v for v in refined}

    cases = []
    for key, label, left_name, right_name, status, positive, negative in PAIR_CASES:
        pair = pair_lookup[(left_name, right_name) if left_name < right_name else (right_name, left_name)]
        members = [_member(pair[side]["task014_operation_id"], operations, observed, apis, resolution, graph, pair) for side in ("left", "right")]
        cases.append(_case(key, label, members, status, positive, negative, pair=pair))

    audit = next(v for v in focused if v["case_type"] == "ACTION_DISAMBIGUATION_CONTROL_NOT_EXISTING_PAIR")
    sc_members = [_member(audit[side]["task014_operation_id"], operations, observed, apis, resolution, graph) for side in ("left", "right")]
    approve_id = next(v["task014_operation_id"] for v in sc_members if v["api_name"] == "approverejectscrequest")
    cases.append(_case("sc-request-workflow", "SC Request Workflow", sc_members, "COHESIVE_LOGICAL_API_CANDIDATE", ["Source description explicitly bundles approve/reject and separately documents cancel on the same SC request resource."], ["Approve, reject, and cancel are distinct actions; the bundled endpoint does not make them duplicates."], action_overrides={approve_id: ["approve", "reject"]}))

    bulk_api = next(v for v in api_values if v["identity_name"] == "ajeer-bulk-contracts")
    bulk_members = [_member(v, operations, observed, apis, resolution, graph) for v in bulk_api["operation_record_ids"]]
    cases.append(_case("bulk-contract-single-api", "Bulk Contract Workflow", bulk_members, "PARTIAL_OR_VARIANT_BOUNDARY_REVIEW", ["One accepted canonical API exposes collection, item retrieval, update, and cancellation paths around contracts."], ["The collection-root operation is unresolved and configured backend evidence is API-shared, not operation semantics."], alternatives=["Keep the current single canonical API boundary.", "Review whether collection and item workflow exposures require separate conceptual boundaries."]))

    technical_ids = ["semantic-operation-v2:sha256:b3ee501e32646389de05df839e4ee3414c9bda3a07c0fa217eedd82a2899e440", "semantic-operation-v2:sha256:c70a1c57f37d1c71fcad1945b04df77ba4f449840201c43a051f8a53ab20b630"]
    technical_members = [_member(v, operations, observed, apis, resolution, graph) for v in technical_ids]
    cases.append(_case("technical-health-token-separation", "Technical Health and Token Boundary Control", technical_members, "SEPARATE_LOGICAL_APIS_SUPPORTED", [], ["A system health check and security token issuance have distinct technical intents, contracts, and security context."], alternatives=["Retain separate health and token conceptual boundaries; no consolidation is proposed."]))

    cases.sort(key=lambda v: v["boundary_case_id"])
    if len(cases) != 10:
        raise ValueError("Representative mock must contain exactly ten bounded cases")
    queue = []
    for case in cases:
        if case["disposition"] == "COHESIVE_LOGICAL_API_CANDIDATE":
            question = "Does the proposed resource/workflow boundary reflect the intended consumer-facing API while preserving every distinct action?"
        elif case["disposition"] == "PARTIAL_OR_VARIANT_BOUNDARY_REVIEW":
            question = "Which exposure or version differences are intentional consumer contracts versus candidates for one conceptual boundary?"
        elif case["disposition"] == "SEPARATE_LOGICAL_APIS_SUPPORTED":
            question = "Confirm that the technical intents remain separate conceptual APIs."
        else:
            question = "What targeted business-owner, consumer, or operation-routing evidence would make formation decidable?"
        queue.append({
            "review_item_id": _id("task017-review-item", case["boundary_case_id"]),
            "boundary_case_id": case["boundary_case_id"],
            "priority": "DECISIVE_SAMPLE_REVIEW",
            "question": question,
            "requested_evidence": ["Business-owner validation", "Known consumer/version intent", "Operation-level routing evidence when material"],
            "review_all_task016_pairs_required": False,
            "status": "OPEN",
        })
    _write_jsonl(case_path, cases)
    _write_jsonl(queue_path, queue)
    dispositions = dict(sorted(Counter(v["disposition"] for v in cases).items()))
    member_ids = [m["task014_operation_id"] for case in cases for m in case["candidate_members"]]
    manifest = {
        "rules_version": RULES_VERSION,
        "summary": {"case_count": len(cases), "membership_occurrence_count": len(member_ids), "unique_member_operation_count": len(set(member_ids)), "review_item_count": len(queue), "dispositions": dispositions},
        "scope": "REPRESENTATIVE_MOCK_ONLY",
        "full_estate_formation_performed": False,
        "all_task016_pairs_reviewed": False,
        "staging_read_for_task017": False,
        "staging_modified": False,
        "transitive_equivalence_used": False,
        "domain_or_capability_assigned": False,
        "kong_or_retirement_decision_made": False,
        "inputs": {name: _fingerprint(path, root) for name, path in inputs.items()},
        "outputs": {"cases": _fingerprint(case_path, root, len(cases)), "review_queue": _fingerprint(queue_path, root, len(queue))},
    }
    _write_json(manifest_path, manifest)
    return {"cases": cases, "review_queue": queue, "manifest": manifest}
