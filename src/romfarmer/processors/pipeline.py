"""Pipeline processor for multi-stage ROM processing."""

import shutil
import time
from pathlib import Path
from typing import Optional

from rich.progress import Progress, TaskID

from .base import BaseProcessor, ProcessedRom, ProcessingError, ProcessingStage
from .hooks import HookRegistry, HookContext, HookPoint
from .profiles import PlatformProfile
from ..models.rom import Rom


class PipelineProcessor(BaseProcessor):
    """Execute a multi-stage processing pipeline.
    
    This is the main processor that orchestrates multiple processing stages
    based on a platform profile. Each stage is executed in order, with the
    output of one stage becoming the input to the next.
    
    Example:
        >>> from romfarmer.processors.stages import ExtractArchiveStage
        >>> from romfarmer.processors.profiles import get_profile
        >>> 
        >>> stages = {
        ...     'extract_archive': ExtractArchiveStage(),
        ... }
        >>> profile = get_profile('nes')
        >>> processor = PipelineProcessor(profile, stages)
        >>> 
        >>> result = await processor.process(
        ...     input_path=Path("Super Mario Bros (USA).zip"),
        ...     output_dir=Path("/roms/nes/"),
        ... )
    """
    
    def __init__(
        self,
        profile: PlatformProfile,
        stages: dict[str, ProcessingStage],
        hooks: Optional[HookRegistry] = None,
    ):
        """Initialize pipeline processor.
        
        Args:
            profile: Platform profile defining the pipeline
            stages: Dictionary mapping stage names to stage instances
            hooks: Optional hook registry for pipeline events
        """
        self.profile = profile
        self.stages = stages
        self.hooks = hooks or HookRegistry()
    
    async def process(
        self,
        input_path: Path,
        output_dir: Path,
        rom: Optional[Rom] = None,
        progress: Optional[Progress] = None,
        task: Optional[TaskID] = None,
        keep_intermediates: bool = False,
    ) -> ProcessedRom:
        """Execute the processing pipeline.
        
        Args:
            input_path: Input file or directory
            output_dir: Output directory
            rom: Optional ROM metadata from parser
            progress: Optional Rich progress bar
            task: Optional progress task ID
            keep_intermediates: Keep temporary files for debugging
            
        Returns:
            ProcessedRom with final output path and metadata
            
        Raises:
            ProcessingError: If any stage fails
        """
        pipeline_start_time = time.time()
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup context shared between stages
        temp_dir = output_dir / ".temp" / input_path.stem
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        context = {
            'rom': rom,
            'temp_dir': temp_dir,
            'output_dir': output_dir,
            'profile': self.profile,
            'transformations': [],
            'keep_intermediates': keep_intermediates,
        }
        
        current_path = input_path
        success = True
        error_msg = None
        error_exception = None
        
        # Create hook context for pipeline
        hook_ctx = HookContext(
            hook_point=HookPoint.BEFORE_PIPELINE,
            input_path=input_path,
            output_path=None,
            pipeline_context=context,
            rom=rom,
        )
        
        try:
            # Trigger BEFORE_PIPELINE hooks
            await self.hooks.trigger(HookPoint.BEFORE_PIPELINE, hook_ctx)
            
            # Validate input
            hook_ctx.hook_point = HookPoint.VALIDATE_INPUT
            await self.hooks.trigger(HookPoint.VALIDATE_INPUT, hook_ctx)
            
            # Execute each stage in order
            for i, stage_name in enumerate(self.profile.stages):
                # Get stage
                stage = self.stages.get(stage_name)
                if not stage:
                    raise ProcessingError(f"Unknown stage: {stage_name}")
                
                # Update progress
                if progress and task:
                    progress.update(
                        task,
                        description=f"[cyan]{stage_name}[/cyan]",
                        completed=i,
                        total=len(self.profile.stages),
                    )
                
                # Check if stage can process current path
                if not stage.can_process(current_path):
                    # Trigger STAGE_SKIP hook
                    hook_ctx.hook_point = HookPoint.STAGE_SKIP
                    hook_ctx.stage_name = stage_name
                    hook_ctx.input_path = current_path
                    await self.hooks.trigger(HookPoint.STAGE_SKIP, hook_ctx)
                    continue
                
                # Apply stage-specific config
                if stage_name in self.profile.stage_config:
                    stage.configure(self.profile.stage_config[stage_name])
                
                # Trigger BEFORE_STAGE hooks
                stage_start_time = time.time()
                hook_ctx.hook_point = HookPoint.BEFORE_STAGE
                hook_ctx.stage_name = stage_name
                hook_ctx.input_path = current_path
                hook_ctx.output_path = None
                await self.hooks.trigger(HookPoint.BEFORE_STAGE, hook_ctx)
                
                try:
                    # Execute stage
                    previous_path = current_path
                    current_path = await stage.process(current_path, context)
                    context['transformations'].append(stage_name)
                    
                    # Trigger AFTER_STAGE hooks
                    stage_duration = time.time() - stage_start_time
                    hook_ctx.hook_point = HookPoint.AFTER_STAGE
                    hook_ctx.output_path = current_path
                    hook_ctx.duration = stage_duration
                    hook_ctx.success = True
                    await self.hooks.trigger(HookPoint.AFTER_STAGE, hook_ctx)
                    
                except Exception as stage_error:
                    # Trigger STAGE_ERROR hooks
                    hook_ctx.hook_point = HookPoint.STAGE_ERROR
                    hook_ctx.error = stage_error
                    hook_ctx.success = False
                    await self.hooks.trigger(HookPoint.STAGE_ERROR, hook_ctx)
                    raise
            
            # Update final progress
            if progress and task:
                progress.update(
                    task,
                    description="[green]Complete[/green]",
                    completed=len(self.profile.stages),
                )
            
            # Validate output
            hook_ctx.hook_point = HookPoint.VALIDATE_OUTPUT
            hook_ctx.output_path = current_path
            await self.hooks.trigger(HookPoint.VALIDATE_OUTPUT, hook_ctx)
            
            # Trigger AFTER_PIPELINE hooks
            pipeline_duration = time.time() - pipeline_start_time
            hook_ctx.hook_point = HookPoint.AFTER_PIPELINE
            hook_ctx.output_path = current_path
            hook_ctx.duration = pipeline_duration
            hook_ctx.success = True
            await self.hooks.trigger(HookPoint.AFTER_PIPELINE, hook_ctx)
        
        except Exception as e:
            success = False
            error_msg = str(e)
            error_exception = e
            current_path = input_path
            
            # Trigger ON_ERROR hooks
            hook_ctx.hook_point = HookPoint.ON_ERROR
            hook_ctx.error = error_exception
            hook_ctx.success = False
            await self.hooks.trigger(HookPoint.ON_ERROR, hook_ctx)
        
        finally:
            # Trigger ON_COMPLETE hooks (always runs)
            pipeline_duration = time.time() - pipeline_start_time
            hook_ctx.hook_point = HookPoint.ON_COMPLETE
            hook_ctx.output_path = current_path if success else None
            hook_ctx.duration = pipeline_duration
            hook_ctx.success = success
            await self.hooks.trigger(HookPoint.ON_COMPLETE, hook_ctx)
            
            # Cleanup temp directory
            if not keep_intermediates:
                shutil.rmtree(temp_dir.parent, ignore_errors=True)
        
        return ProcessedRom(
            original=rom,
            original_path=input_path,
            processed_path=current_path if success else None,
            format=self.profile.output_format if success else "",
            transformations=context['transformations'],
            disc_files=context.get('disc_files', []),
            metadata=hook_ctx.metadata,
            success=success,
            error=error_msg,
        )
