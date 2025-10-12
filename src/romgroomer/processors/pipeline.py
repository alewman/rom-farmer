"""Pipeline processor for multi-stage ROM processing."""

import shutil
from pathlib import Path
from typing import Optional

from rich.progress import Progress, TaskID

from .base import BaseProcessor, ProcessedRom, ProcessingError, ProcessingStage
from .profiles import PlatformProfile
from ..models.rom import Rom


class PipelineProcessor(BaseProcessor):
    """Execute a multi-stage processing pipeline.
    
    This is the main processor that orchestrates multiple processing stages
    based on a platform profile. Each stage is executed in order, with the
    output of one stage becoming the input to the next.
    
    Example:
        >>> from romgroomer.processors.stages import ExtractArchiveStage
        >>> from romgroomer.processors.profiles import get_profile
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
    ):
        """Initialize pipeline processor.
        
        Args:
            profile: Platform profile defining the pipeline
            stages: Dictionary mapping stage names to stage instances
        """
        self.profile = profile
        self.stages = stages
    
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
        
        try:
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
                    continue
                
                # Apply stage-specific config
                if stage_name in self.profile.stage_config:
                    stage.configure(self.profile.stage_config[stage_name])
                
                # Execute stage
                current_path = await stage.process(current_path, context)
                context['transformations'].append(stage_name)
            
            # Update final progress
            if progress and task:
                progress.update(
                    task,
                    description="[green]Complete[/green]",
                    completed=len(self.profile.stages),
                )
        
        except Exception as e:
            success = False
            error_msg = str(e)
            current_path = input_path
        
        finally:
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
            metadata=context.get('metadata', {}),
            success=success,
            error=error_msg,
        )
