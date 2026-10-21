"""Compatibility forwarding for the accepted Capability-KG/015-A API.

The owned implementation moved to :mod:`business_capability_kg` in Task 019-A.
This module intentionally preserves existing imports and the legacy CLI entry.
"""

from business_capability_kg.inventory_normalization import (
    CSV_FIELDS,
    EXPECTED_COLUMNS,
    PILOT_MODULE,
    SCHEMA_VERSION,
    ParsedReference,
    _collision_keys,
    _csv_bytes,
    _normalize,
    _parse_reference,
    _read_source,
    _reference_pointer,
    _render_tables,
    _sha256,
    _slug,
    build_common_inventory,
    legacy_main as main,
)

__all__ = [
    "CSV_FIELDS",
    "EXPECTED_COLUMNS",
    "PILOT_MODULE",
    "SCHEMA_VERSION",
    "ParsedReference",
    "build_common_inventory",
    "main",
]
