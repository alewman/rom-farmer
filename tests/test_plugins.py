"""Tests for the plugin protocol, registry, event bus, adapter, catalog, and pipeline."""

import pytest
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

from romfarmer.plugins.protocol import (
    Plugin,
    PluginCapability,
    PluginMeta,
    PluginError,
    PluginValidationError,
    PHASE_ORDER,
)
from romfarmer.plugins.registry import PluginRegistry
from romfarmer.plugins.events import (
    Event,
    EventBus,
    EventPriority,
    PipelineEvent,
    StageEvent,
    FileEvent,
    CacheEvent,
)
from romfarmer.plugins.adapter import StageAdapter, _stage_name_to_plugin_name
from romfarmer.plugins.catalog import (
    STAGE_CONTRACTS,
    create_plugin,
    register_builtin_plugins,
    get_contract,
    list_contracts,
)
from romfarmer.plugins.pipeline import PluginPipeline
from romfarmer.stages.base import Stage, StageContext, StageResult, StageStatus


# ═══════════════════════════════════════════════════════════════════════════════
# Test fixtures
# ═══════════════════════════════════════════════════════════════════════════════


class DummyPlugin:
    """Minimal plugin for testing. Satisfies Plugin protocol via structural typing."""

    def __init__(
        self,
        name: str = "dummy",
        capability: PluginCapability = PluginCapability.FILTER,
        requires: frozenset = frozenset(),
        provides: frozenset = frozenset(),
        priority: int = 50,
        platforms: frozenset = frozenset(),
    ):
        self._meta = PluginMeta(
            name=name,
            capability=capability,
            requires=requires,
            provides=provides,
            priority=priority,
            platforms=platforms,
        )
        self.execute_count = 0

    @property
    def meta(self) -> PluginMeta:
        return self._meta

    def execute(self, context: StageContext) -> StageResult:
        self.execute_count += 1
        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"{self._meta.name} executed",
            files_processed=1,
        )

    def should_skip(self, context: StageContext) -> bool:
        return False

    def validate(self, context: StageContext) -> Optional[str]:
        return None


class DummyStage(Stage):
    """Minimal Stage subclass for adapter testing."""

    def __init__(self, name: str = "Test Stage"):
        super().__init__(name)
        self.executed = False

    def execute(self, context: StageContext) -> StageResult:
        self.executed = True
        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"{self.name} done",
            files_processed=5,
        )


def make_context(**kwargs) -> StageContext:
    """Create a minimal StageContext for testing."""
    defaults = {
        "platform_name": "nes",
        "platform_config": MagicMock(),
        "target_name": "test-target",
        "source_dir": Path("/tmp/source"),
        "work_dir": Path("/tmp/work"),
        "output_dir": Path("/tmp/output"),
    }
    defaults.update(kwargs)
    return StageContext(**defaults)


# ═══════════════════════════════════════════════════════════════════════════════
# Plugin Protocol Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPluginProtocol:
    """Test the Plugin protocol and PluginMeta."""

    def test_dummy_satisfies_protocol(self):
        """DummyPlugin should satisfy the Plugin protocol."""
        plugin = DummyPlugin()
        assert isinstance(plugin, Plugin)

    def test_non_plugin_fails_protocol(self):
        """A random object should NOT satisfy the Plugin protocol."""
        assert not isinstance("not a plugin", Plugin)
        assert not isinstance(42, Plugin)

    def test_meta_immutable(self):
        """PluginMeta should be frozen (immutable)."""
        meta = PluginMeta(name="test")
        with pytest.raises(AttributeError):
            meta.name = "changed"

    def test_meta_defaults(self):
        """PluginMeta defaults should be sensible."""
        meta = PluginMeta(name="test")
        assert meta.version == "1.0.0"
        assert meta.capability == PluginCapability.FILTER
        assert meta.requires == frozenset()
        assert meta.provides == frozenset()
        assert meta.priority == 50
        assert meta.enabled_by_default is True

    def test_meta_platform_filter(self):
        """Platform filtering should work correctly."""
        # No restriction = applies to all
        meta = PluginMeta(name="universal")
        assert meta.applies_to_platform("nes")
        assert meta.applies_to_platform("psx")

        # Restricted
        meta = PluginMeta(name="ps3-only", platforms=frozenset({"ps3"}))
        assert meta.applies_to_platform("ps3")
        assert not meta.applies_to_platform("nes")

    def test_capability_enum_values(self):
        """All capabilities should have a phase order entry."""
        for cap in PluginCapability:
            assert cap in PHASE_ORDER, f"{cap.name} missing from PHASE_ORDER"

    def test_plugin_error(self):
        """PluginError should include plugin name."""
        err = PluginError("my-plugin", "something broke")
        assert "my-plugin" in str(err)
        assert "something broke" in str(err)

    def test_plugin_validation_error(self):
        """PluginValidationError should list missing fields."""
        err = PluginValidationError("my-plugin", frozenset({"dat_file", "source_files"}))
        assert "dat_file" in str(err)
        assert "source_files" in str(err)


# ═══════════════════════════════════════════════════════════════════════════════
# Plugin Registry Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPluginRegistry:
    """Test plugin registry operations."""

    def test_register_and_get(self):
        """Register a plugin and retrieve it by name."""
        reg = PluginRegistry()
        plugin = DummyPlugin(name="test-filter")
        reg.register(plugin)

        assert reg.get("test-filter") is plugin
        assert reg.count == 1

    def test_register_duplicate_raises(self):
        """Registering same name twice should raise."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(name="dupe"))
        with pytest.raises(PluginError):
            reg.register(DummyPlugin(name="dupe"))

    def test_unregister(self):
        """Unregister should remove plugin."""
        reg = PluginRegistry()
        plugin = DummyPlugin(name="removable")
        reg.register(plugin)
        assert reg.count == 1

        removed = reg.unregister("removable")
        assert removed is plugin
        assert reg.count == 0
        assert reg.get("removable") is None

    def test_unregister_nonexistent(self):
        """Unregister of unknown name returns None."""
        reg = PluginRegistry()
        assert reg.unregister("nope") is None

    def test_enable_disable(self):
        """Enable/disable should control plugin availability."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(name="toggler"))

        assert reg.get_enabled("toggler") is not None

        reg.disable("toggler")
        assert reg.get_enabled("toggler") is None
        assert reg.get("toggler") is not None  # Still registered

        reg.enable("toggler")
        assert reg.get_enabled("toggler") is not None

    def test_get_by_capability(self):
        """Filter plugins by capability."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(name="f1", capability=PluginCapability.FILTER, priority=10))
        reg.register(DummyPlugin(name="f2", capability=PluginCapability.FILTER, priority=20))
        reg.register(DummyPlugin(name="c1", capability=PluginCapability.COMPRESS))

        filters = reg.get_by_capability(PluginCapability.FILTER)
        assert len(filters) == 2
        assert filters[0].meta.name == "f1"  # Lower priority first
        assert filters[1].meta.name == "f2"

        compressors = reg.get_by_capability(PluginCapability.COMPRESS)
        assert len(compressors) == 1

    def test_get_by_capability_enabled_only(self):
        """Disabled plugins should be excluded by default."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(name="active", capability=PluginCapability.FILTER))
        reg.register(DummyPlugin(name="inactive", capability=PluginCapability.FILTER))
        reg.disable("inactive")

        assert len(reg.get_by_capability(PluginCapability.FILTER)) == 1
        assert len(reg.get_by_capability(PluginCapability.FILTER, enabled_only=False)) == 2

    def test_get_for_platform(self):
        """Platform filtering should work."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(name="universal", capability=PluginCapability.FILTER))
        reg.register(DummyPlugin(
            name="ps3-extract",
            capability=PluginCapability.EXTRACT,
            platforms=frozenset({"ps3"}),
        ))
        reg.register(DummyPlugin(
            name="nes-filter",
            capability=PluginCapability.FILTER,
            platforms=frozenset({"nes"}),
        ))

        nes_plugins = reg.get_for_platform("nes")
        nes_names = [p.meta.name for p in nes_plugins]
        assert "universal" in nes_names
        assert "nes-filter" in nes_names
        assert "ps3-extract" not in nes_names

        ps3_plugins = reg.get_for_platform("ps3")
        ps3_names = [p.meta.name for p in ps3_plugins]
        assert "universal" in ps3_names
        assert "ps3-extract" in ps3_names
        assert "nes-filter" not in ps3_names

    def test_get_for_platform_sorted_by_phase(self):
        """Platform query should sort by phase order then priority."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(name="organize", capability=PluginCapability.ORGANIZE, priority=10))
        reg.register(DummyPlugin(name="filter", capability=PluginCapability.FILTER, priority=10))
        reg.register(DummyPlugin(name="compress", capability=PluginCapability.COMPRESS, priority=10))

        plugins = reg.get_for_platform("nes")
        names = [p.meta.name for p in plugins]
        assert names == ["filter", "compress", "organize"]

    def test_resolve_order_simple(self):
        """Simple dependency resolution: A provides X, B requires X."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(
            name="producer",
            capability=PluginCapability.FILTER,
            provides=frozenset({"matched_files"}),
        ))
        reg.register(DummyPlugin(
            name="consumer",
            capability=PluginCapability.EXTRACT,
            requires=frozenset({"matched_files"}),
        ))

        ordered = reg.resolve_order()
        names = [p.meta.name for p in ordered]
        assert names.index("producer") < names.index("consumer")

    def test_resolve_order_chain(self):
        """Chain: A→B→C."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(
            name="c",
            capability=PluginCapability.ORGANIZE,
            requires=frozenset({"extracted"}),
        ))
        reg.register(DummyPlugin(
            name="a",
            capability=PluginCapability.FILTER,
            provides=frozenset({"matched"}),
        ))
        reg.register(DummyPlugin(
            name="b",
            capability=PluginCapability.EXTRACT,
            requires=frozenset({"matched"}),
            provides=frozenset({"extracted"}),
        ))

        ordered = reg.resolve_order()
        names = [p.meta.name for p in ordered]
        assert names == ["a", "b", "c"]

    def test_resolve_order_circular_raises(self):
        """Circular dependency should raise PluginError."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(
            name="chicken",
            capability=PluginCapability.FILTER,
            requires=frozenset({"egg"}),
            provides=frozenset({"chicken"}),
        ))
        reg.register(DummyPlugin(
            name="egg",
            capability=PluginCapability.FILTER,
            requires=frozenset({"chicken"}),
            provides=frozenset({"egg"}),
        ))

        with pytest.raises(PluginError, match="Circular dependency"):
            reg.resolve_order()

    def test_resolve_order_unsatisfied_requirement_ok(self):
        """Unsatisfied requirements should be allowed (satisfied by context init)."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(
            name="needs-source",
            capability=PluginCapability.FILTER,
            requires=frozenset({"source_files"}),  # Provided by pipeline, not a plugin
        ))

        # Should NOT raise — source_files comes from pipeline initialization
        ordered = reg.resolve_order()
        assert len(ordered) == 1

    def test_list_plugins(self):
        """list_plugins should return summary dicts."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(name="alpha"))
        reg.register(DummyPlugin(name="beta"))

        info = reg.list_plugins()
        assert len(info) == 2
        names = {p["name"] for p in info}
        assert names == {"alpha", "beta"}
        assert "capability" in info[0]
        assert "enabled" in info[0]

    def test_clear(self):
        """Clear should empty the registry."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(name="a"))
        reg.register(DummyPlugin(name="b"))
        assert reg.count == 2

        reg.clear()
        assert reg.count == 0

    def test_discover_returns_zero_with_no_entry_points(self):
        """Discover should return 0 when no plugins are installed."""
        reg = PluginRegistry()
        count = reg.discover()
        # No third-party plugins installed, so should be 0
        assert count == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Event Bus Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEventBus:
    """Test the event bus pub/sub system."""

    def test_emit_and_receive(self):
        """Basic emit/receive."""
        bus = EventBus()
        received = []

        bus.on("test.event", lambda e: received.append(e))
        bus.emit(Event(name="test.event", source="test"))

        assert len(received) == 1
        assert received[0].name == "test.event"

    def test_wildcard_listener(self):
        """Wildcard 'stage.*' should match all stage events."""
        bus = EventBus()
        received = []

        bus.on("stage.*", lambda e: received.append(e.name))
        bus.emit(Event(name="stage.start"))
        bus.emit(Event(name="stage.end"))
        bus.emit(Event(name="pipeline.start"))  # Should NOT match

        assert received == ["stage.start", "stage.end"]

    def test_global_listener(self):
        """Listener with no filter should receive all events."""
        bus = EventBus()
        received = []

        bus.on(callback=lambda e: received.append(e.name))
        bus.emit(Event(name="a"))
        bus.emit(Event(name="b"))
        bus.emit(Event(name="c"))

        assert len(received) == 3

    def test_pipeline_event_enum(self):
        """PipelineEvent enum values should work as filters."""
        bus = EventBus()
        received = []

        bus.on(PipelineEvent.STAGE_END, lambda e: received.append(e))
        bus.emit(Event(name=PipelineEvent.STAGE_END.value))
        bus.emit(Event(name=PipelineEvent.STAGE_START.value))  # No match

        assert len(received) == 1

    def test_priority_ordering(self):
        """Listeners should fire in priority order."""
        bus = EventBus()
        order = []

        bus.on("test", lambda e: order.append("last"), priority=EventPriority.LAST)
        bus.on("test", lambda e: order.append("first"), priority=EventPriority.FIRST)
        bus.on("test", lambda e: order.append("normal"), priority=EventPriority.NORMAL)

        bus.emit(Event(name="test"))
        assert order == ["first", "normal", "last"]

    def test_event_cancel(self):
        """Cancelling an event should stop subsequent listeners."""
        bus = EventBus()
        order = []

        def canceller(e):
            order.append("canceller")
            e.cancel()

        bus.on("test", canceller, priority=EventPriority.FIRST)
        bus.on("test", lambda e: order.append("should-not-run"), priority=EventPriority.NORMAL)

        bus.emit(Event(name="test"))
        assert order == ["canceller"]

    def test_listener_error_doesnt_propagate(self):
        """Errors in listeners should be logged, not propagated."""
        bus = EventBus()
        received = []

        bus.on("test", lambda e: 1 / 0, priority=EventPriority.FIRST)  # Raises
        bus.on("test", lambda e: received.append("ok"), priority=EventPriority.NORMAL)

        # Should not raise
        bus.emit(Event(name="test"))
        assert received == ["ok"]

    def test_off_by_callback(self):
        """Remove listener by callback reference."""
        bus = EventBus()
        received = []

        def handler(e):
            received.append(e.name)

        bus.on("test", handler)
        bus.emit(Event(name="test"))
        assert len(received) == 1

        removed = bus.off(callback=handler)
        assert removed == 1

        bus.emit(Event(name="test"))
        assert len(received) == 1  # No new events

    def test_off_by_name(self):
        """Remove listener by name."""
        bus = EventBus()
        received = []

        bus.on("test", lambda e: received.append(1), name="my-listener")
        bus.emit(Event(name="test"))
        assert len(received) == 1

        bus.off(name="my-listener")
        bus.emit(Event(name="test"))
        assert len(received) == 1

    def test_decorator_syntax(self):
        """Event bus should support @bus.on() decorator syntax."""
        bus = EventBus()
        received = []

        @bus.on("test")
        def handler(event):
            received.append(event.name)

        bus.emit(Event(name="test"))
        assert received == ["test"]

    def test_stage_event(self):
        """StageEvent subclass should carry stage-specific data."""
        bus = EventBus()
        received = []

        bus.on(PipelineEvent.STAGE_END, lambda e: received.append(e))

        bus.emit(StageEvent(
            name=PipelineEvent.STAGE_END.value,
            source="filter-dat",
            stage_name="filter-dat",
            files_processed=42,
            duration=1.5,
        ))

        assert len(received) == 1
        evt = received[0]
        assert isinstance(evt, StageEvent)
        assert evt.stage_name == "filter-dat"
        assert evt.files_processed == 42

    def test_file_event(self):
        """FileEvent should carry file operation data."""
        evt = FileEvent(
            name=PipelineEvent.FILE_WRITE.value,
            input_path=Path("/tmp/rom.bin"),
            output_path=Path("/tmp/rom.chd"),
            file_size=1024,
        )
        assert evt.input_path == Path("/tmp/rom.bin")
        assert evt.file_size == 1024

    def test_cache_event(self):
        """CacheEvent should carry cache data."""
        evt = CacheEvent(
            name=PipelineEvent.CACHE_HIT.value,
            cache_key="abc123",
            saved_bytes=5_000_000,
        )
        assert evt.cache_key == "abc123"
        assert evt.saved_bytes == 5_000_000

    def test_clear(self):
        """Clear should remove all listeners."""
        bus = EventBus()
        bus.on("a", lambda e: None)
        bus.on("b", lambda e: None)
        assert bus.listener_count == 2

        bus.clear()
        assert bus.listener_count == 0

    def test_emit_returns_event(self):
        """Emit should return the (possibly modified) event."""
        bus = EventBus()
        bus.on("test", lambda e: e.metadata.update({"enriched": True}))

        event = bus.emit(Event(name="test"))
        assert event.metadata.get("enriched") is True


# ═══════════════════════════════════════════════════════════════════════════════
# Stage Adapter Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestStageAdapter:
    """Test the Stage-to-Plugin adapter."""

    def test_adapter_satisfies_protocol(self):
        """StageAdapter should satisfy the Plugin protocol."""
        stage = DummyStage("My Stage")
        adapter = StageAdapter(stage, capability=PluginCapability.FILTER)
        assert isinstance(adapter, Plugin)

    def test_adapter_execute(self):
        """Adapter should delegate execute to wrapped stage."""
        stage = DummyStage("My Stage")
        adapter = StageAdapter(stage, capability=PluginCapability.FILTER)
        ctx = make_context()

        result = adapter.execute(ctx)
        assert result.status == StageStatus.SUCCESS
        assert stage.executed is True

    def test_adapter_meta(self):
        """Adapter should generate correct metadata."""
        stage = DummyStage("Filter DAT")
        adapter = StageAdapter(
            stage,
            capability=PluginCapability.FILTER,
            requires=frozenset({"source_files"}),
            provides=frozenset({"matched_files"}),
        )

        assert adapter.meta.name == "filter-dat"
        assert adapter.meta.capability == PluginCapability.FILTER
        assert "source_files" in adapter.meta.requires
        assert "matched_files" in adapter.meta.provides

    def test_adapter_should_skip(self):
        """Adapter should delegate should_skip."""
        stage = DummyStage("Skip Test")
        stage.should_skip = lambda ctx: True  # Override

        adapter = StageAdapter(stage, capability=PluginCapability.FILTER)
        ctx = make_context()
        assert adapter.should_skip(ctx) is True

    def test_adapter_validate(self):
        """Adapter should delegate validate_context."""
        stage = DummyStage("Validate Test")
        stage.validate_context = lambda ctx: "missing dat_file"

        adapter = StageAdapter(stage, capability=PluginCapability.FILTER)
        ctx = make_context()
        assert adapter.validate(ctx) == "missing dat_file"

    def test_adapter_exposes_underlying_stage(self):
        """Should be able to access the wrapped stage."""
        stage = DummyStage("Inner")
        adapter = StageAdapter(stage, capability=PluginCapability.FILTER)
        assert adapter.stage is stage

    def test_adapter_repr(self):
        """repr should be informative."""
        stage = DummyStage("Test Stage")
        adapter = StageAdapter(stage, capability=PluginCapability.COMPRESS)
        r = repr(adapter)
        assert "Test Stage" in r
        assert "COMPRESS" in r


class TestStageNameConversion:
    """Test the name conversion utility."""

    def test_simple_names(self):
        assert _stage_name_to_plugin_name("Filter DAT") == "filter-dat"
        assert _stage_name_to_plugin_name("Compress CHD") == "compress-chd"
        assert _stage_name_to_plugin_name("Extract Archive") == "extract-archive"

    def test_camel_case(self):
        assert _stage_name_to_plugin_name("FilterDAT") == "filter-dat"
        assert _stage_name_to_plugin_name("CompressCHD") == "compress-chd"

    def test_underscores(self):
        assert _stage_name_to_plugin_name("apply_lists") == "apply-lists"

    def test_already_kebab(self):
        assert _stage_name_to_plugin_name("filter-dat") == "filter-dat"

    def test_multiple_spaces(self):
        assert _stage_name_to_plugin_name("Create  M3U  Files") == "create-m3u-files"


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPluginIntegration:
    """Integration tests combining registry, events, and adapter."""

    def test_register_adapted_stages_and_resolve(self):
        """Wrap stages as plugins, register, and resolve order."""
        reg = PluginRegistry()

        # Simulate wrapping existing stages
        filter_plugin = StageAdapter(
            DummyStage("Filter DAT"),
            capability=PluginCapability.FILTER,
            requires=frozenset({"source_files", "dat_file"}),
            provides=frozenset({"matched_files", "file_md5s"}),
            priority=10,
        )
        extract_plugin = StageAdapter(
            DummyStage("Extract Archive"),
            capability=PluginCapability.EXTRACT,
            requires=frozenset({"matched_files"}),
            provides=frozenset({"extracted_files"}),
        )
        compress_plugin = StageAdapter(
            DummyStage("Compress CHD"),
            capability=PluginCapability.COMPRESS,
            requires=frozenset({"extracted_files"}),
            provides=frozenset({"compressed_files"}),
        )
        organize_plugin = StageAdapter(
            DummyStage("Organize"),
            capability=PluginCapability.ORGANIZE,
            requires=frozenset({"compressed_files"}),
            provides=frozenset({"organized_files"}),
        )

        reg.register(organize_plugin)
        reg.register(filter_plugin)
        reg.register(compress_plugin)
        reg.register(extract_plugin)

        # Resolve should produce correct order regardless of registration order
        ordered = reg.resolve_order()
        names = [p.meta.name for p in ordered]
        assert names == ["filter-dat", "extract-archive", "compress-chd", "organize"]

    def test_event_bus_with_plugin_execution(self):
        """Run a plugin and emit events around it."""
        bus = EventBus()
        events_log = []

        bus.on("stage.*", lambda e: events_log.append(e.name))

        plugin = DummyPlugin(name="test-filter")
        ctx = make_context()

        # Simulate pipeline executing a plugin with events
        bus.emit(StageEvent(
            name=PipelineEvent.STAGE_START.value,
            source=plugin.meta.name,
            stage_name=plugin.meta.name,
        ))
        result = plugin.execute(ctx)
        bus.emit(StageEvent(
            name=PipelineEvent.STAGE_END.value,
            source=plugin.meta.name,
            stage_name=plugin.meta.name,
            files_processed=result.files_processed,
        ))

        assert events_log == ["stage.start", "stage.end"]
        assert plugin.execute_count == 1

    def test_full_pipeline_simulation(self):
        """Simulate a complete pipeline: register → resolve → execute with events."""
        reg = PluginRegistry()
        bus = EventBus()
        execution_log = []

        # Track execution order
        bus.on(PipelineEvent.STAGE_START, lambda e: execution_log.append(f"start:{e.source}"))
        bus.on(PipelineEvent.STAGE_END, lambda e: execution_log.append(f"end:{e.source}"))

        # Register plugins
        plugins = [
            DummyPlugin(
                name="compress",
                capability=PluginCapability.COMPRESS,
                requires=frozenset({"extracted"}),
                provides=frozenset({"compressed"}),
            ),
            DummyPlugin(
                name="filter",
                capability=PluginCapability.FILTER,
                provides=frozenset({"matched"}),
            ),
            DummyPlugin(
                name="extract",
                capability=PluginCapability.EXTRACT,
                requires=frozenset({"matched"}),
                provides=frozenset({"extracted"}),
            ),
        ]
        for p in plugins:
            reg.register(p)

        # Resolve order
        ordered = reg.resolve_order()
        assert [p.meta.name for p in ordered] == ["filter", "extract", "compress"]

        # Execute
        ctx = make_context()
        for plugin in ordered:
            bus.emit(StageEvent(
                name=PipelineEvent.STAGE_START.value,
                source=plugin.meta.name,
            ))
            plugin.execute(ctx)
            bus.emit(StageEvent(
                name=PipelineEvent.STAGE_END.value,
                source=plugin.meta.name,
            ))

        assert execution_log == [
            "start:filter", "end:filter",
            "start:extract", "end:extract",
            "start:compress", "end:compress",
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# Catalog Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCatalog:
    """Test the built-in plugin catalog."""

    def test_all_contracts_have_required_fields(self):
        """Every contract should have capability and description."""
        for name, contract in STAGE_CONTRACTS.items():
            assert "capability" in contract, f"{name} missing capability"
            assert isinstance(contract["capability"], PluginCapability), (
                f"{name} capability is not PluginCapability"
            )
            assert "description" in contract, f"{name} missing description"

    def test_all_contracts_have_valid_requires_provides(self):
        """requires and provides should be frozensets of strings."""
        for name, contract in STAGE_CONTRACTS.items():
            req = contract.get("requires", frozenset())
            prov = contract.get("provides", frozenset())
            assert isinstance(req, frozenset), f"{name} requires is not frozenset"
            assert isinstance(prov, frozenset), f"{name} provides is not frozenset"
            for field in req:
                assert isinstance(field, str), f"{name} has non-str require: {field}"
            for field in prov:
                assert isinstance(field, str), f"{name} has non-str provide: {field}"

    def test_contract_count(self):
        """Should have contracts for all known stages."""
        assert len(STAGE_CONTRACTS) >= 21, (
            f"Expected at least 21 stage contracts, got {len(STAGE_CONTRACTS)}"
        )

    def test_get_contract(self):
        """get_contract should return correct contract."""
        contract = get_contract("filter-dat")
        assert contract is not None
        assert contract["capability"] == PluginCapability.FILTER

    def test_get_contract_unknown(self):
        """get_contract should return None for unknown."""
        assert get_contract("nonexistent") is None

    def test_list_contracts(self):
        """list_contracts should return all contracts."""
        all_contracts = list_contracts()
        assert len(all_contracts) == len(STAGE_CONTRACTS)
        assert "filter-dat" in all_contracts

    def test_create_plugin_no_arg_stage(self):
        """create_plugin should work for stages with no constructor args."""
        plugin = create_plugin("filter-dat")
        assert isinstance(plugin, StageAdapter)
        assert isinstance(plugin, Plugin)
        assert plugin.meta.name == "filter-dat"
        assert plugin.meta.capability == PluginCapability.FILTER

    def test_create_plugin_unknown_raises(self):
        """create_plugin should raise for unknown stage name."""
        with pytest.raises(ValueError, match="Unknown plugin"):
            create_plugin("nonexistent-stage")

    def test_register_builtin_plugins(self):
        """register_builtin_plugins should register no-arg stages."""
        reg = PluginRegistry()
        count = register_builtin_plugins(reg)
        assert count >= 9  # At least the no-arg stages
        assert reg.get("filter-dat") is not None
        assert reg.get("extract-archive") is not None
        assert reg.get("organize") is not None

    def test_register_builtin_with_config(self):
        """register_builtin_plugins should accept stage configs."""
        reg = PluginRegistry()
        # CachePreCheckStage needs cache_manager and output_format
        count = register_builtin_plugins(reg, stage_configs={
            "cache-pre-check": {"cache_manager": MagicMock(), "output_format": "7z"},
        })
        # Should register the configured stage plus the no-arg ones
        assert reg.get("cache-pre-check") is not None

    def test_catalog_plugins_satisfy_protocol(self):
        """All catalog-created plugins should satisfy Plugin protocol."""
        for name in ["filter-dat", "filter-1g1r", "extract-archive", "organize"]:
            plugin = create_plugin(name)
            assert isinstance(plugin, Plugin), f"{name} doesn't satisfy Plugin protocol"

    def test_all_capabilities_represented(self):
        """The catalog should cover all major capability categories."""
        capabilities = {c["capability"] for c in STAGE_CONTRACTS.values()}
        # Must have at least FILTER, EXTRACT, COMPRESS, ORGANIZE, METADATA
        assert PluginCapability.FILTER in capabilities
        assert PluginCapability.EXTRACT in capabilities
        assert PluginCapability.COMPRESS in capabilities
        assert PluginCapability.ORGANIZE in capabilities
        assert PluginCapability.METADATA in capabilities


# ═══════════════════════════════════════════════════════════════════════════════
# Plugin Pipeline Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPluginPipeline:
    """Test the plugin-aware pipeline executor."""

    def test_empty_pipeline(self):
        """Empty pipeline should succeed with no results."""
        pipeline = PluginPipeline(plugins=[])
        ctx = make_context()
        results = pipeline.execute(ctx)
        assert results == []

    def test_single_plugin(self):
        """Pipeline with one plugin should execute it."""
        plugin = DummyPlugin(name="test")
        pipeline = PluginPipeline(plugins=[plugin])
        ctx = make_context()
        results = pipeline.execute(ctx)

        assert len(results) == 1
        assert results[0].status == StageStatus.SUCCESS
        assert plugin.execute_count == 1

    def test_multiple_plugins_in_order(self):
        """Plugins should execute in order."""
        order = []
        
        class OrderPlugin:
            def __init__(self, name):
                self._meta = PluginMeta(name=name, capability=PluginCapability.FILTER)
            @property
            def meta(self): return self._meta
            def execute(self, ctx):
                order.append(self._meta.name)
                return StageResult(status=StageStatus.SUCCESS, message=f"{self._meta.name} done")
            def should_skip(self, ctx): return False
            def validate(self, ctx): return None

        pipeline = PluginPipeline(plugins=[
            OrderPlugin("first"),
            OrderPlugin("second"),
            OrderPlugin("third"),
        ])
        ctx = make_context()
        results = pipeline.execute(ctx)

        assert len(results) == 3
        assert order == ["first", "second", "third"]

    def test_pipeline_stops_on_failure(self):
        """Pipeline should stop executing after a failure."""
        class FailPlugin:
            def __init__(self, name):
                self._meta = PluginMeta(name=name)
            @property
            def meta(self): return self._meta
            def execute(self, ctx):
                return StageResult(status=StageStatus.FAILED, message=f"{self._meta.name} failed")
            def should_skip(self, ctx): return False
            def validate(self, ctx): return None

        pipeline = PluginPipeline(plugins=[
            DummyPlugin(name="works"),
            FailPlugin("breaks"),
            DummyPlugin(name="never-runs"),
        ])
        ctx = make_context()
        results = pipeline.execute(ctx)

        assert len(results) == 2  # Third plugin never ran
        assert results[0].status == StageStatus.SUCCESS
        assert results[1].status == StageStatus.FAILED

    def test_pipeline_handles_exceptions(self):
        """Pipeline should catch exceptions and create failure results."""
        class ExplodePlugin:
            _meta = PluginMeta(name="exploder")
            @property
            def meta(self): return self._meta
            def execute(self, ctx): raise RuntimeError("boom")
            def should_skip(self, ctx): return False
            def validate(self, ctx): return None

        pipeline = PluginPipeline(plugins=[ExplodePlugin()])
        ctx = make_context()
        results = pipeline.execute(ctx)

        assert len(results) == 1
        assert results[0].status == StageStatus.FAILED
        assert "boom" in str(results[0].error)

    def test_pipeline_skip_plugin(self):
        """Plugins that return should_skip=True should be skipped."""
        class SkipPlugin:
            _meta = PluginMeta(name="skipper")
            @property
            def meta(self): return self._meta
            def execute(self, ctx):
                raise AssertionError("Should not be called!")
            def should_skip(self, ctx): return True
            def validate(self, ctx): return None

        pipeline = PluginPipeline(plugins=[SkipPlugin()])
        ctx = make_context()
        results = pipeline.execute(ctx)

        assert len(results) == 1
        assert results[0].status == StageStatus.SKIPPED

    def test_pipeline_emits_events(self):
        """Pipeline should emit lifecycle events."""
        bus = EventBus()
        events = []
        bus.on(callback=lambda e: events.append(e.name))

        pipeline = PluginPipeline(
            plugins=[DummyPlugin(name="test")],
            event_bus=bus,
        )
        ctx = make_context()
        pipeline.execute(ctx)

        event_names = [e for e in events]
        assert PipelineEvent.PIPELINE_START.value in event_names
        assert PipelineEvent.STAGE_START.value in event_names
        assert PipelineEvent.STAGE_END.value in event_names
        assert PipelineEvent.PIPELINE_END.value in event_names

    def test_pipeline_from_registry(self):
        """Pipeline should work with registry-resolved plugins."""
        reg = PluginRegistry()
        reg.register(DummyPlugin(
            name="filter",
            capability=PluginCapability.FILTER,
            provides=frozenset({"matched"}),
        ))
        reg.register(DummyPlugin(
            name="extract",
            capability=PluginCapability.EXTRACT,
            requires=frozenset({"matched"}),
        ))

        pipeline = PluginPipeline(registry=reg)
        assert len(pipeline.plugins) == 2

    def test_pipeline_add_plugin(self):
        """add_plugin should append to the pipeline."""
        pipeline = PluginPipeline(plugins=[])
        pipeline.add_plugin(DummyPlugin(name="late-arrival"))
        assert len(pipeline.plugins) == 1

    def test_pipeline_event_bus_accessible(self):
        """Event bus should be accessible for external listeners."""
        bus = EventBus()
        pipeline = PluginPipeline(plugins=[], event_bus=bus)
        assert pipeline.event_bus is bus

    def test_pipeline_with_adapted_stages(self):
        """Pipeline should work with StageAdapter-wrapped stages."""
        stage = DummyStage("Test Stage")
        adapter = StageAdapter(stage, capability=PluginCapability.FILTER)

        pipeline = PluginPipeline(plugins=[adapter])
        ctx = make_context()
        results = pipeline.execute(ctx)

        assert len(results) == 1
        assert results[0].status == StageStatus.SUCCESS
        assert stage.executed is True
