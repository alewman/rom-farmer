"""Plugin registry — discovery, registration, and querying.

The registry is the central catalog of all available plugins. It discovers
plugins from three sources:

1. **Built-in**: Hardcoded registrations in code (e.g., StageAdapter wrappers)
2. **Entry points**: `romfarmer.plugins` group in installed packages
3. **Config**: User YAML config enabling/disabling/configuring plugins

The registry also handles dependency resolution via topological sort
of plugin requires/provides declarations.
"""

from __future__ import annotations

import importlib.metadata
import logging
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Type,
)

from .protocol import (
    PHASE_ORDER,
    Plugin,
    PluginCapability,
    PluginMeta,
    PluginError,
)

logger = logging.getLogger(__name__)

# Entry point group name for plugin discovery
ENTRY_POINT_GROUP = "romfarmer.plugins"


@dataclass
class RegisteredPlugin:
    """A plugin registered in the system.

    Wraps a plugin instance with additional registry metadata.
    """

    plugin: Plugin
    enabled: bool = True
    source: str = "built-in"  # "built-in", "entry-point", "config"

    @property
    def meta(self) -> PluginMeta:
        return self.plugin.meta


class PluginRegistry:
    """Central plugin registry with discovery and dependency resolution.

    Example::

        registry = PluginRegistry()

        # Discover from entry_points
        registry.discover()

        # Register built-in
        registry.register(MyFilterPlugin())

        # Query
        filters = registry.get_by_capability(PluginCapability.FILTER)

        # Resolve execution order
        ordered = registry.resolve_order(platform="nes")
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, RegisteredPlugin] = {}

    # ── Registration ──────────────────────────────────────────────────────

    def register(
        self,
        plugin: Plugin,
        enabled: Optional[bool] = None,
        source: str = "built-in",
    ) -> None:
        """Register a plugin.

        Args:
            plugin: Plugin instance to register
            enabled: Override enabled state (None = use plugin default)
            source: Where the plugin came from ("built-in", "entry-point", etc.)

        Raises:
            PluginError: If a plugin with the same name is already registered
        """
        meta = plugin.meta
        if meta.name in self._plugins:
            raise PluginError(
                meta.name,
                f"Plugin already registered (source: {self._plugins[meta.name].source})",
            )

        is_enabled = enabled if enabled is not None else meta.enabled_by_default
        self._plugins[meta.name] = RegisteredPlugin(
            plugin=plugin,
            enabled=is_enabled,
            source=source,
        )
        logger.debug(
            f"Registered plugin: {meta.name} "
            f"(capability={meta.capability.name}, "
            f"priority={meta.priority}, "
            f"source={source}, "
            f"enabled={is_enabled})"
        )

    def unregister(self, name: str) -> Optional[Plugin]:
        """Remove a plugin from the registry.

        Args:
            name: Plugin name to remove

        Returns:
            The removed plugin, or None if not found
        """
        entry = self._plugins.pop(name, None)
        if entry:
            logger.debug(f"Unregistered plugin: {name}")
            return entry.plugin
        return None

    # ── Discovery ─────────────────────────────────────────────────────────

    def discover(self, group: str = ENTRY_POINT_GROUP) -> int:
        """Discover and register plugins from Python entry_points.

        Scans all installed packages for the `romfarmer.plugins` entry point
        group. Each entry point should resolve to either:
        - A Plugin class (will be instantiated)
        - A Plugin instance (used directly)
        - A factory function that returns a Plugin

        Args:
            group: Entry point group name to scan

        Returns:
            Number of plugins discovered
        """
        count = 0
        try:
            entry_points = importlib.metadata.entry_points()
            # Python 3.12+: entry_points() returns a SelectableGroups
            if hasattr(entry_points, "select"):
                eps = entry_points.select(group=group)
            else:
                eps = entry_points.get(group, [])
        except Exception as e:
            logger.warning(f"Failed to scan entry points: {e}")
            return 0

        for ep in eps:
            try:
                obj = ep.load()

                # Handle class vs instance vs factory
                if isinstance(obj, type):
                    plugin = obj()
                elif callable(obj) and not isinstance(obj, Plugin):
                    plugin = obj()
                else:
                    plugin = obj

                if not isinstance(plugin, Plugin):
                    logger.warning(
                        f"Entry point '{ep.name}' did not resolve to a Plugin: {type(plugin)}"
                    )
                    continue

                self.register(plugin, source="entry-point")
                count += 1
                logger.info(f"Discovered plugin from entry point: {ep.name}")

            except Exception as e:
                logger.error(f"Failed to load plugin from entry point '{ep.name}': {e}")

        logger.info(f"Discovered {count} plugin(s) from entry points")
        return count

    # ── Querying ──────────────────────────────────────────────────────────

    def get(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None
        """
        entry = self._plugins.get(name)
        return entry.plugin if entry else None

    def get_enabled(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name only if enabled.

        Args:
            name: Plugin name

        Returns:
            Plugin instance if found and enabled, else None
        """
        entry = self._plugins.get(name)
        if entry and entry.enabled:
            return entry.plugin
        return None

    def get_by_capability(
        self,
        capability: PluginCapability,
        enabled_only: bool = True,
    ) -> List[Plugin]:
        """Get all plugins with a given capability.

        Args:
            capability: Capability to filter by
            enabled_only: If True, only return enabled plugins

        Returns:
            List of plugins sorted by priority
        """
        results = []
        for entry in self._plugins.values():
            if entry.meta.capability != capability:
                continue
            if enabled_only and not entry.enabled:
                continue
            results.append(entry.plugin)

        results.sort(key=lambda p: p.meta.priority)
        return results

    def get_for_platform(
        self,
        platform: str,
        enabled_only: bool = True,
    ) -> List[Plugin]:
        """Get all plugins applicable to a platform.

        Args:
            platform: Platform name (e.g., "nes", "psx", "ps3")
            enabled_only: If True, only return enabled plugins

        Returns:
            List of applicable plugins sorted by phase then priority
        """
        results = []
        for entry in self._plugins.values():
            if enabled_only and not entry.enabled:
                continue
            if not entry.meta.applies_to_platform(platform):
                continue
            results.append(entry.plugin)

        # Sort by phase order first, then priority within phase
        def _sort_key(p: Plugin) -> tuple:
            phase = PHASE_ORDER.get(p.meta.capability, 50)
            return (phase, p.meta.priority)

        results.sort(key=_sort_key)
        return results

    # ── Enable/Disable ────────────────────────────────────────────────────

    def enable(self, name: str) -> bool:
        """Enable a plugin.

        Args:
            name: Plugin name

        Returns:
            True if plugin was found and enabled
        """
        entry = self._plugins.get(name)
        if entry:
            entry.enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a plugin (stays registered but won't execute).

        Args:
            name: Plugin name

        Returns:
            True if plugin was found and disabled
        """
        entry = self._plugins.get(name)
        if entry:
            entry.enabled = False
            return True
        return False

    # ── Dependency Resolution ─────────────────────────────────────────────

    def resolve_order(
        self,
        plugins: Optional[Sequence[Plugin]] = None,
        platform: Optional[str] = None,
    ) -> List[Plugin]:
        """Resolve plugin execution order via topological sort.

        Orders plugins so that each plugin's `requires` fields are
        satisfied by preceding plugins' `provides` fields. Within
        the same dependency level, plugins are ordered by phase
        then priority.

        Args:
            plugins: Specific plugins to order (default: all enabled)
            platform: If provided, filter to platform-applicable plugins

        Returns:
            Plugins in dependency-resolved execution order

        Raises:
            PluginError: If there's a circular dependency or unsatisfied requirement
        """
        if plugins is None:
            if platform:
                plugins = self.get_for_platform(platform)
            else:
                plugins = [
                    entry.plugin
                    for entry in self._plugins.values()
                    if entry.enabled
                ]

        if not plugins:
            return []

        # Build dependency graph
        # Map: plugin name -> set of plugin names it depends on
        by_name: Dict[str, Plugin] = {p.meta.name: p for p in plugins}
        provides_map: Dict[str, str] = {}  # field -> plugin name that provides it

        # First pass: build provides map
        for p in plugins:
            for field_name in p.meta.provides:
                provides_map[field_name] = p.meta.name

        # Second pass: build adjacency (who must come before whom)
        deps: Dict[str, Set[str]] = {p.meta.name: set() for p in plugins}
        for p in plugins:
            for req in p.meta.requires:
                provider = provides_map.get(req)
                if provider and provider != p.meta.name:
                    deps[p.meta.name].add(provider)
                # If no provider found, requirement may be satisfied by
                # pipeline context initialization (source_files, dat_file, etc.)

        # Topological sort (Kahn's algorithm)
        in_degree: Dict[str, int] = {name: len(d) for name, d in deps.items()}
        queue: List[str] = [name for name, deg in in_degree.items() if deg == 0]

        # Sort initial queue by phase + priority for deterministic ordering
        def _sort_key(name: str) -> tuple:
            p = by_name[name]
            phase = PHASE_ORDER.get(p.meta.capability, 50)
            return (phase, p.meta.priority)

        queue.sort(key=_sort_key)

        ordered: List[str] = []
        while queue:
            # Pick the first (highest priority) ready plugin
            current = queue.pop(0)
            ordered.append(current)

            # Reduce in-degree for dependents
            for name, dep_set in deps.items():
                if current in dep_set:
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)
                        queue.sort(key=_sort_key)

        if len(ordered) != len(plugins):
            # Circular dependency detected
            remaining = set(by_name.keys()) - set(ordered)
            raise PluginError(
                "registry",
                f"Circular dependency detected among plugins: {', '.join(sorted(remaining))}",
            )

        return [by_name[name] for name in ordered]

    # ── Introspection ─────────────────────────────────────────────────────

    @property
    def names(self) -> List[str]:
        """All registered plugin names."""
        return list(self._plugins.keys())

    @property
    def count(self) -> int:
        """Total number of registered plugins."""
        return len(self._plugins)

    @property
    def enabled_count(self) -> int:
        """Number of enabled plugins."""
        return sum(1 for e in self._plugins.values() if e.enabled)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Get summary info for all registered plugins.

        Returns:
            List of dicts with name, capability, enabled, source, priority
        """
        return [
            {
                "name": entry.meta.name,
                "capability": entry.meta.capability.name,
                "enabled": entry.enabled,
                "source": entry.source,
                "priority": entry.meta.priority,
                "version": entry.meta.version,
                "requires": sorted(entry.meta.requires),
                "provides": sorted(entry.meta.provides),
            }
            for entry in self._plugins.values()
        ]

    def clear(self) -> None:
        """Remove all plugins from registry."""
        self._plugins.clear()
