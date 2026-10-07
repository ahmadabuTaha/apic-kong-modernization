"""Phase 4 catalog-property indexing and backend target resolution."""

from .resolver import (
    CACHE_SCHEMA_VERSION,
    PARSER_VERSION,
    build_resolution_indexes,
    index_catalog_properties,
    resolve_target_expression,
)

__all__ = [
    "CACHE_SCHEMA_VERSION",
    "PARSER_VERSION",
    "build_resolution_indexes",
    "index_catalog_properties",
    "resolve_target_expression",
]
