"""Event bus for decoupled pub/sub communication.

Provides a synchronous, priority-based event system that replaces the
disconnected async hook system in processors/hooks.py. Events are the
primary mechanism for cross-cutting concerns (logging, metrics, hash
capture, transformation tracking) without coupling plugins together.

Design:
- Synchronous first (production pipeline is sync)
- Priority-ordered listeners (lower = earlier)
- Type-safe events with dataclass payloads
- Listeners can modify event data (e.g., enrich context)
- Errors in listeners are logged but don't halt the pipeline
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

# Type variable for event subclasses
E = TypeVar("E", bound="Event")


class EventPriority(int, Enum):
    """Listener execution priority (lower = earlier)."""

    FIRST = 0        # System-level (logging, metrics start)
    HIGH = 25        # Validation, pre-checks
    NORMAL = 50      # Default priority
    LOW = 75         # Post-processing, enrichment
    LAST = 100       # Cleanup, final metrics


class PipelineEvent(Enum):
    """Well-known pipeline events.

    These mirror (and unify) the hook points from processors/hooks.py
    but work with the synchronous stage-based pipeline.
    """

    # Pipeline lifecycle
    PIPELINE_START = "pipeline.start"
    PIPELINE_END = "pipeline.end"
    PIPELINE_ERROR = "pipeline.error"

    # Stage lifecycle
    STAGE_START = "stage.start"
    STAGE_END = "stage.end"
    STAGE_SKIP = "stage.skip"
    STAGE_ERROR = "stage.error"

    # File operations
    FILE_READ = "file.read"
    FILE_WRITE = "file.write"
    FILE_EXTRACT = "file.extract"
    FILE_COMPRESS = "file.compress"

    # Validation
    VALIDATE_INPUT = "validate.input"
    VALIDATE_OUTPUT = "validate.output"

    # Cache
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    CACHE_STORE = "cache.store"


@dataclass
class Event:
    """Base event payload.

    All events carry a name and optional metadata. Subclass for
    typed payloads, or use the base class with metadata dict.

    Attributes:
        name: Event name (use PipelineEvent values for well-known events)
        source: Name of the plugin/component that emitted the event
        metadata: Arbitrary key-value data
        cancelled: If True, subsequent listeners won't be called
    """

    name: str
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False

    def cancel(self) -> None:
        """Cancel this event — remaining listeners won't be called."""
        self.cancelled = True


@dataclass
class StageEvent(Event):
    """Event emitted during stage/plugin lifecycle."""

    stage_name: str = ""
    stage_index: int = 0
    total_stages: int = 0
    platform: str = ""
    duration: float = 0.0
    files_processed: int = 0
    error: Optional[Exception] = None


@dataclass
class FileEvent(Event):
    """Event emitted during file operations."""

    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    file_size: int = 0
    hash_md5: Optional[str] = None
    hash_crc32: Optional[str] = None


@dataclass
class CacheEvent(Event):
    """Event emitted during cache operations."""

    cache_key: str = ""
    file_path: Optional[Path] = None
    saved_bytes: int = 0


# Type alias for event listener callbacks
EventListener = Callable[[Event], None]


@dataclass
class _RegisteredListener:
    """Internal: a listener registered on the bus."""

    callback: EventListener
    priority: EventPriority
    event_filter: Optional[str]  # None = all events, or specific event name
    name: str = ""  # For debugging/unregistration


class EventBus:
    """Synchronous, priority-based event bus.

    Example::

        bus = EventBus()

        # Subscribe to all stage events
        def on_stage(event: Event):
            print(f"Stage: {event.name} from {event.source}")

        bus.on("stage.*", on_stage)

        # Subscribe to specific event
        bus.on(PipelineEvent.STAGE_END, lambda e: print(f"Done: {e.source}"))

        # Emit
        bus.emit(StageEvent(
            name=PipelineEvent.STAGE_END.value,
            source="filter-dat",
            stage_name="filter-dat",
            files_processed=42,
        ))
    """

    def __init__(self) -> None:
        self._listeners: List[_RegisteredListener] = []
        self._sorted = True  # Track if we need to re-sort

    def on(
        self,
        event: str | PipelineEvent | None = None,
        callback: Optional[EventListener] = None,
        priority: EventPriority = EventPriority.NORMAL,
        name: str = "",
    ) -> Callable:
        """Register a listener for events.

        Can be used as a method call or decorator::

            # Method call
            bus.on(PipelineEvent.STAGE_END, my_handler)

            # Decorator
            @bus.on(PipelineEvent.STAGE_END)
            def my_handler(event):
                ...

            # Wildcard: listen to all events in a namespace
            bus.on("stage.*", handler)

            # Global: listen to ALL events
            bus.on(callback=handler)

        Args:
            event: Event name, PipelineEvent enum, or glob pattern.
                   None means listen to all events.
            callback: Listener function. If None, returns decorator.
            priority: Execution priority (lower = earlier)
            name: Optional name for the listener (for debugging/removal)

        Returns:
            The callback, or a decorator if callback is None
        """
        event_filter = None
        if event is not None:
            event_filter = event.value if isinstance(event, PipelineEvent) else str(event)

        def _register(fn: EventListener) -> EventListener:
            listener = _RegisteredListener(
                callback=fn,
                priority=priority,
                event_filter=event_filter,
                name=name or getattr(fn, "__qualname__", str(fn)),
            )
            self._listeners.append(listener)
            self._sorted = False
            return fn

        if callback is not None:
            _register(callback)
            return callback

        return _register

    def off(self, callback: Optional[EventListener] = None, name: str = "") -> int:
        """Remove listener(s) by callback reference or name.

        Args:
            callback: Callback to remove (matches by identity)
            name: Listener name to remove (matches all with this name)

        Returns:
            Number of listeners removed
        """
        before = len(self._listeners)
        self._listeners = [
            rl
            for rl in self._listeners
            if not (
                (callback is not None and rl.callback is callback)
                or (name and rl.name == name)
            )
        ]
        return before - len(self._listeners)

    def emit(self, event: Event) -> Event:
        """Emit an event to all matching listeners.

        Listeners are called in priority order. If a listener calls
        event.cancel(), remaining listeners are skipped.

        Errors in listeners are logged but don't propagate.

        Args:
            event: Event to emit

        Returns:
            The event (possibly modified by listeners)
        """
        if not self._sorted:
            self._listeners.sort(key=lambda rl: rl.priority)
            self._sorted = True

        for rl in self._listeners:
            if event.cancelled:
                break

            if not self._matches(rl.event_filter, event.name):
                continue

            try:
                rl.callback(event)
            except Exception as e:
                logger.error(
                    f"Event listener '{rl.name}' failed on '{event.name}': {e}",
                    exc_info=True,
                )

        return event

    def clear(self) -> None:
        """Remove all listeners."""
        self._listeners.clear()
        self._sorted = True

    @property
    def listener_count(self) -> int:
        """Number of registered listeners."""
        return len(self._listeners)

    def _matches(self, pattern: Optional[str], event_name: str) -> bool:
        """Check if an event name matches a listener's filter pattern.

        Supports:
        - None: matches everything
        - Exact match: "stage.start" matches "stage.start"
        - Wildcard suffix: "stage.*" matches "stage.start", "stage.end"

        Args:
            pattern: Filter pattern (None = match all)
            event_name: Event name to check

        Returns:
            True if event matches the pattern
        """
        if pattern is None:
            return True
        if pattern == event_name:
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return event_name.startswith(prefix + ".")
        return False
