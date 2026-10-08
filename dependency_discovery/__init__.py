"""Phase 4 API dependency observation discovery."""

from .discovery import (
    CACHE_SCHEMA_VERSION,
    PARSER_VERSION,
    build_dependency_indexes,
    extract_dependency_candidates,
)

__all__ = [
    "CACHE_SCHEMA_VERSION",
    "PARSER_VERSION",
    "build_dependency_indexes",
    "extract_dependency_candidates",
]
