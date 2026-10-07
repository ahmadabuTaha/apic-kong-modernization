import hashlib
import json
import threading
from pathlib import Path
from urllib.request import urlopen

import pytest

from codegraph import CodeGraph, build_codegraph
from codegraph_explorer import CodeGraphExplorer
from codegraph_explorer.explorer import create_server


ROOT = Path(__file__).resolve().parents[1]
RELATIONSHIPS = ROOT / "indexes/relationship_index.jsonl"
PHASE2 = ROOT / "indexes/apic_identity_resolution.json"
TASK_010_EVIDENCE = ROOT / "tests/evidence/task-010"


def _identity(identifier: str, kind: str, name: str) -> dict:
    return {
        "canonical_identity_record_id": identifier,
        "canonical_object_type": kind,
        "name": name,
        "title": name.title(),
        "version": "1.0.0" if kind in {"product", "api_artifact"} else None,
        "apic_object_id": f"object-{identifier}",
        "apic_object_url": f"https://example.invalid/{identifier}",
    }


def _relationship(
    identifier: str,
    kind: str,
    source: str,
    source_type: str,
    target: str,
    target_type: str,
    categories: list[str],
) -> dict:
    return {
        "relationship_id": identifier,
        "relationship_type": kind,
        "source_canonical_identity_record_id": source,
        "source_canonical_object_type": source_type,
        "target_canonical_identity_record_id": target,
        "target_canonical_object_type": target_type,
        "evidence_state": "STRUCTURALLY_CONFIRMED",
        "evidence_source_categories": categories,
        "contributing_extracted_record_ids": [f"record-{identifier}"],
        "provenance": [
            {
                "evidence_source_category": category,
                "extracted_record_id": f"record-{identifier}-{category}",
                "source_relative_path": f"staging/{identifier}.json",
                "source_object_pointer": "/results/0",
                "raw_reference": "never-expose-sensitive-value",
                "client_secret": "never-expose-client-secret",
                "phase2_resolution_outcome": "RESOLVED",
            }
            for category in categories
        ],
    }


def _explorer(*, node_limit: int = 80, edge_limit: int = 120) -> CodeGraphExplorer:
    identities = [
        _identity("product", "product", "Alpha Product"),
        _identity("plan", "plan", "Gold Plan"),
        _identity("api", "api_artifact", "Work Permit API"),
        _identity("target", "api_artifact", "Target API"),
        _identity("application", "application", "Reviewer App"),
        _identity("consumer", "consumer_org", "Reviewer Org"),
        _identity("subscription", "subscription", "Reviewer Subscription"),
        _identity("isolated", "catalog_config", "Isolated Catalog"),
    ]
    relationships = [
        _relationship("e-product-plan", "product_contains_plan", "product", "product", "plan", "plan", ["authoritative_artifact", "registry_reference"]),
        _relationship("e-plan-api", "plan_entitles_api", "plan", "plan", "api", "api_artifact", ["registry_reference"]),
        _relationship("e-api-target", "api_invokes_target", "api", "api_artifact", "target", "api_artifact", ["registry_reference"]),
        _relationship("e-app-org", "application_belongs_to_consumer_org", "application", "application", "consumer", "consumer_org", ["registry_reference"]),
        _relationship("e-sub-app", "subscription_belongs_to_application", "subscription", "subscription", "application", "application", ["registry_reference"]),
        _relationship("e-sub-product", "subscription_targets_product", "subscription", "subscription", "product", "product", ["registry_reference"]),
        _relationship("e-sub-plan", "subscription_uses_plan", "subscription", "subscription", "plan", "plan", ["registry_reference"]),
    ]
    built = build_codegraph(
        {"canonical_identity_records": identities, "unresolved_occurrences": []},
        relationships,
    )
    return CodeGraphExplorer(
        CodeGraph(built["nodes"], built["edges"], built["adjacency"]),
        relationships,
        node_limit=node_limit,
        edge_limit=edge_limit,
    )


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_search_by_id_exact_name_substring_and_approved_type_filter() -> None:
    explorer = _explorer()
    assert explorer.search("api")["results"][0]["canonical_object_id"] == "api"
    assert explorer.search("Alpha Product")["results"][0]["canonical_object_id"] == "product"
    assert explorer.search("permit")["results"][0]["canonical_object_id"] == "api"
    assert explorer.search("reviewer", node_type="application")["results"] == [
        {
            "canonical_object_id": "application",
            "object_type": "application",
            "label": "Reviewer App",
            "name": "Reviewer App",
            "title": "Reviewer App",
            "version": None,
        }
    ]
    assert explorer.search("reviewer", node_type="product")["results"] == []
    with pytest.raises(ValueError, match="unsupported node type"):
        explorer.search("x", node_type="unapproved")


def test_direction_filters_depths_and_order_are_deterministic() -> None:
    explorer = _explorer()
    incoming = explorer.neighborhood("api", direction="incoming", depth=1)
    assert [edge["relationship_id"] for edge in incoming["edges"]] == ["e-plan-api"]
    outgoing = explorer.neighborhood("api", direction="outgoing", depth=1)
    assert [edge["relationship_id"] for edge in outgoing["edges"]] == ["e-api-target"]
    both = explorer.neighborhood("api", direction="both", depth=1)
    assert [edge["relationship_id"] for edge in both["edges"]] == ["e-api-target", "e-plan-api"]
    assert explorer.neighborhood("product", direction="outgoing", depth=1)["returned_node_count"] == 2
    assert explorer.neighborhood("product", direction="outgoing", depth=2)["returned_node_count"] == 3
    depth3 = explorer.neighborhood("product", direction="outgoing", depth=3)
    assert depth3["returned_node_count"] == 4
    assert depth3 == explorer.neighborhood("product", direction="outgoing", depth=3)
    filtered = explorer.neighborhood(
        "product",
        direction="outgoing",
        depth=3,
        relationship_types=["product_contains_plan", "plan_entitles_api"],
    )
    assert [edge["relationship_id"] for edge in filtered["edges"]] == ["e-plan-api", "e-product-plan"]


def test_limits_isolated_node_and_provenance_are_safe_and_explicit() -> None:
    explorer = _explorer(node_limit=2, edge_limit=1)
    limited = explorer.neighborhood("product", direction="outgoing", depth=3)
    assert limited["visualization_limit_exceeded"] is True
    assert "reduce depth" in limited["visualization_limit_message"]
    assert limited["returned_node_count"] <= 2
    assert limited["returned_edge_count"] <= 1
    isolated = explorer.neighborhood("isolated", direction="both", depth=3)
    assert isolated["returned_node_count"] == 1
    assert isolated["edges"] == []
    registry = explorer.edge_details("e-plan-api")
    dual = explorer.edge_details("e-product-plan")
    assert registry["evidence_source_category"] == "registry_only"
    assert dual["evidence_source_category"] == "dual"
    assert registry["relationship_record_reference"]["index_path"] == "indexes/relationship_index.jsonl"
    assert registry["contributing_occurrence_ids"] == ["record-e-plan-api"]
    serialized = json.dumps([registry, dual], sort_keys=True)
    assert "never-expose-sensitive-value" not in serialized
    assert "never-expose-client-secret" not in serialized
    assert "raw_reference" not in serialized
    assert "client_secret" not in serialized


def test_local_http_server_starts_and_serves_ui_and_queries() -> None:
    server = create_server(_explorer(), "127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(base + "/health", timeout=5) as response:
            health = json.load(response)
        with urlopen(base + "/", timeout=5) as response:
            html = response.read().decode("utf-8")
        assert health["status"] == "ready"
        assert health["graph_node_count"] == 8
        assert "CodeGraph Explorer" in html
        assert "Structural reachability, not runtime consumption." in html
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.skipif(
    not PHASE2.is_file() or not RELATIONSHIPS.is_file(),
    reason="accepted local graph inputs are required for full-corpus validation",
)
def test_full_corpus_acceptance_redaction_unresolved_exclusion_and_immutability() -> None:
    graph_paths = [
        ROOT / "indexes/codegraph_nodes.jsonl",
        ROOT / "indexes/codegraph_edges.jsonl",
        ROOT / "indexes/codegraph_adjacency.jsonl",
    ]
    before_graph = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in graph_paths}
    before_staging = _tree_hashes(ROOT / "staging")
    explorer = CodeGraphExplorer.from_paths(ROOT)
    assert explorer.metadata()["graph_node_count"] == 4718
    assert explorer.metadata()["graph_edge_count"] == 9589
    relationship_records = [json.loads(line) for line in RELATIONSHIPS.read_text(encoding="utf-8").splitlines()]
    registry_id = next(item["relationship_id"] for item in relationship_records if item["evidence_source_categories"] == ["registry_reference"])
    dual_id = next(item["relationship_id"] for item in relationship_records if set(item["evidence_source_categories"]) == {"authoritative_artifact", "registry_reference"})
    assert explorer.edge_details(registry_id)["evidence_source_category"] == "registry_only"
    assert explorer.edge_details(dual_id)["evidence_source_category"] == "dual"
    unresolved = json.loads(PHASE2.read_text(encoding="utf-8"))["unresolved_occurrences"]
    serialized_ids = json.dumps({"nodes": sorted(explorer.graph.nodes), "edges": sorted(explorer.graph.edges)})
    assert all(item["extracted_record_id"] not in serialized_ids for item in unresolved)

    exposed = json.dumps(
        {
            "nodes": [explorer.node_details(node_id) for node_id in explorer.graph.nodes],
            "edges": [explorer.edge_details(edge_id) for edge_id in explorer.graph.edges],
        },
        sort_keys=True,
    ).encode()
    sensitive_values = []
    for path in (ROOT / "staging/credentials").glob("*.json"):
        for item in json.loads(path.read_text(encoding="utf-8")).get("results", []):
            for field in ("client_id", "client_secret", "client_secret_hashed"):
                if isinstance(item.get(field), str) and item[field]:
                    sensitive_values.append(item[field].encode())
    assert sensitive_values
    assert all(value not in exposed for value in sensitive_values)
    assert before_graph == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in graph_paths}
    assert before_staging == _tree_hashes(ROOT / "staging")
    assert json.loads((TASK_010_EVIDENCE / "explorer_acceptance.json").read_text(encoding="utf-8"))["overall_pass"] is True
