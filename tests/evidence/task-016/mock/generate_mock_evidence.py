"""Generate bounded, deterministic Task 016 mock review evidence."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "tests/evidence/task-016/mock"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(name: str, values: list[dict]) -> None:
    (OUT / name).write_text("".join(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" for value in values), encoding="utf-8")


def generate() -> None:
    comparisons = load_jsonl(ROOT / "indexes/task016_mock_candidate_comparisons.jsonl")
    review = load_jsonl(ROOT / "indexes/task016_mock_review_queue.jsonl")
    manifest = json.loads((ROOT / "indexes/task016_mock_manifest.json").read_text())
    gaps = load_jsonl(ROOT / "indexes/task015_full_gap_impact_register.jsonl")
    write_jsonl("candidate_pair_comparisons.jsonl", comparisons)
    write_jsonl("candidate_review_queue.jsonl", review)
    write_json("sample_pair_selection.json", {
        "rules_version": manifest["rules_version"],
        "sample_pair_count": len(comparisons),
        "structural_candidate_pair_count": manifest["structural_candidate_pair_count"],
        "indexed_negative_control_count": manifest["indexed_negative_control_count"],
        "status_distribution": manifest["status_distribution"],
        "category_distribution": manifest["category_distribution"],
        "selection": [{
            "comparison_id": value["comparison_id"],
            "selection_key": value["selection_key"],
            "selection_basis": value["selection_basis"],
            "sample_categories": value["sample_categories"],
            "left_canonical_api_id": value["left"]["canonical_api_id"],
            "left_operation_id": value["left"]["task014_operation_id"],
            "right_canonical_api_id": value["right"]["canonical_api_id"],
            "right_operation_id": value["right"]["task014_operation_id"],
            "comparison_status": value["comparison_status"],
        } for value in sorted(comparisons, key=lambda item: item["selection_key"])],
        "targeted_source_document_count": len(manifest["inputs"]["targeted_source_documents"]),
        "all_pairs_analysis_performed": False,
        "full_estate_grouping_performed": False,
    })

    consumption = []
    type_map = {
        "task014-gap:missing-summary": "METADATA_ABSENT",
        "task014-gap:missing-description": "METADATA_ABSENT",
        "task014-gap:missing-operationid": "METADATA_ABSENT",
        "task014-gap:registry-only-no-operations": "SOURCE_EVIDENCE_NOT_AVAILABLE",
        "task014-gap:no-supported-path-items": "SOURCE_EVIDENCE_NOT_AVAILABLE",
        "task014-gap:native-protocol-semantics-not-extracted": "SOURCE_EVIDENCE_NOT_AVAILABLE",
        "task014-gap:unresolved-product-location": "SOURCE_EVIDENCE_NOT_AVAILABLE",
        "task014-gap:api-shared-backend-candidate-context": "RUNTIME_NOT_EVIDENCED",
        "task014-gap:structural-overlap-candidates": "SEMANTIC_VALIDATION_PENDING",
        "task014-gap:v2-schema-shape-difference": "SEMANTIC_VALIDATION_PENDING",
        "task014-gap:missing-request-schema-shape": "AUTOMATED_INTERPRETATION_LIMIT",
    }
    for gap in gaps:
        consumption.append({
            "gap_id": gap["gap_id"],
            "consumption_classification": type_map[gap["gap_id"]],
            "inherited_severity": gap["severity"],
            "scope": gap["scope"],
            "affected_canonical_api_count": len(gap["affected_canonical_api_ids"]),
            "affected_operation_count": len(gap["affected_operation_ids"]),
            "task016_consumption": gap["downstream_effects"]["016"],
            "mock_handling": "Preserved as pair-specific uncertainty; never interpreted as a production quality, inactivity, or global phase-stop conclusion.",
            "recovery_trigger": gap["recheck_trigger"],
            "frozen_upstream_changed": False,
        })
    write_json("inherited_gap_consumption_assessment.json", {
        "inherited_gap_category_count": len(consumption),
        "consumption_classification_distribution": dict(sorted(Counter(value["consumption_classification"] for value in consumption).items())),
        "downstream_blocker_scope": "Only the affected comparison or unsupported conclusion; never the whole Task 016 phase.",
        "staging_source_qualification": "Missing metadata or runtime evidence in this staging/sandbox-like export is not evidence of a production API defect, inactivity, retirement, or business criticality.",
        "categories": sorted(consumption, key=lambda value: value["gap_id"]),
    })

    v2 = next(value for value in comparisons if value["selection_key"] == "seasonal_visa_v2_contract_change")
    request_lines = "\n".join(f"- `{value['pointer']}`: {value['left']} vs {value['right']} ({value['difference']})." for value in v2["actual_safe_schema_comparison"]["request_shape_differences"])
    material = [value for value in v2["actual_safe_schema_comparison"]["response_shape_differences"] if value["pointer"].endswith("/InsertDate/type") or value["difference"] == "VALUE_DIFFERENCE"][:8]
    response_lines = "\n".join(f"- `{value['pointer']}`: {value['left']} vs {value['right']} ({value['difference']})." for value in material)
    (OUT / "v2_contract_and_function_assessment.md").write_text(f"""# Seasonal visa v2 contract and function assessment

- Comparison: `{v2['comparison_id']}`.
- Proposal status: `{v2['comparison_status']}`; this is not approval of sameness, duplication, substitution, version precedence, retirement, or runtime equivalence.
- Both operations are `POST /searchseasvisareq` and have the same provisional Task 015 wording, `search seasonal visa requests`.
- Both carry API-shared candidate backend context only. The common configured target identity used for blocking does not prove either operation's runtime egress.
- The API versions differ (`{v2['left']['api_version']}` versus `{v2['right']['api_version']}`), but version labels do not establish replacement order.

## Actual safe request-shape differences

{request_lines}

## Material response-shape differences

{response_lines}

The safe comparison found {len(v2['actual_safe_schema_comparison']['response_shape_differences'])} response-shape differences in total, including field presence, required-list and type differences. Descriptions, examples and data values were omitted. The evidence supports review of a possible common apparent search function with different contracts; it does not support automatic merging or safe replacement.
""", encoding="utf-8")

    by_key = {value["selection_key"]: value for value in comparisons}
    (OUT / "false_positive_negative_cases.md").write_text(f"""# Task 016 mock false-positive and false-negative controls

## False-positive controls

- `{by_key['appointment_action_conflict']['comparison_id']}` shares a structural candidate block and path, but provisional source wording distinguishes validating attendance from updating appointment status and the safe request/response shapes differ. Status remains `REVIEW_REQUIRED_CONFLICTING_SIGNALS`.
- `{by_key['farming_establishment_action_conflict']['comparison_id']}` shares path/backend signals while its provisional wording and payload shapes conflict. It is not merged.
- `{by_key['payment_token_generate_vs_delete']['comparison_id']}` intentionally uses the same payment-token object with explicit generate versus delete actions. It is `CLEARLY_DIFFERENT_SUPPORTED`, demonstrating that object similarity is insufficient.
- `{by_key['technical_health_vs_token']['comparison_id']}` separates a health check from token retrieval using explicit path/action/contract evidence. Technical/security endpoints are not forced into a business function.

## Missing-evidence control

- `{by_key['root_get_missing_evidence']['comparison_id']}` contains root-path GET operations with insufficient Task 015 evidence. Shared backend/structure does not fill the semantic gap; status is `NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE`.

## False-negative limits

- Different paths or payload shapes may still represent a common intent behind a façade, adaptor, middleware transform, path rewrite, or versioned contract.
- Schema aliases and field renames can obscure shared intent; equal schema hashes can also hide behavioral differences not represented in configuration.
- Candidate-only backend context and staging configuration do not prove runtime routing. Runtime evidence, named design documentation, or human validation may change a proposal later without reopening frozen identity.
- No full-estate recall claim is made from this ten-pair mock.
""", encoding="utf-8")


if __name__ == "__main__":
    generate()
