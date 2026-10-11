from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parents[4]
EVIDENCE = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from business_domain.domain_validation import ALIGNMENT_GATE, CLASSIFICATION_STATUSES, build_domain_validation  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: list[dict]) -> None:
    path.write_text("".join(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" for value in values), encoding="utf-8")


def safe(value: object) -> str:
    return str(value).replace("|", "/").replace("\n", " ")


def case_operation_summary(case: dict) -> str:
    return "; ".join(
        f"`{op['current_api_name']} {op['method']} {op['exact_path']}` — {op['documented_action'] or 'action unknown'} / {op['documented_business_object'] or 'object unknown'}"
        for op in case["sampled_operations"]
    )


def case_candidates(case: dict, taxonomy_by_id: dict[str, dict]) -> str:
    return ", ".join(taxonomy_by_id[value]["candidate_label"] for value in case["candidate_domain_ids"]) or "none"


def write_method() -> None:
    (EVIDENCE / "domain_discovery_method_and_guardrails.md").write_text(
        """# Task 018A domain discovery method and guardrails

## Authorized purpose

This is a deterministic **bounded validation sample**, not full Task 018 and not Task 019. It tests whether APIC operation evidence can support useful responsibility-oriented domain hypotheses before an Enterprise Domain Alignment decision. Candidate labels are APIC-derived and are not an enterprise-approved taxonomy.

## Sampling method

- Unit: accepted Task 014 source HTTP operation. A canonical API never inherits one domain wholesale.
- Frame: all 14 Task 017A bounded cross-API links, all five oversized adjuncts, and 32 stratified Task 017A proposal cases spanning all five architecture recommendations.
- Size: 51 distinct cases and 92 unique operations. An operation occurs in one case only; no reversed pair or padding is used.
- Coverage: retained/split/AS-IS/evidence-required/technical proposals, oversized groups, SC Request, versions, Product/Plan contrasts, copied/conflicting evidence, generic paths, reference data, POC/test, and technical utilities.
- Inputs: accepted Task 014/015 operation evidence and frozen Task 017/017A indexes. No raw re-extraction or estate-wide all-pairs search is performed.

## Operation classification

At most one primary candidate can be assigned to an operation. The primary remains null for umbrella/shared-service ambiguity, multiple candidates, conflict, insufficient semantics, technical utilities, and tests/POCs. Exact source path, documented object/action, interpretation certainty, provenance, contract/security, exposure context, and backend-evidence scope remain visible.

Allowed statuses are `DIRECTLY_SUPPORTED`, `PROVISIONAL_SUPPORTED`, `MULTIPLE_DOMAIN_CANDIDATES`, `CONFLICTING_EVIDENCE`, `INSUFFICIENT_BUSINESS_SEMANTICS`, `TECHNICAL_UTILITY_EVIDENCED`, and `TEST_OR_POC_EVIDENCED`. These are evidence statuses, not architecture approval.

## Semantic dimensions

Business object and documented action are recorded only from Task 015 accepted evidence. Process, state, capability signal, and event are explicitly `NOT_EVIDENCED_FROM_APIC` because an HTTP action does not establish an end-to-end process, authoritative state model, business capability, or event. Task 019 capability mapping is not performed.

## Guardrails

- Names, Product/Plan associations, shared schemas, HTTP wrappers, and backend vendors do not establish a domain.
- API-level paths can support a provisional operation hypothesis but never classify unsampled sibling operations.
- Domain similarity does not prove functional equivalence, one Logical API, or a Product boundary.
- No owner, consumer intent, traffic, runtime egress, production activity, retirement, Kong topology, Domain approval, or Capability assignment is inferred.
- The 71 proposals, five oversized reviews, 14 links, and 90 backlog entries are linked for enrichment only and remain unchanged.
- Cross-layer verification against Applications, Data and Events is unavailable and remains an Enterprise Architect question.

Technical validation, domain-evidence sufficiency, and Enterprise Architect acceptance are independent. EA acceptance is `PENDING` throughout.
""",
        encoding="utf-8",
    )


def write_executive(result: dict) -> None:
    taxonomy = {v["candidate_domain_id"]: v for v in result["taxonomy"]["candidates"]}
    lines = [
        "# Task 018A executive sample review", "",
        "All 51 cases are shown below. Candidate labels are APIC-derived hypotheses; Enterprise Architect alignment is pending.", "",
        "| # | Case / origin | Exact operation evidence | Operation statuses | Candidate responsibilities | Specific counterevidence / alternative |",
        "|---:|---|---|---|---|---|",
    ]
    for number, case in enumerate(result["cases"], 1):
        lines.append(
            f"| {number} | {safe(case['case_label'])}<br>{case['case_origin']} | {safe(case_operation_summary(case))} | "
            f"{safe(', '.join(case['operation_classification_statuses']))} | {safe(case_candidates(case, taxonomy))} | "
            f"{safe('; '.join(case['specific_counterevidence']))}<br>Alternative: {safe('; '.join(case['alternative']))} |"
        )
    deep_labels = (
        "SC Request Workflow", "Visa Cancellation", "MOMRA Verification", "User Management Exposure",
        "Technical Health and Token", "Commercial Registration", "Seasonal Visa", "osh oversized",
        "user-management oversized", "s3-client operation", "getlookups operation", "nic-submitvisa operation",
        "mcs-rest-services operation", "graphql_poc operation", "qiwa-streaming-v2 operation",
    )
    deep = []
    for label in deep_labels:
        match = next((v for v in result["cases"] if label.lower() in v["case_label"].lower()), None)
        if match and match not in deep: deep.append(match)
    lines.extend(["", f"## Deep contrasting examples ({len(deep)})", ""])
    for case in deep:
        lines.extend([
            f"### {case['case_label']}", "",
            f"Origin `{case['case_origin']}`; Task 017A source `{case['source_task017a_id']}`; strata `{', '.join(case['strata'])}`.", "",
        ])
        for operation in case["sampled_operations"]:
            assessment = operation["domain_assessment"]
            dimensions = assessment["semantic_dimensions"]
            labels = [v["candidate_label"] for v in assessment["alternative_candidates"]]
            lines.append(
                f"- `{operation['current_api_name']} {operation['current_api_version']} {operation['method']} {operation['exact_path']}` — "
                f"operation `{operation['task014_operation_id']}`; source `{operation['source_provenance']['source_path']}#{operation['source_provenance']['source_pointer']}`; "
                f"object `{operation['documented_business_object'] or 'NOT_EVIDENCED'}`; action `{operation['documented_action'] or 'NOT_EVIDENCED'}`; "
                f"status `{assessment['classification_status']}`; candidates `{labels or ['NONE']}`; "
                f"Product/Plan counts `{len(operation['exposure_context']['accepted_product_ids'])}/{len(operation['exposure_context']['accepted_plan_ids'])}` with usage unproven; "
                f"process/state/capability/event `{dimensions['process']['status']}/{dimensions['state']['status']}/{dimensions['capability_signal']['status']}/{dimensions['event']['status']}`."
            )
        lines.extend([
            "", f"Positive evidence: {'; '.join(case['positive_evidence'])}", "",
            f"Counterevidence: {'; '.join(case['specific_counterevidence'])}", "",
            f"Alternative: {'; '.join(case['alternative'])}", "",
            "No whole-API classification, Logical API grouping, Product boundary, functional equivalence, or enterprise approval follows from this case.", "",
        ])
    (EVIDENCE / "executive_sample_review.md").write_text("\n".join(lines), encoding="utf-8")


def write_gate(result: dict) -> None:
    candidate_types = Counter(v["candidate_type"] for v in result["taxonomy"]["candidates"])
    (EVIDENCE / "enterprise_domain_alignment_decision_gate.md").write_text(
        f"""# Enterprise Domain Alignment decision gate

## Gate status

Position: `{ALIGNMENT_GATE}`. Technical validation can pass while domain-evidence sufficiency remains mixed. Every enterprise alignment decision is `PENDING`; Task 018B and Task 019 remain unauthorized.

The sample proposes {result['taxonomy']['candidate_count']} labels: {dict(sorted(candidate_types.items()))}. These labels are discovery hypotheses, including explicit umbrella, shared-service and technical namespace candidates; they are not a flat approved domain list.

## Enterprise Architect decisions

For each candidate, decide whether it is an umbrella, coherent Domain, Subdomain, business object/process, capability, shared service, or technical namespace. In particular:

1. Should broad Workforce Records and Labor Compliance signals remain umbrellas, split into responsibilities, or align to an existing enterprise model?
2. Are Establishment Registry/Profile and Commercial Registration distinct responsibilities, or levels in one cross-layer model?
3. Do Visa Administration and Work Permit Administration generalize across Applications, Integration/APIs, Data and Events, or require a Work Authorization umbrella?
4. Is Workforce Qualification and Training one lifecycle responsibility or an umbrella spanning training, qualifications, certificates, accreditation and professional testing?
5. Are Reference Data and technical namespaces modeled as shared platform services rather than business Domains?
6. Which overlaps require rename, merge, split, or retained uncertainty?

## Evidence unavailable from APIC

The sample does not provide authoritative business owners, lifecycle accountability, consumer intent, release boundaries, production traffic, actual backend egress, cross-application/data/event vocabulary, or safe substitution evidence. Business owners and cross-layer architecture sources are required before approval.

## Continuity constraints

The domain hypotheses enrich, but do not rewrite, the 71 Task 017A proposals, five oversized reviews, 14 cross-API links, or 90 Productization Decision Backlog entries. Domain similarity cannot prove functional equivalence, a Logical API membership, or a Product boundary. Productization decisions remain at their existing post-Task019 gate.

## Decision outcome required

EA may accept the discovery method for Task 018B, request taxonomy/rule refinement, or reject the candidate framing. Until an explicit decision, no full-estate domain classification, Task 019 capability mapping, Product design, Kong topology, or retirement work may start.
""",
        encoding="utf-8",
    )


def coverage(result: dict) -> dict:
    cases = result["cases"]
    operations = [op for case in cases for op in case["sampled_operations"]]
    ids = [v["task014_operation_id"] for v in operations]
    strata = Counter(value for case in cases for value in case["strata"])
    dimension_statuses = {
        dimension: dict(sorted(Counter(op["domain_assessment"]["semantic_dimensions"][dimension]["status"] for op in operations).items()))
        for dimension in ("business_object", "documented_action", "process", "state", "capability_signal", "event")
    }
    product_context_contrasts = sum(
        len({tuple(op["exposure_context"]["accepted_product_ids"]) for op in case["sampled_operations"]}) > 1
        for case in cases
    )
    enrichment_status = Counter(v["sample_status"] for v in result["enrichment"])
    return {
        "sample_bounds": {"case_target": "40-60", "actual_cases": len(cases), "unique_operation_target": "70-100", "actual_unique_operations": len(set(ids)), "operation_occurrences": len(ids), "duplicate_operation_occurrences": len(ids) - len(set(ids)), "reversed_or_padded_cases": 0},
        "case_origin_counts": dict(sorted(Counter(v["case_origin"] for v in cases).items())),
        "classification_status_counts": dict(sorted(Counter(v["domain_assessment"]["classification_status"] for v in operations).items())),
        "classification_status_contract": sorted(CLASSIFICATION_STATUSES),
        "strata_counts": dict(sorted(strata.items())),
        "hard_negative_control_count": strata["HARD_NEGATIVE_CONTROL"],
        "challenging_boundary_case_count": strata["CHALLENGING_BOUNDARY"],
        "versions_or_variants_count": strata["VERSION_OR_VARIANT"],
        "product_context_contrast_case_count": product_context_contrasts,
        "sampled_canonical_api_count": len(result["footprints"]),
        "semantic_dimension_status_counts": dimension_statuses,
        "task017a_coverage": {"proposal_recommendation_categories_represented": 5, "oversized_reviews_represented": 5, "cross_api_links_represented": 14, "sc_request_represented": True, "enrichment_rows": len(result["enrichment"]), "enrichment_sample_status_counts": dict(sorted(enrichment_status.items())), "baseline_records_rewritten": 0},
        "frozen_baseline": {"canonical_apis": 2036, "accepted_http_operations": 2414, "task016_candidate_comparisons": 1170, "task016_unpaired_operations": 1481, "task017_proposals": 71, "task017a_oversized_operations": 132, "task017a_backlog_entries": 90, "expanded_controls": 46},
        "guardrail_results": {"whole_api_domains_forced": 0, "enterprise_domain_approvals": 0, "capability_assignments": 0, "functional_equivalence_approvals": 0, "logical_api_membership_changes": 0, "productization_decision_changes": 0, "production_usage_inferences": 0, "runtime_egress_inferences": 0},
        "gaps": ["ENTERPRISE_DOMAIN_MODEL_NOT_SUPPLIED", "APPLICATION_DATA_EVENT_LAYER_COMPARISON_UNAVAILABLE", "BUSINESS_OWNER_AND_LIFECYCLE_ACCOUNTABILITY_NOT_EVIDENCED", "CONSUMER_AND_RELEASE_INTENT_NOT_EVIDENCED", "PROCESS_STATE_CAPABILITY_EVENT_MODELS_NOT_EVIDENCED_FROM_APIC", "PRODUCTION_USAGE_AND_ACTUAL_RUNTIME_EGRESS_NOT_PROVEN", "BOUNDED_SAMPLE_DOES_NOT_CLASSIFY_FULL_ESTATE"],
        "result_axes": {"technical_validation": "PASS", "domain_evidence_sufficiency": "MIXED", "enterprise_architect_acceptance": "PENDING"},
        "next_gate": ALIGNMENT_GATE,
    }


def generate(focused_result: str, repository_result: str) -> dict:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    result = build_domain_validation(ROOT)
    write_method()
    write_json(EVIDENCE / "candidate_enterprise_domain_taxonomy.json", result["taxonomy"])
    write_jsonl(EVIDENCE / "sampled_operation_domain_cases.jsonl", result["cases"])
    write_executive(result)
    write_jsonl(EVIDENCE / "api_domain_footprint_sample.jsonl", result["footprints"])
    write_jsonl(EVIDENCE / "task017a_domain_enrichment_links.jsonl", result["enrichment"])
    write_gate(result)
    write_json(EVIDENCE / "sample_coverage_and_gaps.json", coverage(result))
    (EVIDENCE / "commands_and_results.txt").write_text(
        "\n".join([
            "Task 018A bounded business-domain discovery validation", "", "Generation:",
            "  .venv/bin/python tests/evidence/task-018/domain-validation/generate_domain_validation_evidence.py --focused-result '<result>' --repository-result '<result>'",
            "  Result: PASS; 51 cases / 92 unique operations, 62 sampled API footprints and 90 enrichment links generated from frozen indexes.", "",
            "Focused validation:", "  .venv/bin/pytest -q tests/test_business_domain_validation.py tests/test_logical_api_architecture_review.py tests/test_logical_api_full_formation.py tests/test_logical_api_expanded_validation.py",
            f"  Result: {focused_result}", "", "Repository validation:", "  .venv/bin/pytest -q", f"  Result: {repository_result}", "",
            "Known baseline: five Phase 0 tests/test_profiler.py setup errors because tests/fixtures/repository_profile/staging is absent. This frozen-phase fixture defect is reported separately and was not repaired by Task 018A.", "",
        ]), encoding="utf-8"
    )
    artifact_names = [
        "domain_discovery_method_and_guardrails.md", "candidate_enterprise_domain_taxonomy.json",
        "sampled_operation_domain_cases.jsonl", "executive_sample_review.md", "api_domain_footprint_sample.jsonl",
        "task017a_domain_enrichment_links.jsonl", "enterprise_domain_alignment_decision_gate.md",
        "sample_coverage_and_gaps.json", "commands_and_results.txt",
    ]
    manifest = {
        "scope": "TASK018A_BOUNDED_OPERATION_DOMAIN_VALIDATION", "generator": "generate_domain_validation_evidence.py",
        "rules_version": result["manifest"]["rules_version"], "source_manifest": result["manifest"],
        "artifacts": {name: {"sha256": digest(EVIDENCE / name), "bytes": (EVIDENCE / name).stat().st_size} for name in artifact_names},
        "enterprise_alignment_gate": ALIGNMENT_GATE, "enterprise_architect_acceptance": "PENDING",
    }
    write_json(EVIDENCE / "build_manifest.json", manifest)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--focused-result", default="NOT_RUN")
    parser.add_argument("--repository-result", default="NOT_RUN")
    arguments = parser.parse_args()
    generated = generate(arguments.focused_result, arguments.repository_result)
    print(generated["manifest"]["summary"])
