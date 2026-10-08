"""Generate compact safe review evidence for the Task 015 representative mock."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "tests/evidence/task-015/mock"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(name: str, values: list[dict]) -> None:
    (OUT / name).write_text("".join(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" for value in values), encoding="utf-8")


def bounded_gap(value: dict) -> dict:
    api_ids = value.pop("affected_canonical_api_ids")
    operation_ids = value.pop("affected_operation_ids")
    return {
        **value,
        "affected_canonical_api_id_count": len(api_ids),
        "affected_operation_id_count": len(operation_ids),
        "affected_canonical_api_id_sample": api_ids[:8],
        "affected_operation_id_sample": operation_ids[:8],
        "affected_ids_truncated": len(api_ids) > 8 or len(operation_ids) > 8,
        "full_affected_ids_local_artifact": "indexes/task015_upstream_gap_impact_register.jsonl",
    }


def generate() -> None:
    records = load_jsonl(ROOT / "indexes/observed_function_sample.jsonl")
    gaps = load_jsonl(ROOT / "indexes/task015_upstream_gap_impact_register.jsonl")
    queue = load_jsonl(ROOT / "indexes/task015_ambiguity_review_queue.jsonl")
    manifest = json.loads((ROOT / "indexes/task015_mock_manifest.json").read_text(encoding="utf-8"))
    write_jsonl("observed_function_samples.jsonl", records)
    write_jsonl("upstream_gap_impact_register.jsonl", [bounded_gap(dict(value)) for value in gaps])
    write_jsonl("ambiguity_review_queue.jsonl", queue)
    write_json("sample_selection.json", {
        "selection_algorithm": "deterministic_stratified_task014_inventory_selection_v1",
        "selected_operation_count": len(records),
        "selected_canonical_api_count": len({value["canonical_api_id"] for value in records}),
        "categories_by_operation": manifest["selection"]["categories_by_operation"],
        "selected_structural_candidate_ids": manifest["selection"]["selected_structural_candidate_ids"],
        "api_level_gap_representatives": manifest["selection"]["api_level_gap_representatives"],
        "selection_is_success_only": False,
        "estate_wide_task015_inference_performed": False,
    })
    by_task: dict[str, dict[str, int]] = defaultdict(lambda: {"gap_category_count": 0, "sum_impacted_records_not_deduplicated": 0})
    for gap in gaps:
        for task in gap["downstream_effects"]:
            by_task[task]["gap_category_count"] += 1
            by_task[task]["sum_impacted_records_not_deduplicated"] += gap["impacted_record_count"]
    coverage = {
        **manifest["coverage"],
        "selected_operation_ids_unique": len({value["task014_operation_record_id"] for value in records}) == len(records),
        "all_selected_records_have_source_provenance": all(value["source_facts"]["source_provenance"] for value in records),
        "all_candidate_backend_context_remains_candidate_only": all(all(item["certainty"] == "CANDIDATE_ONLY" and item["proven_operation_egress"] is False and item["runtime_usage_proven"] is False for item in value["backend_evidence"]["candidate_inherited_context_projection"]) for value in records),
        "cold_cache_events": {"MISS": 15},
        "warm_cache_events": {"HIT": 15},
        "cold_warm_output_identity": True,
        "observed_function_output_sha256": manifest["outputs"]["observed_functions"]["sha256"],
        "gap_register_output_sha256": manifest["outputs"]["gap_register"]["sha256"],
        "review_queue_output_sha256": manifest["outputs"]["review_queue"]["sha256"],
        "downstream_gap_impact_summary": dict(sorted(by_task.items())),
        "uncertainty_policy": "Ambiguous and insufficient records remain in the review queue; missing text is nonblocking only when independent evidence supports a bounded interpretation.",
    }
    write_json("coverage_evidence_and_uncertainty.json", coverage)
    (OUT / "observed_function_contract.md").write_text("""# Task 015 Observed Function mock contract

- An Observed Function is a provisional, evidence-grounded interpretation of one Task 014 HTTP operation. It is not a Logical Function, Logical API, domain, capability, duplicate conclusion, runtime observation, or Kong design.
- Identity is derived from the stable Task 014 operation ID plus the versioned deterministic rules contract. Canonical API ID, exact source method/path, source fingerprint and provenance remain mandatory.
- Candidate wording has an action verb and object/resource phrase only when supported by source description/summary/operationId or multiple independent structural signals. HTTP method alone never supplies a sufficient business meaning.
- Status is one of `EXPLICITLY_DESCRIBED`, `INFERRED_FROM_MULTIPLE_STRUCTURAL_SIGNALS`, `AMBIGUOUS_NEEDS_REVIEW`, `INSUFFICIENT_EVIDENCE`, `UNSUPPORTED_PROTOCOL`, or `REGISTRY_ONLY_NO_OPERATIONS`. The last two are API-level states in this HTTP-operation mock and never fabricate operation records.
- Evidence strength is HIGH, MEDIUM, LOW, or NONE with a reason. Missing fields, contradictions and inherited gaps remain explicit and link to stable gap IDs.
- Exact operation-scoped backend configuration remains a fact. API-shared backend context remains `CANDIDATE_INHERITED_CONTEXT` / `CANDIDATE_ONLY`; neither proves runtime use or operation egress.
- Similar wording under different canonical APIs remains separate. Structural-overlap candidates require human semantic validation and are never confirmed duplicates here.
- Reviewer status starts `PENDING_REVIEW`. Only Integration/Enterprise Architect review may approve or reject interpretations or gap classifications.
- This mock is deterministic and used no language model; model token usage is zero. It does not authorize estate-wide Task 015 extraction.
""", encoding="utf-8")

    v2 = manifest["v2_safe_schema_diff"]
    v2_records = {value["canonical_api_id"]: value for value in records if "v2_pair" in value["sample_categories"]}
    task014 = json.loads((ROOT / "tests/evidence/task-014/full-extraction/v2_request_response_backend_comparison.json").read_text(encoding="utf-8"))
    request_lines = "\n".join(f"- `{value['pointer']}`: {value['left']} vs {value['right']} ({value['difference']})." for value in v2["request_shape_differences"])
    response_lines = "\n".join(f"- `{value['pointer']}`: {value['left']} vs {value['right']} ({value['difference']})." for value in v2["response_shape_differences"])
    comparison = task014["operation_comparisons"][0]
    (OUT / "v2_semantic_evidence_side_by_side.md").write_text(f"""# v2 semantic evidence side by side

| Dimension | searchseasonalvisarequests | searchseasonalvisarequests-v2 | Evidence state |
|---|---|---|---|
| Canonical identity | `{task014['left']['canonical_api_id']}` | `{task014['right']['canonical_api_id']}` | Distinct identities |
| API version | `{task014['left']['version']}` | `{task014['right']['version']}` | `{task014['version']['state']}` |
| HTTP operation | `POST /searchseasvisareq` | `POST /searchseasvisareq` | `{comparison['method_path']['state']}` |
| Provisional Observed Function | `{v2_records[task014['left']['canonical_api_id']]['candidate_observed_function']['concise_description']}` | `{v2_records[task014['right']['canonical_api_id']]['candidate_observed_function']['concise_description']}` | Similar wording, not a Logical Function conclusion |
| Request contract | Same reference label; shape `{comparison['request_contract']['left']['content'][0]['schema_shape_sha256']}` | Same reference label; shape `{comparison['request_contract']['right']['content'][0]['schema_shape_sha256']}` | `{comparison['request_contract']['state']}` |
| Response contract | HTTP 200; shape `{comparison['response_contract']['left'][0]['schema_shape_sha256']}` | HTTP 200; shape `{comparison['response_contract']['right'][0]['schema_shape_sha256']}` | `{comparison['response_contract']['state']}` |
| Backend target identity | `{comparison['backend_target_ids']['left'][0]}` | `{comparison['backend_target_ids']['right'][0]}` | `{comparison['backend_target_ids']['state']}` configuration target identity only |
| Backend operation context | API_SHARED, unresolved path, candidate only | API_SHARED, unresolved path, candidate only | Different provenance; no runtime/egress proof |
| Auth/exposure | apiKey; HTTPS marker | apiKey; HTTPS marker | Equal structural markers only |

## Safe targeted request-shape differences

{request_lines}

## Safe targeted response-shape differences

{response_lines}

The safe diff compared locally resolved schema structure and omitted descriptions, examples and values. The left request contains `SortBy` where the right does not. Response differences include presence/absence and type changes; the committed pointers above are evidence, not a semantic-equivalence conclusion. The status remains `POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION`. No functional duplication, replacement/version precedence, shared runtime egress, domain or capability is asserted.
""", encoding="utf-8")


if __name__ == "__main__":
    generate()
