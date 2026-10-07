"""Generate deterministic Task 009 CodeGraph review evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from codegraph import (  # noqa: E402
    ADJACENCY_RELATIVE_PATH,
    EDGES_RELATIVE_PATH,
    NODES_RELATIVE_PATH,
    CodeGraph,
    build_codegraph,
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _compact_sample(
    sample_name: str,
    result: dict[str, Any],
    *,
    path_filter: Callable[[dict[str, Any]], bool] | None = None,
    path_limit: int = 20,
) -> dict[str, Any]:
    paths = result["paths"]
    if path_filter is not None:
        paths = [path for path in paths if path_filter(path)]
    paths = paths[:path_limit]
    node_ids = [result["start_canonical_identity_record_id"]]
    relationship_ids: list[str] = []
    provenance: list[dict[str, str]] = []
    for path in paths:
        for node_id in path["node_ids"]:
            if node_id not in node_ids:
                node_ids.append(node_id)
        for step in path["steps"]:
            relationship_id = step["relationship_id"]
            if relationship_id not in relationship_ids:
                relationship_ids.append(relationship_id)
            pointer = step["provenance_pointer"]
            if pointer not in provenance:
                provenance.append(pointer)
    return {
        "sample_name": sample_name,
        "start_canonical_identity_record_id": result[
            "start_canonical_identity_record_id"
        ],
        "start_canonical_object_type": (
            result["start_node"]["canonical_object_type"]
            if result["start_node"]
            else None
        ),
        "direction": result["direction"],
        "max_depth": result["max_depth"],
        "relationship_types": result["relationship_types"],
        "ordered_node_ids": node_ids,
        "ordered_relationship_ids": relationship_ids,
        "paths": paths,
        "compact_provenance_references": provenance,
        "structural_reachability_only": True,
    }


def _first_node(
    graph: CodeGraph,
    object_type: str,
    predicate: Callable[[str], bool],
) -> str:
    candidates = sorted(
        node_id
        for node_id, node in graph.nodes.items()
        if node["canonical_object_type"] == object_type and predicate(node_id)
    )
    if not candidates:
        raise ValueError(f"no {object_type} node satisfies the sample predicate")
    return candidates[0]


def _fewest_subscription_application(graph: CodeGraph) -> str:
    candidates = []
    for node_id, node in graph.nodes.items():
        if node["canonical_object_type"] != "application":
            continue
        subscriptions = graph.incoming_relationships(
            node_id, ["subscription_belongs_to_application"]
        )
        consumer = graph.outgoing_relationships(
            node_id, ["application_belongs_to_consumer_org"]
        )
        if subscriptions and consumer:
            candidates.append((len(subscriptions), node_id))
    if not candidates:
        raise ValueError("no connected application is available for traversal samples")
    return min(candidates)[1]


def generate(
    phase2_path: Path,
    relationship_path: Path,
    graph_root: Path,
    output_directory: Path,
) -> dict[str, Any]:
    phase2 = json.loads(phase2_path.read_text(encoding="utf-8"))
    relationships = _load_jsonl(relationship_path)
    expected = build_codegraph(phase2, relationships)
    graph = CodeGraph.from_directory(graph_root)

    graph_paths = {
        "nodes": graph_root / NODES_RELATIVE_PATH,
        "edges": graph_root / EDGES_RELATIVE_PATH,
        "adjacency": graph_root / ADJACENCY_RELATIVE_PATH,
    }
    counts = dict(expected["counts"])
    counts["deterministic_graph_build_sha256"] = {
        key: _sha256(path) for key, path in graph_paths.items()
    }

    api_id = _first_node(
        graph,
        "api_artifact",
        lambda node_id: bool(
            graph.incoming_relationships(node_id, ["product_contains_api"])
        )
        and bool(graph.incoming_relationships(node_id, ["plan_entitles_api"])),
    )
    product_id = _first_node(
        graph,
        "product",
        lambda node_id: bool(
            graph.outgoing_relationships(node_id, ["product_contains_plan"])
        )
        and bool(graph.outgoing_relationships(node_id, ["product_contains_api"])),
    )
    application_id = _fewest_subscription_application(graph)
    isolated_id = _first_node(
        graph,
        "consumer_org",
        lambda node_id: not graph.incoming_relationships(node_id)
        and not graph.outgoing_relationships(node_id),
    )
    registry_only_relationship = next(
        relationship
        for relationship in relationships
        if relationship["relationship_type"] == "product_contains_api"
        and relationship["evidence_source_categories"] == ["registry_reference"]
    )

    samples = [
        _compact_sample(
            "api_incoming_products",
            graph.traverse(
                api_id,
                max_depth=1,
                direction="incoming",
                relationship_types=["product_contains_api"],
                max_paths=50,
            ),
        ),
        _compact_sample(
            "api_incoming_entitling_plans",
            graph.traverse(
                api_id,
                max_depth=1,
                direction="incoming",
                relationship_types=["plan_entitles_api"],
                max_paths=50,
            ),
        ),
        _compact_sample(
            "product_plans_and_entitled_apis",
            graph.traverse(
                product_id,
                max_depth=2,
                direction="outgoing",
                relationship_types=[
                    "product_contains_plan",
                    "plan_entitles_api",
                ],
                max_paths=100,
            ),
        ),
        _compact_sample(
            "application_consumer_organization",
            graph.traverse(
                application_id,
                max_depth=1,
                direction="outgoing",
                relationship_types=["application_belongs_to_consumer_org"],
            ),
        ),
        _compact_sample(
            "application_subscriptions_and_products",
            graph.traverse(
                application_id,
                max_depth=2,
                direction="both",
                relationship_types=[
                    "subscription_belongs_to_application",
                    "subscription_targets_product",
                ],
                max_paths=100,
            ),
        ),
        _compact_sample(
            "application_subscription_product_plan_api_reachability",
            graph.traverse(
                application_id,
                max_depth=3,
                direction="both",
                relationship_types=[
                    "subscription_belongs_to_application",
                    "subscription_targets_product",
                    "subscription_uses_plan",
                    "product_contains_api",
                    "plan_entitles_api",
                ],
                max_paths=500,
            ),
            path_filter=lambda path: path["depth"] == 3
            and graph.nodes[path["end_node_id"]]["canonical_object_type"]
            == "api_artifact",
            path_limit=20,
        ),
        _compact_sample(
            "registry_only_product_api_relationship",
            graph.traverse(
                registry_only_relationship[
                    "source_canonical_identity_record_id"
                ],
                max_depth=1,
                direction="outgoing",
                relationship_types=["product_contains_api"],
                max_paths=100,
            ),
            path_filter=lambda path: registry_only_relationship["relationship_id"]
            in path["relationship_ids"],
            path_limit=1,
        ),
        _compact_sample(
            "isolated_node",
            graph.traverse(isolated_id, max_depth=3, direction="both"),
        ),
    ]

    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "codegraph_integrity.json").write_text(
        json.dumps(expected["integrity"], ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (output_directory / "codegraph_counts.json").write_text(
        json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_directory / "traversal_samples.jsonl").write_text(
        "".join(
            json.dumps(sample, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for sample in samples
        ),
        encoding="utf-8",
    )
    return {
        "integrity": expected["integrity"],
        "counts": counts,
        "traversal_sample_count": len(samples),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase2",
        type=Path,
        default=Path("indexes/apic_identity_resolution.json"),
    )
    parser.add_argument(
        "--relationships",
        type=Path,
        default=Path("indexes/relationship_index.jsonl"),
    )
    parser.add_argument("--graph-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-directory", type=Path, default=Path("tests/evidence/task-009")
    )
    args = parser.parse_args()
    result = generate(
        args.phase2, args.relationships, args.graph_root, args.output_directory
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
