"""Read-only query service and local HTTP UI for the accepted CodeGraph."""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

from backend_target_graph import DEPENDENCY_EDGES_PATH, DEPENDENCY_NODES_PATH
from codegraph import CodeGraph
from codegraph.graph import (
    ADJACENCY_RELATIVE_PATH,
    APPROVED_NODE_TYPES,
    EDGES_RELATIVE_PATH,
    NODES_RELATIVE_PATH,
)
from relationship_builder import APPROVED_RELATIONSHIP_TYPES


DEFAULT_NODE_LIMIT = 80
DEFAULT_EDGE_LIMIT = 120
MAX_SEARCH_RESULTS = 50
STATIC_PATH = Path(__file__).with_name("static") / "index.html"
EXPLORER_NODE_TYPES = (*APPROVED_NODE_TYPES, "backend_target")
BACKEND_CLASSIFICATIONS = (
    "ACE",
    "BACKEND",
    "EXTERNAL_VIA_DATAPOWER",
    "VALIDATION_REQUIRED",
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _label(node: dict[str, Any]) -> str:
    return node.get("title") or node.get("name") or node["graph_node_id"]


class CodeGraphExplorer:
    """Safe projection and targeted visualization queries over frozen indexes."""

    def __init__(
        self,
        graph: CodeGraph,
        relationships: Iterable[dict[str, Any]],
        *,
        node_limit: int = DEFAULT_NODE_LIMIT,
        edge_limit: int = DEFAULT_EDGE_LIMIT,
        structural_node_count: int | None = None,
        structural_edge_count: int | None = None,
        dependency_node_count: int = 0,
        dependency_edge_count: int = 0,
        api_security_metadata: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        if node_limit < 1 or edge_limit < 1:
            raise ValueError("visualization limits must be positive")
        self.graph = graph
        self.relationships = {
            item["relationship_id"]: item for item in relationships
        }
        self.node_limit = node_limit
        self.edge_limit = edge_limit
        self.structural_node_count = structural_node_count or len(graph.nodes)
        self.structural_edge_count = structural_edge_count or len(graph.edges)
        self.dependency_node_count = dependency_node_count
        self.dependency_edge_count = dependency_edge_count
        self.api_security_metadata = api_security_metadata or {}

    @classmethod
    def from_paths(
        cls,
        graph_root: Path,
        relationship_index: Path | None = None,
        **kwargs: Any,
    ) -> "CodeGraphExplorer":
        relationship_path = relationship_index or (
            graph_root / "indexes/relationship_index.jsonl"
        )
        structural_nodes = _load_jsonl(graph_root / NODES_RELATIVE_PATH)
        structural_edges = _load_jsonl(graph_root / EDGES_RELATIVE_PATH)
        dependency_nodes_path = graph_root / DEPENDENCY_NODES_PATH
        dependency_edges_path = graph_root / DEPENDENCY_EDGES_PATH
        dependency_nodes = (
            _load_jsonl(dependency_nodes_path) if dependency_nodes_path.is_file() else []
        )
        dependency_edges = (
            _load_jsonl(dependency_edges_path) if dependency_edges_path.is_file() else []
        )
        if dependency_nodes or dependency_edges:
            graph = CodeGraph(
                [*structural_nodes, *dependency_nodes],
                [*structural_edges, *dependency_edges],
            )
        else:
            graph = CodeGraph(
                structural_nodes,
                structural_edges,
                _load_jsonl(graph_root / ADJACENCY_RELATIVE_PATH),
            )
        security_metadata: dict[str, dict[str, Any]] = {}
        dependency_observations = graph_root / "indexes/api_dependency_observations.jsonl"
        if dependency_observations.is_file():
            grouped: dict[str, list[dict[str, Any]]] = {}
            for item in _load_jsonl(dependency_observations):
                if item.get("observation_class") == "SECURITY_PROVIDER":
                    grouped.setdefault(item["canonical_api_id"], []).append(item)
            for api_id, values in grouped.items():
                security_metadata[api_id] = {
                    "security_provider_observation_count": len(values),
                    "security_mechanisms": sorted(
                        {item["mechanism_or_policy_name"] for item in values}
                    ),
                    "provider_or_scheme_names": sorted(
                        {
                            item["scheme_or_provider_name"]
                            for item in values
                            if item.get("scheme_or_provider_name")
                        }
                    ),
                    "endpoint_resolution_statuses": sorted(
                        {item["resolution_status"] for item in values}
                    ),
                    "graph_representation": "API_ATTRIBUTE_ONLY",
                }
        return cls(
            graph,
            [*_load_jsonl(relationship_path), *dependency_edges],
            structural_node_count=len(structural_nodes),
            structural_edge_count=len(structural_edges),
            dependency_node_count=len(dependency_nodes),
            dependency_edge_count=len(dependency_edges),
            api_security_metadata=security_metadata,
            **kwargs,
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "status": "ready",
            "graph_node_count": self.structural_node_count,
            "graph_edge_count": self.structural_edge_count,
            "combined_graph_node_count": len(self.graph.nodes),
            "combined_graph_edge_count": len(self.graph.edges),
            "structural_graph_node_count": self.structural_node_count,
            "structural_graph_edge_count": self.structural_edge_count,
            "dependency_graph_node_count": self.dependency_node_count,
            "dependency_graph_edge_count": self.dependency_edge_count,
            "approved_node_types": list(EXPLORER_NODE_TYPES),
            "approved_relationship_types": list(APPROVED_RELATIONSHIP_TYPES),
            "backend_classifications": list(BACKEND_CLASSIFICATIONS),
            "dependency_resolution_filters": ["RESOLVED", "UNRESOLVED", "MIXED"],
            "dependency_scope_filters": ["API_SHARED", "OPERATION_SCOPED"],
            "visualization_node_limit": self.node_limit,
            "visualization_edge_limit": self.edge_limit,
            "structural_reachability_notice": (
                "Structural reachability, not runtime consumption."
            ),
        }

    @staticmethod
    def _check_node_type(node_type: str | None) -> None:
        if node_type and node_type not in EXPLORER_NODE_TYPES:
            raise ValueError(f"unsupported node type: {node_type}")

    @staticmethod
    def _check_relationship_types(values: Iterable[str] | None) -> list[str] | None:
        if values is None:
            return None
        result = sorted(set(values))
        unsupported = set(result) - set(APPROVED_RELATIONSHIP_TYPES)
        if unsupported:
            raise ValueError(f"unsupported relationship types: {sorted(unsupported)}")
        return result

    def search(
        self,
        query: str,
        *,
        node_type: str | None = None,
        backend_classification: str | None = None,
        resolution_status: str | None = None,
        limit: int = MAX_SEARCH_RESULTS,
    ) -> dict[str, Any]:
        self._check_node_type(node_type)
        if limit < 1 or limit > MAX_SEARCH_RESULTS:
            raise ValueError(f"search limit must be between 1 and {MAX_SEARCH_RESULTS}")
        term = query.strip()
        folded = term.casefold()
        matches: list[tuple[int, str, dict[str, Any]]] = []
        for node in self.graph.nodes.values():
            if node_type and node["canonical_object_type"] != node_type:
                continue
            if backend_classification and node.get("backend_classification") != backend_classification:
                continue
            if resolution_status and resolution_status not in node.get("resolution_statuses", []):
                continue
            canonical_id = node["graph_node_id"]
            name = node.get("name") or ""
            title = node.get("title") or ""
            searchable = " ".join(
                [
                    name,
                    title,
                    " ".join(node.get("safe_target_path_or_template", [])),
                    " ".join(node.get("symbolic_property_tokens", [])),
                ]
            )
            if not term:
                rank = 4
            elif canonical_id == term:
                rank = 0
            elif folded and name.casefold() == folded:
                rank = 1
            elif folded and title.casefold() == folded:
                rank = 2
            elif folded and folded in searchable.casefold():
                rank = 3
            else:
                continue
            matches.append((rank, canonical_id, self._node_summary(node)))
        matches.sort(key=lambda item: (item[0], item[1]))
        total = len(matches)
        return {
            "query": term,
            "node_type": node_type,
            "backend_classification": backend_classification,
            "resolution_status": resolution_status,
            "total_matches": total,
            "returned_matches": min(total, limit),
            "truncated": total > limit,
            "results": [item[2] for item in matches[:limit]],
        }

    def _node_summary(self, node: dict[str, Any]) -> dict[str, Any]:
        node_id = node["graph_node_id"]
        result = {
            "canonical_object_id": node_id,
            "object_type": node["canonical_object_type"],
            "label": _label(node),
            "name": node.get("name"),
            "title": node.get("title"),
            "version": node.get("version"),
        }
        if node["canonical_object_type"] == "backend_target":
            result.update(
                {
                    "backend_classification": node["backend_classification"],
                    "target_identity_kind": node["target_identity_kind"],
                    "resolution_status": node["resolution_status"],
                }
            )
        return result

    def node_details(self, canonical_id: str) -> dict[str, Any] | None:
        node = self.graph.get_node(canonical_id)
        if node is None:
            return None
        details = {
            **self._node_summary(node),
            "apic_object_id": node.get("apic_object_id"),
            "apic_self_url": node.get("apic_object_url"),
            "incoming_count": len(self.graph.incoming_relationships(canonical_id)),
            "outgoing_count": len(self.graph.outgoing_relationships(canonical_id)),
            "source_canonical_record_reference": node.get("phase2_identity_pointer"),
        }
        if node["canonical_object_type"] == "backend_target":
            details.update(
                {
                    "safe_normalized_target_key": node["safe_normalized_target_key"],
                    "safe_target_path_or_template": node[
                        "safe_target_path_or_template"
                    ],
                    "symbolic_property_tokens": node["symbolic_property_tokens"],
                    "runtime_context_tokens": node["runtime_context_tokens"],
                    "resolution_statuses": node["resolution_statuses"],
                    "classification_evidence_reason": node[
                        "classification_evidence_reason"
                    ],
                    "source_observation_count": node["source_observation_count"],
                    "task011_observation_ids": node["task011_observation_ids"],
                    "task012_observation_ids": node["task012_observation_ids"],
                    "provenance": node["provenance"],
                }
            )
        elif canonical_id in self.api_security_metadata:
            details["security_metadata"] = self.api_security_metadata[canonical_id]
        return details

    @staticmethod
    def _category(categories: list[str]) -> str | None:
        values = set(categories)
        if {"authoritative_artifact", "registry_reference"} <= values:
            return "dual"
        if values == {"registry_reference"}:
            return "registry_only"
        if values == {"authoritative_artifact"}:
            return "authoritative_only"
        return None

    def edge_details(self, relationship_id: str) -> dict[str, Any] | None:
        edge = self.graph.edges.get(relationship_id)
        if edge is None:
            return None
        accepted = self.relationships.get(relationship_id, {})
        if edge.get("target_canonical_object_type") == "backend_target":
            return {
                "relationship_id": relationship_id,
                "relationship_type": "api_invokes_target",
                "source_canonical_id": edge[
                    "source_canonical_identity_record_id"
                ],
                "source_object_type": "api_artifact",
                "target_canonical_id": edge[
                    "target_canonical_identity_record_id"
                ],
                "target_object_type": "backend_target",
                "evidence_state": edge["evidence_state"],
                "confidence": edge["confidence"],
                "scope_classifications": edge["scope_classifications"],
                "operation_scopes": edge["operation_scopes"],
                "backend_classification": edge["backend_classification"],
                "target_identity_kind": edge["target_identity_kind"],
                "resolution_statuses": edge["resolution_statuses"],
                "symbolic_property_tokens": edge["symbolic_property_tokens"],
                "runtime_context_tokens": edge["runtime_context_tokens"],
                "property_resolution_evidence": edge[
                    "property_resolution_evidence"
                ],
                "task011_observation_ids": edge["task011_observation_ids"],
                "task012_observation_ids": edge["task012_observation_ids"],
                "provenance": edge["provenance"],
                "relationship_record_reference": edge[
                    "dependency_layer_pointer"
                ],
            }
        categories = sorted(accepted.get("evidence_source_categories", []))
        provenance = []
        for item in accepted.get("provenance", []):
            provenance.append(
                {
                    "evidence_source_category": item.get("evidence_source_category"),
                    "extracted_record_id": item.get("extracted_record_id"),
                    "source_relative_path": item.get("source_relative_path"),
                    "source_object_pointer": item.get("source_object_pointer"),
                    "mapped_source_relative_path": item.get("mapped_source_relative_path"),
                    "phase2_resolution_outcome": item.get("phase2_resolution_outcome"),
                }
            )
        provenance.sort(
            key=lambda item: (
                item.get("evidence_source_category") or "",
                item.get("source_relative_path") or "",
                item.get("source_object_pointer") or "",
                item.get("extracted_record_id") or "",
            )
        )
        return {
            "relationship_id": relationship_id,
            "relationship_type": edge["relationship_type"],
            "source_canonical_id": edge["source_canonical_identity_record_id"],
            "source_object_type": edge["source_canonical_object_type"],
            "target_canonical_id": edge["target_canonical_identity_record_id"],
            "target_object_type": edge["target_canonical_object_type"],
            "evidence_state": edge["evidence_state"],
            "evidence_source_categories": categories,
            "evidence_source_category": self._category(categories),
            "relationship_record_reference": edge["task008_relationship_pointer"],
            "contributing_occurrence_ids": sorted(
                accepted.get("contributing_extracted_record_ids", [])
            ),
            "provenance": provenance,
        }

    def neighborhood(
        self,
        start_id: str,
        *,
        direction: str = "both",
        depth: int = 1,
        relationship_types: Iterable[str] | None = None,
        backend_classifications: Iterable[str] | None = None,
        resolution_statuses: Iterable[str] | None = None,
        scope_classifications: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        if direction not in {"incoming", "outgoing", "both"}:
            raise ValueError("direction must be incoming, outgoing, or both")
        if depth not in {1, 2, 3}:
            raise ValueError("depth must be 1, 2, or 3")
        allowed = self._check_relationship_types(relationship_types)
        selected = self.graph.get_node(start_id)
        if selected is None:
            raise KeyError(start_id)
        traversal = self.graph.traverse(
            start_id,
            direction=direction,
            max_depth=depth,
            relationship_types=allowed,
            max_paths=10000,
        )
        backend_filters = set(backend_classifications or [])
        resolution_filters = set(resolution_statuses or [])
        scope_filters = set(scope_classifications or [])
        unsupported_classifications = backend_filters - set(BACKEND_CLASSIFICATIONS)
        if unsupported_classifications:
            raise ValueError(
                f"unsupported backend classifications: {sorted(unsupported_classifications)}"
            )
        def path_matches(path: dict[str, Any]) -> bool:
            if not (backend_filters or resolution_filters or scope_filters):
                return True
            for edge_id in path["relationship_ids"]:
                edge = self.graph.edges[edge_id]
                if edge["relationship_type"] != "api_invokes_target":
                    return False
                if backend_filters and edge.get("backend_classification") not in backend_filters:
                    return False
                if resolution_filters and not resolution_filters.intersection(
                    edge.get("resolution_statuses", [])
                ):
                    return False
                if scope_filters and not scope_filters.intersection(
                    edge.get("scope_classifications", [])
                ):
                    return False
            return True
        paths = [path for path in traversal["paths"] if path_matches(path)]
        candidate_node_ids = {start_id}
        candidate_edge_ids: set[str] = set()
        for path in paths:
            candidate_node_ids.update(path["node_ids"])
            candidate_edge_ids.update(path["relationship_ids"])

        kept_nodes = {start_id}
        kept_edges: set[str] = set()
        for path in paths:
            path_nodes = set(path["node_ids"])
            path_edges = set(path["relationship_ids"])
            if (
                len(kept_nodes | path_nodes) <= self.node_limit
                and len(kept_edges | path_edges) <= self.edge_limit
            ):
                kept_nodes.update(path_nodes)
                kept_edges.update(path_edges)
        limit_exceeded = (
            len(candidate_node_ids) > len(kept_nodes)
            or len(candidate_edge_ids) > len(kept_edges)
            or traversal["truncated"]
        )
        warning = None
        if limit_exceeded:
            warning = (
                f"Visualization limit reached ({self.node_limit} nodes / "
                f"{self.edge_limit} edges). Showing a deterministic subset; "
                "reduce depth or relationship filters."
            )
        return {
            "selected_node_id": start_id,
            "direction": direction,
            "depth": depth,
            "relationship_filters": allowed,
            "backend_classification_filters": sorted(backend_filters),
            "resolution_status_filters": sorted(resolution_filters),
            "scope_classification_filters": sorted(scope_filters),
            "structural_reachability_notice": (
                "Structural reachability, not runtime consumption."
            ),
            "candidate_node_count": len(candidate_node_ids),
            "candidate_edge_count": len(candidate_edge_ids),
            "returned_node_count": len(kept_nodes),
            "returned_edge_count": len(kept_edges),
            "visualization_limit_exceeded": limit_exceeded,
            "visualization_limit_message": warning,
            "nodes": [
                self._node_summary(self.graph.nodes[node_id])
                for node_id in sorted(kept_nodes)
            ],
            "edges": [
                self.edge_details(edge_id) for edge_id in sorted(kept_edges)
            ],
        }


class _Handler(BaseHTTPRequestHandler):
    explorer: CodeGraphExplorer

    def _json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        try:
            if parsed.path == "/":
                body = STATIC_PATH.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif parsed.path in {"/health", "/api/meta"}:
                self._json(self.explorer.metadata())
            elif parsed.path == "/api/search":
                self._json(
                    self.explorer.search(
                        params.get("q", [""])[0],
                        node_type=params.get("type", [None])[0],
                        backend_classification=params.get(
                            "backend_classification", [None]
                        )[0],
                        resolution_status=params.get("resolution", [None])[0],
                    )
                )
            elif parsed.path == "/api/node":
                value = self.explorer.node_details(params.get("id", [""])[0])
                self._json(value, HTTPStatus.OK if value else HTTPStatus.NOT_FOUND)
            elif parsed.path == "/api/edge":
                value = self.explorer.edge_details(params.get("id", [""])[0])
                self._json(value, HTTPStatus.OK if value else HTTPStatus.NOT_FOUND)
            elif parsed.path == "/api/neighborhood":
                relationships = [
                    value
                    for item in params.get("relationship", [])
                    for value in item.split(",")
                    if value
                ]
                self._json(
                    self.explorer.neighborhood(
                        params.get("id", [""])[0],
                        direction=params.get("direction", ["both"])[0],
                        depth=int(params.get("depth", ["1"])[0]),
                        relationship_types=relationships or None,
                        backend_classifications=params.get(
                            "backend_classification", []
                        ),
                        resolution_statuses=params.get("resolution", []),
                        scope_classifications=params.get("scope", []),
                    )
                )
            else:
                self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except KeyError as exc:
            self._json({"error": f"node not found: {exc.args[0]}"}, HTTPStatus.NOT_FOUND)
        except (TypeError, ValueError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: Any) -> None:
        return


def create_server(
    explorer: CodeGraphExplorer, host: str, port: int
) -> ThreadingHTTPServer:
    handler = type("CodeGraphExplorerHandler", (_Handler,), {"explorer": explorer})
    return ThreadingHTTPServer((host, port), handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--graph-root", default=Path("."), type=Path)
    parser.add_argument("--relationship-index", type=Path)
    parser.add_argument("--node-limit", default=DEFAULT_NODE_LIMIT, type=int)
    parser.add_argument("--edge-limit", default=DEFAULT_EDGE_LIMIT, type=int)
    args = parser.parse_args(argv)
    explorer = CodeGraphExplorer.from_paths(
        args.graph_root,
        args.relationship_index,
        node_limit=args.node_limit,
        edge_limit=args.edge_limit,
    )
    server = create_server(explorer, args.host, args.port)
    print(
        f"CodeGraph Explorer ready at http://{args.host}:{server.server_port} "
        f"({len(explorer.graph.nodes)} nodes, {len(explorer.graph.edges)} edges)",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
