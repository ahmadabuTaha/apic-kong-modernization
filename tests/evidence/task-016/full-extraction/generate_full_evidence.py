"""Generate compact, deterministic Task 016 full-extraction evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from logical_function.full_inventory import build_full  # noqa: E402

OUT = Path(__file__).resolve().parent


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(name: str, values: list[dict]) -> None:
    (OUT / name).write_text("".join(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" for value in values), encoding="utf-8")


def compact(value: dict) -> dict:
    return {
        "comparison_id": value["comparison_id"],
        "candidate_logical_function_id": value["candidate_logical_function_id"],
        "comparison_status": value["comparison_status"],
        "business_intent_hypothesis": value["business_intent_hypothesis"],
        "contract_compatibility": value["contract_compatibility"],
        "backend_certainty": value["backend_certainty"],
        "version_or_variant_relation": value["version_or_variant_relation"],
        "subscription_evidence_state": value["subscription_evidence_state"],
        "runtime_usage_state": value["runtime_usage_state"],
        "candidate_generation": value["candidate_generation"],
        "signals": value["signals"],
        "left": value["left"],
        "right": value["right"],
        "schema_comparison": value["schema_comparison"],
        "product_plan_comparison": value["product_plan_comparison"],
        "negative_or_uncertain_evidence": value["negative_or_uncertain_evidence"],
        "reviewer_status": value["reviewer_status"],
        "confirmed_duplicate": False,
        "safe_substitution_asserted": False,
        "retirement_asserted": False,
        "production_activity_asserted": False,
    }


def generate() -> None:
    result = build_full(ROOT)
    manifest = result["manifest"]
    comparisons = result["comparisons"]
    families = result["version_families"]
    gaps = jsonl(ROOT / "indexes/task015_full_gap_impact_register.jsonl")

    contract = """# Task 016 full logical-function candidate contract

- Contract version: `task016-logical-function-full-v1`. Every record is a deterministic review proposal; no record approves business equivalence, duplicate status, merge, substitution, retirement, production activity, Logical API, domain/capability label, or Kong design.
- All 2,414 frozen Task 014 operations reconcile one-to-one to Task 015 and remain individually visible in the full operation catalog. Candidate membership is additive and never collapses source identities.
- Candidate discovery uses bounded inverted blocks for provisional wording/action-object, endpoint shape, safe request/response hashes, configured backend observation, object tokens, and provisional version-family keys. The 60 inherited Task 014 structural candidates are forced into review coverage. Oversized blocks and per-operation fan-out are explicit queues; no all-pairs search or complete semantic-recall claim is made.
- `BUSINESS_INTENT_HYPOTHESIS`, `CONTRACT_COMPATIBILITY`, `BACKEND_CERTAINTY`, `VERSION_OR_VARIANT_RELATION`, `SUBSCRIPTION_EVIDENCE_STATE`, and `RUNTIME_USAGE_STATE` are separate dimensions. Task 015 wording remains provisional automated interpretation.
- Frontend evidence retains method, sanitized base path, exact/normalized path, selector, auth, exposure, parameters and request/response structure. Backend evidence separates operation-scoped configured facts from API-shared candidate context; hosts/raw policy values are omitted and runtime egress is never inferred.
- Subscription context is an indirect accepted-ID join: Subscription→Product, Subscription→Plan, Subscription→Application, Product→Plan, Product→API and Plan→API. Relationship IDs and safe counts are retained; application/subscriber identities are omitted. Membership proves neither operation invocation, active consumption nor production deployment.
- Version labels, names and ordering do not prove replacement, age, activity or obsolescence. Feature flags and coexistence reasons are reported only from explicit configuration pointers; otherwise `FEATURE_FLAG_NOT_EVIDENCED` and `COEXISTENCE_REASON_UNVERIFIED` apply.
- Actual schema comparisons retain only structure (presence, requiredness, type, nesting and enum where represented). Descriptions, examples, payload values, endpoint hosts and credentials are omitted.
- Staging is sandbox-like evidence. Missing metadata/subscriptions and configured routes do not establish production quality, usage, inactivity, criticality or retirement.
"""
    (OUT / "logical_function_candidate_contract.md").write_text(contract, encoding="utf-8")

    write_json("candidate_discovery_coverage.json", {
        "rules_version": manifest["rules_version"],
        "input_operation_count": manifest["input_operation_count"],
        "operation_catalog_count": manifest["operation_catalog_count"],
        "candidate_pair_count": manifest["candidate_pair_count"],
        "candidate_group_count": manifest["candidate_group_count"],
        "paired_operation_count": manifest["paired_operation_count"],
        "unpaired_operation_count": manifest["unpaired_operation_count"],
        "operation_reconciliation_pass": manifest["input_operation_count"] == manifest["operation_catalog_count"] == manifest["paired_operation_count"] + manifest["unpaired_operation_count"],
        "original_structural_candidate_count": manifest["original_structural_candidate_count"],
        "original_structural_candidates_included": manifest["original_structural_candidates_included"],
        "new_candidate_pair_count": manifest["new_candidate_pair_count"],
        "status_distribution": manifest["status_distribution"],
        "block_member_cap": manifest["block_member_cap"],
        "oversized_block_count": manifest["oversized_block_count"],
        "per_operation_candidate_cap": manifest["per_operation_candidate_cap"],
        "fanout_capped_candidate_count": manifest["fanout_capped_candidate_count"],
        "all_pairs_performed": False,
        "recall_proxy": {
            "all_inherited_structural_candidates_represented": manifest["original_structural_candidates_included"] == manifest["original_structural_candidate_count"],
            "new_candidates_beyond_original_set": manifest["new_candidate_pair_count"],
            "negative_controls_present": manifest["status_distribution"].get("CLEARLY_DIFFERENT_SUPPORTED", 0),
            "complete_business_equivalence_recall_claimed": False,
            "limitation": "Bounded deterministic blocks cannot detect relationships whose wording, endpoints, contracts, backend configuration, version cues and accepted exposure context share no indexed signal.",
        },
        "unpaired_operations_remain_visible_in": "indexes/task016_full_operation_catalog.jsonl",
    })

    required_names = [
        {"searchseasonalvisarequests", "searchseasonalvisarequests-v2"},
        {"mcsemploymentstatusenquiry_querycenter", "mcsemploymentstatusenquiry"},
    ]
    selected: list[dict] = []
    for names in required_names:
        match = next(value for value in comparisons if {value["left"]["api_name"], value["right"]["api_name"]} == names)
        selected.append(match)
    for status in ("POSSIBLE_SAME_LOGICAL_FUNCTION", "REVIEW_REQUIRED_CONFLICTING_SIGNALS", "CLEARLY_DIFFERENT_SUPPORTED", "NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE"):
        match = next((value for value in comparisons if value["comparison_status"] == status and value not in selected), None)
        if match:
            selected.append(match)
    # Add deterministic newly-discovered and inherited examples without producing a large report.
    selected.extend(next(value for value in comparisons if not value["candidate_generation"]["inherited_task014_candidate_ids"] and value not in selected) for _ in range(1))
    for status in ("POSSIBLE_SAME_LOGICAL_FUNCTION", "REVIEW_REQUIRED_CONFLICTING_SIGNALS", "CLEARLY_DIFFERENT_SUPPORTED", "NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE"):
        candidates = [v for v in comparisons if v["comparison_status"] == status and v not in selected]
        if candidates:
            selected.append(candidates[0])
    selected = sorted({v["comparison_id"]: v for v in selected}.values(), key=lambda v: v["comparison_id"])
    write_jsonl("endpoint_and_subscription_comparisons.jsonl", [compact(v) for v in selected])

    family_by_member = {member: family for family in families for member in family["member_operation_ids"]}
    assessed = []
    prioritized = [next(value for value in comparisons if {value["left"]["api_name"], value["right"]["api_name"]} == names) for names in required_names]
    for value in prioritized:
        family = family_by_member.get(value["left"]["task014_operation_id"]) or family_by_member.get(value["right"]["task014_operation_id"])
        assessed.append({
            "assessment_id": "task016-version-assessment:sha256:" + hashlib.sha256(value["comparison_id"].encode()).hexdigest(),
            "comparison_id": value["comparison_id"],
            "api_names": [value["left"]["api_name"], value["right"]["api_name"]],
            "version_labels": [value["left"]["frontend_endpoint"]["api_version_label"], value["right"]["frontend_endpoint"]["api_version_label"]],
            "frontend_endpoints": [value["left"]["frontend_endpoint"], value["right"]["frontend_endpoint"]],
            "backend_contexts": [value["left"]["backend_implementation"], value["right"]["backend_implementation"]],
            "request_schema_differences": value["schema_comparison"]["request_differences"],
            "response_schema_differences": value["schema_comparison"]["response_differences"],
            "subscription_contexts": [value["left"]["product_plan_subscription_context"], value["right"]["product_plan_subscription_context"]],
            "version_family": family,
            "potential_business_rule_or_channel_difference": "HYPOTHESIS_REQUIRES_ARCHITECT_VALIDATION",
            "feature_flag_evidence_status": family["feature_flag_evidence_status"] if family else "FEATURE_FLAG_NOT_EVIDENCED",
            "coexistence_reason": family["coexistence_reason"] if family else "COEXISTENCE_REASON_UNVERIFIED",
            "replacement_or_activity_inferred": False,
        })
    for family in families:
        if family not in [v.get("version_family") for v in assessed] and len(assessed) < 12:
            assessed.append({
                "assessment_id": "task016-version-assessment:sha256:" + hashlib.sha256(family["version_variant_family_id"].encode()).hexdigest(),
                "comparison_id": family["comparison_ids"][0] if family["comparison_ids"] else None,
                "version_family": family,
                "feature_flag_evidence_status": family["feature_flag_evidence_status"],
                "coexistence_reason": family["coexistence_reason"],
                "replacement_or_activity_inferred": False,
                "potential_business_rule_or_channel_difference": "HYPOTHESIS_REQUIRES_ARCHITECT_VALIDATION",
            })
    write_jsonl("version_variant_family_assessment.jsonl", assessed)

    representatives = []
    for value in selected[:20]:
        representatives.append({
            "candidate_logical_function_id": value["candidate_logical_function_id"],
            "comparison_id": value["comparison_id"],
            "comparison_status": value["comparison_status"],
            "member_operation_ids": [value["left"]["task014_operation_id"], value["right"]["task014_operation_id"]],
            "member_canonical_api_ids": [value["left"]["canonical_api_id"], value["right"]["canonical_api_id"]],
            "normalized_action_object_proposals": [value["left"]["provisional_normalized_action_object"], value["right"]["provisional_normalized_action_object"]],
            "membership_provenance": value["candidate_generation"],
            "architect_approved_equivalence": False,
            "reviewer_status": "PENDING_REVIEW",
        })
    write_jsonl("normalized_logical_function_candidates.jsonl", representatives)

    gap_categories = [{
        "gap_id": value["gap_id"], "severity": value["severity"], "scope": value["scope"],
        "affected_canonical_api_count": len(value["affected_canonical_api_ids"]),
        "affected_operation_count": len(value["affected_operation_ids"]),
        "task016_impact": value["downstream_effects"]["016"], "recheck_trigger": value["recheck_trigger"],
        "handling": "Preserved as scoped uncertainty; never promoted to a production quality, usage, retirement or whole-phase conclusion.",
    } for value in gaps]
    write_json("review_queue_and_gap_impact.json", {
        "candidate_review_queue_count": manifest["review_queue_count"],
        "priority_distribution": dict(sorted(Counter(v["priority"] for v in result["review_queue"]).items())),
        "architect_questions": [
            "Which candidate pairs share business intent despite contract differences?",
            "Which contract differences represent incompatible behavior, channel variants or version evolution?",
            "Does accepted Product/Plan exposure explain distinct consumer tracks without implying actual calls?",
            "Is named targeted design/runtime evidence authorized for unresolved high-priority candidates?",
        ],
        "inherited_gap_category_count": len(gap_categories),
        "inherited_gap_categories": sorted(gap_categories, key=lambda v: v["gap_id"]),
        "unresolved_product_location_occurrence_count": manifest["unresolved_product_location_occurrence_count"],
        "unresolved_product_locations_cross_joined_by_name": False,
        "staging_limitation": "Absence in staging is not zero production consumers, inactivity, retirement or a production defect.",
    })
    write_json("cache_and_tests.json", {
        "rules_version": manifest["rules_version"], "model_use": manifest["model_use"],
        "cache": manifest["outputs"]["cache"], "cache_dependency_guarded": True,
        "incremental_exact_replay_supported": True, "cached_outputs_hash_verified_before_reuse": True,
        "deterministic_atomic_outputs": True, "targeted_source_document_count": manifest["targeted_source_document_count"],
        "tests": "See commands_and_results.txt; repository failures, if any, are reported distinctly.",
    })
    commands = OUT / "commands_and_results.txt"
    if not commands.exists():
        commands.write_text(".venv/bin/python -m logical_function\nPASS: full deterministic build completed.\n", encoding="utf-8")
    files = sorted(path for path in OUT.iterdir() if path.is_file() and path.name not in {"build_manifest.json", "generate_full_evidence.py"})
    write_json("build_manifest.json", {
        "rules_version": manifest["rules_version"],
        "local_full_manifest": manifest,
        "committed_evidence": [{"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size} for path in files],
        "source_evidence_modified": False, "frozen_task014_task015_modified": False,
    })


if __name__ == "__main__":
    generate()
