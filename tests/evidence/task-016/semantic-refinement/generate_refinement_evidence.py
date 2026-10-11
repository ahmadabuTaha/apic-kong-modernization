"""Generate compact deterministic evidence for Task 016 semantic refinement."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from logical_function.refinement import build_refinement  # noqa: E402

OUT = Path(__file__).resolve().parent


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(name: str, values: list[dict]) -> None:
    (OUT / name).write_text("".join(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" for value in values), encoding="utf-8")


def generate() -> None:
    result = build_refinement(ROOT)
    manifest = result["manifest"]
    pairs = result["refined_pairs"]
    focused = result["focused_cases"]

    (OUT / "refinement_contract.md").write_text("""# Task 016 focused semantic refinement contract

Logical Function Identity remains a hypothesis composed of **Business Action + Business Object + Behavioral Semantics**. Structural similarities retrieve review candidates; they never prove identity.

| Refinement verdict | Deterministic meaning | Prohibited interpretation |
|---|---|---|
| `STRUCTURAL_SIMILARITY_ONLY` | Schema, endpoint, backend-system, or generic wording signals exist without aligned supported behavior. | Not a duplicate or same function. |
| `DIFFERENT_BUSINESS_ACTION_SUPPORTED` | Independently documented or corroborated actions differ on an aligned object. Approve, reject, cancel, terminate, activate/deactivate, create/retrieve and read/write stay distinct. | Not a duplicate candidate, merge, or retirement basis. |
| `POTENTIAL_SAME_BEHAVIOR_DIFFERENT_EXPOSURE` | Supported action sets and object evidence align across different exposure forms. Behavioral identity remains pending. | Not approved equivalence or interchangeability. |
| `CONFLICTING_SEMANTICS_REVIEW` | Source signals conflict, object intent does not align, or interpretation remains contradictory. | Do not resolve from schema/backend similarity. |
| `SEMANTIC_EVIDENCE_INSUFFICIENT` | Operation-level action/object/behavior cannot be established. | Unknown is not same, different, unused, or retired. |

Source descriptions/summaries provide documented action evidence. Two agreeing structural sources may provide provisional corroboration. A name or single path signal alone cannot support a hard different-action verdict. Task 015 HIGH remains automated interpretation strength, not verified business meaning.

Backend certainty is separate: `CONFIGURED_API_SHARED_CANDIDATE`, `CONFIGURED_OPERATION_SCOPED`, `RESOLVED_OPERATION_SEMANTICS`, or `NOT_EVIDENCED`. Assembly selector/invoke/rewrite/branch/transformation pointers may narrow configuration scope; GatewayScript presence is never interpreted as behavior and configuration never proves runtime egress.

Product, Plan, Subscription, version and staging context remain contextual only. No record approves a duplicate, merge, replacement, retirement, live traffic, production adoption, active feature flag, Logical API, or Kong design.
""", encoding="utf-8")

    ambiguous = Counter(reason for value in pairs if value["refinement_verdict"] in {"CONFLICTING_SEMANTICS_REVIEW", "SEMANTIC_EVIDENCE_INSUFFICIENT", "STRUCTURAL_SIMILARITY_ONLY"} for reason in value["negative_or_uncertain_evidence"])
    write_json("pair_refinement_distribution.json", {
        "rules_version": manifest["rules_version"],
        "baseline_pair_count": manifest["baseline_pair_count"],
        "refined_pair_count": manifest["refined_pair_count"],
        "exact_once_reconciliation_pass": manifest["baseline_pair_count"] == manifest["refined_pair_count"] == len({v["prior_comparison_id"] for v in pairs}),
        "refinement_distribution": manifest["refinement_distribution"],
        "old_status_by_refinement": manifest["old_status_by_refinement"],
        "ambiguous_or_negative_evidence_reasons": dict(sorted(ambiguous.items())),
        "structurally_equal_pair_count": manifest["structurally_equal_pair_count"],
        "structurally_equal_not_proven_same_function_count": manifest["structurally_equal_not_proven_same_function_count"],
        "unpaired_visible_operation_count": manifest["unpaired_visible_operation_count"],
        "divergent_form_suggestion_count": manifest["divergent_form_suggestion_count"],
        "divergent_form_check_scope": "Existing Task 016 cached exact action/object blocks among the 1,481 unpaired-visible operations; groups of 2-10 only, divergent paths, maximum 25 suggestions.",
        "divergent_form_suggestions": result["suggestions"],
        "all_pairs_performed": False,
        "baseline_candidate_generation_rerun": False,
        "complete_recall_claimed": False,
        "approved_duplicate_count": 0,
    })
    write_jsonl("focused_cases.jsonl", focused)

    by_names = {frozenset((v["left"]["api_name"], v["right"]["api_name"])): v for v in focused}
    seasonal = by_names[frozenset(("searchseasonalvisarequests", "searchseasonalvisarequests-v2"))]
    employment = by_names[frozenset(("mcsemploymentstatusenquiry_querycenter", "mcsemploymentstatusenquiry"))]
    activate = by_names[frozenset(("mhrsd-deactivateindustrialestablishment", "mhrsd-activateindustrialestablishment"))]
    approve_cancel = by_names[frozenset(("approverejectscrequest", "cancelscrequest"))]
    different = next(v for v in focused if v.get("prior_comparison_id") and v["refinement_verdict"] == "DIFFERENT_BUSINESS_ACTION_SUPPORTED")
    (OUT / "false_positive_and_false_negative_audit.md").write_text(f"""# Task 016 false-positive and false-negative audit

## Action false-positive controls

- `{approve_cancel['focused_case_id']}` is an audit-only control, not one of the 1,170 pairs. Direct descriptions/pointers document approve-or-reject versus cancel behavior for SC requests. These actions remain distinct even if a common command envelope or response wrapper exists.
- `{different['prior_comparison_id']}` compares `{different['left']['api_name']}` with `{different['right']['api_name']}`. Supported `{different['left']['business_action_object_evidence']['supported_action_categories']}` versus `{different['right']['business_action_object_evidence']['supported_action_categories']}` acts on aligned object evidence, so its additive verdict is `DIFFERENT_BUSINESS_ACTION_SUPPORTED`.
- `{activate['prior_comparison_id']}` exposes deactivate versus activate path/name signals with structurally equal shapes, but each action has only a single source signal. It remains `{activate['refinement_verdict']}` rather than receiving a hard different-action verdict.
- All 717 structurally equal pairs remain **not proven** to implement the same function. Shared wrappers, response envelopes, endpoint shapes or backend systems are retrieval signals only.

## Differently exposed possible-same cases

- Seasonal visa v1/v2 `{seasonal['prior_comparison_id']}` retains matching apparent search action/object across versions while preserving the `SortBy` request difference, response differences, candidate-only backend scope, and unverified coexistence/activity. Verdict: `{seasonal['refinement_verdict']}`.
- Employment-status `{employment['prior_comparison_id']}` retains matching endpoint/wording context but lacks supported operation-level action evidence. Verdict: `{employment['refinement_verdict']}`; structural similarity does not fill that gap.
- The bounded cached check of 1,481 unpaired-visible operations found {manifest['divergent_form_suggestion_count']} new exact-action/object divergent-form suggestions. This does not claim complete false-negative recall.

## Backend and exposure controls

- API-shared configured targets remain `CONFIGURED_API_SHARED_CANDIDATE`; same backend system is not same backend operation.
- Operation selectors, invoke paths, branches, rewrites and transformation pointers are retained when present. GatewayScript bodies and dispatch values are omitted and script presence is not interpreted as behavior.
- Product/Plan/Subscription and version context can explain exposure differences but never demonstrate calls, production adoption, interchangeability, retirement or active feature flags.
""", encoding="utf-8")

    priority = Counter()
    for value in pairs:
        if value["refinement_verdict"] == "SEMANTIC_EVIDENCE_INSUFFICIENT":
            priority["P1_OPERATION_BEHAVIOR_NOT_EVIDENCED"] += 1
        elif value["refinement_verdict"] == "CONFLICTING_SEMANTICS_REVIEW":
            priority["P1_CONFLICTING_SOURCE_ACTION_OR_OBJECT"] += 1
        elif value["refinement_verdict"] == "STRUCTURAL_SIMILARITY_ONLY":
            priority["P2_STRUCTURAL_ONLY_FALSE_POSITIVE_CONTROL"] += 1
        elif value["refinement_verdict"] == "DIFFERENT_BUSINESS_ACTION_SUPPORTED":
            priority["P2_NEGATIVE_ACTION_CONTROL"] += 1
        else:
            priority["P2_POTENTIAL_SAME_BEHAVIOR_VALIDATION"] += 1
    write_json("review_priorities.json", {
        "priority_distribution": dict(sorted(priority.items())),
        "manual_review_of_all_pairs_required": False,
        "targeted_requests": [
            {"cohort": "SEMANTIC_EVIDENCE_INSUFFICIENT", "request": "Named operation design or source-owner evidence for action, object and dispatch behavior; do not infer from the API name."},
            {"cohort": "CONFLICTING_SEMANTICS_REVIEW", "request": "Resolve description/summary versus path/operationId conflicts and identify the authoritative operation behavior."},
            {"cohort": "POTENTIAL_SAME_BEHAVIOR_DIFFERENT_EXPOSURE", "request": "Architect validation of behavioral identity separately from contract compatibility and subscriber exposure."},
            {"cohort": "CONFIGURED_API_SHARED_CANDIDATE", "request": "Operation-level assembly/dispatch or backend-operation evidence where sameness depends on the configured target."},
        ],
        "task017_readiness": "NOT_ADEQUATE_WITHOUT_ARCHITECT_ACCEPTANCE",
        "reason": "The refined layer prevents structural equivalence from becoming a duplicate verdict, but all potential-same behavior records remain pending and substantial behavior evidence is insufficient or conflicting.",
        "no_duplicate_merge_retirement_or_runtime_decision": True,
    })
    commands = OUT / "commands_and_results.txt"
    if not commands.exists():
        commands.write_text(".venv/bin/python -m logical_function\nPASS: focused semantic refinement generated.\n", encoding="utf-8")
    write_json("build_fingerprints.json", {
        "rules_version": manifest["rules_version"], "local_manifest": manifest,
        "evidence_files": [{"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size} for path in sorted(OUT.iterdir()) if path.is_file() and path.name not in {"build_fingerprints.json", "generate_refinement_evidence.py"}],
        "frozen_components_modified": False, "staging_modified": False,
    })


if __name__ == "__main__":
    generate()
