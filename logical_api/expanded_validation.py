"""Task 017 additive expanded logical-API boundary validation sample."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from logical_api.mock import _member


RULES_VERSION = "task017-expanded-boundary-validation-v1"
REGISTER_OUTPUT = Path("indexes/task017_expanded_validation_register.jsonl")
MANIFEST_OUTPUT = Path("indexes/task017_expanded_validation_manifest.json")


PAIR_SPECS = (
    ("2711bea7", "User Management Exposure Ambiguity", ["NAMED_LEAD", "NEGATIVE_CONTROL", "SHARED_SCHEMA"], "NOT_EVIDENCED", "INSUFFICIENT", "Generic URI paths and equal shapes do not identify a resource.", "Keep privilege and general user-management exposures separate until resource and authorization semantics are known."),
    ("6ff6b96a", "Commercial Registration Information", ["NAMED_LEAD", "DIVERGENT_EXPOSURE", "PRODUCT_CONTEXT"], "SUPPORTED", "PARTIAL", "Retrieve/basic-CR signals align, but paths request different identifiers and date ranges.", "Separate basic-CR lookup from change-history retrieval."),
    ("86981ba3", "MOMRA Verification Boundary", ["NAMED_LEAD", "NEGATIVE_CONTROL", "SHARED_SCHEMA"], "CONTRADICTED", "INSUFFICIENT", "Equal shapes coexist with violated-establishment versus certificate-validity resource signals.", "Separate establishment-violation and certificate-validity APIs."),
    ("c18c9ab3", "Category Lookup Boundary", ["NAMED_LEAD", "NEGATIVE_CONTROL", "SHARED_SCHEMA"], "NOT_EVIDENCED", "INSUFFICIENT", "The same path and shapes lack supported action/object semantics.", "Retain separate exposures until category ownership and consumers are evidenced."),
    ("46722a6f", "Authentication Indicator Variant", ["NAMED_LEAD", "VERSION_VARIANT", "DIVERGENT_EXPOSURE", "PRODUCT_CONTEXT"], "CONTRADICTED", "INSUFFICIENT", "Names imply authentication while inherited semantic evidence says refunded; the contradiction blocks formation.", "Treat employee and contract indicators as separate until authoritative semantics resolve the copied-description signal."),
    ("7acc6ac9", "Conversation Deletion Variant", ["NAMED_LEAD", "VERSION_VARIANT", "DISAGREEMENT", "SHARED_SCHEMA"], "SUPPORTED", "INSUFFICIENT", "Both DELETE conversation paths align structurally, but supported action evidence is absent.", "Keep streaming versions separate pending consumer and release intent."),
    ("0e0ce4df", "Saudi Certificate Lifecycle", ["DIFFERENT_ACTIONS", "DISAGREEMENT", "BACKEND_UNCERTAINTY"], "SUPPORTED", "INSUFFICIENT", "Validate and retrieve are distinct supported actions on Saudi certificates.", "Separate certificate validation from certificate retrieval."),
    ("fb0f43f8", "Saudi Certificate Submission and Creation", ["DIFFERENT_ACTIONS", "DISAGREEMENT"], "SUPPORTED", "INSUFFICIENT", "Submit and create are distinct supported actions on Saudi certificates.", "Separate submission workflow from certificate creation."),
    ("b6b0a545", "Individual Transfer Request Search", ["DIFFERENT_ACTIONS", "DIVERGENT_EXPOSURE", "DISAGREEMENT"], "SUPPORTED", "INSUFFICIENT", "Search/retrieve wording aligns to individual transfer requests but methods and contracts differ.", "Separate query experiences by consumer contract."),
    ("ca53c026", "Employment Contract Update", ["DIFFERENT_ACTIONS", "VERSION_VARIANT", "DISAGREEMENT"], "SUPPORTED", "INSUFFICIENT", "Update versus create evidence conflicts on an employment-contract object.", "Separate creation and update APIs until copied or contradictory metadata is resolved."),
    ("64f43b1c", "External Contract Cancellation", ["DIFFERENT_ACTIONS", "DISAGREEMENT", "SHARED_PATH"], "SUPPORTED", "INSUFFICIENT", "Create versus cancel evidence conflicts despite the same cancellation path.", "Keep the exposures separate until authoritative behavior confirms cancellation."),
    ("40ff3500", "Establishment Eligibility", ["DIFFERENT_ACTIONS", "DIVERGENT_EXPOSURE", "DISAGREEMENT"], "SUPPORTED", "INSUFFICIENT", "Validate versus issue evidence conflicts on establishment eligibility.", "Separate eligibility validation from certificate or decision issuance."),
    ("099ebab4", "External Contract Update Request", ["DIFFERENT_ACTIONS", "DISAGREEMENT"], "SUPPORTED", "INSUFFICIENT", "Update versus create evidence conflicts across request-update and update paths.", "Separate update-request intake from contract mutation."),
    ("596dedd6", "Labor Office User Details", ["DIFFERENT_ACTIONS", "VERSION_VARIANT", "DISAGREEMENT"], "SUPPORTED", "INSUFFICIENT", "Retrieve versus create evidence conflicts for user details.", "Keep v1 and unversioned exposures separate until metadata is corrected."),
    ("13954b71", "Establishment Address Update Variant", ["VERSION_VARIANT", "SAME_ACTION_OBJECT", "PRODUCT_CONTEXT"], "SUPPORTED", "PARTIAL", "Update action/object and shapes align across version labels.", "Retain v2 and unversioned contracts as separate consumer boundaries."),
    ("4be55154", "Resend Contract List Variant", ["VERSION_VARIANT", "SAME_ACTION_OBJECT", "PRODUCT_CONTEXT"], "SUPPORTED", "PARTIAL", "List/retrieve action and resend-contract object align across versions.", "Preserve version-specific list exposures."),
    ("9713031a", "Employee Salary List Variant", ["VERSION_VARIANT", "SAME_ACTION_OBJECT"], "SUPPORTED", "PARTIAL", "Retrieve action and employee salary object align across versions.", "Preserve each version until consumer and release intent is known."),
    ("25445978", "GOSI Contract Resend Variant", ["VERSION_VARIANT", "SAME_ACTION_OBJECT"], "SUPPORTED", "PARTIAL", "Action/object and shapes align across version labels.", "Keep resend variants as separate contracts."),
    ("3954bb22", "Contract Request Draft Variant", ["VERSION_VARIANT", "SAME_ACTION_OBJECT"], "SUPPORTED", "PARTIAL", "Retrieve draft action/object aligns across versions.", "Preserve version-specific draft retrieval."),
    ("45a1b2b2", "Violation Detail Variant", ["VERSION_VARIANT", "SAME_ACTION_OBJECT", "PRODUCT_CONTEXT"], "SUPPORTED", "PARTIAL", "Retrieve violation detail action/object and path align.", "Preserve v2 and unversioned exposure boundaries."),
    ("94f40b46", "Establishment Information Variant", ["DIVERGENT_EXPOSURE", "SAME_ACTION_OBJECT"], "SUPPORTED", "PARTIAL", "Retrieve and establishment-info signals align, while advanced versus premium may be materially different products.", "Separate advanced and premium information APIs."),
    ("d9243406", "Graduate Qualification Retrieval", ["DIVERGENT_EXPOSURE", "SAME_ACTION_OBJECT", "PRODUCT_CONTEXT"], "SUPPORTED", "PARTIAL", "Retrieve graduate-qualification intent aligns across GET and POST forms.", "Separate institution-specific qualification contracts."),
    ("1bb70ff3", "Monthly Establishment Report", ["DIVERGENT_EXPOSURE", "SAME_ACTION_OBJECT"], "SUPPORTED", "PARTIAL", "Retrieve establishment-report signals align across distinct paths.", "Separate on-demand and establishment report products."),
    ("e41641b6", "Employee Historical Information", ["DIVERGENT_EXPOSURE", "SAME_ACTION_OBJECT"], "SUPPORTED", "PARTIAL", "Retrieve employee-history intent aligns while identifier paths differ.", "Keep REST and legacy historical-information exposures separate."),
    ("733e9af9", "Establishment Training Retrieval", ["DIVERGENT_EXPOSURE", "SAME_ACTION_OBJECT"], "SUPPORTED", "PARTIAL", "Retrieve training intent aligns, but summary versus detail paths may serve distinct needs.", "Separate training summary and training-detail APIs."),
    ("19170d5b", "Qiwa Workspace Establishments", ["DIVERGENT_EXPOSURE", "SAME_ACTION_OBJECT", "VERSION_VARIANT"], "SUPPORTED", "PARTIAL", "Retrieve workspace-establishment intent aligns across differently named exposures.", "Preserve Qiwa UM v2 and legacy boundaries."),
    ("4c26a682", "Subscription Price vs Authentication Control", ["NEGATIVE_CONTROL", "COPIED_SEMANTICS", "DIVERGENT_EXPOSURE"], "CONTRADICTED", "INSUFFICIENT", "API/path intent contradicts the shared refunded semantic signal.", "Keep pricing and authentication-indicator APIs separate."),
    ("08a48c74", "Turnover Indicator vs Callback Control", ["NEGATIVE_CONTROL", "GENERIC_WRAPPER", "DIVERGENT_EXPOSURE"], "CONTRADICTED", "INSUFFICIENT", "A generic report signal cannot join turnover indicator and authentication callback paths.", "Keep turnover reporting and callback processing separate."),
    ("4bf713aa", "Worker Examination vs Contract Creation Control", ["NEGATIVE_CONTROL", "COPIED_SEMANTICS", "DIVERGENT_EXPOSURE"], "CONTRADICTED", "INSUFFICIENT", "Copied worker-examination text conflicts with an employment-contract creation path.", "Keep examination lookup and contract creation separate."),
    ("dbc68c7a", "Tier Termination vs Refund Update Control", ["NEGATIVE_CONTROL", "COPIED_SEMANTICS", "DIVERGENT_EXPOSURE"], "CONTRADICTED", "INSUFFICIENT", "Shared update/refunded evidence conflicts with terminate-tier naming and path.", "Keep tier termination and refund update separate."),
    ("ce19f252", "Establishment Opening License Control", ["NEGATIVE_CONTROL", "COPIED_SEMANTICS", "DIVERGENT_EXPOSURE"], "CONTRADICTED", "INSUFFICIENT", "Copied laborer retrieval text cannot establish one boundary for GSBI-license and farming-file opening.", "Separate establishment-opening workflows by license/process until ownership is known."),
    ("93444189", "Cancelled Visa vs Dependents Control", ["NEGATIVE_CONTROL", "COPIED_SEMANTICS", "DIVERGENT_EXPOSURE"], "CONTRADICTED", "INSUFFICIENT", "Shared sponsor-information text conflicts with cancelled-visa versus dependents paths.", "Keep visa cancellation history and dependent listing separate."),
)

MULTI_SPECS = (
    ("nic-submitvisa", "Visa Resource Lifecycle", ["MULTI_OPERATION_API", "DIFFERENT_ACTIONS", "PRODUCT_CONTEXT"], "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY", "GET, POST, and DELETE share an explicit establishment/visa resource path.", "Split visa submission from visa lookup/deletion if consumers, ownership, or release paths differ."),
    ("nic-prtissuespecialpermit", "Special Permit Resource Lifecycle", ["MULTI_OPERATION_API", "DIFFERENT_ACTIONS", "PRODUCT_CONTEXT"], "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY", "GET, POST, and DELETE share an explicit special-permit resource.", "Separate permit issuance from retrieval and deletion if authorization ownership differs."),
    ("nic-submitrunawayrequest", "Runaway Request Workflow", ["MULTI_OPERATION_API", "DIFFERENT_ACTIONS", "PRODUCT_CONTEXT"], "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY", "Retrieve, create, and validate operations share an explicit runaway-request path family.", "Separate request validation from request submission and retrieval."),
    ("mcs-rest-services", "Employee Information Queries", ["MULTI_OPERATION_API", "AMBIGUOUS_BOUNDARY", "BACKEND_UNCERTAINTY"], "PARTIAL", "Three retrieval operations concern employee information.", "Separate qualifications, employment history, and employee core information APIs."),
)

ANCHOR_TAGS = {
    "SC Request Workflow": ["ORIGINAL_ANCHOR", "DIFFERENT_ACTIONS", "PRODUCT_CONTEXT", "SC_DEEP_DIVE"],
    "Establishment Training Disclosure": ["ORIGINAL_ANCHOR", "DIFFERENT_ACTIONS"],
    "Seasonal Visa Request Search": ["ORIGINAL_ANCHOR", "VERSION_VARIANT", "PRODUCT_CONTEXT"],
    "Employment Status Enquiry": ["ORIGINAL_ANCHOR", "BACKEND_UNCERTAINTY", "DISAGREEMENT"],
    "Visa Cancellation": ["ORIGINAL_ANCHOR", "DIVERGENT_EXPOSURE"],
    "Bulk Contract Workflow": ["ORIGINAL_ANCHOR", "MULTI_OPERATION_API"],
    "Appointment Status Workflow": ["ORIGINAL_ANCHOR", "NEGATIVE_CONTROL", "SHARED_PATH"],
    "WPS Certificate Retrieval": ["ORIGINAL_ANCHOR", "NEGATIVE_CONTROL", "SHARED_SCHEMA"],
    "Technical Health and Token Boundary Control": ["ORIGINAL_ANCHOR", "NEGATIVE_CONTROL", "TECHNICAL_SECURITY"],
    "Unidentified Root Test Operations": ["ORIGINAL_ANCHOR", "NEGATIVE_CONTROL", "AMBIGUOUS_BOUNDARY"],
}


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


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


def _shape_summary(member: dict[str, Any]) -> dict[str, Any]:
    request = member.get("request_contract", {})
    responses = member.get("response_contract", [])
    return {
        "request_schema_shape_sha256": sorted({v.get("schema_shape_sha256") for v in request.get("content", []) if v.get("schema_shape_sha256")}),
        "request_schema_refs": sorted({ref for v in request.get("content", []) for ref in v.get("schema_refs", [])}),
        "response_schema_shape_sha256": sorted({v.get("schema_shape_sha256") for v in responses if v.get("schema_shape_sha256")}),
        "response_statuses": sorted({v.get("status") for v in responses if v.get("status")}),
    }


def _exposure_summary(member: dict[str, Any], full_context: dict[str, Any] | None) -> dict[str, Any]:
    if full_context:
        return {
            "accepted_product_ids": full_context.get("accepted_product_ids", []),
            "accepted_plan_ids": full_context.get("accepted_plan_ids", []),
            "accepted_product_relationship_ids": full_context.get("accepted_product_relationship_ids", []),
            "accepted_plan_relationship_ids": full_context.get("accepted_plan_relationship_ids", []),
            "subscription_evidence_state": full_context.get("subscription_evidence_state", "NOT_EVIDENCED"),
            "subscription_join_count": full_context.get("subscription_join_count", 0),
            "operation_consumption_proven": False,
            "runtime_activity_proven": False,
        }
    context = member.get("as_is_product_plan_context", {})
    products = context.get("product_contains_api", [])
    plans = context.get("plan_entitles_api", [])
    return {
        "accepted_product_ids": sorted({v["product_canonical_id"] for v in products}),
        "accepted_plan_ids": sorted({v["plan_canonical_id"] for v in plans}),
        "accepted_product_relationship_ids": sorted({v["relationship_id"] for v in products}),
        "accepted_plan_relationship_ids": sorted({v["relationship_id"] for v in plans}),
        "subscription_evidence_state": "NOT_ASSESSED_FOR_NONPAIR_MEMBER",
        "subscription_join_count": 0,
        "operation_consumption_proven": False,
        "runtime_activity_proven": False,
    }


def _compact_member(member: dict[str, Any], full_context: dict[str, Any] | None = None) -> dict[str, Any]:
    backend = member.get("backend_context", {})
    return {
        "canonical_api_id": member["canonical_api_id"], "api_name": member["api_name"], "api_version": member.get("api_version"),
        "task014_operation_id": member["task014_operation_id"], "task015_observed_function_id": member["task015_observed_function_id"],
        "task016_comparison_refs": member.get("task016_comparison_refs", []), "task016_refinement_refs": member.get("task016_refinement_refs", []),
        "method": member["method"], "exact_path": member["exact_path"], "normalized_path": member.get("normalized_path"),
        "supported_actions": member.get("supported_actions", []), "observed_action": member.get("observed_action"), "observed_object": member.get("observed_object"),
        "interpretation_status": member.get("interpretation_status"), "contract": _shape_summary(member),
        "security_context": member.get("security_context", {}), "exposure_contract": member.get("exposure_context", {}),
        "backend": {"certainty": backend.get("certainty", "NOT_EVIDENCED"), "configured_paths": [v.get("safe_backend_operation_path") for v in backend.get("configured_operations", []) if v.get("safe_backend_operation_path")], "source_pointers": [v.get("source_pointer") for v in backend.get("configured_operations", []) if v.get("source_pointer")], "runtime_egress_proven": False},
        "transformation_dispatch_evidence": "NOT_EVIDENCED_IN_ACCEPTED_OPERATION_INDEX",
        "product_plan_subscription_context": _exposure_summary(member, full_context),
        "source_provenance": member["source_provenance"], "source_variant_fingerprint": member.get("source_variant_fingerprint"),
        "product_is_logical_api": False, "runtime_activity_proven": False,
    }


def _refs(members: list[dict[str, Any]]) -> list[str]:
    return [f"{v['source_provenance']['source_path']}#{v['source_provenance']['source_pointer']}" for v in members]


def _rubric(members: list[dict[str, Any]], r1: str, r2: str, pro: str, con: str) -> dict[str, Any]:
    refs = _refs(members)
    backend_supported = all(v["backend"]["certainty"] in {"CONFIGURED_OPERATION_SCOPED", "RESOLVED_OPERATION_SEMANTICS"} for v in members)
    products = sorted({x for v in members for x in v["product_plan_subscription_context"]["accepted_product_ids"]})
    return {
        "R1": {"status": r1, "rationale": pro if r1 == "SUPPORTED" else con, "evidence_refs": refs},
        "R2": {"status": r2, "rationale": "Distinct actions and a current resource path family support a provisional lifecycle boundary." if r2 == "SUPPORTED" else "Action evidence does not prove shared lifecycle, responsibility, ownership, or release path.", "evidence_refs": refs},
        "R3": {"status": "NOT_EVIDENCED", "rationale": f"Accepted exposure context exists for {len(products)} Product IDs, but consumer intent, ownership, roles, and actual calls are not proven.", "evidence_refs": products},
        "R4": {"status": "SUPPORTED", "rationale": "Exact paths, versions, security declarations, and request/response shape hashes are retained; compatibility is not inferred.", "evidence_refs": refs},
        "R5": {"status": "SUPPORTED" if backend_supported else "NOT_EVIDENCED", "rationale": "Operation-level configured backend evidence is present." if backend_supported else "Backend evidence is API-shared, unresolved, or absent; behavior and runtime egress are not proven.", "evidence_refs": [p for v in members for p in v["backend"]["source_pointers"]]},
        "R6": {"status": "SUPPORTED", "rationale": con, "evidence_refs": refs},
        "R7": {"status": "SUPPORTED", "rationale": "Every membership retains accepted IDs, source pointer, source hash, and scope-specific certainty.", "evidence_refs": refs},
    }


def _membership_rubric(member: dict[str, Any], candidate_rubric: dict[str, Any]) -> dict[str, Any]:
    ref = f"{member['source_provenance']['source_path']}#{member['source_provenance']['source_pointer']}"
    action_object = bool(member["supported_actions"] and member["observed_object"])
    return {
        "R1": {"status": "SUPPORTED" if member["observed_object"] else "NOT_EVIDENCED", "rationale": "Member object/resource signal retained." if member["observed_object"] else "Member resource is unresolved.", "evidence_refs": [ref]},
        "R2": {"status": "SUPPORTED" if action_object and candidate_rubric["R2"]["status"] == "SUPPORTED" else "NOT_EVIDENCED", "rationale": "Member action and direct resource-family link support membership." if action_object and candidate_rubric["R2"]["status"] == "SUPPORTED" else "A member action or its coherent-boundary link remains unproven.", "evidence_refs": [ref]},
        "R3": candidate_rubric["R3"], "R4": candidate_rubric["R4"], "R5": candidate_rubric["R5"],
        "R6": candidate_rubric["R6"], "R7": {"status": "SUPPORTED", "rationale": "Exact member provenance is retained.", "evidence_refs": [ref]},
    }


def _record(case_id: str, label: str, origin: str, tags: list[str], members: list[dict[str, Any]], evidence_sufficiency: str, rubric: dict[str, Any], pro: str, con: str, alternative: str, *, original: dict[str, Any] | None = None, pair: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "expanded_case_id": case_id, "sample_origin": origin, "candidate_boundary_label": label, "strata": sorted(tags),
        "original_mock_case_id": original.get("boundary_case_id") if original else None,
        "original_mock_disposition": original.get("disposition") if original else None,
        "original_anchor_record_sha256": _hash(original) if original else None,
        "task016_comparison_id": pair.get("prior_comparison_id") if pair else None,
        "task016_refinement_id": pair.get("refinement_id") if pair else None,
        "task016_refinement_verdict": pair.get("refinement_verdict") if pair else None,
        "members": [{**v, "membership_rubric": _membership_rubric(v, rubric), "membership_status": "CONCEPTUAL_GROUPING_HYPOTHESIS" if evidence_sufficiency in {"PARTIAL", "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY"} else "NOT_ASSERTED"} for v in members],
        "candidate_rubric": rubric, "evidence_for": [pro], "evidence_against": [con], "alternative_boundary": alternative,
        "functional_equivalence_approved": False, "member_ids_collapsed": False, "transitive_equivalence_inferred": False,
        "result_axes": {"technical_validation": "PASS", "evidence_sufficiency": evidence_sufficiency, "architect_acceptance": "PENDING"},
        "domain_assignment": None, "capability_assignment": None, "kong_topology": None, "retirement_decision": None,
        "production_usage_inferred": False, "product_is_logical_api": False,
    }


def build_expanded_validation(root: Path, *, register_path: Path | None = None, manifest_path: Path | None = None) -> dict[str, Any]:
    root = root.resolve(); register_path = register_path or root / REGISTER_OUTPUT; manifest_path = manifest_path or root / MANIFEST_OUTPUT
    inputs = {
        "original_mock": root / "tests/evidence/task-017/mock/representative_boundary_cases.jsonl",
        "apis": root / "indexes/semantic_api_inventory.jsonl", "operations": root / "indexes/semantic_operation_inventory.jsonl",
        "observed": root / "indexes/observed_function_inventory.jsonl", "task016_refined": root / "indexes/task016_semantic_refinement_pairs.jsonl",
        "task016_baseline": root / "indexes/task016_full_candidate_pairs.jsonl", "backend_resolution": root / "indexes/backend_target_resolution.jsonl",
        "codegraph_dependency_edges": root / "indexes/codegraph_dependency_edges.jsonl", "implementation": Path(__file__).resolve(),
    }
    originals = _jsonl(inputs["original_mock"]); api_values = _jsonl(inputs["apis"]); operation_values = _jsonl(inputs["operations"]); observed_values = _jsonl(inputs["observed"])
    refined = _jsonl(inputs["task016_refined"]); baseline = _jsonl(inputs["task016_baseline"])
    if len(originals) != 10 or len(api_values) != 2036 or len(operation_values) != 2414 or len(refined) != len(baseline) != 1170:
        raise ValueError("Frozen Task 014--017 mock reconciliation mismatch")
    operations = {v["semantic_operation_inventory_id"]: v for v in operation_values}; observed = {v["task014_operation_record_id"]: v for v in observed_values}; apis = {v["canonical_api_id"]: v for v in api_values}
    resolution = {v["target_observation_id"]: v for v in _jsonl(inputs["backend_resolution"])}; graph: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in _jsonl(inputs["codegraph_dependency_edges"]): graph[edge["source_canonical_identity_record_id"]].append(edge)
    baseline_by_id = {v["comparison_id"]: v for v in baseline}; records = []

    for original in originals:
        members = [_compact_member(v) for v in original["candidate_members"]]
        disposition = original["disposition"]
        sufficiency = "SUPPORTED_SEPARATE" if disposition == "SEPARATE_LOGICAL_APIS_SUPPORTED" else "INSUFFICIENT" if disposition == "INSUFFICIENT_EVIDENCE_TO_FORM" else "PARTIAL"
        r1 = "NOT_EVIDENCED" if sufficiency == "INSUFFICIENT" else "CONTRADICTED" if sufficiency == "SUPPORTED_SEPARATE" else "SUPPORTED"
        pro = original["logical_api_cohesion"]["positive_evidence"][0] if original["logical_api_cohesion"]["positive_evidence"] else "No positive cohesion evidence in the original anchor."
        con = original["logical_api_cohesion"]["reasons_not_to_group"][0] if original["logical_api_cohesion"]["reasons_not_to_group"] else "Consumer, ownership, and release-path evidence remains absent."
        rubric = _rubric(members, r1, "NOT_EVIDENCED", pro, con)
        records.append(_record(original["boundary_case_id"], original["provisional_business_neutral_label"], "ORIGINAL_MOCK_ANCHOR", ANCHOR_TAGS[original["provisional_business_neutral_label"]], members, sufficiency, rubric, pro, con, original["boundary_alternatives"][0], original=original))

    used_member_sets: set[tuple[str, ...]] = set()
    for suffix, label, tags, r1, sufficiency, pro, alternative in PAIR_SPECS:
        matches = [v for v in refined if v["prior_comparison_id"].endswith(suffix)]
        if len(matches) != 1: raise ValueError(f"Expected one comparison ending {suffix}, found {len(matches)}")
        pair = matches[0]; baseline_pair = baseline_by_id[pair["prior_comparison_id"]]
        contexts = {baseline_pair[s]["task014_operation_id"]: baseline_pair[s]["product_plan_subscription_context"] for s in ("left", "right")}
        members = [_compact_member(_member(pair[s]["task014_operation_id"], operations, observed, apis, resolution, graph, pair), contexts[pair[s]["task014_operation_id"]]) for s in ("left", "right")]
        signature = tuple(sorted(v["task014_operation_id"] for v in members))
        if signature in used_member_sets: raise ValueError("Reversed or duplicated pair selected")
        used_member_sets.add(signature)
        con = alternative
        rubric = _rubric(members, r1, "CONTRADICTED" if "NEGATIVE_CONTROL" in tags else "NOT_EVIDENCED", pro, con)
        records.append(_record(_id("task017-expanded-case", pair["prior_comparison_id"], RULES_VERSION), label, "EXPANDED_TASK016_PAIR", tags, members, sufficiency, rubric, pro, con, alternative, pair=pair))

    for api_name, label, tags, sufficiency, pro, alternative in MULTI_SPECS:
        api = next(v for v in api_values if v["identity_name"] == api_name)
        members = [_compact_member(_member(oid, operations, observed, apis, resolution, graph)) for oid in api["operation_record_ids"]]
        r2 = "SUPPORTED" if sufficiency == "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY" else "NOT_EVIDENCED"
        rubric = _rubric(members, "SUPPORTED", r2, pro, alternative)
        records.append(_record(_id("task017-expanded-multi-api-case", api["canonical_api_id"], RULES_VERSION), label, "EXPANDED_MULTI_OPERATION_API", tags, members, sufficiency, rubric, pro, alternative, alternative))

    records.sort(key=lambda v: v["expanded_case_id"])
    if len(records) != 46 or sum(v["sample_origin"] != "ORIGINAL_MOCK_ANCHOR" for v in records) != 36:
        raise ValueError("Expanded sample must contain 10 anchors and 36 new cases")
    _write_jsonl(register_path, records)
    member_ids = [m["task014_operation_id"] for v in records for m in v["members"]]
    strata = Counter(tag for v in records for tag in v["strata"])
    axes = Counter(v["result_axes"]["evidence_sufficiency"] for v in records)
    manifest = {
        "rules_version": RULES_VERSION, "scope": "EXPANDED_VALIDATION_SAMPLE_NOT_FULL_ESTATE",
        "summary": {"total_case_count": len(records), "original_anchor_count": 10, "new_case_count": 36, "member_occurrence_count": len(member_ids), "unique_operation_count": len(set(member_ids)), "unique_canonical_api_count": len({m["canonical_api_id"] for v in records for m in v["members"]}), "strata": dict(sorted(strata.items())), "evidence_sufficiency": dict(sorted(axes.items()))},
        "original_mock_fingerprint": _fingerprint(inputs["original_mock"], root, 10), "full_estate_formation_performed": False,
        "all_pairs_search_performed": False, "architect_acceptance_count": 0, "staging_read_for_expansion": False, "staging_modified": False,
        "inputs": {name: _fingerprint(path, root) for name, path in inputs.items()}, "outputs": {"register": _fingerprint(register_path, root, len(records))},
    }
    _write_json(manifest_path, manifest)
    return {"records": records, "manifest": manifest}
