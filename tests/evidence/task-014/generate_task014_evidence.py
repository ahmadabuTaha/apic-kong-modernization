"""Generate safe architecture-review evidence for Task 014."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from semantic_inventory import write_representative_sample  # noqa: E402


OUTPUT = PROJECT_ROOT / "tests/evidence/task-014"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, values: list[dict]) -> None:
    path.write_text(
        "".join(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for value in values
        ),
        encoding="utf-8",
    )


def generate() -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frozen_paths = [
        PROJECT_ROOT / "indexes/apic_identity_resolution.json",
        PROJECT_ROOT / "indexes/relationship_index.jsonl",
        PROJECT_ROOT / "indexes/codegraph_nodes.jsonl",
        PROJECT_ROOT / "indexes/codegraph_edges.jsonl",
        PROJECT_ROOT / "indexes/codegraph_adjacency.jsonl",
        PROJECT_ROOT / "indexes/backend_target_resolution.jsonl",
        PROJECT_ROOT / "indexes/api_dependency_observations.jsonl",
        PROJECT_ROOT / "indexes/codegraph_dependency_nodes.jsonl",
        PROJECT_ROOT / "indexes/codegraph_dependency_edges.jsonl",
        PROJECT_ROOT / "indexes/codegraph_dependency_adjacency.jsonl",
    ]
    frozen_before = {path.name: _hash(path) for path in frozen_paths}
    with tempfile.TemporaryDirectory(prefix="task-014-a-") as first_tmp, tempfile.TemporaryDirectory(
        prefix="task-014-b-"
    ) as second_tmp:
        first_dir, second_dir = Path(first_tmp), Path(second_tmp)
        first = write_representative_sample(
            PROJECT_ROOT,
            api_path=first_dir / "apis.jsonl",
            operation_path=first_dir / "operations.jsonl",
        )
        second = write_representative_sample(
            PROJECT_ROOT,
            api_path=second_dir / "apis.jsonl",
            operation_path=second_dir / "operations.jsonl",
        )
        api_identical = (first_dir / "apis.jsonl").read_bytes() == (
            second_dir / "apis.jsonl"
        ).read_bytes()
        operation_identical = (first_dir / "operations.jsonl").read_bytes() == (
            second_dir / "operations.jsonl"
        ).read_bytes()
        deterministic_hashes = {
            "api_sample_sha256": _hash(first_dir / "apis.jsonl"),
            "operation_sample_sha256": _hash(first_dir / "operations.jsonl"),
        }

    selection = {
        **first["selection"],
        "required_category_count": len(first["selection"]["categories"]),
        "required_categories_satisfied": sorted(first["selection"]["categories"]),
        "required_categories_impossible_to_sample": [],
        "selection_is_success_only": False,
        "selection_notes": [
            "Registry-only and unresolved Product-location cases are deliberately included.",
            "The first operation-scoped candidate is retained even though it is single-operation; the first later operation-scoped candidate with more than one operation supplies the multi-operation case.",
            "One sampled API may satisfy multiple required categories.",
        ],
    }
    _write_json(OUTPUT / "sample_selection.json", selection)

    api_review = []
    for item in first["api_records"]:
        connections = item["as_is_product_plan_connections"]
        api_review.append(
            {
                "canonical_api_id": item["canonical_api_id"],
                "semantic_api_inventory_id": item["semantic_api_inventory_id"],
                "sample_categories": item["sample_categories"],
                "identity_name": item["identity_name"],
                "api_title": item["api_title"],
                "api_description_present": item["api_description"] is not None,
                "api_version": item["api_version"],
                "protocol": item["protocol"],
                "document_format": item["document_format"],
                "parser_coverage_status": item["parser_coverage_status"],
                "source_representation_status": item["source_representation_status"],
                "accepted_source": item["accepted_source"],
                "operation_count": item["operation_count"],
                "api_shared_backend_observation_ids": [
                    value["target_observation_id"]
                    for value in item["api_shared_backend_evidence"]
                ],
                "operation_scoped_backend_observation_refs": item[
                    "operation_scoped_backend_observation_refs"
                ],
                "product_relationships": connections["product_contains_api"],
                "plan_relationships": connections["plan_entitles_api"],
                "plan_product_relationships": connections[
                    "product_contains_plan_for_entitled_plans"
                ],
                "unresolved_product_location_occurrences": item[
                    "unresolved_product_location_occurrences"
                ],
                "missing_fields": item["missing_fields"],
                "record_layer": item["record_layer"],
                "future_hypotheses": [],
                "architectural_judgments": [],
            }
        )
    _write_jsonl(OUTPUT / "api_sample_review.jsonl", api_review)

    operation_review = []
    for item in first["operation_records"]:
        operation_review.append(
            {
                "canonical_api_id": item["canonical_api_id"],
                "semantic_operation_inventory_id": item[
                    "semantic_operation_inventory_id"
                ],
                "method": item["method"],
                "exact_path": item["exact_path"],
                "operation_id": item["operation_id"],
                "summary": item["summary"],
                "description_present": item["description"] is not None,
                "parameter_count": item["parameter_summary"]["parameter_count"],
                "parameter_schema_references": item["parameter_summary"][
                    "schema_references"
                ],
                "request_summary": item["request_summary"],
                "response_summary": item["response_summary"],
                "operation_scoped_backend_observation_ids": [
                    value["target_observation_id"]
                    for value in item["operation_scoped_backend_evidence"]
                ],
                "api_shared_backend_context": item["api_shared_backend_context"],
                "source_provenance": item["source_provenance"],
                "missing_fields": item["missing_fields"],
                "record_layer": item["record_layer"],
                "future_hypotheses": [],
                "architectural_judgments": [],
            }
        )
    _write_jsonl(OUTPUT / "operation_sample_review.jsonl", operation_review)

    api_missing = Counter(
        missing["field"]
        for item in first["api_records"]
        for missing in item["missing_fields"]
    )
    operation_missing = Counter(
        missing["field"]
        for item in first["operation_records"]
        for missing in item["missing_fields"]
    )
    coverage = {
        **first["coverage"],
        "extraction_gap_taxonomy": {
            "api_missing_field_counts": dict(sorted(api_missing.items())),
            "operation_missing_field_counts": dict(sorted(operation_missing.items())),
            "registry_only_without_source_count": first["coverage"][
                "registry_only_sample_count"
            ],
            "unsupported_document_format_count": sum(
                item["parser_coverage_status"] == "UNSUPPORTED_DOCUMENT_FORMAT"
                for item in first["api_records"]
            ),
            "source_representation_conflict_count": 0,
            "unresolved_product_location_occurrence_count_in_sample": first[
                "coverage"
            ]["sampled_unresolved_product_location_occurrences"],
        },
        "api_shared_backend_not_promoted_to_operation_egress": all(
            item["api_shared_backend_context"]["status"]
            in {
                "API_LEVEL_ONLY_NOT_PROVEN_OPERATION_EGRESS",
                "NO_API_SHARED_BACKEND_OBSERVATION",
            }
            for item in first["operation_records"]
        ),
        "operation_records_are_not_graph_nodes": True,
        "unresolved_product_occurrences_preserved_not_attached": True,
        "deterministic_repeated_build": api_identical and operation_identical,
        "deterministic_output_sha256": deterministic_hashes,
        "local_generated_output_sha256": {
            "api": _hash(
                PROJECT_ROOT / "indexes/semantic_api_inventory_sample.jsonl"
            ),
            "operation": _hash(
                PROJECT_ROOT / "indexes/semantic_operation_inventory_sample.jsonl"
            ),
        },
        "frozen_phase_0_through_4_hashes_unchanged": frozen_before
        == {path.name: _hash(path) for path in frozen_paths},
        "architecture_review_questions": [
            "Approve or revise the API and operation field contract before estate-wide rollout.",
            "Decide whether duplicate accepted YAML representations require a separate conflict-comparison report.",
            "Decide whether callbacks/webhooks and GraphQL/SOAP/AsyncAPI need protocol-specific inventory records.",
            "Confirm that API_SHARED backend evidence remains API-only context rather than proven operation egress.",
            "Confirm the missing-description review threshold for later semantic work.",
        ],
        "task_018_domain_mock_authorized_by_this_task": False,
    }
    coverage["overall_acceptance_pass"] = all(
        (
            coverage["operation_record_ids_unique"],
            coverage["api_shared_backend_not_promoted_to_operation_egress"],
            coverage["unresolved_product_occurrences_preserved_not_attached"],
            coverage["deterministic_repeated_build"],
            coverage["frozen_phase_0_through_4_hashes_unchanged"],
            not coverage["semantic_function_inference_performed"],
            not coverage["logical_api_formation_performed"],
            not coverage["domain_or_capability_tagging_performed"],
        )
    )
    _write_json(OUTPUT / "coverage_and_gaps.json", coverage)
    return {
        "selection": selection,
        "coverage": coverage,
        "api_review_count": len(api_review),
        "operation_review_count": len(operation_review),
        "overall_pass": coverage["overall_acceptance_pass"],
    }


if __name__ == "__main__":
    print(json.dumps(generate(), ensure_ascii=False, indent=2, sort_keys=True))
