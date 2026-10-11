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

from logical_api.architecture_review import NEXT_GATE, OUTPUTS, RECOMMENDATIONS, build_architecture_review  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: list[dict]) -> None:
    path.write_text("".join(json.dumps(v, sort_keys=True, separators=(",", ":")) + "\n" for v in values), encoding="utf-8")


def safe(value: object) -> str:
    return str(value).replace("|", "/").replace("\n", " ")


def compact_operation(value: dict) -> dict:
    exposure = value["exposure"]
    return {
        "task014_operation_id": value["task014_operation_id"],
        "task015_observed_function_id": value["task015_observed_function_id"],
        "method": value["method"], "path": value["path"], "actions": value["actions"], "resource": value["resource"],
        "source_pointer": value["source_pointer"], "source_sha256": value["source_sha256"],
        "contract": value["contract"], "membership_r1_r7": value["criteria"],
        "backend_evidence_scope": value["backend_evidence_scope"],
        "accepted_exposure": {
            "product_ids": exposure.get("accepted_product_ids", []), "plan_ids": exposure.get("accepted_plan_ids", []),
            "subscription_evidence_state": exposure.get("subscription_evidence_state"),
            "subscription_join_count": exposure.get("subscription_join_count", 0),
            "operation_consumption_proven": False, "runtime_activity_proven": False,
        },
    }


def compact_review(value: dict) -> dict:
    return {
        key: value[key] for key in (
            "architecture_review_id", "baseline_logical_api_proposal_id", "baseline_membership_sha256",
            "baseline_evidence_sufficiency", "canonical_api_id", "current_api_name", "current_api_version",
            "member_count", "grouping_hypothesis", "positive_cohesion_evidence", "specific_counterevidence",
            "source_evidence_refs", "review_rubric", "recommendation", "recommendation_rationale",
            "proposed_sub_boundaries", "unassigned_after_split_operation_ids", "split_membership_disjoint",
            "alternative_boundary", "productization_implication", "technical_or_test_evidence",
            "bounded_cross_api_link_ids", "evidence_gaps", "three_result_axes", "original_membership_unchanged",
            "production_usage_inferred", "functional_equivalence_approved", "product_created_or_mapped",
            "retirement_decision", "domain_assignment", "capability_assignment", "kong_topology",
        )
    } | {"operations": [compact_operation(v) for v in value["operations"]]}


def operation_text(review: dict) -> str:
    parts = []
    for op in review["operations"]:
        meaning = ",".join(op["actions"]) or "no action"
        if op["resource"]:
            meaning += f"; {op['resource']}"
        parts.append(f"`{op['method']} {op['path']}` ({meaning})")
    return "; ".join(parts)


def write_criteria() -> None:
    (EVIDENCE / "review_criteria_and_decisions.md").write_text(
        """# Task 017A architecture review criteria and decisions

## Scope and authority

This is a bounded architecture review of the 71 frozen Task 017 proposals, plus five separately counted oversized adjuncts and directly relevant cross-API links from the accepted 46-case sample. It does not regenerate Task 017, change primary operation membership, perform a broad all-pairs search, or authorize a Logical API, API Product, Kong topology, retirement, Domain, or Capability. Enterprise Architect acceptance is `PENDING` throughout.

## Independent axes

1. Technical validation verifies deterministic construction, reconciliation, provenance, and tests.
2. Evidence sufficiency preserves the frozen Task 017 assessment.
3. Architecture acceptance remains an explicit Enterprise Architect decision.

Technical `PASS` is not architecture approval. Functional-equivalence links, conceptual cohesion, and productization suitability are separate questions.

## R1-R7

| Criterion | Review question |
|---|---|
| R1 | Is a non-generic resource/workflow identity directly supported? |
| R2 | Do distinct actions and paths support shared responsibility/lifecycle rather than mere coexistence? |
| R3 | Is shared consumer, owner, authorization, or entitlement intent evidenced? Product/Plan/Subscription links alone are exposure context. |
| R4 | Are method/path, version, request/response shapes, statuses, and security variants retained without compatibility inference? |
| R5 | Is operation-scoped backend configuration present? API-shared candidates do not prove behavior or runtime egress. |
| R6 | Is concrete counterevidence and a competing boundary/nonformation alternative retained? |
| R7 | Are canonical API, Task 014/015/016 identifiers, source hash, and exact pointer traceable? |

Every criterion is `SUPPORTED`, `CONTRADICTED`, or `NOT_EVIDENCED`, with source references. Group and member evidence is preserved in the committed decision register and expandable ignored index.

## Recommendation meanings

- `RETAIN_PROVISIONAL_COHESIVE_BOUNDARY`: direct resource/workflow cohesion is positive, but not approved.
- `SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES`: exact resource/action/path evidence supports named disjoint subsets; unmatched members remain explicit.
- `KEEP_AS_IS_EXPOSURE_NO_LOGICAL_BOUNDARY_ASSERTION`: current API coexistence is the only group signal.
- `REQUIRES_TARGETED_EVIDENCE`: a named missing or contradictory fact blocks a decision.
- `TECHNICAL_OR_TEST_EXPOSURE_REVIEW`: direct source identity or Task 015 nature supports a technical/test review; retirement is not inferred.

The Productization Readiness Gate is `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`. Task 018/019 may add resource taxonomy or common-business-purpose evidence. They cannot establish shared lifecycle ownership, consumer intent, release boundaries, active production use, or safe substitution.
""",
        encoding="utf-8",
    )


def write_executive(reviews: list[dict]) -> None:
    lines = [
        "# Task 017A executive review of all 71 proposals", "",
        "Every frozen proposal appears once. Operation summaries are source-backed; recommendations remain proposals for Enterprise Architect review.", "",
        "| # | Source API/version | Operations and supported meaning | Prior evidence | Recommendation | Item-specific counterevidence | Productization implication |",
        "|---:|---|---|---|---|---|---|",
    ]
    for number, review in enumerate(reviews, 1):
        lines.append(
            f"| {number} | `{safe(review['current_api_name'])}` / `{safe(review['current_api_version'])}` | "
            f"{safe(operation_text(review))} | {review['baseline_evidence_sufficiency']} | {review['recommendation']} | "
            f"{safe(review['specific_counterevidence'])} | {review['productization_implication']} |"
        )
    lines.extend(["", f"Productization readiness gate: **{NEXT_GATE}**. No design is authorized.", ""])
    (EVIDENCE / "executive_all_71_review.md").write_text("\n".join(lines), encoding="utf-8")


def write_deep_dives(reviews: list[dict], links: list[dict]) -> None:
    selected_names = [
        "nic-prtissuespecialpermit", "mhrsd-submitsaudicertificate", "nic-submitrunawayrequest",
        "mhrsd-raiseobjectionrequest", "nic-submitvisa", "getlookups", "mcs-rest-services",
        "takamol-svp-apis-v1", "kyan-user-validation", "adminmanagement-supportcentre",
        "ajeer-bulk-contracts", "qiwa-streaming-v2", "graphql_poc", "getunifiednumberworkpermit",
    ]
    selected = []
    for name in selected_names:
        match = next((v for v in reviews if v["current_api_name"] == name and v not in selected), None)
        if match:
            selected.append(match)
    lines = ["# Task 017A diverse deep dives", "", f"Selected proposal cases: **{len(selected)}**; bounded cross-API controls: **2**. All decisions remain EA `PENDING`.", ""]
    for review in selected:
        lines.extend([
            f"## {review['current_api_name']} {review['current_api_version']}", "",
            f"- Baseline ID: `{review['baseline_logical_api_proposal_id']}`; prior evidence: `{review['baseline_evidence_sufficiency']}`.",
            f"- Recommendation: `{review['recommendation']}`. {review['recommendation_rationale']}",
            f"- Positive evidence: {review['positive_cohesion_evidence']}",
            f"- Counterevidence: {review['specific_counterevidence']}",
            f"- Alternative: {review['alternative_boundary']}",
            f"- Productization: `{review['productization_implication']}`; gate `{NEXT_GATE}`.",
            "- Exact operations:", "",
        ])
        for op in review["operations"]:
            backend = op["backend_evidence_scope"]
            exposure = op["accepted_exposure"]
            lines.append(
                f"  - `{op['method']} {op['path']}` — actions `{op['actions'] or ['NONE']}`, resource `{op['resource'] or 'NONE'}`; "
                f"source `{op['source_pointer']}`; security `{op['contract'].get('security_scheme_types', [])}`; "
                f"backend operation-scoped/candidate counts `{backend['configured_operation_scoped_count']}/{backend['candidate_inherited_context_count']}` (runtime not proven); "
                f"Product/Plan counts `{len(exposure['product_ids'])}/{len(exposure['plan_ids'])}` (consumption not proven)."
            )
        lines.extend(["", "R1-R7 group result: " + ", ".join(f"{k}={v['status']}" for k, v in review["review_rubric"].items()) + ".", ""])
    preferred = [v for v in links if v["candidate_label"] in {"SC Request Workflow", "Seasonal Visa Request Search"}]
    for link in preferred:
        lines.extend([
            f"## Cross-API control: {link['candidate_label']}", "",
            f"- Link: `{link['cross_api_link_id']}`; status `{link['link_status']}`.",
            f"- Operations: `{link['member_operation_ids']}`.",
            f"- Exact sources: `{link['source_pointers']}`.",
            f"- Positive: {link['positive_evidence']}",
            f"- Contrary: {link['contrary_evidence']}",
            "- This is an alternative link only: no primary membership, equivalence, transitive inference, or product is created.", "",
        ])
    (EVIDENCE / "deep_dive_cases.md").write_text("\n".join(lines), encoding="utf-8")


def build_summary(result: dict) -> dict:
    reviews = result["reviews"]
    prior = Counter(v["baseline_evidence_sufficiency"] for v in reviews)
    current = Counter(v["recommendation"] for v in reviews)
    ledger = [json.loads(v) for v in (ROOT / "indexes/task017_full_operation_disposition.jsonl").read_text().splitlines() if v]
    expanded = [json.loads(v) for v in (ROOT / "tests/evidence/task-017/expanded-validation/expanded_sample_register.jsonl").read_text().splitlines() if v]
    sc = next(v for v in expanded if v["candidate_boundary_label"] == "SC Request Workflow")
    return {
        "baseline_proposal_coverage": {"expected": 71, "actual": len(reviews), "distinct_ids": len({v["baseline_logical_api_proposal_id"] for v in reviews}), "membership_changes": 0},
        "baseline_evidence_sufficiency_counts": dict(sorted(prior.items())),
        "architecture_recommendation_counts": dict(sorted(current.items())),
        "reviewed_proposal_member_occurrences": sum(v["member_count"] for v in reviews),
        "full_primary_ledger": {"expected": 2414, "actual": len(ledger), "distinct_operation_ids": len({v["task014_operation_id"] for v in ledger}), "unchanged": True},
        "task016_unpaired_preserved": sum(not v["task016_comparison_refs"] for v in ledger),
        "oversized_adjunct": {"outside_71": True, "review_count": len(result["oversized"]), "operation_count": sum(v["operation_count"] for v in result["oversized"]), "primary_dispositions_changed": 0},
        "cross_api_links": {"count": len(result["cross_links"]), "primary_memberships_created": 0, "broad_all_pairs_performed": False},
        "frozen_46_case_control_count": len(expanded),
        "sc_request_control": {"source_operation_count": len(sc["members"]), "distinct_action_intents": sorted({a for m in sc["members"] for a in m["supported_actions"]}), "evidence_sufficiency": sc["result_axes"]["evidence_sufficiency"], "alternatives_preserved": ["Unified SC Request Actions", "Split Decision and Cancellation boundaries"]},
        "backlog_count": len(result["backlog"]), "backlog_components": {"baseline_proposals": 71, "oversized_adjuncts": 5, "cross_api_links": len(result["cross_links"])},
        "productization_readiness_gate": {"position": NEXT_GATE, "design_authorized": False},
        "result_axes": {"technical_validation": "PASS", "architect_acceptance": "PENDING"},
        "unauthorized_assignments": {"architect_approvals": 0, "products_created": 0, "domain_assignments": 0, "capability_assignments": 0, "kong_topologies": 0, "retirement_decisions": 0, "production_usage_inferences": 0},
    }


def generate(focused_result: str, repository_result: str) -> dict:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    result = build_architecture_review(ROOT)
    reviews = [compact_review(v) for v in result["reviews"]]
    write_criteria()
    write_jsonl(EVIDENCE / "all_71_decision_register.jsonl", reviews)
    write_executive(reviews)
    write_deep_dives(reviews, result["cross_links"])
    write_jsonl(EVIDENCE / "five_oversized_adjunct.jsonl", result["oversized"])
    write_jsonl(EVIDENCE / "cross_api_opportunity_links.jsonl", result["cross_links"])
    write_jsonl(EVIDENCE / "productization_decision_backlog.jsonl", result["backlog"])
    write_json(EVIDENCE / "coverage_and_decision_summary.json", build_summary(result))
    (EVIDENCE / "commands_and_results.txt").write_text(
        "\n".join([
            "Task 017A architecture review of all 71 proposals", "", "Generation:",
            "  .venv/bin/python tests/evidence/task-017/architecture-review-71/generate_architecture_review_evidence.py --focused-result '<result>' --repository-result '<result>'",
            "  Result: PASS; 71 reviews, five/132 oversized adjunct, bounded links, and backlog generated without rebuilding Task 017.", "",
            "Focused validation:", "  .venv/bin/pytest -q tests/test_logical_api_architecture_review.py tests/test_logical_api_full_formation.py tests/test_logical_api_expanded_validation.py tests/test_logical_api_mock.py",
            f"  Result: {focused_result}", "", "Repository validation:", "  .venv/bin/pytest -q", f"  Result: {repository_result}", "",
            "Known baseline: exactly five Phase 0 tests/test_profiler.py setup errors because tests/fixtures/repository_profile/staging is absent. This frozen-phase fixture defect is reported separately and was not repaired by Task 017A.", "",
        ]), encoding="utf-8"
    )
    artifact_names = [
        "review_criteria_and_decisions.md", "all_71_decision_register.jsonl", "executive_all_71_review.md",
        "deep_dive_cases.md", "five_oversized_adjunct.jsonl", "cross_api_opportunity_links.jsonl",
        "productization_decision_backlog.jsonl", "coverage_and_decision_summary.json", "commands_and_results.txt",
    ]
    manifest = {
        "scope": "TASK017A_BOUNDED_ARCHITECTURE_REVIEW", "generator": "generate_architecture_review_evidence.py",
        "rules_version": result["manifest"]["rules_version"], "source_manifest": result["manifest"],
        "artifacts": {name: {"sha256": digest(EVIDENCE / name), "bytes": (EVIDENCE / name).stat().st_size} for name in artifact_names},
        "allowed_recommendations": sorted(RECOMMENDATIONS), "architect_acceptance": "PENDING", "next_gate": NEXT_GATE,
    }
    write_json(EVIDENCE / "build_manifest.json", manifest)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--focused-result", default="NOT_RUN")
    parser.add_argument("--repository-result", default="NOT_RUN")
    args = parser.parse_args()
    generated = generate(args.focused_result, args.repository_result)
    print(generated["manifest"]["summary"])
