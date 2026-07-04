"""romfarmer.analysis — CATALOG phase: builds the typed Catalog from raw sources.

Public API:
    CatalogBuilder  — scan + hash + DAT-match + multi-disc grouping → Catalog
    KnowledgeBase   — read-only facade over the romfarmer.db metadata store
"""

from .catalog_builder import CatalogBuilder
from .knowledge import KnowledgeBase

__all__ = ["CatalogBuilder", "KnowledgeBase"]
