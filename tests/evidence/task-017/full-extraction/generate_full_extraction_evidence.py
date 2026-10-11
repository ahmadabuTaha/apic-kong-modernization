from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parents[4]
EVIDENCE = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from logical_api.full_formation import OUTPUTS, build_full_formation  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" for value in values),
        encoding="utf-8",
    )


def safe_cell(value: object) -> str:
    return str(value).replace("|", "/").replace("\n", " ")


def artifact_fingerprint(path: Path) -> dict[str, object]:
    return {
        "sha256": digest(path),
        "bytes": path.stat().st_size,
    }


def write_contract() -> None:
    (EVIDENCE / "logical_api_formation_contract.md").write_text(
        """# Task 017 full Logical API formation contract

## Purpose and boundaries

This is a deterministic, source-provenanced **provisional conceptual boundary**
catalog over the accepted Task 014 HTTP operation inventory. A Logical API is
not an APIC API identity, APIC Product, Kong Service, Kong Route, or Kong Product.
Functional-equivalence candidates and Logical API cohesion are separate axes:
distinct actions can belong to one resource/workflow boundary without being
duplicates; a possible same action across APIs does not establish shared cohesion.

Each accepted Task 014 operation appears exactly once in the primary disposition
ledger. Within-current-API proposals use direct operation assertions. Task 016
cross-API comparisons remain candidate references only. No transitive closure,
automatic merge, retirement, Domain, Capability, Kong design, or production
claim is made. Operations with insufficient evidence, singletons, oversized
groups, and API-level gaps remain visible as nonformation outcomes.

## Evidence criteria R1-R7

Each proposal and each direct member assertion records all seven criteria with a
`SUPPORTED`, `CONTRADICTED`, or `NOT_EVIDENCED` status and source references:

| Criterion | Assessment |
|---|---|
| R1 Resource | Explicit/corroborated non-generic resource, workflow, or resource identity. |
| R2 Cohesion | Distinct actions plus a direct resource-path family or evidenced lifecycle/workflow; shared object tokens alone do not suffice. |
| R3 Consumer/authorization/ownership | Product, Plan, and Subscription links remain exposure context; they do not establish actual consumers, owners, roles, or entitlement intent. |
| R4 Contract and variants | Exact method/path, API version, request/response fingerprints, status codes, and security requirements stay visible; compatibility is not inferred. |
| R5 Backend operation | Operation-scoped configuration is distinct from API-shared candidate context and from proven runtime behavior/egress. |
| R6 Counterevidence | A concrete reason not to group, a plausible alternative, and the evidence that could decide are retained. |
| R7 Provenance | Canonical API, Task 014 operation, Task 015 observed-function, Task 016 candidate/refinement IDs, source hashes, and source pointers are traceable. |

For a bounded current-API resource-path family, R1+R2+R7 can support
`SUFFICIENT_FOR_PROVISIONAL_BOUNDARY` even when R3/R5 remain
`NOT_EVIDENCED`. Cross-canonical-API formation is deliberately not automated in
this pass. Generic wrappers, shared schemas, backend/system matches, Product
overlap, and names alone do not establish cohesion.

## Primary membership and competing alternatives

`task017_full_operation_disposition.jsonl` is the sole primary operation
disposition. Each row has one direct proposal link at most. Proposal alternatives
and Task 016 functional candidates remain separately identified; they do not
duplicate primary membership or collapse source operation IDs. A source
operation may retain multiple action intents (including the SC Request
approve/reject operation) without manufacturing source operations.

## Independent result axes

1. `TECHNICAL_VALIDATION` describes deterministic construction, reconciliation,
   frozen-input integrity, and tests only.
2. `EVIDENCE_SUFFICIENCY` is `SUFFICIENT_FOR_PROVISIONAL_BOUNDARY`, `PARTIAL`,
   `INSUFFICIENT`, or `SUPPORTED_SEPARATE`.
3. `ARCHITECT_ACCEPTANCE` remains `PENDING` for every proposal.

Technical PASS is not architecture PASS. No proposal has been accepted by the
Enterprise Architect in this output.
""",
        encoding="utf-8",
    )


def write_regression_report(result: dict) -> None:
    cases = result["regression_rows"]
    states = Counter(row["change_state"] for row in cases)
    details = [
        "# Task 017 sample regression and contradiction review",
        "",
        "The original 10-case mock and the 46-case expanded register are immutable inputs. Their evidence-sufficiency decisions remain the sample baseline; this full pass adds a separate within-current-API reassessment. Cross-API cases and skipped oversized groups are not silently promoted into primary boundaries.",
        "",
        "## Regression comparison",
        "",
        "| Full-pass comparison | Count |",
        "|---|---:|",
    ]
    for state, count in sorted(states.items()):
        details.append(f"| {safe_cell(state)} | {count} |")
    details.extend(
        [
            "",
            f"Cases: **{len(cases)}**. Status differences requiring review: **{states['STATUS_DIFFERENCE_REQUIRES_REVIEW']}**. Unchanged comparable cases: **{states['UNCHANGED']}**. Cross-API or skipped/no-proposal cases that remain preserved but not directly comparable: **{states['NOT_COMPARABLE_OR_NO_PRIMARY_PROPOSAL']}**.",
            "",
            "| Case | Frozen sample | Full primary assessment | Comparison |",
            "|---|---|---|---|",
        ]
    )
    for row in cases:
        details.append(
            f"| {safe_cell(row['label'])} | {row['frozen_sample_sufficiency']} | "
            f"{row['full_estate_primary_sufficiency']} | {row['change_state']} |"
        )
    changed = [row for row in cases if row["change_state"] == "STATUS_DIFFERENCE_REQUIRES_REVIEW"]
    details.extend(["", "### Differences that must remain visible", ""])
    if changed:
        for row in changed:
            details.append(
                f"- **{row['label']}:** `{row['frozen_sample_sufficiency']}` in the bounded sample versus "
                f"`{row['full_estate_primary_sufficiency']}` for the full current-API family. {row['rationale']}"
            )
    else:
        details.append(
            "No status differences were found among the five directly comparable sample cases. "
            "The remaining 41 cross-API or no-proposal cases retain their frozen sample results and are not treated as full-estate primary memberships."
        )
    details.extend(
        [
            "",
            "## Positive provisional examples",
            "",
            "Five full-estate current-API proposals meet the deterministic R1+R2+R7 rule. Three are the expanded-sample anchors: Visa Resource Lifecycle, Special Permit Resource Lifecycle, and Runaway Request Workflow. Two additional proposals are evidenced resource-path/action families for submitting a Saudi certificate and raising an objection request. All remain provisional; R3 consumer/ownership and R5 runtime/backend-semantic evidence remain unresolved, and EA acceptance is PENDING.",
            "",
            "## Negative controls and counterevidence",
            "",
            "- Generic user-management URI templates remain unformed: `uri` placeholders are not resource evidence.",
            "- Equal request/response schemas or shared backend candidates do not bridge establishment-violation and certificate-validity objects, pricing and authentication indicators, or WPS wrappers.",
            "- Conflicting/copy-like descriptions, materially different actions, and API-wide backend candidates stay explicit counterevidence; no transitive inference is made from Task 016 pairs.",
            "- Version labels and contract variants remain visible on each member; neither newest/oldest nor compatibility is inferred.",
            "",
            "## SC Request regression",
            "",
            "The frozen SC Request sample remains `PARTIAL`: two source operations (`approverejectscrequest` and `cancelscrequest`) carry three logical action intents (approve, reject, cancel). The two source IDs remain distinct. Unified SC Request Actions versus separate Decision and Cancellation boundaries remain competing alternatives. The full pass creates no cross-canonical-API primary boundary and infers no shared ownership, lifecycle, consumer, authorization, backend behavior, or production use.",
            "",
            "## Scope limitations",
            "",
            "Source artifacts are staging/sandbox-like. Production deployment, runtime traffic, active flags, release sequence, live egress, consumer activity, ownership, and safe retirement are not established. These findings are provisional discovery inputs for Integration Architect and Enterprise Architect review, not business/API approval.",
            "",
        ]
    )
    (EVIDENCE / "case_regression_and_contradictions.md").write_text(
        "\n".join(details), encoding="utf-8"
    )


def write_review_queue(result: dict) -> None:
    queue = result["review_queue"]
    proposals = result["proposals"]
    criterion_statuses = {
        f"R{index}": Counter(
            proposal["candidate_rubric"][f"R{index}"]["status"] for proposal in proposals
        )
        for index in range(1, 8)
    }
    high_priority = [item for item in queue if item["priority"] == "HIGH"][:20]
    value = {
        "review_item_count": len(queue),
        "priority_counts": dict(sorted(Counter(item["priority"] for item in queue).items())),
        "reason_counts": dict(
            sorted(Counter(item["primary_failure_or_decision_reason"] for item in queue).items())
        ),
        "criterion_status_counts_across_proposals": {
            criterion: dict(sorted(counts.items()))
            for criterion, counts in criterion_statuses.items()
        },
        "top_prioritized_architecture_questions": high_priority,
        "manual_review_scope": (
            "Prioritize bounded alternatives and failure reasons. Do not manually adjudicate all 2,414 operations or "
            "all 1,170 Task 016 pairs; unformed operations remain searchable in the full ledger."
        ),
        "missing_evidence": {
            "consumer_owner_authorization_entitlement": "NOT_EVIDENCED in current accepted source evidence; Product/Plan/Subscription association is exposure context only.",
            "operation_backend_semantics_and_runtime_egress": "Mostly API-shared configured candidate context; no runtime egress inference.",
            "production_activity_release_lineage_and_feature_flags": "NOT_EVIDENCED; staging export is not production proof.",
            "domain_and_capability": "Out of scope; no assignment made.",
            "retirement_or_substitution": "Out of scope; no decision made.",
        },
        "architect_acceptance_count": 0,
    }
    write_json(EVIDENCE / "review_queue_and_missing_evidence.json", value)


def write_cache_and_tests(result: dict, focused_result: str, repository_result: str) -> None:
    manifest = result["manifest"]
    value = {
        "cache_validation": {
            "task016_candidate_pair_sha256_verified_against_manifest": True,
            "task017_expanded_register_sha256_verified_against_manifest": True,
            "frozen_input_fingerprints": manifest["inputs"],
            "staging_read": False,
            "frozen_inputs_modified": False,
            "all_pairs_search_performed": False,
        },
        "test_runs": {
            "focused_command": (
                ".venv/bin/pytest -q tests/test_logical_api_full_formation.py "
                "tests/test_logical_api_expanded_validation.py tests/test_logical_api_mock.py"
            ),
            "focused_result": focused_result,
            "repository_command": "pytest",
            "repository_result": repository_result,
            "known_baseline": "Five Phase 0 fixture setup errors are documented historical failures caused by missing tests/fixtures/repository_profile/staging; do not reopen frozen Phase 0.",
        },
        "result_axes": {
            "technical_validation": (
                "PASS" if focused_result.startswith("PASS") and repository_result.startswith("PASS") else "SEE_COMMAND_RESULTS"
            ),
            "architect_acceptance": "PENDING",
        },
    }
    write_json(EVIDENCE / "cache_and_tests.json", value)
    (EVIDENCE / "commands_and_results.txt").write_text(
        "\n".join(
            [
                "Task 017 full logical API formation",
                "",
                "Generation:",
                "  .venv/bin/python -m logical_api.full_formation_main",
                "  Result: PASS; deterministic indexes/evidence generated from frozen Task 014-017 indexes.",
                "",
                "Focused validation:",
                "  .venv/bin/pytest -q tests/test_logical_api_full_formation.py "
                "tests/test_logical_api_expanded_validation.py tests/test_logical_api_mock.py",
                f"  Result: {focused_result}",
                "",
                "Required repository validation:",
                "  .venv/bin/pytest",
                f"  Result: {repository_result}",
                "",
                "Architecture decisions:",
                "  Evidence sufficiency is separate from technical validation.",
                "  Enterprise Architect acceptance: PENDING for all proposals.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def update_manifests(result: dict) -> None:
    evidence_files = [
        path for path in EVIDENCE.iterdir()
        if path.is_file() and path.name != "build_manifest.json"
    ]
    evidence_manifest = {
        "scope": "TASK017_FULL_PROVISIONAL_LOGICAL_API_FORMATION",
        "generated_deterministically": True,
        "evidence_files": {
            path.name: {**artifact_fingerprint(path), "path": path.relative_to(ROOT).as_posix()}
            for path in sorted(evidence_files)
        },
        "source_code": {
            path.relative_to(ROOT).as_posix(): artifact_fingerprint(path)
            for path in (
                ROOT / "logical_api/full_formation.py",
                ROOT / "logical_api/full_formation_main.py",
                ROOT / "tests/test_logical_api_full_formation.py",
                EVIDENCE / "generate_full_extraction_evidence.py",
            )
        },
        "technical_validation": {
            "focused_result": ARGS.focused_test_result,
            "repository_result": ARGS.repository_test_result,
        },
        "architect_acceptance": "PENDING",
    }
    write_json(EVIDENCE / "build_manifest.json", evidence_manifest)
    index_manifest_path = ROOT / OUTPUTS["manifest"]
    index_manifest = json.loads(index_manifest_path.read_text(encoding="utf-8"))
    index_manifest["outputs"]["committed_evidence"] = {
        name: {
            "path": entry["path"],
            "sha256": entry["sha256"],
            "bytes": entry["bytes"],
        }
        for name, entry in evidence_manifest["evidence_files"].items()
    }
    index_manifest["technical_validation"] = {
        "focused_result": ARGS.focused_test_result,
        "repository_result": ARGS.repository_test_result,
    }
    write_json(index_manifest_path, index_manifest)


parser = argparse.ArgumentParser()
parser.add_argument("--focused-test-result", default="PENDING")
parser.add_argument("--repository-test-result", default="PENDING")
ARGS = parser.parse_args()

full_result = build_full_formation(ROOT)
write_contract()
write_regression_report(full_result)
write_review_queue(full_result)
write_cache_and_tests(
    full_result,
    ARGS.focused_test_result,
    ARGS.repository_test_result,
)
update_manifests(full_result)
