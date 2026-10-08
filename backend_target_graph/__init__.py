"""Additive Phase 4 backend-target graph construction."""

from .graph import (
    DEPENDENCY_ADJACENCY_PATH,
    DEPENDENCY_EDGES_PATH,
    DEPENDENCY_NODES_PATH,
    build_backend_target_graph,
    write_backend_target_graph,
)

__all__ = [
    "DEPENDENCY_ADJACENCY_PATH",
    "DEPENDENCY_EDGES_PATH",
    "DEPENDENCY_NODES_PATH",
    "build_backend_target_graph",
    "write_backend_target_graph",
]
