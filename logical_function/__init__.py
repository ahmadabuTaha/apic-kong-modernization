"""Task 016 deterministic Logical Function candidate discovery."""

from .mock import MOCK_RULES_VERSION, build_mock
from .full_inventory import RULES_VERSION, build_full

__all__ = ["MOCK_RULES_VERSION", "RULES_VERSION", "build_mock", "build_full"]
