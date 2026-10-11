"""Task 018A bounded, operation-centered business-domain validation sample."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


RULES_VERSION = "task018a-operation-domain-validation-v1"
ALIGNMENT_GATE = "ENTERPRISE_DOMAIN_ALIGNMENT_REVIEW_BEFORE_TASK018B"
OUTPUTS = {
    "taxonomy": Path("indexes/task018a_candidate_enterprise_domain_taxonomy.json"),
    "cases": Path("indexes/task018a_sampled_operation_domain_cases.jsonl"),
    "footprints": Path("indexes/task018a_api_domain_footprint_sample.jsonl"),
    "enrichment": Path("indexes/task018a_task017a_domain_enrichment_links.jsonl"),
    "manifest": Path("indexes/task018a_domain_validation_manifest.json"),
}

CLASSIFICATION_STATUSES = {
    "DIRECTLY_SUPPORTED", "PROVISIONAL_SUPPORTED", "MULTIPLE_DOMAIN_CANDIDATES",
    "CONFLICTING_EVIDENCE", "INSUFFICIENT_BUSINESS_SEMANTICS",
    "TECHNICAL_UTILITY_EVIDENCED", "TEST_OR_POC_EVIDENCED",
}

# Selection is architecture-stratified, not a score or search over the estate.
PROPOSAL_SAMPLE = {
    "RETAIN_PROVISIONAL_COHESIVE_BOUNDARY": (
        "nic-prtissuespecialpermit", "mhrsd-submitsaudicertificate", "nic-submitrunawayrequest",
        "mhrsd-raiseobjectionrequest", "nic-submitvisa",
    ),
    "SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES": (
        "getlookups", "mcs-rest-services", "takamol-svp-apis-v1", "mci-rest-services",
        "mhrsd3-rest-services", "kyan-user-validation", "nic2-rest-services", "s3-client",
        "accessmanagement-supportcenter", "queryqanagement-supportcentre",
        "adminmanagement-supportcentre", "ajeervisaservice",
    ),
    "KEEP_AS_IS_EXPOSURE_NO_LOGICAL_BOUNDARY_ASSERTION": (
        "getunifiednumberworkpermit", "sadad-billupload", "qiwa-qwallet-qwalletcashoutrequest",
        "establishment-profile-contact", "qks-updateappointment",
    ),
    "REQUIRES_TARGETED_EVIDENCE": (
        "ajeer-bulk-contracts", "ethaq-employeecontractinformation", "ajeer-bulk-payments",
        "nic-rest-services", "sadad-billcancel",
    ),
    "TECHNICAL_OR_TEST_EXPOSURE_REVIEW": (
        "graphql_poc", "qiwa-streaming-v2", "validate-jwt",
        "cachemanagement-supportcentre", "test-poc",
    ),
}

# These are hypotheses derived from operation evidence. They are deliberately
# responsibility-oriented and include ambiguous umbrella/technical candidates.
TAXONOMY_RULES = (
    ("Visa Administration", "DOMAIN_CANDIDATE", r"\bvisa\b", "visa applications, transactions and cancellations", "permits and generalized employment"),
    ("Work Permit Administration", "SUBDOMAIN_CANDIDATE", r"permit|work.?permit", "work/special permit records and decisions", "visas and generic authorization tokens"),
    ("Employment Contract Administration", "DOMAIN_CANDIDATE", r"employee contract|employment contract|contract uuid|contract proposal|bulk contract", "employment-contract records and lifecycle actions", "commercial registrations and technical contracts"),
    ("Establishment Registry and Profile", "DOMAIN_CANDIDATE", r"estab|establishment|commercial registration|\bcr details\b|cr number|ownership|branches", "establishment identity, registration and profile facts", "workforce transactions merely carrying an establishment identifier"),
    ("Commercial Registration", "SUBDOMAIN_CANDIDATE", r"commercial registration|\bcr details\b|cr number|basic cr|cr information", "commercial-registration facts and history", "generic establishment operations without registration evidence"),
    ("Workforce Records", "UMBRELLA_CANDIDATE", r"employee|laborer|labour|labor|citizen|foreigner|worker|workforce", "employee/laborer/person workforce records", "identity infrastructure and unrelated user accounts"),
    ("Workforce Qualification and Training", "DOMAIN_CANDIDATE", r"training|qualification|professional accreditation|saudi certificate", "workforce training, qualifications and professional accreditation", "technical test endpoints and generic certificates"),
    ("Professional Testing Services", "SUBDOMAIN_CANDIDATE", r"test center|test_center", "professional test-center records and status requests", "software tests, POCs and mocks"),
    ("Occupational Safety Assessment", "DOMAIN_CANDIDATE", r"assessment.?visit|self.?assessment|performance.?card|occupational safety", "occupational-safety assessments and performance cards", "generic health checks"),
    ("Support Request Management", "DOMAIN_CANDIDATE", r"sc.?request|support request|apprejscreq|cancelscreq", "support-request decisions and cancellation", "support-centre technical administration"),
    ("Reference Data Management", "SHARED_SERVICE_CANDIDATE", r"lookup|countries|embassies|marital|occupations|categor(?:y|ies)", "explicit reusable reference lists", "transactional business records"),
    ("Payment and Billing", "DOMAIN_CANDIDATE", r"payment|bill|credit|cashout|qwallet", "payments, bills, credits and settlement notifications", "non-financial status notifications"),
    ("User Access Administration", "TECHNICAL_NAMESPACE_CANDIDATE", r"grantaccess|revokeaccess|service.?to.?user|user account|authenticate|delegator|owner|national id", "access assignment and identity-verification operations", "business-party ownership unless directly documented"),
    ("Conversation Management", "DOMAIN_CANDIDATE", r"conversation", "conversation records and lifecycle actions", "transport streaming technology"),
    ("Appointment Administration", "DOMAIN_CANDIDATE", r"appointment", "appointment records and status changes", "unrelated scheduling infrastructure"),
    ("Wage Protection Compliance", "SUBDOMAIN_CANDIDATE", r"wps|wage protection", "wage-protection certificates and compliance evidence", "generic certificate retrieval"),
    ("Labor Compliance", "UMBRELLA_CANDIDATE", r"violation|saudization|nitaq|tawteen|runaway|prison status", "labor compliance, localization and worker-status evidence", "general workforce master data"),
    ("Labor Objection Administration", "SUBDOMAIN_CANDIDATE", r"objection", "labor objection requests and references", "generic support tickets"),
    ("Worker Absence Reporting", "SUBDOMAIN_CANDIDATE", r"run.?away", "worker runaway/absence reports and validation", "general worker profiles"),
    ("Employment Status Administration", "SUBDOMAIN_CANDIDATE", r"employment.?status", "employment-status enquiries and records", "broad employee master data"),
    ("Technical Integration Utilities", "TECHNICAL_NAMESPACE_CANDIDATE", r"graphql|jwt|/api/s3|bucket|cache|stream|token|rate.?limit", "protocol, token, storage, caching and transport utilities", "business responsibility domains"),
)

TEST_IDENTITY = re.compile(r"(?:^|[-_])(test|poc|mock)(?:$|[-_])", re.I)


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
        display = path.relative_to(root).as_posix()
    except ValueError:
        display = path.as_posix()
    value: dict[str, Any] = {"path": display, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    if count is not None:
        value["record_count"] = count
    return value


def _taxonomy() -> tuple[list[dict[str, Any]], dict[str, tuple[dict[str, Any], re.Pattern[str]]]]:
    values = []
    matchers = {}
    for name, candidate_type, pattern, inclusion, exclusion in TAXONOMY_RULES:
        candidate_id = _stable_id("task018a-domain-candidate", name, candidate_type)
        row = {
            "candidate_domain_id": candidate_id, "candidate_label": name, "candidate_type": candidate_type,
            "inclusion_rule": inclusion, "exclusion_rule": exclusion, "supported_objects": [], "observed_aliases": [],
            "source_basis": "TASK014_015_OPERATION_EVIDENCE_IN_BOUNDED_SAMPLE",
            "enterprise_alignment": "PENDING", "cross_layer_verification": "UNAVAILABLE",
            "domain_approved": False, "capability_assignment": None,
        }
        values.append(row); matchers[candidate_id] = (row, re.compile(pattern, re.I))
    return values, matchers


def _dimension(status: str, values: list[str], refs: list[str], limitation: str | None = None) -> dict[str, Any]:
    result = {"status": status, "values": values, "evidence_refs": refs}
    if limitation:
        result["limitation"] = limitation
    return result


def _classify_operation(operation: dict[str, Any], observed: dict[str, Any], matchers: dict[str, tuple[dict[str, Any], re.Pattern[str]]]) -> dict[str, Any]:
    function = observed["candidate_observed_function"]
    resource = (function.get("business_object_or_resource_phrase") or "").strip()
    action = (function.get("action_verb") or "").strip()
    provenance = observed["source_facts"]["source_provenance"]
    ref = f"{provenance['source_path']}#{provenance['source_pointer']}"
    facts = observed["source_facts"]
    description = " ".join(str(facts.get(key) or "") for key in ("summary", "description"))
    sources = (("BUSINESS_OBJECT", resource), ("EXACT_PATH", operation["exact_path"]), ("SOURCE_DESCRIPTION", description))
    candidates = []
    for candidate_id, (candidate, matcher) in matchers.items():
        matched_sources = [label for label, text in sources if text and matcher.search(text)]
        if matched_sources:
            candidates.append({
                "candidate_domain_id": candidate_id, "candidate_label": candidate["candidate_label"],
                "candidate_type": candidate["candidate_type"], "matched_evidence": matched_sources,
            })
    candidates.sort(key=lambda v: v["candidate_domain_id"])
    nature = function.get("operation_nature")
    direct_test = bool(TEST_IDENTITY.search(operation["current_api_name"])) and "test center" not in resource.lower()
    technical = nature == "TECHNICAL_OPERATION" or any(v["candidate_type"] == "TECHNICAL_NAMESPACE_CANDIDATE" for v in candidates)
    contradictory = bool(observed.get("contradictory_signals"))
    business_candidates = [v for v in candidates if v["candidate_type"] != "TECHNICAL_NAMESPACE_CANDIDATE"]
    primary = None
    if direct_test:
        status, reason = "TEST_OR_POC_EVIDENCED", "SOURCE_API_IDENTITY_EXPLICIT_TEST_POC_OR_MOCK"
    elif technical and not business_candidates:
        status, reason = "TECHNICAL_UTILITY_EVIDENCED", "OPERATION_EVIDENCE_MATCHES_TECHNICAL_NAMESPACE"
    elif contradictory:
        status, reason = "CONFLICTING_EVIDENCE", "TASK015_CONTRADICTORY_SIGNALS_RETAINED"
    elif len(business_candidates) > 1:
        status, reason = "MULTIPLE_DOMAIN_CANDIDATES", "OPERATION_EVIDENCE_SPANS_MULTIPLE_RESPONSIBILITY_CANDIDATES"
    elif not business_candidates:
        status, reason = "INSUFFICIENT_BUSINESS_SEMANTICS", "NO_RESPONSIBILITY_CANDIDATE_SUPPORTED_BY_OPERATION_EVIDENCE"
    else:
        candidate = business_candidates[0]
        object_match = "BUSINESS_OBJECT" in candidate["matched_evidence"]
        direct = observed["interpretation_status"] == "EXPLICITLY_DESCRIBED" and object_match
        status = "DIRECTLY_SUPPORTED" if direct else "PROVISIONAL_SUPPORTED"
        reason = "EXPLICIT_OBJECT_MATCHES_RESPONSIBILITY_RULE" if direct else "PATH_OR_DESCRIPTION_SUPPORTS_PROVISIONAL_RESPONSIBILITY"
        if candidate["candidate_type"] not in {"UMBRELLA_CANDIDATE", "SHARED_SERVICE_CANDIDATE"}:
            primary = candidate["candidate_domain_id"]
        else:
            reason += "_BUT_UMBRELLA_OR_SHARED_SERVICE_NEEDS_ALIGNMENT"
    if status not in CLASSIFICATION_STATUSES:
        raise ValueError("invalid Task 018A classification status")
    object_status = "DIRECTLY_EVIDENCED" if resource and observed["interpretation_status"] == "EXPLICITLY_DESCRIBED" else ("PROVISIONAL_SIGNAL" if resource else "NOT_EVIDENCED_FROM_APIC")
    action_status = "DIRECTLY_EVIDENCED" if action and observed["interpretation_status"] == "EXPLICITLY_DESCRIBED" else ("PROVISIONAL_SIGNAL" if action else "NOT_EVIDENCED_FROM_APIC")
    return {
        "classification_status": status, "reason_codes": [reason], "primary_domain_candidate_id": primary,
        "alternative_candidates": candidates, "enterprise_alignment": "PENDING",
        "semantic_dimensions": {
            "business_object": _dimension(object_status, [resource] if resource else [], [ref]),
            "documented_action": _dimension(action_status, [action] if action else [], [ref]),
            "process": _dimension("NOT_EVIDENCED_FROM_APIC", [], [ref], "An operation action is not promoted to an end-to-end business process."),
            "state": _dimension("NOT_EVIDENCED_FROM_APIC", [], [ref], "No authoritative business-state model is supplied."),
            "capability_signal": _dimension("NOT_EVIDENCED_FROM_APIC", [], [ref], "Task 019 capability mapping is not authorized."),
            "event": _dimension("NOT_EVIDENCED_FROM_APIC", [], [ref], "HTTP operations are not assumed to be business events."),
        },
        "contradictory_signals": observed.get("contradictory_signals", []),
        "source_limitations": sorted(set(observed.get("confidence_limitations", []) + [
            "APIC_CONFIGURATION_ONLY", "ENTERPRISE_OWNER_AND_CROSS_LAYER_MODEL_UNAVAILABLE",
            "PRODUCTION_USAGE_NOT_PROVEN", "RUNTIME_EGRESS_NOT_PROVEN",
        ])),
    }


def _operation_record(operation_id: str, ledger: dict[str, dict[str, Any]], observed: dict[str, dict[str, Any]], matchers: dict[str, tuple[dict[str, Any], re.Pattern[str]]], task017_refs: dict[str, dict[str, set[str]]]) -> dict[str, Any]:
    source = ledger[operation_id]; interpretation = observed[source["task015_observed_function_id"]]
    facts = interpretation["source_facts"]; function = interpretation["candidate_observed_function"]
    backend = interpretation.get("backend_evidence", {})
    contract = facts.get("contract", {})
    exposure = source["relationship_exposure_context"]
    return {
        "task014_operation_id": operation_id, "task015_observed_function_id": source["task015_observed_function_id"],
        "canonical_api_id": source["canonical_api_id"], "current_api_name": source["current_api_name"],
        "current_api_version": source["current_api_version"], "method": source["method"], "exact_path": source["exact_path"],
        "documented_business_object": function.get("business_object_or_resource_phrase"), "documented_action": function.get("action_verb"),
        "semantic_certainty": interpretation["interpretation_status"], "evidence_strength": interpretation["evidence_strength"],
        "source_provenance": source["source_provenance"],
        "contract_context": {"security_requirement_present": contract.get("auth", {}).get("security_requirement_present"), "security_scheme_types": contract.get("auth", {}).get("security_scheme_types", [])},
        "exposure_context": {"accepted_product_ids": exposure.get("accepted_product_ids", []), "accepted_plan_ids": exposure.get("accepted_plan_ids", []), "subscription_evidence_state": exposure.get("subscription_evidence_state"), "operation_consumption_proven": False, "runtime_activity_proven": False},
        "backend_evidence_scope": {"configured_operation_scoped_count": len(backend.get("configured_operation_scoped_facts", [])), "candidate_inherited_context_count": len(backend.get("candidate_inherited_context_projection", [])), "runtime_egress_proven": False},
        "task017a_source_links": {key: sorted(values) for key, values in task017_refs.get(operation_id, {}).items()},
        "domain_assessment": _classify_operation(source, interpretation, matchers),
        "functional_equivalence_approved": False, "logical_api_membership_changed": False,
        "production_usage_inferred": False, "domain_approved": False,
    }


def _case_strata(origin: str, source: dict[str, Any]) -> list[str]:
    strata = [origin]
    if origin == "CROSS_API_LINK":
        strata.extend(["CROSS_API_RESPONSIBILITY_COMPARISON", "CHALLENGING_BOUNDARY"])
        if source["link_status"] == "NEGATIVE_CONTROL_NO_GROUP": strata.append("HARD_NEGATIVE_CONTROL")
        if source["candidate_label"] == "SC Request Workflow": strata.append("SC_REQUEST_ANCHOR")
        if "Variant" in source["candidate_label"] or "Seasonal Visa" in source["candidate_label"]: strata.append("VERSION_OR_VARIANT")
    elif origin == "OVERSIZED_ADJUNCT":
        strata.extend(["DIVERGING_RESPONSIBILITY_WITHIN_ONE_API", "CHALLENGING_BOUNDARY"])
        if not source["subfamily_candidates"]: strata.append("HARD_NEGATIVE_CONTROL")
    else:
        strata.append(source["recommendation"])
        if source["recommendation"] == "SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES": strata.extend(["DIVERGING_RESPONSIBILITY_WITHIN_ONE_API", "CHALLENGING_BOUNDARY"])
        if source["recommendation"] in {"KEEP_AS_IS_EXPOSURE_NO_LOGICAL_BOUNDARY_ASSERTION", "TECHNICAL_OR_TEST_EXPOSURE_REVIEW"}: strata.append("HARD_NEGATIVE_CONTROL")
        if source["current_api_name"] in {"mcs-rest-services", "nic2-rest-services", "mhrsd3-rest-services"}: strata.append("API_NAME_MASKS_MULTIPLE_PURPOSES")
    return sorted(set(strata))


def _make_case(origin: str, source: dict[str, Any], operation_ids: list[str], ledger: dict[str, dict[str, Any]], observed: dict[str, dict[str, Any]], matchers: dict[str, tuple[dict[str, Any], re.Pattern[str]]], task017_refs: dict[str, dict[str, set[str]]]) -> dict[str, Any]:
    operations = [_operation_record(v, ledger, observed, matchers, task017_refs) for v in operation_ids]
    candidate_ids = sorted({x["candidate_domain_id"] for op in operations for x in op["domain_assessment"]["alternative_candidates"]})
    statuses = sorted({op["domain_assessment"]["classification_status"] for op in operations})
    if origin == "CROSS_API_LINK":
        label = source["candidate_label"]; positive = source["positive_evidence"]; counter = source["contrary_evidence"]
        alternative = source["competing_alternatives"]
        source_id = source["cross_api_link_id"]
    elif origin == "OVERSIZED_ADJUNCT":
        label = f"{source['current_api_name']} oversized responsibility sample"; positive = [f"Bounded sample covers {len(operation_ids)} of {source['operation_count']} operations across direct resource/path evidence."]
        counter = [source["specific_counterevidence"], "This sample cannot classify the unsampled remainder or the whole canonical API."]
        alternative = ["Retain sampled operation hypotheses independently; leave unresolved members unclassified."]
        source_id = source["adjunct_review_id"]
    else:
        label = f"{source['current_api_name']} operation responsibility sample"; positive = [source["positive_cohesion_evidence"]]
        counter = [source["specific_counterevidence"]]; alternative = [source["alternative_boundary"]]
        source_id = source["architecture_review_id"]
    value = {
        "domain_case_id": _stable_id("task018a-domain-case", origin, source_id, operation_ids),
        "case_origin": origin, "source_task017a_id": source_id, "case_label": label,
        "sampled_operation_count": len(operations), "sampled_operations": operations,
        "candidate_domain_ids": candidate_ids, "operation_classification_statuses": statuses,
        "positive_evidence": positive, "specific_counterevidence": counter, "alternative": alternative,
        "strata": _case_strata(origin, source),
        "case_assessment": "OPERATION_LEVEL_HYPOTHESES_ONLY",
        "api_whole_classified": False, "enterprise_domain_alignment": "PENDING",
        "logical_api_or_product_inferred": False, "functional_equivalence_inferred": False,
    }
    if origin == "CROSS_API_LINK":
        value["frozen_task017_control"] = source["frozen_task017_control"]
    return value


def _sample_cases(reviews: list[dict[str, Any]], oversized: list[dict[str, Any]], links: list[dict[str, Any]], ledger: dict[str, dict[str, Any]], observed: dict[str, dict[str, Any]], matchers: dict[str, tuple[dict[str, Any], re.Pattern[str]]], task017_refs: dict[str, dict[str, set[str]]]) -> list[dict[str, Any]]:
    used: set[str] = set(); cases = []
    for link in links:
        operation_ids = [v for v in link["member_operation_ids"] if v not in used]
        if operation_ids:
            used.update(operation_ids); cases.append(_make_case("CROSS_API_LINK", link, operation_ids, ledger, observed, matchers, task017_refs))
    for adjunct in oversized:
        choices = []
        for candidate in adjunct["subfamily_candidates"]:
            match = next((v for v in candidate["member_operation_ids"] if v not in used and v not in choices), None)
            if match: choices.append(match)
        for operation_id in adjunct["unresolved_operation_ids"] + adjunct["original_member_operation_ids"]:
            if len(choices) >= 3: break
            if operation_id not in used and operation_id not in choices: choices.append(operation_id)
        choices = choices[:3]
        if choices:
            used.update(choices); cases.append(_make_case("OVERSIZED_ADJUNCT", adjunct, choices, ledger, observed, matchers, task017_refs))
    for recommendation, names in PROPOSAL_SAMPLE.items():
        for name in names:
            review = next(v for v in reviews if v["recommendation"] == recommendation and v["current_api_name"] == name)
            available = [v["task014_operation_id"] for v in review["operations"] if v["task014_operation_id"] not in used]
            limit = 2 if recommendation in {"RETAIN_PROVISIONAL_COHESIVE_BOUNDARY", "SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES"} else 1
            choices = []
            if recommendation == "SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES" and review["proposed_sub_boundaries"]:
                boundary_order = [review["proposed_sub_boundaries"][0]]
                if len(review["proposed_sub_boundaries"]) > 1:
                    boundary_order.append(review["proposed_sub_boundaries"][-1])
                for boundary in boundary_order:
                    match = next((v for v in boundary["member_operation_ids"] if v in available and v not in choices), None)
                    if match: choices.append(match)
            choices.extend(v for v in available if v not in choices)
            choices = choices[:limit]
            if choices:
                used.update(choices); cases.append(_make_case("TASK017A_PROPOSAL", review, choices, ledger, observed, matchers, task017_refs))
    cases.sort(key=lambda v: v["domain_case_id"])
    if not 40 <= len(cases) <= 60 or not 70 <= len(used) <= 100:
        raise ValueError(f"Task 018A sample outside bounds: {len(cases)} cases / {len(used)} operations")
    return cases


def _footprints(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        for operation in case["sampled_operations"]:
            grouped[operation["canonical_api_id"]].append(operation)
    values = []
    for canonical_api_id, operations in sorted(grouped.items()):
        values.append({
            "api_domain_footprint_id": _stable_id("task018a-api-domain-footprint", canonical_api_id, sorted(v["task014_operation_id"] for v in operations)),
            "canonical_api_id": canonical_api_id, "current_api_name": operations[0]["current_api_name"], "current_api_version": operations[0]["current_api_version"],
            "sampled_operation_count": len(operations), "sampled_operation_ids": sorted(v["task014_operation_id"] for v in operations),
            "primary_candidate_ids": sorted({v["domain_assessment"]["primary_domain_candidate_id"] for v in operations if v["domain_assessment"]["primary_domain_candidate_id"]}),
            "alternative_candidate_ids": sorted({x["candidate_domain_id"] for v in operations for x in v["domain_assessment"]["alternative_candidates"]}),
            "classification_status_counts": dict(sorted(Counter(v["domain_assessment"]["classification_status"] for v in operations).items())),
            "sampled_operations_only": True, "whole_api_domain_classified": False,
            "enterprise_alignment": "PENDING", "domain_approved": False,
        })
    return values


def _enrichment(backlog: list[dict[str, Any]], reviews: list[dict[str, Any]], oversized: list[dict[str, Any]], links: list[dict[str, Any]], cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_operations = {v["baseline_logical_api_proposal_id"]: [x["task014_operation_id"] for x in v["operations"]] for v in reviews}
    source_operations.update({v["adjunct_review_id"]: v["original_member_operation_ids"] for v in oversized})
    source_operations.update({v["cross_api_link_id"]: v["member_operation_ids"] for v in links})
    sampled = {op["task014_operation_id"]: op for case in cases for op in case["sampled_operations"]}
    values = []
    for item in backlog:
        operation_ids = source_operations[item["source_id"]]
        sampled_ops = [sampled[v] for v in operation_ids if v in sampled]
        values.append({
            "domain_enrichment_link_id": _stable_id("task018a-task017a-enrichment", item["backlog_id"], RULES_VERSION),
            "task017a_backlog_id": item["backlog_id"], "task017a_item_type": item["item_type"], "task017a_source_id": item["source_id"],
            "task017a_decision_status_preserved": item["decision_status"], "task017a_record_sha256": _hash(item),
            "sample_status": "SAMPLED" if sampled_ops else "NOT_SAMPLED_IN_BOUNDED_TASK018A",
            "sampled_operation_ids": sorted(v["task014_operation_id"] for v in sampled_ops),
            "candidate_domain_ids": sorted({x["candidate_domain_id"] for v in sampled_ops for x in v["domain_assessment"]["alternative_candidates"]}),
            "primary_domain_candidate_ids": sorted({v["domain_assessment"]["primary_domain_candidate_id"] for v in sampled_ops if v["domain_assessment"]["primary_domain_candidate_id"]}),
            "enrichment_only": True, "baseline_rewritten": False, "logical_api_membership_changed": False,
            "productization_decision_changed": False, "domain_similarity_proves_functional_equivalence": False,
            "enterprise_alignment": "PENDING",
        })
    return sorted(values, key=lambda v: v["domain_enrichment_link_id"])


def build_domain_validation(root: Path, *, output_paths: dict[str, Path] | None = None) -> dict[str, Any]:
    root = root.resolve(); paths = {k: (output_paths or {}).get(k, root / v) for k, v in OUTPUTS.items()}
    inputs = {
        "semantic_operations": root / "indexes/semantic_operation_inventory.jsonl", "observed_functions": root / "indexes/observed_function_inventory.jsonl",
        "task017_ledger": root / "indexes/task017_full_operation_disposition.jsonl", "task017a_reviews": root / "indexes/task017a_all_71_architecture_reviews.jsonl",
        "task017a_oversized": root / "indexes/task017a_five_oversized_adjunct.jsonl", "task017a_links": root / "indexes/task017a_cross_api_opportunity_links.jsonl",
        "task017a_backlog": root / "indexes/task017a_productization_decision_backlog.jsonl", "task017a_manifest": root / "indexes/task017a_architecture_review_manifest.json",
        "task017_expanded": root / "tests/evidence/task-017/expanded-validation/expanded_sample_register.jsonl", "implementation": Path(__file__).resolve(),
    }
    semantic = _jsonl(inputs["semantic_operations"]); observed_values = _jsonl(inputs["observed_functions"]); ledger_values = _jsonl(inputs["task017_ledger"])
    reviews = _jsonl(inputs["task017a_reviews"]); oversized = _jsonl(inputs["task017a_oversized"]); links = _jsonl(inputs["task017a_links"]); backlog = _jsonl(inputs["task017a_backlog"])
    expanded = _jsonl(inputs["task017_expanded"])
    if (len(semantic), len(observed_values), len(ledger_values), len(reviews), len(oversized), len(links), len(backlog), len(expanded)) != (2414, 2414, 2414, 71, 5, 14, 90, 46):
        raise ValueError("Task 018A frozen baseline reconciliation mismatch")
    ledger = {v["task014_operation_id"]: v for v in ledger_values}; observed = {v["observed_function_id"]: v for v in observed_values}
    expanded_by_id = {v["expanded_case_id"]: v for v in expanded}
    for link in links:
        control = expanded_by_id[link["source_case_id"]]
        link["frozen_task017_control"] = {
            "evidence_sufficiency": control["result_axes"]["evidence_sufficiency"],
            "supported_action_intents": sorted({action for member in control["members"] for action in member["supported_actions"]}),
            "alternative_boundary": control["alternative_boundary"],
            "architect_acceptance": control["result_axes"]["architect_acceptance"],
        }
    task017_refs: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for review in reviews:
        for op in review["operations"]: task017_refs[op["task014_operation_id"]]["proposal_review_ids"].add(review["architecture_review_id"])
    for adjunct in oversized:
        for op in adjunct["original_member_operation_ids"]: task017_refs[op]["oversized_adjunct_ids"].add(adjunct["adjunct_review_id"])
    for link in links:
        for op in link["member_operation_ids"]: task017_refs[op]["cross_api_link_ids"].add(link["cross_api_link_id"])
    taxonomy, matchers = _taxonomy()
    cases = _sample_cases(reviews, oversized, links, ledger, observed, matchers, task017_refs)
    for candidate in taxonomy:
        related = [op for case in cases for op in case["sampled_operations"] if any(v["candidate_domain_id"] == candidate["candidate_domain_id"] for v in op["domain_assessment"]["alternative_candidates"])]
        candidate["supported_objects"] = sorted({v["documented_business_object"] for v in related if v["documented_business_object"]})
        candidate["observed_aliases"] = sorted({v["exact_path"] for v in related})[:20]
        candidate["sampled_operation_count"] = len(related)
    footprints = _footprints(cases); enrichment = _enrichment(backlog, reviews, oversized, links, cases)
    taxonomy_document = {
        "rules_version": RULES_VERSION, "taxonomy_status": "APIC_DERIVED_CANDIDATE_NOT_ENTERPRISE_APPROVED",
        "unit_of_classification": "SOURCE_HTTP_OPERATION", "enterprise_alignment": "PENDING",
        "cross_layer_verification": "UNAVAILABLE", "candidate_count": len(taxonomy), "candidates": taxonomy,
        "guardrails": {"whole_api_inheritance": False, "capability_mapping_performed": False, "domain_similarity_proves_equivalence": False, "domain_similarity_proves_product_boundary": False},
    }
    _write_json(paths["taxonomy"], taxonomy_document); _write_jsonl(paths["cases"], cases); _write_jsonl(paths["footprints"], footprints); _write_jsonl(paths["enrichment"], enrichment)
    operations = [op for case in cases for op in case["sampled_operations"]]
    summary = {
        "case_count": len(cases), "unique_operation_count": len({v["task014_operation_id"] for v in operations}),
        "sampled_api_count": len(footprints), "classification_status_counts": dict(sorted(Counter(v["domain_assessment"]["classification_status"] for v in operations).items())),
        "case_origin_counts": dict(sorted(Counter(v["case_origin"] for v in cases).items())),
        "hard_negative_case_count": sum("HARD_NEGATIVE_CONTROL" in v["strata"] for v in cases),
        "challenging_boundary_case_count": sum("CHALLENGING_BOUNDARY" in v["strata"] for v in cases),
        "task017a_enrichment_count": len(enrichment), "enterprise_domain_approval_count": 0,
    }
    manifest = {
        "rules_version": RULES_VERSION, "scope": "TASK018A_BOUNDED_OPERATION_DOMAIN_VALIDATION", "summary": summary,
        "full_task018_performed": False, "task019_performed": False, "all_pairs_search_performed": False,
        "task017a_records_rewritten": 0, "logical_api_memberships_changed": 0, "productization_decisions_changed": 0,
        "enterprise_alignment_gate": {"position": ALIGNMENT_GATE, "architect_acceptance": "PENDING"},
        "inputs": {k: _fingerprint(v, root) for k, v in inputs.items()},
        "outputs": {k: _fingerprint(paths[k], root, count) for k, count in (("taxonomy", len(taxonomy)), ("cases", len(cases)), ("footprints", len(footprints)), ("enrichment", len(enrichment)))},
    }
    _write_json(paths["manifest"], manifest)
    return {"taxonomy": taxonomy_document, "cases": cases, "footprints": footprints, "enrichment": enrichment, "manifest": manifest}
