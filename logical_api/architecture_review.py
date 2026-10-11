"""Task 017A bounded architecture review of the 71 Task 017 proposals."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


RULES_VERSION = "task017a-all-71-architecture-review-v1"
NEXT_GATE = "AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN"
OUTPUTS = {
    "reviews": Path("indexes/task017a_all_71_architecture_reviews.jsonl"),
    "oversized": Path("indexes/task017a_five_oversized_adjunct.jsonl"),
    "cross_links": Path("indexes/task017a_cross_api_opportunity_links.jsonl"),
    "backlog": Path("indexes/task017a_productization_decision_backlog.jsonl"),
    "manifest": Path("indexes/task017a_architecture_review_manifest.json"),
}

RECOMMENDATIONS = {
    "RETAIN_PROVISIONAL_COHESIVE_BOUNDARY",
    "SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES",
    "KEEP_AS_IS_EXPOSURE_NO_LOGICAL_BOUNDARY_ASSERTION",
    "REQUIRES_TARGETED_EVIDENCE",
    "TECHNICAL_OR_TEST_EXPOSURE_REVIEW",
}

SPLIT_RULES: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    "getlookups": [
        ("Country lookup", ("getcountries",)), ("Embassy lookup", ("getembassies",)),
        ("General lookup", ("getlookups",)), ("Marital-status lookup", ("getmaritalstatus",)),
        ("Occupation lookup", ("getoccupations",)),
    ],
    "mcs-rest-services": [
        ("Employee history query", ("historical",)), ("Employee core-information query", ("employee-info",)),
        ("Employee qualification query", ("qualifications",)),
    ],
    "mci-rest-services": [("Commercial-registration detail query", ("cr-details",)), ("All-detail query", ("all-details",))],
    "mhrsd3-rest-services": [
        ("Establishment ownership check", ("checkestabownership",)), ("Establishment branch detail", ("getestabbranches",)),
        ("Establishment Nitaq history", ("getestabnitaq",)), ("Tawteen information queries", ("gettawteeninfo",)),
    ],
    "kyan-user-validation": [("User-role verification", ("verifydelegator", "verifyowner")), ("Test utility", ("/test",))],
    "nic2-rest-services": [
        ("Mobile identity authentication", ("authenticateuser",)), ("Person identity information", ("citizen-info", "foreigner-info")),
        ("Laborer status information", ("getlaborerborder", "getlaborerprison")),
    ],
    "s3-client": [("Bucket operations", ("/api/s3/",)), ("Object operations", ("/{bucket}/{name}",))],
    "takamol-svp-apis-v1": [
        ("Workforce reference data", ("categories", "occupations", "international_labors", "/labors")),
        ("Professional accreditation", ("professional_accreditation",)), ("Test-center operations", ("test_center",)),
    ],
    "takamol-svp-apis-v11": [
        ("Workforce reference data", ("categories", "occupations", "international_labors", "/labors")),
        ("Professional accreditation", ("professional_accreditation",)), ("Test-center operations", ("test_center",)),
    ],
    "takamol-svp-rest-api-v1": [
        ("Workforce reference data", ("categories", "occupations", "international_labors", "/labors")),
        ("Professional accreditation", ("professional_accreditation",)), ("Test-center operations", ("test_center",)),
    ],
    "accessmanagement-supportcenter": [
        ("Service catalog", ("services", "servicemodules")), ("User-service access assignment", ("grantaccess", "revokeaccess", "servicetouser", "unassignedservices")),
    ],
    "queryqanagement-supportcentre": [
        ("Query definitions", ("query",)), ("DSN configuration", ("getdsn",)), ("Query module/card metadata", ("module", "cardsdata")),
    ],
    "adminmanagement-supportcentre": [
        ("DSN administration", ("/dsn/",)), ("Query administration", ("/queries/",)), ("User-account administration", ("/users/",)),
    ],
    "ajeervisaservice": [("Credit operations", ("credit",)), ("Visa transaction submission", ("visatransaction",))],
}

CROSS_LINK_LABELS = (
    "SC Request Workflow", "Seasonal Visa Request Search", "Employment Status Enquiry", "Visa Cancellation",
    "Establishment Training Disclosure", "Appointment Status Workflow", "WPS Certificate Retrieval",
    "Technical Health and Token Boundary Control", "User Management Exposure Ambiguity",
    "Commercial Registration Information", "MOMRA Verification Boundary", "Authentication Indicator Variant",
    "Conversation Deletion Variant", "Graduate Qualification Retrieval",
)

TECHNICAL_IDENTITY_PATTERNS = re.compile(
    r"(?:^|[-_])(test|poc|mock)(?:$|[-_])|jwt|graphql|streaming|s3-client|cachemanagement", re.I
)


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}:sha256:{_hash(parts)}"


def _write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text("".join(json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n" for v in values), encoding="utf-8")
    os.replace(temporary, path)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _fingerprint(path: Path, root: Path, count: int | None = None) -> dict[str, Any]:
    try:
        display_path = path.relative_to(root).as_posix()
    except ValueError:
        display_path = path.as_posix()
    value: dict[str, Any] = {"path": display_path, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    if count is not None: value["record_count"] = count
    return value


def _source_ref(member: dict[str, Any]) -> str:
    p = member["source_provenance"]
    return f"{p['source_path']}#{p['source_pointer']}"


def _operation_summary(member: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    backend = observed.get("backend_evidence", {})
    configured = backend.get("configured_operation_scoped_facts", [])
    inherited = backend.get("candidate_inherited_context_projection", [])
    return {
        "task014_operation_id": member["task014_operation_id"], "task015_observed_function_id": member["task015_observed_function_id"],
        "method": member.get("method") or member["source_provenance"]["source_pointer"].split("/")[-1].upper(),
        "path": member.get("exact_path") or "NOT_IN_PROPOSAL_COMPACT_MEMBER", "actions": member.get("actions", []),
        "resource": member.get("resource"), "source_pointer": _source_ref(member), "source_sha256": member["source_provenance"]["source_sha256"],
        "contract": member["contract"], "criteria": member["criteria"],
        "exposure": member["relationship_exposure_context"],
        "backend_evidence_scope": {
            "configured_operation_scoped_count": len(configured),
            "candidate_inherited_context_count": len(inherited),
            "configured_source_pointers": sorted({v.get("source_pointer") for v in configured if v.get("source_pointer")}),
            "candidate_source_pointers": sorted({v.get("source_pointer") for v in inherited if v.get("source_pointer")}),
            "runtime_egress_proven": False,
        },
    }


def _member_paths(proposal: dict[str, Any], ledger_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    by_id = {v["task014_operation_id"]: v for v in proposal["direct_member_assertions"]}
    for operation_id in proposal["member_operation_ids"]:
        member = dict(by_id[operation_id]); ledger = ledger_by_id[operation_id]
        member["method"] = ledger["method"]; member["exact_path"] = ledger["exact_path"]
        result.append(member)
    return result


def _split_candidates(api_name: str, members: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    if api_name == "s3-client":
        object_ids = sorted(v["task014_operation_id"] for v in members if v["exact_path"].endswith("/{bucket}/{name}"))
        bucket_ids = sorted(v["task014_operation_id"] for v in members if not v["exact_path"].endswith("/{bucket}/{name}"))
        candidates = []
        for label, ids in (("Bucket operations", bucket_ids), ("Object operations", object_ids)):
            if not ids:
                continue
            candidates.append({
                "sub_boundary_id": _stable_id("task017a-sub-boundary", api_name, label, ids),
                "provisional_label": label, "member_operation_ids": ids,
                "evidence_refs": sorted(_source_ref(v) for v in members if v["task014_operation_id"] in ids),
                "architect_acceptance": "PENDING", "productization_design_authorized": False,
            })
        return candidates, []
    rules = SPLIT_RULES.get(api_name, [])
    assigned: set[str] = set(); candidates = []
    for label, patterns in rules:
        ids = []
        for member in members:
            operation_id = member["task014_operation_id"]
            if operation_id in assigned: continue
            path = member["exact_path"].lower()
            if any(pattern.lower() in path for pattern in patterns):
                ids.append(operation_id)
        if ids:
            assigned.update(ids)
            refs = [_source_ref(v) for v in members if v["task014_operation_id"] in ids]
            candidates.append({
                "sub_boundary_id": _stable_id("task017a-sub-boundary", api_name, label, sorted(ids)),
                "provisional_label": label, "member_operation_ids": sorted(ids), "evidence_refs": sorted(refs),
                "architect_acceptance": "PENDING", "productization_design_authorized": False,
            })
    unassigned = sorted({v["task014_operation_id"] for v in members} - assigned)
    return candidates, unassigned


def _case_evidence(proposal: dict[str, Any], members: list[dict[str, Any]]) -> tuple[str, str, list[str], list[str]]:
    actions = sorted({a for m in members for a in m.get("actions", [])})
    resources = sorted({m.get("resource") for m in members if m.get("resource")})
    paths = sorted({m["exact_path"] for m in members})
    missing_action_count = sum(not m.get("actions") for m in members)
    contracts = {_hash(m["contract"]) for m in members}
    security = {json.dumps({k: m["contract"].get(k) for k in ("security_requirement_present", "security_scheme_types")}, sort_keys=True) for m in members}
    product_sets = {tuple(m["relationship_exposure_context"].get("accepted_product_ids", [])) for m in members}
    plan_sets = {tuple(m["relationship_exposure_context"].get("accepted_plan_ids", [])) for m in members}
    positive = (
        f"Accepted API {proposal['current_api_name']} contains {len(members)} exact operations; evidenced actions={actions or ['NONE']} and resources={resources or ['NONE']}."
    )
    details = []
    if len(resources) > 1: details.append(f"resource signals diverge across {resources[:6]}")
    if missing_action_count: details.append(f"{missing_action_count}/{len(members)} members lack supported actions")
    if len(paths) > 1: details.append(f"{len(paths)} exact paths expose separate path responsibilities")
    if len(contracts) > 1: details.append(f"{len(contracts)} contract/security fingerprints differ")
    if len(security) > 1: details.append("security declarations differ")
    if len(product_sets) > 1: details.append(f"accepted AS-IS Product exposure differs across {len(product_sets)} member contexts")
    if len(plan_sets) > 1: details.append(f"accepted AS-IS Plan exposure differs across {len(plan_sets)} member contexts")
    if not details: details.append("coexistence in one current API is the only group-level signal")
    counter = "; ".join(details) + "."
    refs = sorted(_source_ref(m) for m in members)
    return positive, counter, refs, paths


def _review_rubric(proposal: dict[str, Any], counter: str) -> dict[str, Any]:
    rubric = json.loads(json.dumps(proposal["candidate_rubric"]))
    rubric["R6"]["rationale"] = counter + " No transitive equivalence or product boundary is inferred."
    return rubric


def _recommendation(proposal: dict[str, Any], members: list[dict[str, Any]], observed_by_id: dict[str, dict[str, Any]]) -> tuple[str, str, list[dict[str, Any]], list[str], list[str]]:
    sufficiency = proposal["three_result_axes"]["evidence_sufficiency"]
    sub_boundaries, unassigned = _split_candidates(proposal["current_api_name"], members)
    nature_values = [observed_by_id[m["task015_observed_function_id"]]["candidate_observed_function"].get("operation_nature") for m in members]
    technical_evidence = []
    if TECHNICAL_IDENTITY_PATTERNS.search(proposal["current_api_name"]):
        technical_evidence.append(f"accepted API identity `{proposal['current_api_name']}` directly labels a technical/test/POC exposure")
    technical_members = sum(v == "TECHNICAL_OPERATION" for v in nature_values)
    if technical_members:
        technical_evidence.append(f"Task 015 marks {technical_members}/{len(members)} members TECHNICAL_OPERATION")
    if sufficiency == "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY":
        return "RETAIN_PROVISIONAL_COHESIVE_BOUNDARY", "R1+R2+R7 remain supported with distinct actions on one explicit resource path family.", [], [], technical_evidence
    if len(sub_boundaries) >= 2:
        return "SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES", f"Direct paths identify {len(sub_boundaries)} disjoint resource/responsibility subsets; unmatched members remain unresolved.", sub_boundaries, unassigned, technical_evidence
    if technical_evidence:
        return "TECHNICAL_OR_TEST_EXPOSURE_REVIEW", "; ".join(technical_evidence) + "; this is a lifecycle/policy review, not retirement.", [], [], technical_evidence
    actions = [a for m in members for a in m.get("actions", [])]
    resources = [m.get("resource") for m in members if m.get("resource")]
    if sufficiency == "INSUFFICIENT" and not actions and not resources:
        return "KEEP_AS_IS_EXPOSURE_NO_LOGICAL_BOUNDARY_ASSERTION", "No supported action/resource evidence exists beyond current API coexistence.", [], [], technical_evidence
    return "REQUIRES_TARGETED_EVIDENCE", "Concrete lifecycle, resource-responsibility, owner, or consumer evidence is required to decide cohesion versus split.", [], [], technical_evidence


def _productization_implication(recommendation: str) -> str:
    return {
        "RETAIN_PROVISIONAL_COHESIVE_BOUNDARY": "PROVISIONAL_REUSABLE_RESOURCE_CANDIDATE_NOT_A_PRODUCT",
        "SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES": "SEPARATE_RESOURCE_POLICY_OR_CONSUMER_BOUNDARY_CONSIDERATIONS_NOT_PRODUCTS",
        "KEEP_AS_IS_EXPOSURE_NO_LOGICAL_BOUNDARY_ASSERTION": "AS_IS_STRUCTURAL_EXPOSURE_ONLY_NOT_A_PRODUCT_CANDIDATE",
        "REQUIRES_TARGETED_EVIDENCE": "DEFER_PRODUCTIZATION_BOUNDARY_PENDING_NAMED_EVIDENCE",
        "TECHNICAL_OR_TEST_EXPOSURE_REVIEW": "STRUCTURAL_OR_TECHNICAL_LIFECYCLE_CANDIDATE_NOT_A_BUSINESS_PRODUCT",
    }[recommendation]


def _oversized_family(path: str) -> str | None:
    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", path).lower()
    tokens = re.findall(r"[a-z0-9]+", value)
    ignored = {"get", "post", "put", "patch", "delete", "all", "by", "id", "with", "save", "update", "create", "list", "api"}
    useful = [v for v in tokens if v not in ignored and not v.isdigit()]
    if not useful or all(v in {"uri", "uri2", "uri3", "uri4", "uri5", "uri6"} for v in useful): return None
    return " ".join(useful[:3])


def _build_oversized(diagnostic: dict[str, Any], ledger_by_id: dict[str, dict[str, Any]], observed_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[str]] = defaultdict(list)
    for operation_id in diagnostic["member_operation_ids"]:
        row = ledger_by_id[operation_id]
        observed = observed_by_id[row["task015_observed_function_id"]]
        phrase = observed["candidate_observed_function"].get("business_object_or_resource_phrase")
        explicit = observed["interpretation_status"] == "EXPLICITLY_DESCRIBED"
        family = re.sub(r"\s+", " ", (phrase or "").strip().lower()) if explicit and phrase else _oversized_family(row["exact_path"])
        if family: groups[family].append(operation_id)
    candidates = []
    assigned: set[str] = set()
    for family, ids in sorted(groups.items()):
        if len(ids) < 2: continue
        ids = sorted(ids); assigned.update(ids)
        candidates.append({
            "subfamily_id": _stable_id("task017a-oversized-subfamily", diagnostic["canonical_api_id"], family, ids),
            "provisional_label": family, "member_operation_ids": ids,
            "evidence_refs": [f"{ledger_by_id[v]['source_provenance']['source_path']}#{ledger_by_id[v]['source_provenance']['source_pointer']}" for v in ids],
            "status": "BOUNDED_PATH_RESOURCE_SUBFAMILY_REQUIRES_ARCHITECT_REVIEW",
        })
    unresolved = sorted(set(diagnostic["member_operation_ids"]) - assigned)
    recommendation = "SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES" if len(candidates) >= 2 else "REQUIRES_TARGETED_EVIDENCE"
    return {
        "adjunct_review_id": _stable_id("task017a-oversized-review", diagnostic["canonical_api_id"], RULES_VERSION),
        "baseline_proposal_count_inclusion": False, "canonical_api_id": diagnostic["canonical_api_id"], "current_api_name": diagnostic["api_name"],
        "operation_count": diagnostic["operation_count"], "original_member_operation_ids": diagnostic["member_operation_ids"],
        "original_primary_dispositions_unchanged": True, "cap_relaxed": False, "subfamily_candidates": candidates,
        "subfamily_membership_disjoint": len(assigned) == sum(len(v["member_operation_ids"]) for v in candidates),
        "unresolved_operation_ids": unresolved, "recommendation": recommendation,
        "specific_counterevidence": f"The API has {diagnostic['operation_count']} operations; only {len(assigned)} are covered by repeated direct resource/path signals and {len(unresolved)} remain unresolved.",
        "productization_implication": _productization_implication(recommendation),
        "three_result_axes": {"technical_validation": "PASS", "evidence_sufficiency": "PARTIAL" if candidates else "INSUFFICIENT", "architect_acceptance": "PENDING"},
        "production_usage_inferred": False, "retirement_decision": None, "domain_assignment": None, "capability_assignment": None, "kong_topology": None,
    }


def build_architecture_review(root: Path, *, output_paths: dict[str, Path] | None = None) -> dict[str, Any]:
    root = root.resolve(); paths = {k: (output_paths or {}).get(k, root / v) for k, v in OUTPUTS.items()}
    inputs = {
        "proposals": root / "indexes/task017_full_logical_api_proposals.jsonl", "ledger": root / "indexes/task017_full_operation_disposition.jsonl",
        "diagnostics": root / "indexes/task017_full_formation_diagnostics.jsonl", "full_manifest": root / "indexes/task017_full_manifest.json",
        "observed": root / "indexes/observed_function_inventory.jsonl", "expanded_sample": root / "tests/evidence/task-017/expanded-validation/expanded_sample_register.jsonl",
        "task016_refinement": root / "indexes/task016_semantic_refinement_pairs.jsonl", "relationships": root / "indexes/relationship_index.jsonl",
        "implementation": Path(__file__).resolve(),
    }
    proposals = _jsonl(inputs["proposals"]); ledger = _jsonl(inputs["ledger"]); diagnostics = _jsonl(inputs["diagnostics"])
    observed_values = _jsonl(inputs["observed"]); expanded = _jsonl(inputs["expanded_sample"])
    if len(proposals) != 71 or len(ledger) != 2414 or len(expanded) != 46: raise ValueError("Task 017 frozen baseline reconciliation mismatch")
    ledger_by_id = {v["task014_operation_id"]: v for v in ledger}; observed_by_id = {v["observed_function_id"]: v for v in observed_values}

    links = []
    for case in expanded:
        if case["candidate_boundary_label"] not in CROSS_LINK_LABELS: continue
        canonical_ids = sorted({v["canonical_api_id"] for v in case["members"]})
        if len(canonical_ids) < 2: continue
        sufficiency = case["result_axes"]["evidence_sufficiency"]
        links.append({
            "cross_api_link_id": _stable_id("task017a-cross-api-link", case["expanded_case_id"], RULES_VERSION),
            "source_case_id": case["expanded_case_id"], "candidate_label": case["candidate_boundary_label"],
            "canonical_api_ids": canonical_ids, "member_operation_ids": [v["task014_operation_id"] for v in case["members"]],
            "source_pointers": [f"{v['source_provenance']['source_path']}#{v['source_provenance']['source_pointer']}" for v in case["members"]],
            "positive_evidence": case["evidence_for"], "contrary_evidence": case["evidence_against"],
            "competing_alternatives": (
                ["Unified SC Request Actions boundary retaining approve, reject, and cancel as distinct intents.",
                 "Split Decision boundary (approve/reject) from Cancellation boundary (cancel)."]
                if case["candidate_boundary_label"] == "SC Request Workflow"
                else [case["alternative_boundary"]]
            ),
            "link_status": "NEGATIVE_CONTROL_NO_GROUP" if sufficiency in {"INSUFFICIENT", "SUPPORTED_SEPARATE"} else "BOUNDED_CROSS_API_ALTERNATIVE_PENDING",
            "primary_membership_created": False, "functional_equivalence_approved": False, "transitive_equivalence_inferred": False,
            "architect_acceptance": "PENDING", "productization_implication": "CROSS_API_EXPOSURE_ALTERNATIVE_REQUIRES_GATE_DECISION_NOT_A_PRODUCT",
        })
    links.sort(key=lambda v: v["cross_api_link_id"]); link_by_operation: dict[str, list[str]] = defaultdict(list)
    for link in links:
        for operation_id in link["member_operation_ids"]: link_by_operation[operation_id].append(link["cross_api_link_id"])

    reviews = []
    for proposal in proposals:
        members = _member_paths(proposal, ledger_by_id); positive, counter, refs, paths_seen = _case_evidence(proposal, members)
        recommendation, rationale, sub_boundaries, unassigned, technical_evidence = _recommendation(proposal, members, observed_by_id)
        review = {
            "architecture_review_id": _stable_id("task017a-proposal-review", proposal["logical_api_proposal_id"], RULES_VERSION),
            "baseline_logical_api_proposal_id": proposal["logical_api_proposal_id"], "baseline_membership_sha256": _hash(sorted(proposal["member_operation_ids"])),
            "baseline_evidence_sufficiency": proposal["three_result_axes"]["evidence_sufficiency"], "canonical_api_id": proposal["canonical_api_id"],
            "current_api_name": proposal["current_api_name"], "current_api_version": proposal["current_api_version"], "member_count": len(members),
            "operations": [_operation_summary(v, observed_by_id[v["task015_observed_function_id"]]) for v in members], "grouping_hypothesis": proposal["boundary_label"],
            "product_plan_subscription_context": proposal["product_plan_subscription_context"],
            "positive_cohesion_evidence": positive, "specific_counterevidence": counter, "source_evidence_refs": refs,
            "review_rubric": _review_rubric(proposal, counter), "recommendation": recommendation, "recommendation_rationale": rationale,
            "proposed_sub_boundaries": sub_boundaries, "unassigned_after_split_operation_ids": unassigned,
            "split_membership_disjoint": len({x for v in sub_boundaries for x in v["member_operation_ids"]}) == sum(len(v["member_operation_ids"]) for v in sub_boundaries),
            "alternative_boundary": proposal["alternative_boundary"], "productization_implication": _productization_implication(recommendation),
            "technical_or_test_evidence": technical_evidence, "bounded_cross_api_link_ids": sorted({x for m in members for x in link_by_operation[m["task014_operation_id"]]}),
            "evidence_gaps": ["COMMON_LIFECYCLE_OWNER_NOT_EVIDENCED", "CONSUMER_AND_ENTITLEMENT_INTENT_NOT_EVIDENCED", "PRODUCTION_USAGE_AND_RELEASE_BOUNDARY_NOT_EVIDENCED", "OPERATION_BACKEND_RUNTIME_NOT_PROVEN"],
            "three_result_axes": {"technical_validation": "PASS", "evidence_sufficiency": proposal["three_result_axes"]["evidence_sufficiency"], "architect_acceptance": "PENDING"},
            "original_membership_unchanged": True, "production_usage_inferred": False, "functional_equivalence_approved": False,
            "product_created_or_mapped": False, "retirement_decision": None, "domain_assignment": None, "capability_assignment": None, "kong_topology": None,
        }
        if review["recommendation"] not in RECOMMENDATIONS: raise ValueError("Invalid recommendation")
        reviews.append(review)
    reviews.sort(key=lambda v: v["baseline_logical_api_proposal_id"])

    oversized_diagnostics = [v for v in diagnostics if v["diagnostic_type"] == "OVERSIZED_CANONICAL_API_GROUP_SKIPPED"]
    oversized = sorted((_build_oversized(v, ledger_by_id, observed_by_id) for v in oversized_diagnostics), key=lambda v: v["current_api_name"])
    if len(oversized) != 5 or sum(v["operation_count"] for v in oversized) != 132: raise ValueError("Oversized adjunct reconciliation mismatch")

    backlog = []
    for review in reviews:
        backlog.append({
            "backlog_id": _stable_id("task017a-productization-backlog", "PROPOSAL", review["baseline_logical_api_proposal_id"]), "item_type": "BASELINE_PROPOSAL",
            "source_id": review["baseline_logical_api_proposal_id"], "decision_status": review["recommendation"],
            "productization_implication": review["productization_implication"], "open_dependencies": review["evidence_gaps"],
            "task018_019_may_help": ["RESOURCE_TAXONOMY", "COMMON_BUSINESS_PURPOSE"],
            "task018_019_cannot_prove": ["SHARED_LIFECYCLE_OWNER", "CONSUMER_INTENT", "RELEASE_BOUNDARY", "ACTIVE_PRODUCTION_USAGE", "SAFE_SUBSTITUTION"],
            "next_gate": NEXT_GATE, "architect_acceptance": "PENDING", "product_design_authorized": False,
        })
    for adjunct in oversized:
        backlog.append({
            "backlog_id": _stable_id("task017a-productization-backlog", "OVERSIZED", adjunct["adjunct_review_id"]), "item_type": "OVERSIZED_ADJUNCT",
            "source_id": adjunct["adjunct_review_id"], "decision_status": adjunct["recommendation"], "productization_implication": adjunct["productization_implication"],
            "open_dependencies": ["UNRESOLVED_OVERSIZED_MEMBERS", "OWNER_CONSUMER_AND_RELEASE_EVIDENCE"],
            "task018_019_may_help": ["RESOURCE_TAXONOMY", "COMMON_BUSINESS_PURPOSE"], "task018_019_cannot_prove": ["SHARED_LIFECYCLE_OWNER", "ACTIVE_PRODUCTION_USAGE", "SAFE_SUBSTITUTION"],
            "next_gate": NEXT_GATE, "architect_acceptance": "PENDING", "product_design_authorized": False,
        })
    for link in links:
        backlog.append({
            "backlog_id": _stable_id("task017a-productization-backlog", "CROSS_LINK", link["cross_api_link_id"]), "item_type": "CROSS_API_LINK",
            "source_id": link["cross_api_link_id"], "decision_status": link["link_status"], "productization_implication": link["productization_implication"],
            "open_dependencies": ["CROSS_API_LIFECYCLE_OWNER", "CONSUMER_AND_CONTRACT_INTENT"],
            "task018_019_may_help": ["RESOURCE_TAXONOMY", "COMMON_BUSINESS_PURPOSE"], "task018_019_cannot_prove": ["SHARED_LIFECYCLE_OWNER", "CONSUMER_INTENT", "ACTIVE_PRODUCTION_USAGE", "SAFE_SUBSTITUTION"],
            "next_gate": NEXT_GATE, "architect_acceptance": "PENDING", "product_design_authorized": False,
        })
    backlog.sort(key=lambda v: v["backlog_id"])

    _write_jsonl(paths["reviews"], reviews); _write_jsonl(paths["oversized"], oversized); _write_jsonl(paths["cross_links"], links); _write_jsonl(paths["backlog"], backlog)
    manifest = {
        "rules_version": RULES_VERSION, "scope": "TASK017A_BOUNDED_ARCHITECTURE_REVIEW",
        "summary": {"proposal_review_count": len(reviews), "recommendation_counts": dict(sorted(Counter(v["recommendation"] for v in reviews).items())), "reviewed_member_occurrence_count": sum(v["member_count"] for v in reviews), "oversized_review_count": len(oversized), "oversized_operation_count": sum(v["operation_count"] for v in oversized), "cross_api_link_count": len(links), "backlog_count": len(backlog)},
        "full_task017_regenerated": False, "all_pairs_search_performed": False, "primary_memberships_changed": 0, "architect_approval_count": 0,
        "productization_readiness_gate": {"position": NEXT_GATE, "design_authorized": False},
        "inputs": {k: _fingerprint(v, root) for k, v in inputs.items()},
        "outputs": {k: _fingerprint(paths[k], root, len(value)) for k, value in (("reviews", reviews), ("oversized", oversized), ("cross_links", links), ("backlog", backlog))},
    }
    _write_json(paths["manifest"], manifest)
    return {"reviews": reviews, "oversized": oversized, "cross_links": links, "backlog": backlog, "manifest": manifest}
