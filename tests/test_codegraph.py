import hashlib
import json
from pathlib import Path

import pytest

from codegraph import (
    ADJACENCY_RELATIVE_PATH,
    EDGES_RELATIVE_PATH,
    NODES_RELATIVE_PATH,
    CodeGraph,
    build_codegraph,
    write_codegraph,
)


ROOT = Path(__file__).resolve().parents[1]
PHASE2 = ROOT / "indexes/apic_identity_resolution.json"
RELATIONSHIPS = ROOT / "indexes/relationship_index.jsonl"
TASK_009_EVIDENCE = ROOT / "tests/evidence/task-009"


def _identity(identity_id: str, object_type: str, **extra: object) -> dict:
    value = {
        "canonical_identity_record_id": identity_id,
        "canonical_object_type": object_type,
        "name": identity_id,
        "title": identity_id.title(),
        "version": None,
        "apic_object_id": None,
        "apic_object_url": None,
    }
    value.update(extra)
    return value


def _relationship(
    relationship_id: str,
    relationship_type: str,
    source_id: str,
    source_type: str,
    target_id: str,
    target_type: str,
) -> dict:
    return {
        "relationship_id": relationship_id,
        "relationship_type": relationship_type,
        "source_canonical_identity_record_id": source_id,
        "source_canonical_object_type": source_type,
        "target_canonical_identity_record_id": target_id,
        "target_canonical_object_type": target_type,
        "evidence_state": "STRUCTURALLY_CONFIRMED",
    }


def _synthetic_inputs() -> tuple[dict, list[dict]]:
    identities = [
        _identity("product", "product"),
        _identity("plan", "plan"),
        _identity("api-a", "api_artifact"),
        _identity("api-b", "api_artifact"),
        _identity("isolated", "catalog_config"),
        _identity(
            "credential",
            "credential",
            unknown_sensitive_payload="must-not-be-copied",
        ),
    ]
    relationships = [
        _relationship(
            "edge-product-api",
            "product_contains_api",
            "product",
            "product",
            "api-a",
            "api_artifact",
        ),
        _relationship(
            "edge-product-plan",
            "product_contains_plan",
            "product",
            "product",
            "plan",
            "plan",
        ),
        _relationship(
            "edge-plan-api",
            "plan_entitles_api",
            "plan",
            "plan",
            "api-b",
            "api_artifact",
        ),
        _relationship(
            "edge-api-a-b",
            "api_invokes_target",
            "api-a",
            "api_artifact",
            "api-b",
            "api_artifact",
        ),
        _relationship(
            "edge-api-b-a",
            "api_invokes_target",
            "api-b",
            "api_artifact",
            "api-a",
            "api_artifact",
        ),
    ]
    phase2 = {
        "canonical_identity_records": identities,
        "unresolved_occurrences": [
            {
                "extracted_record_id": "unresolved-copy",
                "outcome": "UNRESOLVED",
            }
        ],
    }
    return phase2, relationships


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_build_preserves_each_accepted_node_and_edge_without_inference() -> None:
    phase2, relationships = _synthetic_inputs()
    result = build_codegraph(phase2, relationships)

    assert len(result["nodes"]) == len({node["graph_node_id"] for node in result["nodes"]}) == 6
    assert len(result["edges"]) == len({edge["graph_edge_id"] for edge in result["edges"]}) == 5
    assert result["integrity"]["overall_integrity_passed"] is True
    assert result["integrity"]["graph_only_inferred_edge_count"] == 0
    assert result["integrity"]["task_007_unresolved_occurrence_promotion_count"] == 0
    assert result["counts"]["isolated_node_count"] == 2
    assert not any(
        edge["source_canonical_identity_record_id"] == "product"
        and edge["target_canonical_identity_record_id"] == "api-b"
        for edge in result["edges"]
    )
    serialized = json.dumps(result, sort_keys=True)
    assert "must-not-be-copied" not in serialized


def test_adjacency_filters_bounded_paths_cycles_isolates_and_missing_nodes() -> None:
    phase2, relationships = _synthetic_inputs()
    result = build_codegraph(phase2, relationships)
    graph = CodeGraph(result["nodes"], result["edges"], result["adjacency"])

    assert graph.get_node("product")["canonical_object_type"] == "product"
    assert graph.get_node("missing") is None
    assert graph.outgoing_relationships("missing") == []
    assert graph.incoming_relationships("missing") == []
    assert graph.neighbors("missing") == []

    assert [
        edge["accepted_relationship_id"]
        for edge in graph.outgoing_relationships("product")
    ] == ["edge-product-api", "edge-product-plan"]
    assert [
        edge["accepted_relationship_id"]
        for edge in graph.outgoing_relationships(
            "product", ["product_contains_plan"]
        )
    ] == ["edge-product-plan"]
    assert [
        edge["accepted_relationship_id"]
        for edge in graph.incoming_relationships("api-b")
    ] == ["edge-api-a-b", "edge-plan-api"]

    traversal = graph.traverse(
        "product",
        max_depth=2,
        direction="outgoing",
        relationship_types=["product_contains_plan", "plan_entitles_api"],
    )
    assert [path["node_ids"] for path in traversal["paths"]] == [
        ["product", "plan"],
        ["product", "plan", "api-b"],
    ]
    assert traversal["paths"][1]["relationship_ids"] == [
        "edge-product-plan",
        "edge-plan-api",
    ]

    cycle = graph.traverse(
        "api-a",
        max_depth=8,
        direction="outgoing",
        relationship_types=["api_invokes_target"],
    )
    assert [path["node_ids"] for path in cycle["paths"]] == [
        ["api-a", "api-b"]
    ]
    assert graph.traverse("isolated", max_depth=8, direction="both")["paths"] == []
    missing = graph.traverse("missing", max_depth=2)
    assert missing["missing_start_node"] is True
    assert missing["paths"] == []
    with pytest.raises(ValueError, match="max_depth"):
        graph.traverse("product", max_depth=9)


def test_missing_relationship_endpoint_fails_without_fabrication() -> None:
    phase2, relationships = _synthetic_inputs()
    relationships.append(
        _relationship(
            "missing-edge",
            "product_contains_api",
            "product",
            "product",
            "not-a-node",
            "api_artifact",
        )
    )
    with pytest.raises(ValueError, match="missing relationship endpoints"):
        build_codegraph(phase2, relationships)


@pytest.mark.skipif(
    not PHASE2.is_file() or not RELATIONSHIPS.is_file(),
    reason="local ignored Phase 2/Task 008 indexes are required for full-corpus validation",
)
def test_full_corpus_graph_is_deterministic_complete_redacted_and_source_safe(
    tmp_path: Path,
) -> None:
    staging = ROOT / "staging"
    before = _tree_hashes(staging)
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = write_codegraph(PHASE2, RELATIONSHIPS, first_root)
    second = write_codegraph(PHASE2, RELATIONSHIPS, second_root)

    assert first == second
    for relative_path in (
        NODES_RELATIVE_PATH,
        EDGES_RELATIVE_PATH,
        ADJACENCY_RELATIVE_PATH,
    ):
        assert (first_root / relative_path).read_bytes() == (
            second_root / relative_path
        ).read_bytes()
    assert first["integrity"]["overall_integrity_passed"] is True
    assert first["integrity"]["actual_graph_node_count"] == 4718
    assert first["integrity"]["actual_graph_edge_count"] == 9589
    assert first["integrity"]["graph_only_inferred_edge_count"] == 0
    assert first["integrity"]["task_007_unresolved_occurrence_promotion_count"] == 0
    assert first["counts"]["connected_node_count"] == 4697
    assert first["counts"]["isolated_node_count"] == 21
    assert _tree_hashes(staging) == before

    committed_integrity = json.loads(
        (TASK_009_EVIDENCE / "codegraph_integrity.json").read_text(
            encoding="utf-8"
        )
    )
    committed_counts = json.loads(
        (TASK_009_EVIDENCE / "codegraph_counts.json").read_text(encoding="utf-8")
    )
    assert committed_integrity == first["integrity"]
    assert committed_counts == first["counts"]

    graph = CodeGraph.from_directory(first_root)
    assert len(graph.nodes) == 4718
    assert len(graph.edges) == 9589
    assert sum(len(graph.outgoing_relationships(node_id)) for node_id in graph.nodes) == 9589
    assert sum(len(graph.incoming_relationships(node_id)) for node_id in graph.nodes) == 9589

    phase2 = json.loads(PHASE2.read_text(encoding="utf-8"))
    graph_bytes = b"".join(
        (first_root / path).read_bytes()
        for path in (
            NODES_RELATIVE_PATH,
            EDGES_RELATIVE_PATH,
            ADJACENCY_RELATIVE_PATH,
        )
    )
    assert all(
        occurrence["extracted_record_id"].encode() not in graph_bytes
        for occurrence in phase2["unresolved_occurrences"]
    )

    evidence_bytes = graph_bytes + b"".join(
        path.read_bytes()
        for path in (
            TASK_009_EVIDENCE / "codegraph_integrity.json",
            TASK_009_EVIDENCE / "codegraph_counts.json",
            TASK_009_EVIDENCE / "traversal_samples.jsonl",
        )
    )
    sensitive_values: list[bytes] = []
    for path in (staging / "credentials").glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("results", []):
            for field in ("client_id", "client_secret", "client_secret_hashed"):
                value = item.get(field)
                if isinstance(value, str) and value:
                    sensitive_values.append(value.encode())
    assert sensitive_values
    assert all(value not in evidence_bytes for value in sensitive_values)
