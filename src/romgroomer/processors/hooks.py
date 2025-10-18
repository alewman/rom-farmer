"""
Hook system for ROM processing pipelines.

This module provides a flexible hook system that allows injecting custom behavior
at various points in the processing pipeline without modifying the core pipeline code.

Hooks enable:
- Hash capture before/after transformations
- Transformation tracking to database
- Custom validation and verification
- Progress monitoring and metrics
- Metadata enrichment from external sources
- Error recovery and fallback strategies

Example Usage:
    >>> from romgroomer.processors.hooks import HookRegistry, Hook, HookContext
    >>> from romgroomer.processors.pipeline import PipelineProcessor
    >>> 
    >>> # Define a custom hook
    >>> class HashCaptureHook(Hook):
    ...     async def before_stage(self, context: HookContext):
    ...         # Calculate hash of input file
    ...         context.metadata['source_hash'] = calculate_hash(context.input_path)
    ...     
    ...     async def after_stage(self, context: HookContext):
    ...         # Calculate hash of output file
    ...         context.metadata['output_hash'] = calculate_hash(context.output_path)
    >>> 
    >>> # Register hooks
    >>> registry = HookRegistry()
    >>> registry.register('hash_capture', HashCaptureHook(), priority=10)
    >>> 
    >>> # Use with pipeline
    >>> processor = PipelineProcessor(profile, stages, hooks=registry)
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class HookPoint(Enum):
    """Points in the pipeline where hooks can be triggered."""
    
    # Pipeline-level hooks
    BEFORE_PIPELINE = "before_pipeline"  # Before any stages run
    AFTER_PIPELINE = "after_pipeline"    # After all stages complete
    ON_ERROR = "on_error"                # When an error occurs
    ON_COMPLETE = "on_complete"          # Always runs at end (error or success)
    
    # Stage-level hooks
    BEFORE_STAGE = "before_stage"        # Before each stage runs
    AFTER_STAGE = "after_stage"          # After each stage completes
    STAGE_ERROR = "stage_error"          # When a stage fails
    STAGE_SKIP = "stage_skip"            # When a stage is skipped
    
    # File operation hooks
    BEFORE_READ = "before_read"          # Before reading input file
    AFTER_READ = "after_read"            # After reading input file
    BEFORE_WRITE = "before_write"        # Before writing output file
    AFTER_WRITE = "after_write"          # After writing output file
    
    # Validation hooks
    VALIDATE_INPUT = "validate_input"    # Validate input before processing
    VALIDATE_OUTPUT = "validate_output"  # Validate output after processing
    VERIFY_INTEGRITY = "verify_integrity"  # Verify file integrity


@dataclass
class HookContext:
    """Context passed to hooks during execution.
    
    Attributes:
        hook_point: Which point in the pipeline triggered the hook
        input_path: Current input file path
        output_path: Current output file path (may be None before processing)
        stage_name: Name of current stage (if applicable)
        pipeline_context: Full pipeline context dict
        rom: ROM metadata from parser
        error: Error that occurred (if hook_point is an error hook)
        metadata: Shared metadata dict for hooks to communicate
        success: Whether the operation was successful
        duration: Time taken for operation (in seconds)
    """
    
    hook_point: HookPoint
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    stage_name: Optional[str] = None
    pipeline_context: dict[str, Any] = field(default_factory=dict)
    rom: Optional[Any] = None
    error: Optional[Exception] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    duration: float = 0.0
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from metadata or pipeline context.
        
        Args:
            key: Key to look up
            default: Default value if key not found
            
        Returns:
            Value from metadata (first) or pipeline context (fallback)
        """
        return self.metadata.get(key, self.pipeline_context.get(key, default))
    
    def set(self, key: str, value: Any) -> None:
        """Set value in metadata for other hooks to access.
        
        Args:
            key: Key to set
            value: Value to store
        """
        self.metadata[key] = value


class Hook(ABC):
    """Base class for pipeline hooks.
    
    Subclass this and override the hook methods you need. Each method
    is called at a specific point in the pipeline execution.
    
    All hook methods are optional - only implement what you need.
    """
    
    def __init__(self, name: Optional[str] = None):
        """Initialize hook.
        
        Args:
            name: Optional name for the hook (defaults to class name)
        """
        self.name = name or self.__class__.__name__
    
    # Pipeline-level hooks
    
    async def before_pipeline(self, context: HookContext) -> None:
        """Called before pipeline starts processing.
        
        Use this for:
        - Initial validation
        - Resource setup
        - Logging pipeline start
        
        Args:
            context: Hook context with pipeline information
        """
        pass
    
    async def after_pipeline(self, context: HookContext) -> None:
        """Called after pipeline completes successfully.
        
        Use this for:
        - Final validation
        - Resource cleanup
        - Success logging
        
        Args:
            context: Hook context with results
        """
        pass
    
    async def on_error(self, context: HookContext) -> None:
        """Called when an error occurs in the pipeline.
        
        Use this for:
        - Error logging
        - Cleanup after failure
        - Error recovery attempts
        
        Args:
            context: Hook context with error information
        """
        pass
    
    async def on_complete(self, context: HookContext) -> None:
        """Called when pipeline completes (success or failure).
        
        This ALWAYS runs, even if errors occurred. Use this for:
        - Final cleanup
        - Resource release
        - Metrics recording
        
        Args:
            context: Hook context with completion status
        """
        pass
    
    # Stage-level hooks
    
    async def before_stage(self, context: HookContext) -> None:
        """Called before each stage runs.
        
        Use this for:
        - Hash calculation of input
        - Stage-specific validation
        - Progress updates
        
        Args:
            context: Hook context with stage information
        """
        pass
    
    async def after_stage(self, context: HookContext) -> None:
        """Called after each stage completes successfully.
        
        Use this for:
        - Hash calculation of output
        - Transformation tracking
        - Intermediate validation
        
        Args:
            context: Hook context with stage results
        """
        pass
    
    async def stage_error(self, context: HookContext) -> None:
        """Called when a stage fails.
        
        Use this for:
        - Stage-specific error handling
        - Fallback attempts
        - Error logging with stage context
        
        Args:
            context: Hook context with error information
        """
        pass
    
    async def stage_skip(self, context: HookContext) -> None:
        """Called when a stage is skipped (can't process input).
        
        Use this for:
        - Logging skipped stages
        - Conditional processing decisions
        
        Args:
            context: Hook context with skip reason
        """
        pass
    
    # File operation hooks
    
    async def before_read(self, context: HookContext) -> None:
        """Called before reading an input file.
        
        Use this for:
        - File existence validation
        - Permissions check
        - Pre-read metrics
        
        Args:
            context: Hook context with file information
        """
        pass
    
    async def after_read(self, context: HookContext) -> None:
        """Called after reading an input file.
        
        Use this for:
        - Content validation
        - Corruption detection
        - Read metrics
        
        Args:
            context: Hook context with read results
        """
        pass
    
    async def before_write(self, context: HookContext) -> None:
        """Called before writing an output file.
        
        Use this for:
        - Disk space check
        - Output validation
        - Pre-write backup
        
        Args:
            context: Hook context with write information
        """
        pass
    
    async def after_write(self, context: HookContext) -> None:
        """Called after writing an output file.
        
        Use this for:
        - Write verification
        - Permissions setting
        - Post-write metrics
        
        Args:
            context: Hook context with write results
        """
        pass
    
    # Validation hooks
    
    async def validate_input(self, context: HookContext) -> bool:
        """Validate input file before processing.
        
        Use this for:
        - Format validation
        - Corruption check
        - DAT file verification
        
        Args:
            context: Hook context with input file
            
        Returns:
            True if validation passed, False otherwise
        """
        return True
    
    async def validate_output(self, context: HookContext) -> bool:
        """Validate output file after processing.
        
        Use this for:
        - Format validation
        - Integrity check
        - Size sanity check
        
        Args:
            context: Hook context with output file
            
        Returns:
            True if validation passed, False otherwise
        """
        return True
    
    async def verify_integrity(self, context: HookContext) -> bool:
        """Verify file integrity (hash check, etc.).
        
        Use this for:
        - Hash verification
        - Checksum validation
        - Corruption detection
        
        Args:
            context: Hook context with file information
            
        Returns:
            True if integrity check passed, False otherwise
        """
        return True


@dataclass
class RegisteredHook:
    """A hook registered in the system.
    
    Attributes:
        hook: The hook instance
        priority: Execution priority (lower = earlier)
        enabled: Whether the hook is currently enabled
        hook_points: Specific hook points to trigger (None = all)
    """
    
    hook: Hook
    priority: int = 50
    enabled: bool = True
    hook_points: Optional[set[HookPoint]] = None
    
    def should_trigger(self, hook_point: HookPoint) -> bool:
        """Check if this hook should trigger for a given hook point.
        
        Args:
            hook_point: The hook point to check
            
        Returns:
            True if hook should trigger
        """
        if not self.enabled:
            return False
        
        if self.hook_points is None:
            return True
        
        return hook_point in self.hook_points


class HookRegistry:
    """Registry for managing hooks in the processing pipeline.
    
    Example:
        >>> registry = HookRegistry()
        >>> 
        >>> # Register hooks with different priorities
        >>> registry.register('hash', HashCaptureHook(), priority=10)
        >>> registry.register('transform', TransformationTrackingHook(), priority=20)
        >>> registry.register('validate', ValidationHook(), priority=30)
        >>> 
        >>> # Enable/disable hooks dynamically
        >>> registry.disable('validate')
        >>> registry.enable('validate')
        >>> 
        >>> # Trigger hooks at a specific point
        >>> context = HookContext(hook_point=HookPoint.BEFORE_STAGE, stage_name='extract')
        >>> await registry.trigger(HookPoint.BEFORE_STAGE, context)
    """
    
    def __init__(self):
        """Initialize empty hook registry."""
        self._hooks: dict[str, RegisteredHook] = {}
    
    def register(
        self,
        name: str,
        hook: Hook,
        priority: int = 50,
        hook_points: Optional[list[HookPoint]] = None,
    ) -> None:
        """Register a hook in the system.
        
        Args:
            name: Unique name for the hook
            hook: Hook instance to register
            priority: Execution priority (lower = earlier, default 50)
            hook_points: Specific hook points to trigger (None = all)
        """
        self._hooks[name] = RegisteredHook(
            hook=hook,
            priority=priority,
            enabled=True,
            hook_points=set(hook_points) if hook_points else None,
        )
        logger.debug(f"Registered hook: {name} (priority={priority})")
    
    def unregister(self, name: str) -> None:
        """Unregister a hook from the system.
        
        Args:
            name: Name of hook to unregister
        """
        if name in self._hooks:
            del self._hooks[name]
            logger.debug(f"Unregistered hook: {name}")
    
    def enable(self, name: str) -> None:
        """Enable a registered hook.
        
        Args:
            name: Name of hook to enable
        """
        if name in self._hooks:
            self._hooks[name].enabled = True
            logger.debug(f"Enabled hook: {name}")
    
    def disable(self, name: str) -> None:
        """Disable a registered hook (remains registered but won't trigger).
        
        Args:
            name: Name of hook to disable
        """
        if name in self._hooks:
            self._hooks[name].enabled = False
            logger.debug(f"Disabled hook: {name}")
    
    def get_hooks(self, hook_point: HookPoint) -> list[Hook]:
        """Get all enabled hooks for a specific hook point, sorted by priority.
        
        Args:
            hook_point: The hook point to get hooks for
            
        Returns:
            List of Hook instances sorted by priority
        """
        # Filter hooks that should trigger for this point
        registered = [
            (rh.priority, rh.hook)
            for rh in self._hooks.values()
            if rh.should_trigger(hook_point)
        ]
        
        # Sort by priority (lower = earlier)
        registered.sort(key=lambda x: x[0])
        
        return [hook for _, hook in registered]
    
    async def trigger(self, hook_point: HookPoint, context: HookContext) -> None:
        """Trigger all hooks for a specific hook point.
        
        Hooks are executed in priority order. If a hook raises an exception,
        it is logged but doesn't prevent other hooks from running.
        
        Args:
            hook_point: The hook point to trigger
            context: Context to pass to hooks
        """
        hooks = self.get_hooks(hook_point)
        
        if not hooks:
            return
        
        logger.debug(f"Triggering {len(hooks)} hooks for {hook_point.value}")
        
        # Get the appropriate method for this hook point
        method_name = hook_point.value
        
        for hook in hooks:
            try:
                # Get the method from the hook
                method = getattr(hook, method_name, None)
                if method and callable(method):
                    await method(context)
            except Exception as e:
                logger.error(
                    f"Hook {hook.name} failed at {hook_point.value}: {e}",
                    exc_info=True
                )
    
    def clear(self) -> None:
        """Remove all registered hooks."""
        self._hooks.clear()
        logger.debug("Cleared all hooks")
    
    def list_hooks(self) -> list[tuple[str, bool, int]]:
        """Get list of all registered hooks.
        
        Returns:
            List of (name, enabled, priority) tuples
        """
        return [
            (name, rh.enabled, rh.priority)
            for name, rh in self._hooks.items()
        ]


# Convenience function for creating hook registries with common hooks
def create_default_registry() -> HookRegistry:
    """Create a hook registry with commonly used hooks.
    
    Returns:
        HookRegistry with default hooks registered
    """
    registry = HookRegistry()
    
    # Add default hooks here as they're implemented
    # registry.register('hash_capture', HashCaptureHook(), priority=10)
    # registry.register('transformation_tracking', TransformationTrackingHook(), priority=20)
    # registry.register('progress_monitor', ProgressMonitorHook(), priority=30)
    
    return registry
