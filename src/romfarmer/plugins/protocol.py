"""Plugin protocol and metadata definitions.

Defines the Plugin protocol (structural typing via typing.Protocol) and
associated metadata types. Any class that implements the right methods
IS a plugin — no inheritance required.

Design principles:
- Structural typing: duck-typed via Protocol, not ABC inheritance
- Typed I/O contracts: each plugin declares requires/provides
- Capability tagging: plugins declare their functional category
- Composable: plugins can be sequenced by dependency resolution
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, FrozenSet, Optional, Protocol, runtime_checkable

from ..stages.base import StageContext, StageResult


class PluginCapability(Enum):
    """Functional categories for plugins.

    Used for querying the registry ("give me all filter plugins")
    and for pipeline phase ordering.
    """

    # Phase 1: Input
    SCAN = auto()         # Source file scanning, DAT loading
    
    # Phase 2: Filtering
    FILTER = auto()       # DAT matching, 1G1R, arcade filtering
    
    # Phase 3: Selection
    SELECT = auto()       # Rating/tier/list-based selection
    
    # Phase 4: Extraction
    EXTRACT = auto()      # Archive extraction, PS3 decryption
    
    # Phase 5: Transformation
    COMPRESS = auto()     # CHD, 7z, ZIP, RVZ, XISO, Squashfs
    
    # Phase 6: Output
    ORGANIZE = auto()     # File organization, M3U playlists
    METADATA = auto()     # Metadata generation, scraping
    
    # Cross-cutting
    CACHE = auto()        # Cache pre-check, CAS operations
    VALIDATE = auto()     # Output verification, integrity checks
    HOOK = auto()         # Event hooks (hash capture, transform tracking)


# Canonical phase ordering for pipeline assembly
PHASE_ORDER: Dict[PluginCapability, int] = {
    PluginCapability.SCAN: 0,
    PluginCapability.FILTER: 10,
    PluginCapability.SELECT: 20,
    PluginCapability.CACHE: 25,
    PluginCapability.EXTRACT: 30,
    PluginCapability.COMPRESS: 40,
    PluginCapability.ORGANIZE: 50,
    PluginCapability.METADATA: 60,
    PluginCapability.VALIDATE: 70,
    PluginCapability.HOOK: 99,
}


@dataclass(frozen=True)
class PluginMeta:
    """Immutable metadata describing a plugin.

    Attributes:
        name: Unique plugin identifier (e.g., "filter-dat", "compress-chd")
        version: Semver string (e.g., "1.0.0")
        description: Human-readable description
        capability: Primary functional category
        requires: Context fields this plugin reads from
        provides: Context fields this plugin writes to
        priority: Execution priority within capability phase (lower = earlier)
        platforms: Platform names this plugin applies to (empty = all platforms)
        enabled_by_default: Whether plugin is enabled when discovered
    """

    name: str
    version: str = "1.0.0"
    description: str = ""
    capability: PluginCapability = PluginCapability.FILTER
    requires: FrozenSet[str] = field(default_factory=frozenset)
    provides: FrozenSet[str] = field(default_factory=frozenset)
    priority: int = 50
    platforms: FrozenSet[str] = field(default_factory=frozenset)
    enabled_by_default: bool = True

    def applies_to_platform(self, platform: str) -> bool:
        """Check if this plugin applies to a given platform.

        Args:
            platform: Platform name to check

        Returns:
            True if plugin has no platform restriction or platform is listed
        """
        return not self.platforms or platform in self.platforms


@runtime_checkable
class Plugin(Protocol):
    """Protocol for ROM Farmer plugins.

    Any class that implements these methods IS a plugin — no inheritance
    required. Use @runtime_checkable to allow isinstance() checks.

    Minimal implementation::

        class MyPlugin:
            @property
            def meta(self) -> PluginMeta:
                return PluginMeta(
                    name="my-plugin",
                    capability=PluginCapability.FILTER,
                    requires=frozenset({"source_files"}),
                    provides=frozenset({"matched_files"}),
                )

            def execute(self, context: StageContext) -> StageResult:
                # Do work, mutate context
                ...
    """

    @property
    def meta(self) -> PluginMeta:
        """Plugin metadata including name, capabilities, and I/O contract."""
        ...

    def execute(self, context: StageContext) -> StageResult:
        """Execute the plugin.

        Args:
            context: Mutable pipeline context

        Returns:
            StageResult with execution status and metrics
        """
        ...

    def should_skip(self, context: StageContext) -> bool:
        """Check if this plugin should be skipped for current context.

        Default: False (always run). Override for conditional execution.

        Args:
            context: Pipeline context to check

        Returns:
            True if plugin should be skipped
        """
        ...

    def validate(self, context: StageContext) -> Optional[str]:
        """Validate context before execution.

        Args:
            context: Pipeline context to validate

        Returns:
            Error message if validation fails, None if valid
        """
        ...


class PluginError(Exception):
    """Base exception for plugin errors."""

    def __init__(self, plugin_name: str, message: str):
        self.plugin_name = plugin_name
        super().__init__(f"Plugin '{plugin_name}': {message}")


class PluginValidationError(PluginError):
    """Raised when plugin validation fails."""

    def __init__(self, plugin_name: str, missing_fields: FrozenSet[str]):
        self.missing_fields = missing_fields
        super().__init__(
            plugin_name,
            f"Missing required context fields: {', '.join(sorted(missing_fields))}",
        )
