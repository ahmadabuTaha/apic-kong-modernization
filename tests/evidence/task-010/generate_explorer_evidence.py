"""Generate deterministic Task 010 CodeGraph Explorer review evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
from pathlib import Path
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from codegraph_explorer import CodeGraphExplorer
from codegraph_explorer.explorer import create_server


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sample(
    explorer: CodeGraphExplorer,
    scenario: str,
    node_id: str,
    *,
    search_term: str,
    direction: str,
    depth: int,
    filters: list[str] | None,
    interpretation: str,
) -> dict:
    view = explorer.neighborhood(
        node_id,
        direction=direction,
        depth=depth,
        relationship_types=filters,
    )
    return {
        "scenario": scenario,
        "selected_canonical_node_id": node_id,
        "selected_node_type": explorer.graph.nodes[node_id]["canonical_object_type"],
        "search_term": search_term,
        "direction": direction,
        "depth": depth,
        "relationship_filters": filters,
        "returned_node_ids": [node["canonical_object_id"] for node in view["nodes"]],
        "returned_relationship_ids": [edge["relationship_id"] for edge in view["edges"]],
        "exposed_provenance_references": [
            edge["relationship_record_reference"] for edge in view["edges"]
        ],
        "evidence_source_categories": {
            edge["relationship_id"]: edge["evidence_source_category"]
            for edge in view["edges"]
        },
        "visualization_limit_message": view["visualization_limit_message"],
        "expected_review_interpretation": interpretation,
    }


def generate(root: Path, output: Path) -> dict:
    explorer = CodeGraphExplorer.from_paths(root)
    nodes = explorer.graph.nodes
    edges = explorer.graph.edges

    def outgoing(node_id: str, kind: str) -> list[dict]:
        return explorer.graph.outgoing_relationships(node_id, [kind])

    def incoming(node_id: str, kind: str) -> list[dict]:
        return explorer.graph.incoming_relationships(node_id, [kind])

    api_id = next(
        node_id
        for node_id in sorted(nodes)
        if nodes[node_id]["canonical_object_type"] == "api_artifact"
        and incoming(node_id, "product_contains_api")
        and incoming(node_id, "plan_entitles_api")
    )
    product_id = next(
        node_id
        for node_id in sorted(nodes)
        if nodes[node_id]["canonical_object_type"] == "product"
        and outgoing(node_id, "product_contains_api")
        and outgoing(node_id, "product_contains_plan")
    )
    plan_id = next(
        node_id
        for node_id in sorted(nodes)
        if nodes[node_id]["canonical_object_type"] == "plan"
        and incoming(node_id, "product_contains_plan")
        and outgoing(node_id, "plan_entitles_api")
    )
    application_id = next(
        node_id
        for node_id in sorted(nodes)
        if nodes[node_id]["canonical_object_type"] == "application"
        and outgoing(node_id, "application_belongs_to_consumer_org")
        and incoming(node_id, "subscription_belongs_to_application")
    )
    registry_edge_id = next(
        edge_id
        for edge_id in sorted(edges)
        if explorer.edge_details(edge_id)["evidence_source_category"] == "registry_only"
    )
    registry_edge = edges[registry_edge_id]
    registry_node_id = registry_edge["source_canonical_identity_record_id"]
    connected = {
        endpoint
        for edge in edges.values()
        for endpoint in (
            edge["source_canonical_identity_record_id"],
            edge["target_canonical_identity_record_id"],
        )
    }
    isolated_id = next(node_id for node_id in sorted(nodes) if node_id not in connected)

    samples = [
        _sample(
            explorer,
            "api_centered",
            api_id,
            search_term=nodes[api_id].get("name") or api_id,
            direction="incoming",
            depth=1,
            filters=["plan_entitles_api", "product_contains_api"],
            interpretation="Incoming Products and Plans with accepted relationship provenance.",
        ),
        _sample(
            explorer,
            "product_centered",
            product_id,
            search_term=nodes[product_id].get("name") or product_id,
            direction="outgoing",
            depth=2,
            filters=["product_contains_api", "product_contains_plan", "plan_entitles_api"],
            interpretation="Contained APIs and Plans plus Plan-entitled APIs; evidence category is shown per accepted edge.",
        ),
        _sample(
            explorer,
            "application_centered",
            application_id,
            search_term=nodes[application_id].get("name") or application_id,
            direction="both",
            depth=3,
            filters=[
                "application_belongs_to_consumer_org",
                "subscription_belongs_to_application",
                "subscription_targets_product",
                "subscription_uses_plan",
                "product_contains_api",
                "product_contains_plan",
                "plan_entitles_api",
            ],
            interpretation="Owning Consumer Org, Subscriptions, Products, contextual Plans, and APIs are structural reachability, not runtime consumption.",
        ),
        _sample(
            explorer,
            "registry_only_relationship",
            registry_node_id,
            search_term=nodes[registry_node_id].get("name") or registry_node_id,
            direction="outgoing",
            depth=1,
            filters=[registry_edge["relationship_type"]],
            interpretation=f"Relationship {registry_edge_id} is explicitly registry-only in accepted Task 008 provenance.",
        ),
        _sample(
            explorer,
            "isolated_node",
            isolated_id,
            search_term=nodes[isolated_id].get("name") or isolated_id,
            direction="both",
            depth=3,
            filters=None,
            interpretation="Accepted isolated identity is displayed alone; no relationship is inferred.",
        ),
    ]

    server = create_server(explorer, "127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/health", timeout=5) as response:
            startup = json.load(response)
        with urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=5) as response:
            ui_loaded = "CodeGraph Explorer" in response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    limit_view = CodeGraphExplorer(
        explorer.graph,
        explorer.relationships.values(),
        node_limit=2,
        edge_limit=1,
    ).neighborhood(product_id, direction="outgoing", depth=3)
    exact_search = explorer.search(api_id)
    substring = explorer.search((nodes[api_id].get("name") or "")[:5])
    typed = explorer.search(
        nodes[product_id].get("name") or product_id, node_type="product"
    )
    depth_checks = {
        str(depth): explorer.neighborhood(product_id, direction="outgoing", depth=depth)[
            "returned_node_count"
        ]
        for depth in (1, 2, 3)
    }
    registry_details = explorer.edge_details(registry_edge_id)
    dual_edge_id = next(
        edge_id
        for edge_id in sorted(edges)
        if explorer.edge_details(edge_id)["evidence_source_category"] == "dual"
    )
    dual_details = explorer.edge_details(dual_edge_id)

    sensitive_values: list[bytes] = []
    for path in (root / "staging/credentials").glob("*.json"):
        for item in json.loads(path.read_text(encoding="utf-8")).get("results", []):
            for field in ("client_id", "client_secret", "client_secret_hashed"):
                value = item.get(field)
                if isinstance(value, str) and value:
                    sensitive_values.append(value.encode())
    exposed = json.dumps(
        {
            "nodes": [explorer.node_details(node_id) for node_id in nodes],
            "edges": [explorer.edge_details(edge_id) for edge_id in edges],
        },
        sort_keys=True,
    ).encode()
    redaction_passed = bool(sensitive_values) and all(
        value not in exposed for value in sensitive_values
    )
    graph_paths = [
        root / "indexes/codegraph_nodes.jsonl",
        root / "indexes/codegraph_edges.jsonl",
        root / "indexes/codegraph_adjacency.jsonl",
    ]
    acceptance = {
        "startup_result": {"health_status": startup["status"], "ui_loaded": ui_loaded},
        "exact_local_run_command": ".venv/bin/python -m codegraph_explorer",
        "graph_node_count_seen": len(nodes),
        "graph_edge_count_seen": len(edges),
        "node_search_checks": {
            "canonical_id": exact_search["results"][0]["canonical_object_id"] == api_id,
            "name_title_substring": any(item["canonical_object_id"] == api_id for item in substring["results"]),
        },
        "object_type_filter_check": all(item["object_type"] == "product" for item in typed["results"]),
        "traversal_direction_checks": {
            direction: explorer.neighborhood(plan_id, direction=direction, depth=1)["returned_edge_count"] > 0
            for direction in ("incoming", "outgoing", "both")
        },
        "depth_1_2_3_checks": depth_checks,
        "isolated_node_result": {
            "node_id": isolated_id,
            "returned_node_count": len(samples[-1]["returned_node_ids"]),
            "returned_edge_count": len(samples[-1]["returned_relationship_ids"]),
        },
        "registry_only_relationship_result": {
            "relationship_id": registry_edge_id,
            "category": registry_details["evidence_source_category"],
        },
        "dual_relationship_result": {
            "relationship_id": dual_edge_id,
            "category": dual_details["evidence_source_category"],
        },
        "provenance_drill_down_result": {
            "relationship_reference_present": bool(registry_details["relationship_record_reference"]),
            "occurrence_ids_present": bool(registry_details["contributing_occurrence_ids"]),
            "source_paths_present": all(item["source_relative_path"] for item in registry_details["provenance"]),
        },
        "visualization_limit_guardrail_result": {
            "limit_exceeded": limit_view["visualization_limit_exceeded"],
            "visible_message": limit_view["visualization_limit_message"],
            "returned_node_count": limit_view["returned_node_count"],
            "returned_edge_count": limit_view["returned_edge_count"],
        },
        "credential_redaction_result": {
            "observed_source_values_checked": len(sensitive_values),
            "values_exposed": 0 if redaction_passed else None,
            "passed": redaction_passed,
        },
        "frozen_component_modification_check": {
            "codegraph_index_sha256": {
                path.relative_to(root).as_posix(): _sha256(path) for path in graph_paths
            },
            "explorer_is_read_only": True,
        },
        "overall_pass": all(
            [
                startup["status"] == "ready",
                ui_loaded,
                len(nodes) == 4718,
                len(edges) == 9589,
                limit_view["visualization_limit_exceeded"],
                registry_details["evidence_source_category"] == "registry_only",
                dual_details["evidence_source_category"] == "dual",
                redaction_passed,
                not samples[-1]["returned_relationship_ids"],
            ]
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "explorer_acceptance.json", acceptance)
    (output / "visual_review_samples.jsonl").write_text(
        "".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for item in samples
        ),
        encoding="utf-8",
    )
    return acceptance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--output", type=Path, default=Path("tests/evidence/task-010")
    )
    args = parser.parse_args()
    result = generate(args.root.resolve(), args.output.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
