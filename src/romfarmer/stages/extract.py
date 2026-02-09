"""Extract archive stage for disc-based and cartridge systems."""

import hashlib
import os
import re
import shutil
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from ..config.models import ExtractionType
from .base import Stage, StageContext, StageResult, StageStatus
from .disc_models import CueSheet, IsoDisc

# Standard timestamp for all extracted files (No-Intro/TOSEC standard)
# December 24, 1996 23:32:00 UTC - used for reproducible builds
STANDARD_TIMESTAMP = time.mktime((1996, 12, 24, 23, 32, 0, 0, 0, 0))


class ExtractArchiveStage(Stage):
    """Extract ZIP archives containing disc images or cartridge ROMs.
    
    Supports two extraction modes:
    - DISC: Extract CUE/BIN or ISO files for disc-based systems (Saturn, PS1, PSP, PS2)
    - CARTRIDGE: Extract ROM files for cartridge systems (NES, SNES, Virtual Boy, etc.)
    
    For cartridge extraction, calculates MD5 of extracted ROM for metadata matching.
    """
    
    def __init__(self):
        """Initialize extraction stage."""
        super().__init__("Extract Archives")
        self.disc_pattern = re.compile(r'\(Disc (\d+)\)', re.IGNORECASE)
        # ROM file extensions for cartridge systems
        self.rom_extensions = {
            '.nes', '.sfc', '.smc', '.vb', '.gb', '.gbc', '.gba',
            '.smd', '.bin', '.gen', '.md', '.32x', '.gg', '.sms',
            '.n64', '.v64', '.z64', '.j64', '.nds', '.3ds',
            '.ws', '.wsc',  # WonderSwan and WonderSwan Color
            '.rom', '.mx1', '.mx2',  # MSX, MSX1, MSX2
            '.sg',  # SG-1000
            '.fds',  # Famicom Disk System
            '.lnx', '.lyx',  # Atari Lynx
            '.a26', '.a52', '.a78',  # Atari 2600, 5200, 7800
            '.jag',  # Atari Jaguar
            '.pce', '.sgx',  # PC Engine / SuperGrafx
            '.vec',  # Vectrex
            '.col',  # ColecoVision
            '.ngp', '.ngc',  # Neo Geo Pocket / Color
            '.int',  # Intellivision
            '.min',  # Pokemon Mini
        }
    
    def should_skip(self, context: StageContext) -> bool:
        """Skip if system doesn't require extraction.
        
        Args:
            context: Stage context
            
        Returns:
            True if should skip
        """
        # Skip if no files to extract
        if not context.filtered_files:
            return True
        
        # Skip if extraction not enabled
        if not context.platform_config.extraction.enabled:
            return True
        
        return False
    
    def execute(self, context: StageContext) -> StageResult:
        """Extract archives based on extraction type.
        
        Args:
            context: Stage context
            
        Returns:
            Stage result
        """
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="Extraction not needed for this system",
            )
        
        extraction_type = context.platform_config.extraction.type
        
        if extraction_type == ExtractionType.DISC:
            return self._extract_disc_archives(context)
        elif extraction_type == ExtractionType.CARTRIDGE:
            return self._extract_cartridge_archives(context)
        elif extraction_type == ExtractionType.XISO:
            # XISO extraction: extract ISO from ZIP first, ConvertXISOStage does the conversion
            return self._extract_disc_archives(context)
        else:
            return StageResult(
                status=StageStatus.SKIPPED,
                message=f"Unsupported extraction type: {extraction_type}",
            )
    
    def _extract_disc_archives(self, context: StageContext) -> StageResult:
        """Extract disc archives (CUE/BIN or ISO) and detect multi-disc games.
        
        Supports both:
        - CUE/BIN pairs for CD-based systems (Saturn, PS1, SegaCD, etc.)
        - ISO files for UMD/DVD systems (PSP, PS2, etc.)
        
        Args:
            context: Stage context
            
        Returns:
            Stage result
        """
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="Extraction not needed for this system",
            )
        
        self._log_info(context, f"Extracting {len(context.filtered_files)} archives...")
        
        extracted_discs: List[Union[CueSheet, IsoDisc]] = []
        disc_groups: Dict[str, List[Union[CueSheet, IsoDisc]]] = {}
        failed = 0
        
        for zip_path in context.filtered_files:
            try:
                disc = self._extract_archive(context, zip_path, context.work_dir)
                if disc and disc.is_valid():
                    extracted_discs.append(disc)
                    
                    # Group by base name for multi-disc detection
                    base_name = disc.game_base_name or zip_path.stem
                    if base_name not in disc_groups:
                        disc_groups[base_name] = []
                    disc_groups[base_name].append(disc)
                else:
                    self._log_warning(context, f"Invalid disc in {zip_path.name}")
                    failed += 1
            except Exception as e:
                self._log_error(context, f"Failed to extract {zip_path.name}: {e}")
                failed += 1
        
        # Sort discs within each group
        for base_name, discs in disc_groups.items():
            disc_groups[base_name] = sorted(
                discs,
                key=lambda d: d.disc_number or 0
            )
        
        # Update context - extract the path from either CueSheet or IsoDisc
        context.extracted_files = [
            disc.cue_path if isinstance(disc, CueSheet) else disc.iso_path
            for disc in extracted_discs
        ]
        context.disc_groups = disc_groups
        
        # Build ZIP identity mapping for cache optimization
        # Maps extracted file path -> (crc32, content_size) for pre-check
        for disc in extracted_discs:
            disc_path = disc.cue_path if isinstance(disc, CueSheet) else disc.iso_path
            if disc.source_zip_crc32 and disc.source_zip_content_size:
                context.zip_identity_map[disc_path] = (
                    disc.source_zip_crc32,
                    disc.source_zip_content_size,
                )
        
        # Count multi-disc games
        multi_disc_count = sum(1 for discs in disc_groups.values() if len(discs) > 1)
        
        # Clean up ZIP symlinks from work directory (created by FilterDAT)
        # These are no longer needed after extraction
        for zip_path in context.filtered_files:
            if zip_path.is_symlink() and zip_path.exists():
                try:
                    zip_path.unlink()
                    self._log(context, f"  Cleaned up symlink: {zip_path.name}")
                except Exception as e:
                    self._log_warning(context, f"Failed to remove symlink {zip_path.name}: {e}")
        
        # Determine disc format for logging
        cue_count = sum(1 for d in extracted_discs if isinstance(d, CueSheet))
        iso_count = sum(1 for d in extracted_discs if isinstance(d, IsoDisc))
        
        if cue_count > 0 and iso_count > 0:
            format_info = f"{cue_count} CUE/BIN, {iso_count} ISO"
        elif iso_count > 0:
            format_info = f"{iso_count} ISO files"
        else:
            format_info = f"{cue_count} CUE/BIN"
            
        message = f"Extracted {len(extracted_discs)} discs ({format_info}, {multi_disc_count} multi-disc)"
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=message,
            files_processed=len(context.filtered_files),
            files_matched=len(extracted_discs),
            files_failed=failed,
            details={
                "extracted": [
                    str(disc.cue_path if isinstance(disc, CueSheet) else disc.iso_path)
                    for disc in extracted_discs
                ],
                "disc_groups": {
                    name: [
                        str(d.cue_path if isinstance(d, CueSheet) else d.iso_path)
                        for d in discs
                    ]
                    for name, discs in disc_groups.items()
                },
                "multi_disc_games": multi_disc_count,
                "format": {"cue_count": cue_count, "iso_count": iso_count},
            }
        )
    
    def _extract_cartridge_archives(self, context: StageContext) -> StageResult:
        """Extract cartridge ROM files from archives.
        
        Extracts ROM files (.vb, .nes, .sfc, etc.) from ZIP archives,
        calculates MD5 hash for metadata matching, and preserves files
        for compression stage.
        
        Args:
            context: Stage context
            
        Returns:
            Stage result
        """
        self._log_info(context, f"Extracting {len(context.filtered_files)} cartridge archives...")
        
        extracted_roms: List[Tuple[Path, str]] = []  # (rom_path, md5_hash)
        failed = 0
        
        for zip_path in context.filtered_files:
            try:
                result = self._extract_cartridge_archive(context, zip_path, context.work_dir)
                if result:
                    rom_path, md5_hash = result
                    extracted_roms.append((rom_path, md5_hash))
                else:
                    self._log_warning(context, f"No ROM file found in {zip_path.name}")
                    failed += 1
            except Exception as e:
                self._log_error(context, f"Failed to extract {zip_path.name}: {e}")
                failed += 1
        
        # Update context with extracted ROM paths and MD5 hashes
        context.extracted_files = [rom_path for rom_path, _ in extracted_roms]
        context.rom_md5_map = {rom_path: md5_hash for rom_path, md5_hash in extracted_roms}
        
        # Clean up ZIP symlinks from work directory
        for zip_path in context.filtered_files:
            if zip_path.is_symlink() and zip_path.exists():
                try:
                    zip_path.unlink()
                    self._log(context, f"  Cleaned up symlink: {zip_path.name}")
                except Exception as e:
                    self._log_warning(context, f"Failed to remove symlink {zip_path.name}: {e}")
        
        message = f"Extracted {len(extracted_roms)} ROM files"
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=message,
            files_processed=len(context.filtered_files),
            files_matched=len(extracted_roms),
            files_failed=failed,
            details={
                "extracted": [str(rom_path) for rom_path, _ in extracted_roms],
                "rom_hashes": {str(rom_path): md5_hash for rom_path, md5_hash in extracted_roms},
            }
        )
    
    def _extract_cartridge_archive(
        self, 
        context: StageContext, 
        zip_path: Path, 
        work_dir: Path
    ) -> Optional[Tuple[Path, str]]:
        """Extract a cartridge ROM file from archive and calculate MD5.
        
        Args:
            context: Stage context
            zip_path: Path to ZIP file
            work_dir: Working directory for extraction
            
        Returns:
            Tuple of (rom_path, md5_hash) or None if failed
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Find ROM file by extension
                rom_files = [
                    f for f in zf.namelist()
                    if Path(f).suffix.lower() in self.rom_extensions
                ]
                
                if not rom_files:
                    self._log_warning(context, f"No ROM file found in {zip_path.name}")
                    return None
                
                if len(rom_files) > 1:
                    self._log_warning(
                        context,
                        f"Multiple ROM files in {zip_path.name}, using first: {rom_files[0]}"
                    )
                
                rom_file = rom_files[0]
                
                # Extract ROM file
                rom_data = zf.read(rom_file)
                rom_path = work_dir / Path(rom_file).name
                
                # Write ROM file to work directory
                with open(rom_path, 'wb') as f:
                    f.write(rom_data)
                
                # Set standard timestamp (No-Intro/TOSEC convention)
                os.utime(rom_path, (STANDARD_TIMESTAMP, STANDARD_TIMESTAMP))
                
                # Calculate MD5 hash of ROM data for metadata matching
                md5_hash = hashlib.md5(rom_data).hexdigest()
                
                self._log(context, f"  Extracted {rom_path.name} (MD5: {md5_hash[:8]}...)")
                
                return (rom_path, md5_hash)
                
        except Exception as e:
            self._log_error(context, f"Failed to extract {zip_path.name}: {e}")
            return None
    
    def _extract_archive(self, context: StageContext, zip_path: Path, work_dir: Path) -> Optional[Union[CueSheet, IsoDisc]]:
        """Extract archive and parse disc information.
        
        Supports both CUE/BIN (CD) and ISO (UMD/DVD) formats:
        - First checks for CUE files (Saturn, PS1, SegaCD, etc.)
        - Falls back to ISO files (PSP, PS2, etc.)
        
        Also captures ZIP identity (CRC32 + size) from headers for cache
        pre-check optimization.
        
        Args:
            context: Stage context
            zip_path: Path to ZIP file
            work_dir: Working directory for extraction
            
        Returns:
            CueSheet for CUE/BIN, IsoDisc for ISO, or None if failed
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Capture ZIP identity from the largest file (main content)
                # This is used for cache pre-check (skip extraction if cached)
                zip_crc32 = None
                zip_content_size = None
                largest_size = 0
                
                for info in zf.infolist():
                    if not info.is_dir() and info.file_size > largest_size:
                        largest_size = info.file_size
                        zip_crc32 = format(info.CRC, '08x')
                        zip_content_size = info.file_size
                
                # Extract all files
                zf.extractall(work_dir)
                
                # Normalize timestamps on all extracted files (No-Intro/TOSEC standard)
                for filename in zf.namelist():
                    file_path = work_dir / filename
                    if file_path.exists() and file_path.is_file():
                        os.utime(file_path, (STANDARD_TIMESTAMP, STANDARD_TIMESTAMP))
                
                # First, try to find CUE file (CD-based systems)
                cue_files = [
                    f for f in zf.namelist()
                    if f.lower().endswith('.cue')
                ]
                
                if cue_files:
                    if len(cue_files) > 1:
                        self._log_warning(
                            context,
                            f"Multiple CUE files in {zip_path.name}, using first"
                        )
                    
                    cue_path = work_dir / cue_files[0]
                    disc = self._parse_cue_sheet(cue_path)
                    if disc:
                        disc.source_zip_path = zip_path
                        disc.source_zip_crc32 = zip_crc32
                        disc.source_zip_content_size = zip_content_size
                    return disc
                
                # No CUE found - check for ISO files (UMD/DVD systems like PSP, PS2)
                iso_files = [
                    f for f in zf.namelist()
                    if f.lower().endswith('.iso')
                ]
                
                if iso_files:
                    if len(iso_files) > 1:
                        self._log_warning(
                            context,
                            f"Multiple ISO files in {zip_path.name}, using first"
                        )
                    
                    iso_path = work_dir / iso_files[0]
                    disc = self._parse_iso_disc(iso_path)
                    if disc:
                        disc.source_zip_path = zip_path
                        disc.source_zip_crc32 = zip_crc32
                        disc.source_zip_content_size = zip_content_size
                    return disc
                
                # Neither CUE nor ISO found
                self._log_warning(context, f"No CUE or ISO file found in {zip_path.name}")
                return None
                
        except Exception as e:
            self._log_error(context, f"Failed to extract {zip_path.name}: {e}")
            return None
    
    def _parse_iso_disc(self, iso_path: Path) -> IsoDisc:
        """Parse ISO disc to extract metadata.
        
        Args:
            iso_path: Path to ISO file
            
        Returns:
            IsoDisc with parsed metadata
        """
        # Detect disc number from filename
        disc_number = None
        game_base_name = None
        
        match = self.disc_pattern.search(iso_path.stem)
        if match:
            disc_number = int(match.group(1))
            # Remove disc info from base name
            game_base_name = self.disc_pattern.sub('', iso_path.stem).strip()
        else:
            game_base_name = iso_path.stem
        
        return IsoDisc(
            iso_path=iso_path,
            disc_number=disc_number,
            game_base_name=game_base_name,
        )
    
    def _parse_cue_sheet(self, cue_path: Path) -> CueSheet:
        """Parse CUE sheet to find BIN files.
        
        Args:
            cue_path: Path to CUE file
            
        Returns:
            Parsed CUE sheet
        """
        bin_files: List[Path] = []
        
        # Read CUE file
        with open(cue_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Look for FILE lines: FILE "track.bin" BINARY
                if line.strip().upper().startswith('FILE'):
                    # Extract filename between quotes
                    match = re.search(r'FILE\s+"([^"]+)"', line, re.IGNORECASE)
                    if match:
                        bin_name = match.group(1)
                        bin_path = cue_path.parent / bin_name
                        bin_files.append(bin_path)
        
        # Detect disc number from filename
        disc_number = None
        game_base_name = None
        
        match = self.disc_pattern.search(cue_path.stem)
        if match:
            disc_number = int(match.group(1))
            # Remove disc info from base name
            game_base_name = self.disc_pattern.sub('', cue_path.stem).strip()
        else:
            game_base_name = cue_path.stem
        
        return CueSheet(
            cue_path=cue_path,
            bin_files=bin_files,
            disc_number=disc_number,
            game_base_name=game_base_name,
        )
