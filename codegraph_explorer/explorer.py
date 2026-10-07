"""Read-only query service and local HTTP UI for the accepted CodeGraph."""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

from codegraph import CodeGraph
from codegraph.graph import APPROVED_NODE_TYPES
from relationship_builder import APPROVED_RELATIONSHIP_TYPES


DEFAULT_NODE_LIMIT = 80
DEFAULT_EDGE_LIMIT = 120
MAX_SEARCH_RESULTS = 50
STATIC_PATH = Path(__file__).with_name("static") / "index.html"


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
    ) -> None:
        if node_limit < 1 or edge_limit < 1:
            raise ValueError("visualization limits must be positive")
        self.graph = graph
        self.relationships = {
            item["relationship_id"]: item for item in relationships
        }
        self.node_limit = node_limit
        self.edge_limit = edge_limit

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
        return cls(
            CodeGraph.from_directory(graph_root),
            _load_jsonl(relationship_path),
            **kwargs,
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "status": "ready",
            "graph_node_count": len(self.graph.nodes),
            "graph_edge_count": len(self.graph.edges),
            "approved_node_types": list(APPROVED_NODE_TYPES),
            "approved_relationship_types": list(APPROVED_RELATIONSHIP_TYPES),
            "visualization_node_limit": self.node_limit,
            "visualization_edge_limit": self.edge_limit,
            "structural_reachability_notice": (
                "Structural reachability, not runtime consumption."
            ),
        }

    @staticmethod
    def _check_node_type(node_type: str | None) -> None:
        if node_type and node_type not in APPROVED_NODE_TYPES:
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
            canonical_id = node["graph_node_id"]
            name = node.get("name") or ""
            title = node.get("title") or ""
            if canonical_id == term:
                rank = 0
            elif folded and name.casefold() == folded:
                rank = 1
            elif folded and title.casefold() == folded:
                rank = 2
            elif folded and (folded in name.casefold() or folded in title.casefold()):
                rank = 3
            else:
                continue
            matches.append((rank, canonical_id, self._node_summary(node)))
        matches.sort(key=lambda item: (item[0], item[1]))
        total = len(matches)
        return {
            "query": term,
            "node_type": node_type,
            "total_matches": total,
            "returned_matches": min(total, limit),
            "truncated": total > limit,
            "results": [item[2] for item in matches[:limit]],
        }

    def _node_summary(self, node: dict[str, Any]) -> dict[str, Any]:
        node_id = node["graph_node_id"]
        return {
            "canonical_object_id": node_id,
            "object_type": node["canonical_object_type"],
            "label": _label(node),
            "name": node.get("name"),
            "title": node.get("title"),
            "version": node.get("version"),
        }

    def node_details(self, canonical_id: str) -> dict[str, Any] | None:
        node = self.graph.get_node(canonical_id)
        if node is None:
            return None
        return {
            **self._node_summary(node),
            "apic_object_id": node.get("apic_object_id"),
            "apic_self_url": node.get("apic_object_url"),
            "incoming_count": len(self.graph.incoming_relationships(canonical_id)),
            "outgoing_count": len(self.graph.outgoing_relationships(canonical_id)),
            "source_canonical_record_reference": node.get("phase2_identity_pointer"),
        }

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
        candidate_node_ids = {start_id}
        candidate_edge_ids: set[str] = set()
        for path in traversal["paths"]:
            candidate_node_ids.update(path["node_ids"])
            candidate_edge_ids.update(path["relationship_ids"])

        kept_nodes = {start_id}
        kept_edges: set[str] = set()
        for path in traversal["paths"]:
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
