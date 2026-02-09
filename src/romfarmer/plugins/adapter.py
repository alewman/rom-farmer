"""Stage-to-Plugin adapter for zero-breakage migration.

Wraps any existing Stage subclass as a Plugin, preserving all behavior
while exposing the Plugin protocol. This means the entire existing
pipeline can work through the plugin system immediately — we don't need
to rewrite all 22 stages before the plugin architecture is usable.

Usage::

    from romfarmer.stages import FilterDATStage
    from romfarmer.plugins import StageAdapter, PluginCapability

    # Wrap an existing stage as a plugin
    plugin = StageAdapter(
        stage=FilterDATStage(),
        capability=PluginCapability.FILTER,
        requires=frozenset({"source_files", "dat_file"}),
        provides=frozenset({"matched_files", "file_md5s"}),
    )

    # It's now a full Plugin
    result = plugin.execute(context)
    print(plugin.meta.name)  # "filter-dat"
"""

from __future__ import annotations

import re
from typing import FrozenSet, Optional

from ..stages.base import Stage, StageContext, StageResult
from .protocol import Plugin, PluginCapability, PluginMeta


def _stage_name_to_plugin_name(stage_name: str) -> str:
    """Convert a stage name to a plugin-style kebab-case name.

    Examples:
        "Filter DAT" -> "filter-dat"
        "Compress CHD" -> "compress-chd"
        "Extract Archive" -> "extract-archive"
        "Create M3U Files" -> "create-m3u-files"

    Args:
        stage_name: Human-readable stage name

    Returns:
        Kebab-case plugin name
    """
    # Replace spaces and underscores with hyphens first (preserves word boundaries)
    s = re.sub(r"[\s_]+", "-", stage_name)
    # Insert hyphen between lowercase/digit and uppercase: "filterDat" -> "filter-Dat"
    s = re.sub(r"(?<=[a-z])([A-Z])", r"-\1", s)
    # Insert hyphen between uppercase run and uppercase+lowercase: "DATFile" -> "DAT-File"
    s = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"-\1", s)
    # Collapse multiple hyphens
    s = re.sub(r"-+", "-", s)
    return s.lower().strip("-")


class StageAdapter:
    """Wraps a legacy Stage as a Plugin.

    This is the migration bridge — every existing Stage can participate
    in the plugin architecture without modification.

    The adapter implements the Plugin protocol (structural typing) so
    isinstance(adapter, Plugin) is True.
    """

    def __init__(
        self,
        stage: Stage,
        capability: PluginCapability = PluginCapability.FILTER,
        requires: FrozenSet[str] = frozenset(),
        provides: FrozenSet[str] = frozenset(),
        priority: int = 50,
        platforms: FrozenSet[str] = frozenset(),
        version: str = "1.0.0",
    ):
        """Initialize adapter.

        Args:
            stage: The legacy Stage instance to wrap
            capability: Plugin capability category
            requires: Context fields this stage reads
            provides: Context fields this stage writes
            priority: Priority within capability phase
            platforms: Platform restrictions (empty = all)
            version: Plugin version string
        """
        self._stage = stage
        self._meta = PluginMeta(
            name=_stage_name_to_plugin_name(stage.name),
            version=version,
            description=f"Adapted from Stage: {stage.name}",
            capability=capability,
            requires=requires,
            provides=provides,
            priority=priority,
            platforms=platforms,
        )

    @property
    def meta(self) -> PluginMeta:
        """Plugin metadata."""
        return self._meta

    @property
    def stage(self) -> Stage:
        """Access the underlying Stage instance."""
        return self._stage

    def execute(self, context: StageContext) -> StageResult:
        """Execute the wrapped stage.

        Args:
            context: Pipeline context

        Returns:
            StageResult from the underlying stage
        """
        return self._stage.execute(context)

    def should_skip(self, context: StageContext) -> bool:
        """Check if the wrapped stage should be skipped.

        Args:
            context: Pipeline context

        Returns:
            True if stage should skip
        """
        return self._stage.should_skip(context)

    def validate(self, context: StageContext) -> Optional[str]:
        """Validate context via the wrapped stage.

        Args:
            context: Pipeline context

        Returns:
            Error message or None
        """
        return self._stage.validate_context(context)

    def __repr__(self) -> str:
        return f"StageAdapter({self._stage.name!r}, capability={self._meta.capability.name})"
