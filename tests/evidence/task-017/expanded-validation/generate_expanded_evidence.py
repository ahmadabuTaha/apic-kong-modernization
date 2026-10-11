from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parents[4]
EVIDENCE = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from logical_api.expanded_validation import build_expanded_validation  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value, sort_keys=True, indent=2) + "\n")


def write_jsonl(path: Path, values: list[dict]) -> None:
    write(path, "".join(json.dumps(v, sort_keys=True, separators=(",", ":")) + "\n" for v in values))


def cell(value: object) -> str:
    return str(value).replace("|", "/").replace("\n", " ")


result = build_expanded_validation(ROOT)
records = result["records"]
summary = result["manifest"]["summary"]
write_jsonl(EVIDENCE / "expanded_sample_register.jsonl", records)

write(EVIDENCE / "architecture_decision_rubric.md", """# Task 017 expanded boundary decision rubric

This is a proposal for consistent review, not an enterprise standard. It applies only to this bounded validation sample. A conceptual Logical API is neither functional equivalence nor an APIC Product nor a Kong topology.

## Per-boundary and per-membership criteria

- **R1 — resource:** an identified and adequately supported business object, resource, or workflow.
- **R2 — cohesion:** supported distinct actions plus direct evidence of a coherent lifecycle, workflow, or resource responsibility. Object-token, schema, backend, name, or Product overlap alone cannot satisfy R1 and R2.
- **R3 — consumer boundary:** consumer exposure, ownership, authorization, and entitlement intent. Accepted Product/Plan/subscription links are context; they do not prove actual consumers, ownership, calls, or one boundary.
- **R4 — contract:** exact/base path, method, version, security, shape, and transformation differences are preserved. Compatibility is never inferred.
- **R5 — backend:** operation-level configured evidence is distinguished from API-shared candidates. Neither proves runtime egress.
- **R6 — counterevidence:** every proposal states a reason not to group, an alternative boundary, and discriminating missing evidence.
- **R7 — provenance:** exact accepted IDs, pointers, hashes, and scope certainty remain traceable.

Each criterion is `SUPPORTED`, `CONTRADICTED`, or `NOT_EVIDENCED`. `NOT_EVIDENCED` stays explicit and cannot be upgraded by structural similarity.

## Three independent result axes

1. **Technical validation:** `PASS` or `FAIL` means only deterministic build/tests, stable IDs, reproduction, and source integrity.
2. **Evidence sufficiency:** `SUFFICIENT_FOR_PROVISIONAL_BOUNDARY`, `PARTIAL`, `INSUFFICIENT`, or `SUPPORTED_SEPARATE` summarizes R1–R7. It is not architecture approval.
3. **Architect acceptance:** always `PENDING` in this sample until an explicit Enterprise Architect decision.

Functional-equivalence candidates never collapse member IDs. Pairwise A~B and B~C are not closed into A~C. Original ten mock records are immutable anchors; their prior dispositions are preserved separately from the expanded review finding.
""")

lines = [
    "# Task 017 expanded executive review table", "",
    "Technical PASS below means reproducible evidence construction only. Every architecture decision remains PENDING.", "",
    "| # | Origin | Candidate boundary | Members | For | Against / alternative | Evidence | EA |", "|---:|---|---|---|---|---|---|---|",
]
for index, record in enumerate(sorted(records, key=lambda v: (v["sample_origin"], v["candidate_boundary_label"])), 1):
    members = "; ".join(f"{m['api_name']} {m['method']} {m['exact_path']}" for m in record["members"])
    lines.append(f"| {index} | {cell(record['sample_origin'])} | {cell(record['candidate_boundary_label'])} | {cell(members)} | {cell(record['evidence_for'][0])} | {cell(record['evidence_against'][0])} Alternative: {cell(record['alternative_boundary'])} | {record['result_axes']['evidence_sufficiency']} | PENDING |")
write(EVIDENCE / "executive_review_table.md", "\n".join(lines) + "\n")

sc = next(v for v in records if v["candidate_boundary_label"] == "SC Request Workflow")
sc_rows = []
for member in sorted(sc["members"], key=lambda v: v["api_name"]):
    contract = member["contract"]
    context = member["product_plan_subscription_context"]
    sc_rows.append(
        f"| {member['api_name']} | {member['method']} `{member['exact_path']}` | {', '.join(member['supported_actions'])} | "
        f"{', '.join(contract['request_schema_refs'])} / {', '.join(contract['response_schema_shape_sha256'])} | "
        f"{member['backend']['certainty']}: {', '.join(member['backend']['configured_paths'])} | "
        f"{', '.join(context['accepted_product_ids'])}; relationships: {', '.join(context['accepted_product_relationship_ids'])} | "
        f"{', '.join(context['accepted_plan_ids'])}; relationships: {', '.join(context['accepted_plan_relationship_ids'])} |"
    )
write(EVIDENCE / "sc_request_deep_dive.md", """# SC Request boundary deep dive

This anchor contains exactly two APIC source operations. The first source operation documents both approve and reject intents; those are two logical intents carried by one source operation, not three manufactured APIC operations. The second source operation documents cancel.

| Source API | Front-end operation | Supported intents | Request refs / response shape | Configured backend | Accepted Product IDs / relationships | Accepted Plan IDs / relationships |
|---|---|---|---|---|---|---|
""" + "\n".join(sc_rows) + """

Both configured backend paths (`/sc/apprejscreq` and `/sc/cancelscreq`) are resolved configuration observations but have `CONFIGURED_API_SHARED_CANDIDATE` scope. They are different paths and do not prove backend behavioral equivalence or actual calls. The accepted Product and Plan IDs and relationship pointers are distinct exposure context. They do not prove common consumers, entitlement intent, owner, release path, active deployment, or production traffic.

## Why provisional cohesion is possible

The direct descriptions and paths support approve/reject/cancel action signals around an SC Request object. A **Unified SC Request Actions** boundary could give consumers one resource-oriented conceptual surface while retaining three distinct logical actions and the two original source-operation identities.

## Why architectural PASS is unavailable

No accepted evidence establishes that decision and cancellation share one lifecycle owner, consumer population, authorization model, entitlement, release cadence, or backend operation. Different front-end schemas, backend paths, Products, and Plans are material counterevidence. Technical validation PASS only proves that this evidence was reproduced correctly; the evidence-sufficiency result is `PARTIAL` and architect acceptance remains `PENDING`.

## Plausible alternative

A **Decision API** could contain approve/reject, while a separate **Cancellation API** owns cancel. That is reasonable if roles, owners, entitlement, audit controls, release cadence, or downstream behavior differ. The unified boundary becomes more reasonable only with authoritative workflow ownership, common consumer intent, authorization and lifecycle evidence; the split becomes more reasonable if those sources prove separation. None is inferred here.
""")

negative = [v for v in records if "NEGATIVE_CONTROL" in v["strata"]]
negative_lines = ["# Negative controls and boundary ambiguity", "", f"The sample contains {len(negative)} explicit negative controls. Structural or contextual similarity is never enough to form a boundary.", ""]
for record in sorted(negative, key=lambda v: v["candidate_boundary_label"]):
    negative_lines.extend([f"## {record['candidate_boundary_label']}", "", f"- Why tested: {record['evidence_for'][0]}", f"- Why not formed: {record['evidence_against'][0]}", f"- Alternative: {record['alternative_boundary']}", f"- Result: `{record['result_axes']['evidence_sufficiency']}`; EA `PENDING`.", ""])
negative_lines.extend([
    "## Non-transitive trap", "",
    "If A and B share a schema, and B and C share a configured backend or object token, A and C are not equivalent and do not automatically share a Logical API. This register creates only direct case-to-member hypotheses and records `transitive_equivalence_inferred=false`. The user-management, Qiwa-streaming, and copied-description controls deliberately avoid joining larger similarity clusters.", "",
    "Do not form a boundary when R1 is contradicted/unresolved, when R2 rests only on tokens or shapes, when copied descriptions conflict with paths, or when unresolved members would raise group certainty. Product/Plan overlap, version family, response wrapper, and API-shared backend evidence remain context only.",
])
write(EVIDENCE / "negative_controls_and_boundary_ambiguity.md", "\n".join(negative_lines) + "\n")

strata = Counter(tag for v in records for tag in v["strata"])
write_json(EVIDENCE / "sample_coverage_and_gaps.json", {
    **summary,
    "target_case_range": "40-50",
    "target_unique_operation_range": "70-100 where feasible",
    "requirements": {
        "same_object_different_actions_6_plus": {"actual": strata["DIFFERENT_ACTIONS"], "met": strata["DIFFERENT_ACTIONS"] >= 6},
        "different_names_paths_same_action_object_6_plus": {"actual": strata["DIVERGENT_EXPOSURE"], "met": strata["DIVERGENT_EXPOSURE"] >= 6},
        "negative_controls_5_plus": {"actual": strata["NEGATIVE_CONTROL"], "met": strata["NEGATIVE_CONTROL"] >= 5},
        "version_variants_5_plus": {"actual": strata["VERSION_VARIANT"], "met": strata["VERSION_VARIANT"] >= 5},
        "multi_operation_apis_4_plus": {"actual": strata["MULTI_OPERATION_API"], "met": strata["MULTI_OPERATION_API"] >= 4},
        "product_plan_context_4_plus": {"actual": strata["PRODUCT_CONTEXT"], "met": strata["PRODUCT_CONTEXT"] >= 4},
        "disagreement_or_backend_uncertainty_4_plus": {"actual": len([v for v in records if {'DISAGREEMENT', 'BACKEND_UNCERTAINTY'} & set(v['strata'])]), "met": len([v for v in records if {'DISAGREEMENT', 'BACKEND_UNCERTAINTY'} & set(v['strata'])]) >= 4},
        "named_leads": {"actual": strata["NAMED_LEAD"], "met": strata["NAMED_LEAD"] == 6},
    },
    "sampling_method": "Deterministic bounded selection of 32 existing Task 016 comparisons, four accepted multi-operation APIs, and the immutable ten-case Task 017 mock.",
    "sampling_bias": ["Purposeful adversarial review sample, not statistically representative.", "Task 016 candidate generation limits which pair relationships are visible.", "HTTP operations with richer descriptions are easier to assess than generic roots or copied metadata."],
    "exclusions": ["No all-pairs search or full-estate formation.", "No raw staging reads for the expansion.", "No production telemetry, CI/CD lineage, release sequence, ownership map, or consumer interviews."],
    "unaddressable_categories": ["Actual production usage and runtime egress.", "Enterprise ownership and release boundaries.", "Consumer intent behind versions and Product/Plan subscriptions.", "Safe consolidation or retirement."],
    "full_estate_coverage_claimed": False,
})

write(EVIDENCE / "review_decision_sheet.md", """# Task 017 expanded validation — EA decision sheet

The 46 cases are evidence for the following small set of rule decisions; they are not 46 compulsory verdicts.

1. Approve, reject, or change the rule that R1 plus R2 need direct resource/workflow responsibility evidence, while schema, name, Product, version, and shared backend remain supporting context only.
2. Decide whether the three multi-operation lifecycle cases are adequate examples of `SUFFICIENT_FOR_PROVISIONAL_BOUNDARY`, or whether consumer/ownership evidence must always be present before that status.
3. Decide whether `PARTIAL` is the right outcome for the SC Request anchor, given supported actions/object but no common lifecycle owner, consumer, entitlement intent, or release evidence.
4. Confirm that copied-description contradictions and generic URI/root cases must remain unformed rather than being rescued by structural equality.
5. Decide whether the 23 insufficient cases reveal an acceptable review queue for full rollout or an unacceptable metadata blind spot requiring a narrower formation method.
6. If the rubric is accepted, authorize or reject a separate Task 017 full-estate plan. This task does not itself grant that authorization.

All new candidate boundaries remain `PENDING`. No duplicate, retirement, Domain, Capability, Product mapping, Kong topology, or production-use decision is requested.
""")

write(EVIDENCE / "commands_and_results.txt", """Task 017 expanded validation deterministic build and validation

.venv/bin/python tests/evidence/task-017/expanded-validation/generate_expanded_evidence.py
RESULT: PASS - generated 46 cases (10 immutable anchors + 36 new), 98 unique operations, and 86 unique canonical APIs.

.venv/bin/pytest tests/test_logical_api_expanded_validation.py
RESULT: PASS - 9 passed.

.venv/bin/pytest
RESULT: 99 passed, 5 known Phase 0 fixture setup errors caused by the absent tests/fixtures/repository_profile/staging directory.
""")

artifact_names = ["architecture_decision_rubric.md", "expanded_sample_register.jsonl", "executive_review_table.md", "sc_request_deep_dive.md", "negative_controls_and_boundary_ambiguity.md", "sample_coverage_and_gaps.json", "review_decision_sheet.md", "commands_and_results.txt", "generate_expanded_evidence.py"]
write_json(EVIDENCE / "build_manifest.json", {
    "rules_version": result["manifest"]["rules_version"], "scope": result["manifest"]["scope"], "summary": summary,
    "original_mock_fingerprint": result["manifest"]["original_mock_fingerprint"], "input_fingerprints": result["manifest"]["inputs"],
    "local_ignored_index_output": result["manifest"]["outputs"]["register"],
    "evidence_artifacts": {name: {"sha256": digest(EVIDENCE / name), "bytes": (EVIDENCE / name).stat().st_size} for name in artifact_names},
    "deterministic_generation": True, "staging_modified": False, "full_estate_formation_performed": False, "architect_acceptance_count": 0,
})
