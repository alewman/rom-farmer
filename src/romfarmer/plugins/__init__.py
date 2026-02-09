"""Plugin architecture for ROM Farmer.

Provides a pluggable, event-driven pipeline where each processing capability
(filter, extract, compress, organize, metadata) is a discoverable plugin.

Key components:
- Plugin: Protocol that any processing unit implements
- PluginRegistry: Discovers and manages plugins (entry_points + built-in)
- EventBus: Pub/sub event system for cross-cutting concerns
- StageAdapter: Wraps legacy Stage classes as Plugins (zero-breakage migration)
"""

from .protocol import (
    Plugin,
    PluginCapability,
    PluginMeta,
    PluginError,
    PluginValidationError,
)
from .registry import PluginRegistry
from .events import Event, EventBus, EventPriority, PipelineEvent
from .adapter import StageAdapter

__all__ = [
    # Protocol
    "Plugin",
    "PluginCapability",
    "PluginMeta",
    "PluginError",
    "PluginValidationError",
    # Registry
    "PluginRegistry",
    # Events
    "Event",
    "EventBus",
    "EventPriority",
    "PipelineEvent",
    # Adapter
    "StageAdapter",
]
