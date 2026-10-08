import hashlib
import json
from pathlib import Path

import pytest

from semantic_inventory import extract_api_inventory, write_representative_sample


ROOT = Path(__file__).resolve().parents[1]
PHASE2 = ROOT / "indexes/apic_identity_resolution.json"
TASK014_EVIDENCE = ROOT / "tests/evidence/task-014"


def _identity(*, sources: bool = True) -> dict:
    return {
        "canonical_identity_record_id": "api-1",
        "canonical_object_type": "api_artifact",
        "name": "sample",
        "title": "Sample",
        "version": "1.0.0",
        "authoritative_artifact_occurrence_ids": ["occurrence-a", "occurrence-b"]
        if sources
        else [],
        "contributing_extracted_record_ids": ["occurrence-a", "occurrence-b"]
        if sources
        else ["registry-occurrence"],
        "source_evidence": [
            {
                "extracted_record_id": occurrence,
                "source_relative_path": "staging/apis/sample.yaml",
                "source_object_pointer": "",
            }
            for occurrence in ("occurrence-a", "occurrence-b")
        ]
        if sources
        else [
            {
                "extracted_record_id": "registry-occurrence",
                "source_relative_path": "staging/apis/_catalog/_list.json",
                "source_object_pointer": "/results/0",
            }
        ],
    }


def _backend(scope: str, identifier: str, operation_scope: list[dict] | None = None) -> dict:
    return {
        "target_observation_id": identifier,
        "scope_classification": scope,
        "operation_scope": operation_scope,
        "target_classification": "CATALOG_PROPERTY_RESOLVED",
        "resolution_status": "RESOLVED",
        "resolution_reason": "all_catalog_properties_resolved_exactly",
        "symbolic_property_tokens": ["backend"],
        "runtime_parameter_tokens": [],
        "source_path": "staging/apis/sample.yaml",
        "source_pointer": "/assembly/0/invoke/target-url",
        "source_sha256": "a" * 64,
        "target_path_suffix_or_template": "/safe-path",
    }


def test_multi_operation_ids_missing_metadata_refs_scope_and_duplicate_source_occurrences() -> None:
    document = {
        "swagger": "2.0",
        "info": {"title": "Sample", "version": "1.0.0"},
        "x-ibm-configuration": {"type": "rest"},
        "paths": {
            "/items": {
                "parameters": [{"$ref": "#/parameters/Correlation"}],
                "get": {
                    "operationId": "listItems",
                    "summary": "List items",
                    "responses": {"200": {"schema": {"$ref": "#/definitions/Item"}}},
                },
                "post": {
                    "description": "Create without a summary",
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {"$ref": "#/definitions/NewItem"},
                        }
                    ],
                    "responses": {"201": {"description": "created"}},
                },
            }
        },
    }
    shared = _backend("API_SHARED", "shared")
    scoped = _backend(
        "OPERATION_SCOPED",
        "scoped",
        [{"verb": "post", "path": "/items", "operation_id": None}],
    )
    api, operations = extract_api_inventory(
        _identity(),
        document,
        source_path="staging/apis/sample.yaml",
        source_sha256="a" * 64,
        backend_observations=[shared, scoped],
        relationships=[],
        unresolved_product_occurrences=[],
        sample_categories=["test"],
    )
    assert api["operation_count"] == 2
    assert api["accepted_source"]["source_occurrence_ids"] == [
        "occurrence-a",
        "occurrence-b",
    ]
    assert len({item["semantic_operation_inventory_id"] for item in operations}) == 2
    assert {(item["method"], item["exact_path"]) for item in operations} == {
        ("GET", "/items"),
        ("POST", "/items"),
    }
    get = next(item for item in operations if item["method"] == "GET")
    post = next(item for item in operations if item["method"] == "POST")
    assert get["description"] is None
    assert {item["field"] for item in get["missing_fields"]} == {"description"}
    assert get["parameter_summary"]["schema_references"] == [
        "#/parameters/Correlation"
    ]
    assert get["response_summary"]["schema_references"] == [
        "#/definitions/Item"
    ]
    assert post["request_summary"]["schema_references"] == [
        "#/definitions/NewItem"
    ]
    assert post["operation_scoped_backend_evidence"][0][
        "target_observation_id"
    ] == "scoped"
    assert get["operation_scoped_backend_evidence"] == []
    assert all(
        item["api_shared_backend_context"]["status"]
        == "API_LEVEL_ONLY_NOT_PROVEN_OPERATION_EGRESS"
        for item in operations
    )
    assert all(
        item["api_shared_backend_context"]["target_observation_ids"] == ["shared"]
        for item in operations
    )
    again = extract_api_inventory(
        _identity(),
        document,
        source_path="staging/apis/sample.yaml",
        source_sha256="a" * 64,
        backend_observations=[shared, scoped],
        relationships=[],
        unresolved_product_occurrences=[],
        sample_categories=["test"],
    )
    assert operations == again[1]


def test_registry_only_missing_states_and_no_operation_node_or_semantic_hypothesis() -> None:
    api, operations = extract_api_inventory(
        _identity(sources=False),
        None,
        source_path=None,
        source_sha256=None,
        backend_observations=[],
        relationships=[],
        unresolved_product_occurrences=[],
        sample_categories=["registry_only_canonical_api"],
    )
    assert operations == []
    assert api["source_representation_status"] == "REGISTRY_ONLY"
    assert api["parser_coverage_status"] == "REGISTRY_ONLY_NO_ACCEPTED_API_YAML"
    assert {item["field"] for item in api["missing_fields"]} == {
        "api_title",
        "api_description",
        "api_version",
        "protocol",
        "operations",
    }
    serialized = json.dumps(api).casefold()
    assert '"future_hypotheses": []' in serialized
    assert '"architectural_judgments": []' in serialized
    assert "business_capability" not in serialized
    assert "logical_api" not in serialized


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.skipif(
    not PHASE2.is_file(), reason="accepted compact indexes are required"
)
def test_full_representative_sample_determinism_coverage_redaction_and_frozen_integrity(
    tmp_path: Path,
) -> None:
    frozen = [
        ROOT / "indexes/apic_identity_resolution.json",
        ROOT / "indexes/relationship_index.jsonl",
        ROOT / "indexes/backend_target_resolution.jsonl",
        ROOT / "indexes/api_dependency_observations.jsonl",
        ROOT / "indexes/codegraph_nodes.jsonl",
        ROOT / "indexes/codegraph_edges.jsonl",
        ROOT / "indexes/codegraph_adjacency.jsonl",
        ROOT / "indexes/codegraph_dependency_nodes.jsonl",
        ROOT / "indexes/codegraph_dependency_edges.jsonl",
        ROOT / "indexes/codegraph_dependency_adjacency.jsonl",
    ]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen}
    staging_before = _tree_hashes(ROOT / "staging")
    first = write_representative_sample(
        ROOT,
        api_path=tmp_path / "first/apis.jsonl",
        operation_path=tmp_path / "first/operations.jsonl",
    )
    second = write_representative_sample(
        ROOT,
        api_path=tmp_path / "second/apis.jsonl",
        operation_path=tmp_path / "second/operations.jsonl",
    )
    assert first["selection"]["selected_api_count"] == 6
    assert set(first["selection"]["categories"]) == {
        "explicit_multi_operation_rest_api",
        "single_operation_api",
        "missing_or_unresolved_operation_metadata",
        "api_shared_backend_scope",
        "operation_scoped_backend_evidence",
        "as_is_product_and_plan_relationship",
        "registry_only_canonical_api",
        "multiple_backend_targets",
        "unresolved_product_location_occurrence",
    }
    assert first["coverage"]["sample_operation_count"] == 35
    assert first["coverage"]["estate_unresolved_product_location_occurrences_preserved"] == 113
    assert first["coverage"]["unresolved_product_location_occurrences_attached_as_relationships"] == 0
    assert first["coverage"]["semantic_function_inference_performed"] is False
    assert first["coverage"]["logical_api_formation_performed"] is False
    assert first["coverage"]["domain_or_capability_tagging_performed"] is False
    assert first["selection"]["estate_wide_source_scan_performed"] is False
    assert (tmp_path / "first/apis.jsonl").read_bytes() == (
        tmp_path / "second/apis.jsonl"
    ).read_bytes()
    assert (tmp_path / "first/operations.jsonl").read_bytes() == (
        tmp_path / "second/operations.jsonl"
    ).read_bytes()
    payload = (tmp_path / "first/apis.jsonl").read_bytes() + (
        tmp_path / "first/operations.jsonl"
    ).read_bytes()
    sensitive_values = []
    for path in (ROOT / "staging/credentials").glob("*.json"):
        for item in json.loads(path.read_text(encoding="utf-8")).get("results", []):
            for field in ("client_id", "client_secret", "client_secret_hashed"):
                if isinstance(item.get(field), str) and item[field]:
                    sensitive_values.append(item[field].encode())
    assert sensitive_values
    assert all(value not in payload for value in sensitive_values)
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen}
    assert staging_before == _tree_hashes(ROOT / "staging")
    if (TASK014_EVIDENCE / "coverage_and_gaps.json").is_file():
        assert json.loads(
            (TASK014_EVIDENCE / "coverage_and_gaps.json").read_text()
        )["sample_operation_count"] == 35
