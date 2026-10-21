"""Phase 6 / Task 019 Business Capability Knowledge Graph workstream."""

from .inventory_normalization import (
    build_all_modules_inventory,
    build_common_inventory,
    consolidate_accepted_baseline,
)

__all__ = ["build_all_modules_inventory", "build_common_inventory", "consolidate_accepted_baseline"]
