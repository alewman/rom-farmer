"""Create M3U playlist files for multi-disc games."""

import re
from pathlib import Path
from typing import Dict, List, Optional

from .base import Stage, StageContext, StageResult, StageStatus
from .disc_models import DiscMetadata


class CreateM3UStage(Stage):
    """Create M3U playlist files for multi-disc games.
    
    For games with multiple discs, creates an M3U file listing all CHD files.
    The M3U file becomes the "primary" file for the game, used in gamelist.xml.
    
    Metadata (title, images, etc.) should always come from Disc 1.
    """
    
    def __init__(self):
        """Initialize M3U creation stage."""
        super().__init__("Create M3U Playlists")
        self.disc_pattern = re.compile(r'\(Disc (\d+)\)', re.IGNORECASE)
    
    def should_skip(self, context: StageContext) -> bool:
        """Skip if no compressed files or multi-disc not enabled.
        
        Args:
            context: Stage context
            
        Returns:
            True if should skip
        """
        if not context.platform_config.multi_disc_handling:
            return True
        
        # Check if we have compressed files OR if CHDs exist in work directory
        # (CHDs might exist from previous runs when CompressCHD skips)
        has_chds = False
        if context.compressed_files:
            has_chds = True
        elif context.work_dir:
            # Scan work directory for existing CHDs
            chd_files = list(context.work_dir.glob("*.chd"))
            has_chds = len(chd_files) > 0
        
        return not has_chds
    
    def execute(self, context: StageContext) -> StageResult:
        """Create M3U files for multi-disc games.
        
        Args:
            context: Stage context
            
        Returns:
            Stage result
        """
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="M3U creation not needed",
            )
        
        # Get list of CHD files to process
        # If compressed_files is empty (CHDs already existed), scan work directory
        chd_files = context.compressed_files
        if not chd_files and context.work_dir:
            chd_files = list(context.work_dir.glob("*.chd"))
            self._log_info(context, f"Found {len(chd_files)} existing CHD files in work directory")
        
        self._log_info(context, f"Analyzing {len(chd_files)} discs for multi-disc games...")
        
        # Group CHD files by base name
        disc_groups = self._group_discs(chd_files)
        
        # Create M3U files for multi-disc games
        m3u_files: List[Path] = []
        disc_metadata: Dict[str, DiscMetadata] = {}
        multi_disc_count = 0
        
        for base_name, discs in disc_groups.items():
            if len(discs) > 1:
                # Multi-disc game - create M3U
                m3u_path = self._create_m3u(context, base_name, discs)
                if m3u_path:
                    m3u_files.append(m3u_path)
                    multi_disc_count += 1
                
                # Create metadata (use first disc)
                metadata = self._create_metadata(base_name, discs, m3u_path)
                disc_metadata[base_name] = metadata
            else:
                # Single-disc game - just create metadata
                metadata = self._create_metadata(base_name, discs, None)
                disc_metadata[base_name] = metadata
        
        # Update context
        context.m3u_files = m3u_files
        context.disc_metadata = disc_metadata
        
        message = f"Created {len(m3u_files)} M3U files for multi-disc games"
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=message,
            files_processed=len(disc_groups),
            files_matched=len(m3u_files),
            details={
                "m3u_files": [str(p) for p in m3u_files],
                "multi_disc_games": multi_disc_count,
                "single_disc_games": len(disc_groups) - multi_disc_count,
                "total_discs": len(context.compressed_files),
            }
        )
    
    def _group_discs(self, chd_files: List[Path]) -> Dict[str, List[Path]]:
        """Group CHD files by base game name.
        
        Args:
            chd_files: List of CHD file paths
            
        Returns:
            Dictionary mapping base name to list of disc paths
        """
        groups: Dict[str, List[Path]] = {}
        
        for chd_path in chd_files:
            # Extract base name without disc number
            base_name = self._get_base_name(chd_path.stem)
            
            if base_name not in groups:
                groups[base_name] = []
            groups[base_name].append(chd_path)
        
        # Sort discs within each group by disc number
        for base_name in groups:
            groups[base_name] = sorted(
                groups[base_name],
                key=lambda p: self._get_disc_number(p.stem)
            )
        
        return groups
    
    def _get_base_name(self, filename: str) -> str:
        """Extract base game name without disc number.
        
        Args:
            filename: Filename (without extension)
            
        Returns:
            Base game name
        """
        # Remove disc info: "Game (USA) (Disc 1)" → "Game (USA)"
        return self.disc_pattern.sub('', filename).strip()
    
    def _get_disc_number(self, filename: str) -> int:
        """Extract disc number from filename.
        
        Args:
            filename: Filename (without extension)
            
        Returns:
            Disc number (1 if not found)
        """
        match = self.disc_pattern.search(filename)
        if match:
            return int(match.group(1))
        return 1
    
    def _create_m3u(self, context: StageContext, base_name: str, discs: List[Path]) -> Optional[Path]:
        """Create M3U playlist file.
        
        Args:
            context: Stage context for logging
            base_name: Base game name
            discs: List of disc CHD paths (already sorted)
            
        Returns:
            Path to created M3U file or None if failed
        """
        try:
            # M3U file in same directory as first disc
            m3u_path = discs[0].parent / f"{base_name}.m3u"
            
            # Write M3U with relative paths
            with open(m3u_path, 'w', encoding='utf-8') as f:
                for disc in discs:
                    # Use just the filename (same directory)
                    f.write(f"{disc.name}\n")
            
            self._log_info(context, f"Created M3U: {m3u_path.name} ({len(discs)} discs)")
            return m3u_path
            
        except Exception as e:
            self._log_error(context, f"Failed to create M3U for {base_name}: {e}")
            return None
    
    def _create_metadata(
        self,
        base_name: str,
        discs: List[Path],
        m3u_path: Optional[Path]
    ) -> DiscMetadata:
        """Create disc metadata for a game.
        
        Args:
            base_name: Base game name
            discs: List of disc CHD paths
            m3u_path: Path to M3U file (None for single-disc)
            
        Returns:
            Disc metadata
        """
        # Extract region from base name (basic heuristic)
        region = None
        if "(USA)" in base_name:
            region = "USA"
        elif "(Europe)" in base_name or "(EU)" in base_name:
            region = "Europe"
        elif "(Japan)" in base_name or "(JP)" in base_name:
            region = "Japan"
        
        # Clean title (remove region tags)
        title = base_name
        for region_tag in ["(USA)", "(Europe)", "(EU)", "(Japan)", "(JP)", "(World)"]:
            title = title.replace(region_tag, "")
        title = title.strip()
        
        return DiscMetadata(
            game_base_name=base_name,
            first_disc_path=discs[0],
            all_discs=discs,
            disc_count=len(discs),
            title=title,
            region=region,
            needs_m3u=len(discs) > 1,
            m3u_path=m3u_path,
            primary_file=m3u_path if m3u_path else discs[0],
        )
