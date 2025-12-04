#!/usr/bin/env python3
"""Test hooks integration with PipelineProcessor."""

import asyncio
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from romfarmer.processors.pipeline import PipelineProcessor
from romfarmer.processors.hooks import HookRegistry, HookContext, HookPoint, Hook
from romfarmer.processors.profiles import PlatformProfile
from romfarmer.metadata import MetadataDatabase


class TestHook(Hook):
    """Simple test hook that logs all hook points."""
    
    def __init__(self):
        self.events = []
    
    async def on_before_pipeline(self, context: HookContext):
        self.events.append(('before_pipeline', context.input_path.name))
        print(f"✓ BEFORE_PIPELINE: {context.input_path.name}")
    
    async def on_validate_input(self, context: HookContext):
        self.events.append(('validate_input', context.input_path.name))
        print(f"✓ VALIDATE_INPUT: {context.input_path.name}")
    
    async def on_before_stage(self, context: HookContext):
        self.events.append(('before_stage', context.stage_name))
        print(f"✓ BEFORE_STAGE: {context.stage_name} ({context.input_path.name})")
    
    async def on_after_stage(self, context: HookContext):
        self.events.append(('after_stage', context.stage_name, f"{context.duration:.2f}s"))
        print(f"✓ AFTER_STAGE: {context.stage_name} ({context.output_path.name}) - {context.duration:.2f}s")
    
    async def on_stage_skip(self, context: HookContext):
        self.events.append(('stage_skip', context.stage_name))
        print(f"✓ STAGE_SKIP: {context.stage_name}")
    
    async def on_validate_output(self, context: HookContext):
        self.events.append(('validate_output', context.output_path.name))
        print(f"✓ VALIDATE_OUTPUT: {context.output_path.name}")
    
    async def on_after_pipeline(self, context: HookContext):
        self.events.append(('after_pipeline', f"{context.duration:.2f}s"))
        print(f"✓ AFTER_PIPELINE: {context.output_path.name} - {context.duration:.2f}s")
    
    async def on_complete(self, context: HookContext):
        self.events.append(('complete', context.success))
        print(f"✓ ON_COMPLETE: success={context.success}")


async def test_basic_integration():
    """Test that hooks are triggered correctly."""
    print("\n=== Testing Hooks Integration ===\n")
    
    # Create test hook
    test_hook = TestHook()
    
    # Create hook registry
    registry = HookRegistry()
    registry.register('test', test_hook, priority=10)
    
    # Create simple profile (no actual processing stages)
    profile = PlatformProfile(
        name="test",
        description="Test profile",
        parser_type="test",
        stages=[],
        output_format="test",
    )
    
    # Create processor with hooks
    processor = PipelineProcessor(profile, {}, hooks=registry)
    
    # Create test input
    test_input = Path(__file__)  # Use this file as test input
    test_output = Path("/tmp/test_hooks_output")
    test_output.mkdir(exist_ok=True)
    
    # Process
    result = await processor.process(
        input_path=test_input,
        output_dir=test_output,
        keep_intermediates=True
    )
    
    # Verify hooks were called
    print(f"\n=== Results ===")
    print(f"Success: {result.success}")
    print(f"Events captured: {len(test_hook.events)}")
    print(f"\nEvent sequence:")
    for i, event in enumerate(test_hook.events, 1):
        print(f"  {i}. {event}")
    
    # Verify expected hook points were triggered
    expected_points = [
        'before_pipeline',
        'validate_input',
        'validate_output',
        'after_pipeline',
        'complete',
    ]
    
    actual_points = [e[0] for e in test_hook.events]
    
    print(f"\nExpected hook points: {expected_points}")
    print(f"Actual hook points: {actual_points}")
    
    missing = set(expected_points) - set(actual_points)
    if missing:
        print(f"⚠ Missing hook points: {missing}")
    else:
        print("✓ All expected hook points triggered!")
    
    return result.success


async def test_with_builtin_hooks():
    """Test with built-in hooks that use the database."""
    print("\n=== Testing Built-in Hooks ===\n")
    
    from romfarmer.processors.builtin_hooks import (
        HashCaptureHook,
        TransformationTrackingHook,
        ProgressMonitorHook,
    )
    
    # Setup database
    db_path = Path("/data/emu/rom-farmer-python/metadata/database/romfarmer.db")
    if not db_path.exists():
        print(f"⚠ Database not found at {db_path}")
        return False
    
    db = MetadataDatabase(db_path)
    
    # Create hook registry with built-in hooks
    registry = HookRegistry()
    registry.register('progress', ProgressMonitorHook(), priority=5)
    registry.register('hash', HashCaptureHook(db), priority=10)
    registry.register('track', TransformationTrackingHook(db), priority=20)
    
    # Create profile
    profile = PlatformProfile(
        name="test",
        description="Test profile",
        parser_type="test",
        stages=[],
        output_format="test",
    )
    
    # Create processor
    processor = PipelineProcessor(profile, {}, hooks=registry)
    
    # Process test file
    test_input = Path(__file__)
    test_output = Path("/tmp/test_builtin_hooks")
    test_output.mkdir(exist_ok=True)
    
    result = await processor.process(
        input_path=test_input,
        output_dir=test_output,
    )
    
    print(f"\n=== Results ===")
    print(f"Success: {result.success}")
    print(f"Metadata keys: {list(result.metadata.keys())}")
    
    # Check if hashes were calculated
    if 'source_hashes' in result.metadata:
        hashes = result.metadata['source_hashes']
        print(f"\n✓ Source hashes calculated:")
        for hash_type, hash_value in hashes.items():
            print(f"  {hash_type}: {hash_value}")
    else:
        print("⚠ No source hashes in metadata")
    
    return result.success


if __name__ == '__main__':
    print("Starting hooks integration tests...")
    
    # Test basic integration
    success1 = asyncio.run(test_basic_integration())
    
    # Test with built-in hooks
    success2 = asyncio.run(test_with_builtin_hooks())
    
    if success1 and success2:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠ Some tests failed")
        sys.exit(1)
