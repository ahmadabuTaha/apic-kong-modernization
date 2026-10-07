"""Compact deterministic CodeGraph construction, adjacency, and traversal."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from relationship_builder import APPROVED_RELATIONSHIP_TYPES


NODES_RELATIVE_PATH = Path("indexes/codegraph_nodes.jsonl")
EDGES_RELATIVE_PATH = Path("indexes/codegraph_edges.jsonl")
ADJACENCY_RELATIVE_PATH = Path("indexes/codegraph_adjacency.jsonl")

APPROVED_NODE_TYPES = (
    "api_artifact",
    "product",
    "plan",
    "consumer_org",
    "application",
    "credential",
    "subscription",
    "catalog_config",
    "catalog_property",
)

DEFAULT_MAX_DEPTH = 3
MAX_TRAVERSAL_DEPTH = 8
DEFAULT_MAX_PATHS = 1000
MAX_TRAVERSAL_PATHS = 10000


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _node(identity: dict[str, Any]) -> dict[str, Any]:
    canonical_id = identity["canonical_identity_record_id"]
    return {
        "graph_node_id": canonical_id,
        "canonical_identity_record_id": canonical_id,
        "canonical_object_type": identity["canonical_object_type"],
        "name": identity.get("name"),
        "title": identity.get("title"),
        "version": identity.get("version"),
        "apic_object_id": identity.get("apic_object_id"),
        "apic_object_url": identity.get("apic_object_url"),
        "phase2_identity_pointer": {
            "index_path": "indexes/apic_identity_resolution.json",
            "canonical_identity_record_id": canonical_id,
        },
    }


def _edge(relationship: dict[str, Any]) -> dict[str, Any]:
    relationship_id = relationship["relationship_id"]
    return {
        "graph_edge_id": relationship_id,
        "accepted_relationship_id": relationship_id,
        "relationship_type": relationship["relationship_type"],
        "source_canonical_identity_record_id": relationship[
            "source_canonical_identity_record_id"
        ],
        "source_canonical_object_type": relationship[
            "source_canonical_object_type"
        ],
        "target_canonical_identity_record_id": relationship[
            "target_canonical_identity_record_id"
        ],
        "target_canonical_object_type": relationship[
            "target_canonical_object_type"
        ],
        "evidence_state": relationship["evidence_state"],
        "task008_relationship_pointer": {
            "index_path": "indexes/relationship_index.jsonl",
            "relationship_id": relationship_id,
        },
    }


def _edge_sort_key(edge: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        edge["relationship_type"],
        edge["source_canonical_identity_record_id"],
        edge["target_canonical_identity_record_id"],
        edge["accepted_relationship_id"],
    )


def build_codegraph(
    phase2: dict[str, Any],
    relationships: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build minimal nodes, accepted edges, adjacency, and integrity evidence."""

    identities = phase2["canonical_identity_records"]
    canonical_ids = [
        identity["canonical_identity_record_id"] for identity in identities
    ]
    duplicate_node_ids = sorted(
        value for value, count in Counter(canonical_ids).items() if count > 1
    )
    unsupported_node_types = sorted(
        {
            identity["canonical_object_type"]
            for identity in identities
            if identity["canonical_object_type"] not in APPROVED_NODE_TYPES
        }
    )
    if duplicate_node_ids:
        raise ValueError(f"duplicate canonical node IDs: {duplicate_node_ids}")
    if unsupported_node_types:
        raise ValueError(f"unsupported canonical node types: {unsupported_node_types}")

    nodes = sorted((_node(identity) for identity in identities), key=lambda item: item["graph_node_id"])
    node_ids = {node["graph_node_id"] for node in nodes}

    relationship_ids = [relationship["relationship_id"] for relationship in relationships]
    duplicate_edge_ids = sorted(
        value for value, count in Counter(relationship_ids).items() if count > 1
    )
    unsupported_relationship_types = sorted(
        {
            relationship["relationship_type"]
            for relationship in relationships
            if relationship["relationship_type"] not in APPROVED_RELATIONSHIP_TYPES
        }
    )
    missing_endpoints = sorted(
        {
            endpoint
            for relationship in relationships
            for endpoint in (
                relationship["source_canonical_identity_record_id"],
                relationship["target_canonical_identity_record_id"],
            )
            if endpoint not in node_ids
        }
    )
    if duplicate_edge_ids:
        raise ValueError(f"duplicate accepted relationship IDs: {duplicate_edge_ids}")
    if unsupported_relationship_types:
        raise ValueError(
            f"unsupported relationship types: {unsupported_relationship_types}"
        )
    if missing_endpoints:
        raise ValueError(f"missing relationship endpoints: {missing_endpoints}")

    edges = sorted((_edge(relationship) for relationship in relationships), key=_edge_sort_key)
    outgoing: dict[str, list[dict[str, Any]]] = {node_id: [] for node_id in node_ids}
    incoming: dict[str, list[dict[str, Any]]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        outgoing[edge["source_canonical_identity_record_id"]].append(edge)
        incoming[edge["target_canonical_identity_record_id"]].append(edge)
    adjacency = []
    for node_id in sorted(node_ids):
        outgoing_edges = sorted(outgoing[node_id], key=_edge_sort_key)
        incoming_edges = sorted(incoming[node_id], key=_edge_sort_key)
        adjacency.append(
            {
                "canonical_identity_record_id": node_id,
                "outgoing_relationship_ids": [
                    edge["accepted_relationship_id"] for edge in outgoing_edges
                ],
                "incoming_relationship_ids": [
                    edge["accepted_relationship_id"] for edge in incoming_edges
                ],
            }
        )

    connected_node_ids = {
        endpoint
        for edge in edges
        for endpoint in (
            edge["source_canonical_identity_record_id"],
            edge["target_canonical_identity_record_id"],
        )
    }
    accepted_edge_keys = {
        (
            relationship["relationship_id"],
            relationship["relationship_type"],
            relationship["source_canonical_identity_record_id"],
            relationship["target_canonical_identity_record_id"],
        )
        for relationship in relationships
    }
    graph_edge_keys = {
        (
            edge["accepted_relationship_id"],
            edge["relationship_type"],
            edge["source_canonical_identity_record_id"],
            edge["target_canonical_identity_record_id"],
        )
        for edge in edges
    }
    unresolved_ids = {
        occurrence["extracted_record_id"]
        for occurrence in phase2.get("unresolved_occurrences", [])
    }
    graph_identifiers = (
        node_ids
        | {edge["accepted_relationship_id"] for edge in edges}
        | {
            endpoint
            for edge in edges
            for endpoint in (
                edge["source_canonical_identity_record_id"],
                edge["target_canonical_identity_record_id"],
            )
        }
    )
    integrity = {
        "expected_canonical_node_count": len(identities),
        "actual_graph_node_count": len(nodes),
        "unique_canonical_node_id_count": len(node_ids),
        "expected_accepted_relationship_count": len(relationships),
        "actual_graph_edge_count": len(edges),
        "unique_relationship_id_count": len(
            {edge["accepted_relationship_id"] for edge in edges}
        ),
        "missing_relationship_endpoints": missing_endpoints,
        "orphan_edge_count": 0,
        "duplicate_node_ids": duplicate_node_ids,
        "duplicate_edge_ids": duplicate_edge_ids,
        "unsupported_node_types": unsupported_node_types,
        "unsupported_relationship_types": unsupported_relationship_types,
        "connected_node_count": len(connected_node_ids),
        "isolated_node_count": len(node_ids - connected_node_ids),
        "task_007_unresolved_occurrence_count": len(unresolved_ids),
        "task_007_unresolved_occurrence_promotion_count": len(
            unresolved_ids & graph_identifiers
        ),
        "graph_only_inferred_edge_count": len(graph_edge_keys - accepted_edge_keys),
        "accepted_relationships_missing_from_graph_count": len(
            accepted_edge_keys - graph_edge_keys
        ),
    }
    integrity["overall_integrity_passed"] = all(
        (
            integrity["expected_canonical_node_count"]
            == integrity["actual_graph_node_count"]
            == integrity["unique_canonical_node_id_count"],
            integrity["expected_accepted_relationship_count"]
            == integrity["actual_graph_edge_count"]
            == integrity["unique_relationship_id_count"],
            not integrity["missing_relationship_endpoints"],
            integrity["orphan_edge_count"] == 0,
            not integrity["duplicate_node_ids"],
            not integrity["duplicate_edge_ids"],
            not integrity["unsupported_node_types"],
            not integrity["unsupported_relationship_types"],
            integrity["task_007_unresolved_occurrence_promotion_count"] == 0,
            integrity["graph_only_inferred_edge_count"] == 0,
            integrity["accepted_relationships_missing_from_graph_count"] == 0,
        )
    )
    counts = {
        "total_graph_nodes": len(nodes),
        "nodes_by_approved_object_type": {
            object_type: sum(
                node["canonical_object_type"] == object_type for node in nodes
            )
            for object_type in APPROVED_NODE_TYPES
        },
        "total_graph_edges": len(edges),
        "edges_by_approved_relationship_type": {
            relationship_type: sum(
                edge["relationship_type"] == relationship_type for edge in edges
            )
            for relationship_type in APPROVED_RELATIONSHIP_TYPES
        },
        "total_outgoing_adjacency_references": sum(
            len(item["outgoing_relationship_ids"]) for item in adjacency
        ),
        "total_incoming_adjacency_references": sum(
            len(item["incoming_relationship_ids"]) for item in adjacency
        ),
        "connected_node_count": len(connected_node_ids),
        "isolated_node_count": len(node_ids - connected_node_ids),
    }
    return {
        "nodes": nodes,
        "edges": edges,
        "adjacency": adjacency,
        "integrity": integrity,
        "counts": counts,
    }


class CodeGraph:
    """In-memory query view loaded only from compact CodeGraph indexes."""

    def __init__(
        self,
        nodes: Iterable[dict[str, Any]],
        edges: Iterable[dict[str, Any]],
        adjacency: Iterable[dict[str, Any]] | None = None,
    ) -> None:
        node_values = list(nodes)
        edge_values = list(edges)
        self.nodes = {node["graph_node_id"]: node for node in node_values}
        self.edges = {
            edge["accepted_relationship_id"]: edge for edge in edge_values
        }
        if len(self.nodes) != len(node_values):
            raise ValueError("duplicate graph node ID")
        if len(self.edges) != len(edge_values):
            raise ValueError("duplicate graph edge ID")
        self._outgoing: dict[str, list[str]] = {
            node_id: [] for node_id in self.nodes
        }
        self._incoming: dict[str, list[str]] = {
            node_id: [] for node_id in self.nodes
        }
        if adjacency is None:
            for edge in edge_values:
                source = edge["source_canonical_identity_record_id"]
                target = edge["target_canonical_identity_record_id"]
                if source not in self.nodes or target not in self.nodes:
                    raise ValueError("graph edge references a missing node")
                self._outgoing[source].append(edge["accepted_relationship_id"])
                self._incoming[target].append(edge["accepted_relationship_id"])
            for node_id in self.nodes:
                self._outgoing[node_id].sort(
                    key=lambda edge_id: _edge_sort_key(self.edges[edge_id])
                )
                self._incoming[node_id].sort(
                    key=lambda edge_id: _edge_sort_key(self.edges[edge_id])
                )
        else:
            adjacency_values = list(adjacency)
            if len(adjacency_values) != len(self.nodes):
                raise ValueError("adjacency does not contain exactly one row per node")
            seen_node_ids: set[str] = set()
            seen_outgoing: list[str] = []
            seen_incoming: list[str] = []
            for item in adjacency_values:
                node_id = item["canonical_identity_record_id"]
                if node_id not in self.nodes:
                    raise ValueError("adjacency references a missing node")
                if node_id in seen_node_ids:
                    raise ValueError("duplicate adjacency node ID")
                seen_node_ids.add(node_id)
                self._outgoing[node_id] = list(item["outgoing_relationship_ids"])
                self._incoming[node_id] = list(item["incoming_relationship_ids"])
                for edge_id in self._outgoing[node_id]:
                    edge = self.edges.get(edge_id)
                    if edge is None or edge["source_canonical_identity_record_id"] != node_id:
                        raise ValueError("invalid outgoing adjacency relationship")
                    seen_outgoing.append(edge_id)
                for edge_id in self._incoming[node_id]:
                    edge = self.edges.get(edge_id)
                    if edge is None or edge["target_canonical_identity_record_id"] != node_id:
                        raise ValueError("invalid incoming adjacency relationship")
                    seen_incoming.append(edge_id)
            expected_edge_ids = sorted(self.edges)
            if sorted(seen_outgoing) != expected_edge_ids:
                raise ValueError("outgoing adjacency does not cover every edge exactly once")
            if sorted(seen_incoming) != expected_edge_ids:
                raise ValueError("incoming adjacency does not cover every edge exactly once")

    @classmethod
    def from_directory(cls, graph_root: Path) -> "CodeGraph":
        return cls(
            _load_jsonl(graph_root / NODES_RELATIVE_PATH),
            _load_jsonl(graph_root / EDGES_RELATIVE_PATH),
            _load_jsonl(graph_root / ADJACENCY_RELATIVE_PATH),
        )

    def get_node(self, canonical_id: str) -> dict[str, Any] | None:
        return self.nodes.get(canonical_id)

    @staticmethod
    def _type_filter(
        relationship_types: Iterable[str] | None,
    ) -> set[str] | None:
        if relationship_types is None:
            return None
        values = set(relationship_types)
        unsupported = values - set(APPROVED_RELATIONSHIP_TYPES)
        if unsupported:
            raise ValueError(f"unsupported relationship types: {sorted(unsupported)}")
        return values

    def outgoing_relationships(
        self,
        canonical_id: str,
        relationship_types: Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        allowed = self._type_filter(relationship_types)
        return [
            self.edges[edge_id]
            for edge_id in self._outgoing.get(canonical_id, [])
            if allowed is None or self.edges[edge_id]["relationship_type"] in allowed
        ]

    def incoming_relationships(
        self,
        canonical_id: str,
        relationship_types: Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        allowed = self._type_filter(relationship_types)
        return [
            self.edges[edge_id]
            for edge_id in self._incoming.get(canonical_id, [])
            if allowed is None or self.edges[edge_id]["relationship_type"] in allowed
        ]

    def neighbors(
        self,
        canonical_id: str,
        *,
        direction: str = "outgoing",
        relationship_types: Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        if canonical_id not in self.nodes:
            return []
        if direction not in {"outgoing", "incoming", "both"}:
            raise ValueError("direction must be outgoing, incoming, or both")
        result = []
        if direction in {"outgoing", "both"}:
            for edge in self.outgoing_relationships(
                canonical_id, relationship_types
            ):
                target_id = edge["target_canonical_identity_record_id"]
                result.append(
                    {
                        "traversal_direction": "outgoing",
                        "relationship": edge,
                        "neighbor_node": self.nodes[target_id],
                    }
                )
        if direction in {"incoming", "both"}:
            for edge in self.incoming_relationships(
                canonical_id, relationship_types
            ):
                source_id = edge["source_canonical_identity_record_id"]
                result.append(
                    {
                        "traversal_direction": "incoming",
                        "relationship": edge,
                        "neighbor_node": self.nodes[source_id],
                    }
                )
        result.sort(
            key=lambda item: (
                item["relationship"]["relationship_type"],
                item["neighbor_node"]["graph_node_id"],
                item["relationship"]["accepted_relationship_id"],
                item["traversal_direction"],
            )
        )
        return result

    def traverse(
        self,
        start_canonical_id: str,
        *,
        max_depth: int = DEFAULT_MAX_DEPTH,
        direction: str = "outgoing",
        relationship_types: Iterable[str] | None = None,
        max_paths: int = DEFAULT_MAX_PATHS,
    ) -> dict[str, Any]:
        if max_depth < 0 or max_depth > MAX_TRAVERSAL_DEPTH:
            raise ValueError(
                f"max_depth must be between 0 and {MAX_TRAVERSAL_DEPTH}"
            )
        if max_paths < 1 or max_paths > MAX_TRAVERSAL_PATHS:
            raise ValueError(
                f"max_paths must be between 1 and {MAX_TRAVERSAL_PATHS}"
            )
        allowed = self._type_filter(relationship_types)
        if direction not in {"outgoing", "incoming", "both"}:
            raise ValueError("direction must be outgoing, incoming, or both")
        start_node = self.get_node(start_canonical_id)
        if start_node is None:
            return {
                "start_canonical_identity_record_id": start_canonical_id,
                "start_node": None,
                "missing_start_node": True,
                "direction": direction,
                "max_depth": max_depth,
                "relationship_types": sorted(allowed) if allowed is not None else None,
                "paths": [],
                "truncated": False,
            }

        frontier = [
            {
                "node_ids": [start_canonical_id],
                "relationship_ids": [],
                "steps": [],
            }
        ]
        paths = []
        truncated = False
        for _ in range(max_depth):
            next_frontier = []
            for path in frontier:
                current_id = path["node_ids"][-1]
                for neighbor in self.neighbors(
                    current_id,
                    direction=direction,
                    relationship_types=allowed,
                ):
                    neighbor_id = neighbor["neighbor_node"]["graph_node_id"]
                    if neighbor_id in path["node_ids"]:
                        continue
                    edge = neighbor["relationship"]
                    next_path = {
                        "depth": len(path["relationship_ids"]) + 1,
                        "start_node_id": start_canonical_id,
                        "end_node_id": neighbor_id,
                        "node_ids": path["node_ids"] + [neighbor_id],
                        "relationship_ids": path["relationship_ids"]
                        + [edge["accepted_relationship_id"]],
                        "steps": path["steps"]
                        + [
                            {
                                "from_node_id": current_id,
                                "relationship_id": edge[
                                    "accepted_relationship_id"
                                ],
                                "relationship_type": edge[
                                    "relationship_type"
                                ],
                                "to_node_id": neighbor_id,
                                "traversal_direction": neighbor[
                                    "traversal_direction"
                                ],
                                "provenance_pointer": edge[
                                    "task008_relationship_pointer"
                                ],
                            }
                        ],
                    }
                    next_frontier.append(next_path)
            next_frontier.sort(
                key=lambda item: (
                    item["node_ids"],
                    item["relationship_ids"],
                    [step["traversal_direction"] for step in item["steps"]],
                )
            )
            remaining = max_paths - len(paths)
            if len(next_frontier) > remaining:
                next_frontier = next_frontier[:remaining]
                truncated = True
            paths.extend(next_frontier)
            frontier = next_frontier
            if not frontier or len(paths) >= max_paths:
                if frontier and len(paths) >= max_paths:
                    truncated = True
                break
        return {
            "start_canonical_identity_record_id": start_canonical_id,
            "start_node": start_node,
            "missing_start_node": False,
            "direction": direction,
            "max_depth": max_depth,
            "relationship_types": sorted(allowed) if allowed is not None else None,
            "paths": paths,
            "truncated": truncated,
        }


def write_codegraph(
    phase2_path: Path,
    relationship_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    phase2 = json.loads(phase2_path.read_text(encoding="utf-8"))
    result = build_codegraph(phase2, _load_jsonl(relationship_path))
    paths = {
        "nodes": output_root / NODES_RELATIVE_PATH,
        "edges": output_root / EDGES_RELATIVE_PATH,
        "adjacency": output_root / ADJACENCY_RELATIVE_PATH,
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    for key in ("nodes", "edges", "adjacency"):
        paths[key].write_text(
            "".join(
                json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n"
                for item in result[key]
            ),
            encoding="utf-8",
        )
    hashes = {key: _sha256(path) for key, path in paths.items()}
    counts = dict(result["counts"])
    counts["deterministic_graph_build_sha256"] = hashes
    return {"integrity": result["integrity"], "counts": counts}


def _json_output(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument(
        "--phase2",
        type=Path,
        default=Path("indexes/apic_identity_resolution.json"),
    )
    build_parser.add_argument(
        "--relationships",
        type=Path,
        default=Path("indexes/relationship_index.jsonl"),
    )
    build_parser.add_argument("--output-root", type=Path, default=Path("."))

    for name in ("node", "neighbors", "traverse"):
        query_parser = subparsers.add_parser(name)
        query_parser.add_argument("canonical_id")
        query_parser.add_argument("--graph-root", type=Path, default=Path("."))
        if name in {"neighbors", "traverse"}:
            query_parser.add_argument(
                "--direction",
                choices=("outgoing", "incoming", "both"),
                default="outgoing",
            )
            query_parser.add_argument(
                "--relationship-type",
                action="append",
                choices=APPROVED_RELATIONSHIP_TYPES,
            )
        if name == "traverse":
            query_parser.add_argument(
                "--max-depth", type=int, default=DEFAULT_MAX_DEPTH
            )
            query_parser.add_argument(
                "--max-paths", type=int, default=DEFAULT_MAX_PATHS
            )

    args = parser.parse_args(argv)
    if args.command == "build":
        _json_output(
            write_codegraph(args.phase2, args.relationships, args.output_root)
        )
        return 0

    graph = CodeGraph.from_directory(args.graph_root)
    if args.command == "node":
        _json_output(graph.get_node(args.canonical_id))
    elif args.command == "neighbors":
        _json_output(
            graph.neighbors(
                args.canonical_id,
                direction=args.direction,
                relationship_types=args.relationship_type,
            )
        )
    else:
        _json_output(
            graph.traverse(
                args.canonical_id,
                max_depth=args.max_depth,
                direction=args.direction,
                relationship_types=args.relationship_type,
                max_paths=args.max_paths,
            )
        )
    return 0
