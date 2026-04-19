"""Generate gamelist.xml metadata for EmulationStation.

This stage demonstrates how disc metadata from CreateM3UStage is used
to properly handle multi-disc games in the final gamelist.xml.
"""

import os
import shutil
import zipfile  # Added for ZIP handling
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

from .base import Stage, StageContext, StageResult, StageStatus, StagePhase
from .disc_models import DiscMetadata
from ..core.hashing import calculate_md5


class GenerateMetadataStage(Stage):
    PHASE = StagePhase.FINALIZE

    """Generate gamelist.xml for EmulationStation/Batocera.
    
    Key Features:
    - For multi-disc games: Show M3U, hide individual CHDs
    - For single-disc games: Show CHD directly
    - Use first disc metadata for title, image, etc.
    - Pull metadata from database and rehydrate media files
    - Support subdirectories from ApplyListsStage
    - Video optimization: Transcode videos for handheld devices
    """
    
    def __init__(self, metadata_db_path: Optional[Path] = None):
        """Initialize metadata generation stage.
        
        Args:
            metadata_db_path: Path to metadata database (default: metadata/database/romfarmer.db)
        """
        super().__init__("Generate Metadata")
        self.metadata_db_path = metadata_db_path or Path("metadata/database/romfarmer.db")
        self.metadata_db = None
        self.video_converter = None
        self.video_profile = None
        self.image_converter = None
        self.image_profile = None
    
    def should_skip(self, context: StageContext) -> bool:
        """Skip if metadata not enabled for target."""
        target = next(
            (t for t in context.platform_config.targets if t.name == context.target_name),
            None
        )
        return not target or not target.metadata
    
    def execute(self, context: StageContext) -> StageResult:
        """Generate gamelist.xml.
        
        Args:
            context: Stage context
            
        Returns:
            Stage result
        """
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="Metadata generation not enabled",
            )
        
        self._log_info(context, "Generating gamelist.xml...")
        
        # Initialize metadata database connection
        self._init_metadata_db(context)
        
        # Initialize video converter for device-optimized videos
        self._init_video_converter(context)
        
        # Initialize image converter for device-optimized images
        self._init_image_converter(context)
        
        # Create gamelist.xml root
        gamelist = ET.Element("gameList")
        
        # Track files we've already processed
        processed_files = set()
        
        # First, add disc-based games (M3U + hidden individual discs)
        if context.disc_metadata:
            self._add_disc_games(context, gamelist, processed_files)
        
        # Then add any remaining files not in disc_metadata
        # Support various output formats: CHD (disc), 7z/zip (cartridge), RVZ (GameCube/Wii), raw ROMs, etc.
        output_files = []
        patterns = [
            "*.chd", "*.m3u", "*.iso", "*.cso",  # Disc formats
            "*.7z", "*.zip",  # Compressed archives
            "*.rvz", "*.wua",  # GameCube/Wii
            "*.j64", "*.n64", "*.z64", "*.v64",  # N64/Jaguar raw
            "*.gb", "*.gbc", "*.gba",  # Game Boy raw
            "*.nes", "*.sfc", "*.smc",  # NES/SNES raw
            "*.smd", "*.gen", "*.bin", "*.32x",  # Sega raw
            "*.vb",  # Virtual Boy raw
            "*.nds", "*.3ds",  # Nintendo DS/3DS raw
            "*.ws", "*.wsc",  # WonderSwan raw
            "*.pce", "*.sgx",  # PC Engine raw
            "*.a26", "*.a52", "*.a78",  # Atari raw
            "*.lnx", "*.lyx",  # Atari Lynx raw
            "*.col",  # ColecoVision raw
            "*.int",  # Intellivision raw
            "*.vec",  # Vectrex raw
            "*.ngp", "*.ngc",  # Neo Geo Pocket raw
            "*.sg",  # SG-1000 raw
            "*.gg",  # Game Gear raw
            "*.sms",  # Master System raw
            "*.fds",  # Famicom Disk System raw
            "*.mx1", "*.mx2", "*.rom",  # MSX raw
        ]
        # Only collect files directly under output_dir (depth 1).  Any files
        # in subdirectories are hardlinks/symlinks created by organizers (By Genre,
        # Best Games, PlayStation Classic USA, etc.) and must be excluded to avoid
        # duplicate gamelist entries.
        for pattern in patterns:
            for f in context.output_dir.rglob(pattern):
                if f.parent == context.output_dir:
                    output_files.append(f)

        for file_path in output_files:
            if file_path not in processed_files:
                # Get metadata from database
                game_metadata = self._get_game_metadata(context, file_path)
                
                # For arcade systems, prefer DAT description over scraped name
                # This ensures each version has a unique, descriptive name
                arcade_info = None
                if self._is_arcade_system(context):
                    arcade_info = self._get_arcade_display_info(context, file_path)
                
                if arcade_info:
                    # Use DAT description for display, parent name for sorting
                    game_name, arcade_sortname = arcade_info
                    # Override scraped sortname with parent game for grouping
                    if game_metadata:
                        game_metadata["sortname"] = arcade_sortname
                    else:
                        # No scraped metadata - create minimal dict for sortname
                        game_metadata = {"sortname": arcade_sortname}
                else:
                    # Non-arcade: use scraped name or extract from filename
                    game_name = game_metadata["name"] if game_metadata else self._extract_game_name(file_path)
                
                game_elem = self._create_game_element(
                    context=context,
                    file_path=file_path,
                    game_name=game_name,
                    hidden=False,
                    game_metadata=game_metadata,
                )
                gamelist.append(game_elem)
                processed_files.add(file_path)
                
                # Copy media files if available, then add paths to XML
                if game_metadata:
                    self._copy_media_files(context, game_metadata, file_path)
                    self._add_media_paths_to_element(context, game_elem, file_path)
        
        # Sort games by sortname (if available) then by name
        # This ensures game families (e.g., all 1942 variants) are grouped together
        def get_sort_key(game_elem):
            sortname_elem = game_elem.find("sortname")
            name_elem = game_elem.find("name")
            # Primary sort: sortname or name (for grouping families)
            primary = (sortname_elem.text if sortname_elem is not None else name_elem.text).lower()
            # Secondary sort: name (for ordering within a family)
            secondary = name_elem.text.lower() if name_elem is not None else ""
            return (primary, secondary)
        
        games = gamelist.findall("game")
        sorted_games = sorted(games, key=get_sort_key)
        gamelist.clear()
        for game in sorted_games:
            gamelist.append(game)
        
        # Create media directories under media/
        # Filter based on composed_target's supported media types
        media_base = context.output_dir / "media"
        all_media_dirs = ["images", "videos", "marquees", "thumbnails", "wheels", "manuals"]
        
        if context.composed_target:
            from romfarmer.config.frontend import MediaType
            # Filter to only create directories for supported media types
            media_dirs = []
            media_dir_support = {
                "images": None,  # Always supported
                "thumbnails": None,  # Always supported
                "wheels": None,  # Always supported
                "videos": MediaType.VIDEO,
                "marquees": MediaType.MARQUEE,
                "manuals": MediaType.MANUAL,
            }
            for dir_name in all_media_dirs:
                media_type = media_dir_support.get(dir_name)
                if media_type is None or context.composed_target.supports_media(media_type):
                    media_dirs.append(dir_name)
        else:
            media_dirs = all_media_dirs
        
        for media_dir in media_dirs:
            media_path = media_base / media_dir
            media_path.mkdir(parents=True, exist_ok=True)
            self._log_info(context, f"Created media directory: media/{media_dir}/")
        
        # Write gamelist.xml
        gamelist_path = context.output_dir / "gamelist.xml"
        tree = ET.ElementTree(gamelist)
        ET.indent(tree, space="  ")
        tree.write(gamelist_path, encoding="utf-8", xml_declaration=True)
        
        total_games = len(sorted_games)
        message = f"Generated gamelist.xml with {total_games} entries"
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=message,
            files_processed=total_games,
            details={
                "gamelist_path": str(gamelist_path),
                "total_games": total_games,
                "disc_games": len(context.disc_metadata) if context.disc_metadata else 0,
            }
        )
    
    def _add_disc_games(
        self,
        context: StageContext,
        gamelist: ET.Element,
        processed_files: set
    ):
        """Add disc-based games to gamelist.
        
        Args:
            context: Stage context
            gamelist: Gamelist XML root element
            processed_files: Set of files already processed
        """
        for game_base_name, metadata in context.disc_metadata.items():
            # Translate paths from temp/work directory to output directory
            # After organize stage, files have been moved
            primary_file = self._translate_to_output_path(context, metadata.primary_file)
            
            # Skip if file doesn't exist in output (not organized yet)
            if not primary_file.exists():
                continue
            
            # Get metadata from database
            # For M3U files, use first disc's CHD for metadata lookup
            if metadata.needs_m3u and metadata.first_disc_path:
                first_disc_output = self._translate_to_output_path(context, metadata.first_disc_path)
                game_metadata = self._get_game_metadata(context, first_disc_output)
            else:
                # Single disc game - use the CHD file directly
                game_metadata = self._get_game_metadata(context, primary_file)
            
            # Use database name if available, otherwise use disc metadata title
            # For M3U, always use metadata.title (the series name without disc number)
            if metadata.needs_m3u:
                game_name = metadata.title
            else:
                game_name = game_metadata["name"] if game_metadata else metadata.title
            
            # Add primary entry (M3U or single CHD)
            game_elem = self._create_game_element(
                context=context,
                file_path=primary_file,
                game_name=game_name,
                hidden=False,
                metadata=metadata,
                game_metadata=game_metadata,
            )
            gamelist.append(game_elem)
            processed_files.add(primary_file)
            
            # Copy media files if available
            # For M3U, use first disc's path for media file naming
            if game_metadata:
                media_source_file = first_disc_output if (metadata.needs_m3u and metadata.first_disc_path) else primary_file
                self._copy_media_files(context, game_metadata, media_source_file)
                self._add_media_paths_to_element(context, game_elem, media_source_file)
            
            # If M3U exists, hide individual disc CHDs
            if metadata.needs_m3u:
                for disc_path in metadata.all_discs:
                    # Translate disc path to output directory
                    output_disc_path = self._translate_to_output_path(context, disc_path)
                    
                    # Skip if file doesn't exist in output
                    if not output_disc_path.exists():
                        continue
                    
                    # Create hidden entry for each disc
                    hidden_elem = self._create_game_element(
                        context=context,
                        file_path=output_disc_path,
                        game_name=f"{metadata.title} (Disc {self._get_disc_number(disc_path)})",
                        hidden=True,  # ← KEY: Hide individual discs!
                        metadata=None,  # No scraping for hidden entries
                    )
                    gamelist.append(hidden_elem)
                    # Mark BOTH temp and output paths as processed
                    processed_files.add(disc_path)
                    processed_files.add(output_disc_path)
                
                self._log_info(
                    context,
                    f"Added M3U game: {game_base_name} "
                    f"({len(metadata.all_discs)} discs hidden)"
                )
            else:
                # Single disc game
                processed_files.add(metadata.first_disc_path)
                processed_files.add(primary_file)  # Also mark output path as processed
                self._log_info(context, f"Added game: {game_base_name}")
    
    def _add_regular_games(
        self,
        context: StageContext,
        gamelist: ET.Element,
        processed_files: set
    ):
        """Add regular (non-disc) games to gamelist.
        
        Args:
            context: Stage context
            gamelist: Gamelist XML root element
            processed_files: Set of files already processed
        """
        # Check if this is an arcade system (use DAT descriptions)
        is_arcade = self._is_arcade_system(context)
        
        # Process organized files (from OrganizeStage)
        for subdir, files in context.organized_files.items():
            for file_path in files:
                if file_path not in processed_files:
                    # For arcade systems, use DAT description for display name
                    game_metadata = None
                    arcade_sortname = None
                    
                    if is_arcade:
                        arcade_info = self._get_arcade_display_info(context, file_path)
                        if arcade_info:
                            game_name, arcade_sortname = arcade_info
                        else:
                            game_name = self._extract_game_name(file_path)
                    else:
                        # Non-arcade: extract from filename
                        game_name = self._extract_game_name(file_path)
                    
                    # Build minimal game_metadata for sortname if arcade
                    if arcade_sortname:
                        game_metadata = {"sortname": arcade_sortname}
                    
                    game_elem = self._create_game_element(
                        context=context,
                        file_path=file_path,
                        game_name=game_name,
                        hidden=False,
                        game_metadata=game_metadata,
                    )
                    gamelist.append(game_elem)
                    processed_files.add(file_path)
    
    def _create_game_element(
        self,
        context: StageContext,
        file_path: Path,
        game_name: str,
        hidden: bool = False,
        metadata: Optional[DiscMetadata] = None,
        game_metadata: Optional[dict] = None,
    ) -> ET.Element:
        """Create <game> element for gamelist.xml.
        
        Args:
            context: Stage context
            file_path: Path to game file
            game_name: Display name
            hidden: Whether to hide in UI
            metadata: Optional disc metadata for images
            game_metadata: Optional scraped metadata from database
            
        Returns:
            XML game element
        """
        game = ET.Element("game")
        
        # Path (relative to output directory)
        rel_path = file_path.relative_to(context.output_dir)
        path_elem = ET.SubElement(game, "path")
        path_elem.text = f"./{rel_path}"
        
        # Name
        name_elem = ET.SubElement(game, "name")
        name_elem.text = game_name
        
        # Sortname
        # ARRM stores sortnames as "NNNN =-  Title" (ScreenScraper ID prefix).
        # Strip that prefix so ES sorts alphabetically, not by database ID.
        if game_metadata and game_metadata.get("sortname"):
            raw_sort = game_metadata["sortname"]
            import re as _re
            cleaned = _re.sub(r'^\d+\s*=-\s*', '', raw_sort).strip()
            # Only write sortname when it differs from the display name
            if cleaned and cleaned.lower() != game_name.lower():
                sort_elem = ET.SubElement(game, "sortname")
                sort_elem.text = cleaned
        
        # Hidden (for individual discs in M3U games)
        # If hidden=True passed (M3U component), force hidden
        # Otherwise check metadata
        is_hidden = hidden
        if not is_hidden and game_metadata and game_metadata.get("hidden"):
            is_hidden = True
            
        if is_hidden:
            hidden_elem = ET.SubElement(game, "hidden")
            hidden_elem.text = "true"
            if hidden: # If it's an M3U component, stop here
                return game  # Don't add more metadata for hidden entries
        
        # Add rich metadata from database if available
        if game_metadata:
            if game_metadata.get("desc"):
                desc_elem = ET.SubElement(game, "desc")
                desc_elem.text = game_metadata["desc"]
            
            if game_metadata.get("developer"):
                dev_elem = ET.SubElement(game, "developer")
                dev_elem.text = game_metadata["developer"]
            
            if game_metadata.get("publisher"):
                pub_elem = ET.SubElement(game, "publisher")
                pub_elem.text = game_metadata["publisher"]
            
            if game_metadata.get("genre"):
                genre_elem = ET.SubElement(game, "genre")
                genre_elem.text = game_metadata["genre"]
            
            if game_metadata.get("releasedate"):
                date_elem = ET.SubElement(game, "releasedate")
                date_elem.text = game_metadata["releasedate"]
            
            if game_metadata.get("players"):
                players_elem = ET.SubElement(game, "players")
                players_elem.text = game_metadata["players"]
            
            if game_metadata.get("rating"):
                rating_elem = ET.SubElement(game, "rating")
                rating_elem.text = str(game_metadata["rating"])
            
            # Additional ARRM fields
            if game_metadata.get("region"):
                region_elem = ET.SubElement(game, "region")
                region_elem.text = game_metadata["region"]
            
            if game_metadata.get("language"):
                lang_elem = ET.SubElement(game, "lang")
                lang_elem.text = game_metadata["language"]

            if game_metadata.get("favorite"):
                fav_elem = ET.SubElement(game, "favorite")
                fav_elem.text = "true"
            
            if game_metadata.get("kidgame"):
                kid_elem = ET.SubElement(game, "kidgame")
                kid_elem.text = "true"

            if game_metadata.get("playcount"):
                pc_elem = ET.SubElement(game, "playcount")
                pc_elem.text = str(game_metadata["playcount"])

            if game_metadata.get("lastplayed"):
                lp_elem = ET.SubElement(game, "lastplayed")
                # Format datetime back to string
                if isinstance(game_metadata["lastplayed"], datetime):
                    lp_elem.text = game_metadata["lastplayed"].strftime("%Y%m%dT%H%M%S")
                else:
                    lp_elem.text = str(game_metadata["lastplayed"])
        
        # Media paths will be added separately via _add_media_paths_to_element
        # after media files are copied
        
        return game
    
    def _add_media_paths_to_element(self, context: StageContext, game_elem: ET.Element, file_path: Path):
        """Add media file paths to an existing game element.
        
        Call this AFTER copying media files to ensure they exist.
        
        Args:
            context: Stage context
            game_elem: Game XML element to add media paths to
            file_path: Path to game file
        """
        base_name = file_path.stem
        media_base = context.output_dir / "media"
        
        # Helper to find and add media
        def add_media_tag(tag_name, folder_name, extensions=[".png", ".jpg", ".mp4", ".pdf"]):
            for ext in extensions:
                path = media_base / folder_name / f"{base_name}{ext}"
                if path.exists():
                    elem = ET.SubElement(game_elem, tag_name)
                    elem.text = f"./media/{folder_name}/{path.name}"
                    return path
            return None

        # 1. Add specific media tags
        mix_path = add_media_tag("mix", "mix")
        boxart_path = add_media_tag("boxart", "boxart")
        screenshot_path = add_media_tag("screenshot", "screenshots")
        title_path = add_media_tag("title", "titles") # Some themes use 'title'
        cartridge_path = add_media_tag("cartridge", "cartridges")
        
        add_media_tag("wheel", "wheels")
        add_media_tag("marquee", "marquees")
        add_media_tag("video", "videos")
        add_media_tag("manual", "manuals")

        # 2. Determine primary <image> tag (Mix > Boxart > Screenshot > Title > Cartridge)
        primary_image = None
        if mix_path:
            primary_image = f"./media/mix/{mix_path.name}"
        elif boxart_path:
            primary_image = f"./media/boxart/{boxart_path.name}"
        elif screenshot_path:
            primary_image = f"./media/screenshots/{screenshot_path.name}"
        elif title_path:
            primary_image = f"./media/titles/{title_path.name}"
        elif cartridge_path:
            primary_image = f"./media/cartridges/{cartridge_path.name}"
            
        if primary_image:
            # Check if <image> already exists (it shouldn't, but good to be safe)
            if game_elem.find("image") is None:
                image_elem = ET.SubElement(game_elem, "image")
                image_elem.text = primary_image
    
    def _extract_game_name(self, file_path: Path) -> str:
        """Extract clean game name from filename.
        
        Args:
            file_path: Path to game file
            
        Returns:
            Clean game name
        """
        # Remove extension
        name = file_path.stem
        
        # Remove region tags
        for tag in ["(USA)", "(Europe)", "(Japan)", "(World)", "(En)", "(Fr)", "(De)"]:
            name = name.replace(tag, "")
        
        # Clean up extra spaces
        name = " ".join(name.split())
        
        return name
    
    def _get_arcade_display_info(
        self, context: StageContext, file_path: Path
    ) -> Optional[tuple[str, str]]:
        """Get display name and sortname from DAT for arcade games.
        
        For arcade systems, the DAT file contains accurate descriptions
        that distinguish between game versions (e.g., "1942 (Revision B)")
        while the scraped data often shows just the parent name ("1942").
        
        This method looks up the game in the DAT and returns:
        - display_name: The DAT description (unique, descriptive)
        - sortname: The parent game name (for grouping families together)
        
        Args:
            context: Stage context (must have filtered_dat or dat_file)
            file_path: Path to ROM file (e.g., "1942h.zip")
            
        Returns:
            Tuple of (display_name, sortname) if found, None otherwise.
            
        Example:
            For "1942h.zip" returns: ("Supercharger 1942", "1942")
            For "1942.zip" returns: ("1942 (Revision B)", "1942")
        """
        # Get the DAT - prefer filtered_dat (from arcade stage) over dat_file
        dat = getattr(context, 'filtered_dat', None) or context.dat_file
        if not dat:
            return None
        
        # Arcade ROMs use the filename stem as the game name
        game_name = file_path.stem
        
        # Build lookup dict if not already cached
        if not hasattr(self, '_dat_game_lookup'):
            self._dat_game_lookup = {}
        
        # Cache DAT games by name for quick lookup
        dat_id = id(dat)  # Use object id to detect DAT changes
        if getattr(self, '_dat_lookup_id', None) != dat_id:
            self._dat_game_lookup = {game.name: game for game in dat.games}
            self._dat_lookup_id = dat_id
        
        # Look up the game
        dat_game = self._dat_game_lookup.get(game_name)
        if not dat_game:
            return None
        
        # Get display name from DAT description (or fall back to name)
        display_name = dat_game.description or dat_game.name
        
        # Get sortname for grouping game families together
        # - For clones: use the parent name (cloneof)
        # - For parents: use their own name (so they group with their clones)
        sortname = dat_game.cloneof or dat_game.name
        
        return (display_name, sortname)
    
    def _is_arcade_system(self, context: StageContext) -> bool:
        """Check if current platform is an arcade system.
        
        Arcade systems include FBNeo, MAME, and Neo Geo.
        These systems use DAT descriptions for display names.
        
        Args:
            context: Stage context with platform_config
            
        Returns:
            True if platform is an arcade system
        """
        arcade_platforms = {'fbneo', 'mame', 'neogeo', 'naomi', 'atomiswave', 'cps1', 'cps2', 'cps3'}
        platform_name = context.platform_config.name.lower()
        return platform_name in arcade_platforms
    
    def _get_disc_number(self, disc_path: Path) -> str:
        """Extract disc number from filename.
        
        Args:
            disc_path: Path to disc file
            
        Returns:
            Disc number string (e.g., "1", "2", "A")
        """
        import re
        match = re.search(r'\(Disc ([0-9A-Z]+)\)', disc_path.stem, re.IGNORECASE)
        if match:
            return match.group(1)
        return "?"
    
    def _translate_to_output_path(self, context: StageContext, file_path: Path) -> Path:
        """Translate a file path from work/temp directory to output directory.
        
        After the organize stage moves files from work_dir to output_dir,
        we need to update paths accordingly.
        
        Args:
            context: Stage context
            file_path: Original file path (may be in work_dir)
            
        Returns:
            Translated path in output_dir
        """
        # If file is already in output directory, return as-is
        try:
            file_path.relative_to(context.output_dir)
            return file_path
        except ValueError:
            pass
        
        # File is in work directory, translate to output directory
        # Just use the filename in the output directory (flat organization)
        return context.output_dir / file_path.name
    
    def _init_metadata_db(self, context: StageContext):
        """Initialize connection to metadata database.
        
        Args:
            context: Stage context
        """
        if self.metadata_db is not None:
            return  # Already initialized
        
        try:
            from romfarmer.metadata.database import MetadataDatabase
            
            # Use absolute path if relative
            db_path = self.metadata_db_path
            if not db_path.is_absolute():
                db_path = Path.cwd() / db_path
            
            if not db_path.exists():
                self._log_info(context, f"Metadata database not found at {db_path}")
                self._log_info(context, "Generating minimal gamelist.xml without scraped metadata")
                return
            
            self.metadata_db = MetadataDatabase(db_path)
            self._log_info(context, f"Loaded metadata database: {db_path}")
            
        except ImportError:
            self._log_info(context, "Metadata database module not available")
        except Exception as e:
            self._log_info(context, f"Failed to load metadata database: {e}")
    
    def _init_video_converter(self, context: StageContext):
        """Initialize video converter based on device configuration.
        
        If the target has a device with video constraints, we'll use
        the video converter to transcode videos for optimal storage.
        
        Args:
            context: Stage context
        """
        if self.video_converter is not None:
            return  # Already initialized
        
        # Check if we have a composed target with device config
        if not context.composed_target:
            self._log_info(context, "No device config - using original videos")
            return
        
        try:
            from romfarmer.utils.video_converter import (
                VideoConverter, 
                get_profile_from_device_config,
            )
            
            device = context.composed_target.device
            media_sizing = device.media_sizing
            
            # Create profile from device config
            self.video_profile = get_profile_from_device_config(media_sizing)
            
            if self.video_profile is None:
                self._log_info(context, "Device allows original quality videos")
                return
            
            # Initialize converter
            media_root = Path.cwd() / "metadata" / "media"
            self.video_converter = VideoConverter(media_root)
            
            self._log_info(
                context, 
                f"Video optimization enabled: {self.video_profile.name} "
                f"({self.video_profile.max_width}x{self.video_profile.max_height} "
                f"@ {self.video_profile.max_bitrate_kbps}kbps)"
            )
            
        except ImportError as e:
            self._log_info(context, f"Video converter not available: {e}")
        except Exception as e:
            self._log_info(context, f"Failed to initialize video converter: {e}")
    
    def _init_image_converter(self, context: StageContext):
        """Initialize image converter based on device configuration.
        
        If the target has a device with image size constraints, we'll use
        the image converter to resize images for optimal storage.
        
        Args:
            context: Stage context
        """
        if self.image_converter is not None:
            return  # Already initialized
        
        # Check if we have a composed target with device config
        if not context.composed_target:
            self._log_info(context, "No device config - using original images")
            return
        
        try:
            from romfarmer.utils.image_converter import (
                ImageConverter, 
                get_profile_from_device_config,
            )
            
            device = context.composed_target.device
            media_sizing = device.media_sizing
            
            # Create profile from device config
            self.image_profile = get_profile_from_device_config(media_sizing)
            
            if self.image_profile is None:
                self._log_info(context, "Device allows original quality images")
                return
            
            # Initialize converter
            media_root = Path.cwd() / "metadata" / "media"
            self.image_converter = ImageConverter(media_root)
            
            self._log_info(
                context, 
                f"Image optimization enabled: {self.image_profile.name} "
                f"({self.image_profile.max_width}x{self.image_profile.max_height})"
            )
            
        except ImportError as e:
            self._log_info(context, f"Image converter not available: {e}")
        except Exception as e:
            self._log_info(context, f"Failed to initialize image converter: {e}")
    
    def _get_game_metadata(self, context: StageContext, file_path: Path) -> Optional[dict]:
        """Get metadata for a game file from the database.
        
        Uses a two-tier lookup strategy:
        1. Primary: Hash-based lookup via ROMTransformation table (most accurate)
        2. Fallback: System + filename lookup (for when transformations aren't recorded)
        
        Args:
            context: Stage context
            file_path: Path to game file (CHD)
            
        Returns:
            Dictionary with game metadata, or None if not found
        """
        if self.metadata_db is None:
            return None
        
        try:
            from romfarmer.metadata.transformation import ROMTransformation
            from romfarmer.metadata.database import ScrapedGame
            
            game = None
            lookup_method = None
            
            with self.metadata_db.get_session() as session:
                # ═══════════════════════════════════════════════════════════
                # TIER 1: Hash-based lookup (most accurate)
                # ═══════════════════════════════════════════════════════════
                # For cartridge systems: Use ROM MD5 from extraction stage
                # For disc systems: Look up via transformation table using CHD MD5
                
                rom_md5 = None
                
                # Check if we have a ROM MD5 from extraction (cartridge systems)
                if hasattr(context, 'rom_md5_map') and context.rom_md5_map:
                    # Find the original ROM file that corresponds to this output file
                    # The output file has same stem as the ROM (just different extension)
                    for rom_path, md5 in context.rom_md5_map.items():
                        if rom_path.stem == file_path.stem:
                            rom_md5 = md5
                            break
                
                # Use ROM MD5 for cartridge systems, or calculate final file MD5 for others
                lookup_md5 = rom_md5 if rom_md5 else self._calculate_md5(file_path, context)
                
                if lookup_md5:
                    self._log_debug(context, f"Attempting MD5 lookup for {file_path.name}: {lookup_md5}")
                    
                    # Determine if this is a direct MD5 lookup or transformation lookup
                    # Direct lookups: cartridge ROM MD5s (rom_md5) or arcade ZIP MD5s
                    is_arcade = context.platform_config.type == 'arcade'
                    use_direct_lookup = rom_md5 is not None or is_arcade
                    
                    # Use metadata_system if specified, otherwise use platform name
                    # This allows platforms to share metadata (e.g., Sega arcade platforms use MAME metadata)
                    metadata_system = context.platform_config.metadata_system or context.platform_config.name
                    
                    if use_direct_lookup:
                        # For cartridge systems and arcade systems: Direct lookup by MD5
                        game = session.query(ScrapedGame).filter(
                            ScrapedGame.system == metadata_system,
                            ScrapedGame.md5 == lookup_md5
                        ).first()
                        
                        if game:
                            lookup_method = "md5-direct" if is_arcade else "rom-hash"
                            self._log_info(context, f"Found metadata for {file_path.name} via MD5 lookup")
                        else:
                            self._log_debug(context, f"No MD5 match for {file_path.name}: {lookup_md5}")
                    else:
                        # For disc systems (CHD/ISO output): Lookup via transformation table
                        # The transformation table stores: source_md5 (CUE) -> final_md5 (CHD)
                        # We have the CHD, so we look up by final_md5 to find the source CUE MD5
                        
                        self._log_debug(context, f"Trying transformation lookup for {file_path.name}: {lookup_md5}")
                        
                        # First, try looking up by final_md5 (CHD -> CUE chain)
                        transformation = session.query(ROMTransformation).filter(
                            ROMTransformation.final_md5 == lookup_md5
                        ).first()
                        
                        if transformation:
                            # Found transformation: CHD -> CUE
                            # Now look up the game by the source (CUE) MD5
                            source_cue_md5 = transformation.source_md5
                            
                            if transformation.game:
                                game = transformation.game
                                lookup_method = "transformation-reverse"
                                self._log_info(context, f"Found metadata for {file_path.name} via transformation (CHD->CUE->game)")
                            else:
                                # Game not linked in transformation, try looking up by source MD5
                                game = session.query(ScrapedGame).filter(
                                    ScrapedGame.system == metadata_system,
                                    ScrapedGame.md5 == source_cue_md5
                                ).first()
                                if game:
                                    lookup_method = "transformation-source-lookup"
                                    self._log_info(context, f"Found metadata for {file_path.name} via source MD5 lookup")
                        else:
                            self._log_debug(context, f"No transformation found for final_md5: {lookup_md5}")
                        
                        # Fallback: Also try source_md5 lookup (for cases where lookup_md5 is actually the source)
                        if not game:
                            transformation = session.query(ROMTransformation).filter(
                                ROMTransformation.source_md5 == lookup_md5
                            ).first()
                            
                            if transformation:
                                # We found a record linking this file to a final MD5
                                if transformation.game:
                                    game = transformation.game
                                    lookup_method = "transformation-forward"
                                    self._log_info(context, f"Found metadata for {file_path.name} via transformation hash lookup")
                                elif transformation.final_md5:
                                    # Try looking up the game by the final MD5
                                    game = session.query(ScrapedGame).filter(
                                        ScrapedGame.system == metadata_system,
                                        ScrapedGame.md5 == transformation.final_md5
                                    ).first()
                                    if game:
                                        lookup_method = "transformation-link"
                                        self._log_info(context, f"Found metadata for {file_path.name} via transformation link")

                        # Special handling for ZIP files without extraction (e.g. NES)
                        # If we didn't find a transformation record, peek inside the ZIP
                        if not game and file_path.suffix.lower() == '.zip':
                            inner_md5, inner_ext = self._get_inner_md5_from_zip(file_path)
                            if inner_md5:
                                # Try lookup with inner MD5
                                game = session.query(ScrapedGame).filter(
                                    ScrapedGame.system == metadata_system,
                                    ScrapedGame.md5 == inner_md5
                                ).first()
                                
                                if game:
                                    lookup_method = "zip-peek"
                                    self._log_info(context, f"Found metadata for {file_path.name} via ZIP peek")
                                    
                                    # Record this relationship for future use
                                    try:
                                        new_trans = ROMTransformation(
                                            source_md5=lookup_md5,
                                            source_format='zip',
                                            final_md5=inner_md5,
                                            final_format=inner_ext or 'bin',
                                            transformation_tool='rom-farmer-zip-peek',
                                            verified=True,
                                            game_id=game.id
                                        )
                                        session.add(new_trans)
                                        session.commit()
                                        self._log_info(context, f"Recorded ZIP transformation: {lookup_md5} -> {inner_md5}")
                                    except Exception as e:
                                        self._log_info(context, f"Failed to record transformation: {e}")
                                        session.rollback()
                
                # ═══════════════════════════════════════════════════════════
                # TIER 2: System + Filename lookup (fallback)
                # ═══════════════════════════════════════════════════════════
                # If hash lookup fails, try matching by system + filename
                # This works because Redump/No-Intro names are standardized
                
                if not game:
                    # Use metadata_system (already set above)
                    
                    # Build filename with ./ prefix to match database format
                    # Database stores: "./filename.zip" or "./filename.chd"
                    filename = f"./{file_path.name}"
                    
                    # Try exact match first
                    game = session.query(ScrapedGame).filter(
                        ScrapedGame.system == metadata_system,
                        ScrapedGame.filename == filename
                    ).first()
                    
                    if game:
                        lookup_method = "filename-exact"
                        self._log_info(context, f"Found metadata for {file_path.name} via filename lookup")
                    else:
                        # Try fuzzy match - remove region tags and compare
                        clean_name = self._extract_game_name(file_path)
                        game = session.query(ScrapedGame).filter(
                            ScrapedGame.system == metadata_system,
                            ScrapedGame.name.like(f"%{clean_name}%")
                        ).first()
                        
                        if game:
                            lookup_method = "filename-fuzzy"
                            self._log_info(context, f"Found metadata for {file_path.name} via fuzzy filename match")
                
                # ═══════════════════════════════════════════════════════════
                # Build metadata response
                # ═══════════════════════════════════════════════════════════
                
                if not game:
                    return None
                
                # Force load relationships BEFORE detaching from session
                # This prevents "not bound to a Session" errors when accessing relationships later
                _ = game.media_links  # Trigger lazy load
                for link in game.media_links:
                    _ = link.media_file  # Ensure nested relationships loaded
                
                # Now safe to detach from session
                session.expunge(game)
                
                # Get media files for this game
                media_files = self.metadata_db.get_game_media(game)
                
                return {
                    "name": game.name,
                    "desc": game.description,
                    "developer": game.developer,
                    "publisher": game.publisher,
                    "genre": game.genre,
                    "releasedate": game.release_date,
                    "players": game.players,
                    "rating": game.rating,
                    "media": media_files,
                    "lookup_method": lookup_method,  # For debugging
                    "sortname": game.sortname,
                    "region": game.region,
                    "language": game.language,
                    "hidden": game.hidden,
                    "favorite": game.favorite,
                    "kidgame": game.kidgame,
                    "playcount": game.playcount,
                    "lastplayed": game.lastplayed,
                }
                
        except Exception as e:
            self._log_info(context, f"Error getting metadata for {file_path.name}: {e}")
            return None
    
    def _calculate_md5(self, file_path: Path, context: StageContext) -> Optional[str]:
        """Calculate MD5 hash of a file using centralized hashing.
        
        Uses the core.hashing module which handles system-aware hashing
        (arcade ZIP files vs cartridge archives vs direct files).
        
        Args:
            file_path: Path to file
            context: Stage context (provides system name)
            
        Returns:
            MD5 hash as hex string, or None on error
        """
        try:
            # Use platform config name for system-aware hashing
            system_name = context.platform_config.name
            return calculate_md5(file_path, system_name)
        except Exception:
            return None
    
    def _copy_media_files(self, context: StageContext, game_metadata: dict, file_path: Path):
        """Copy media files from central storage to output media directories.
        
        Args:
            context: Stage context
            game_metadata: Game metadata dictionary with 'media' key
            file_path: Game file path (for naming media files)
        """
        if "media" not in game_metadata:
            self._log_info(context, f"  No 'media' key in metadata for {file_path.name}")
            return
        
        if not game_metadata["media"]:
            self._log_info(context, f"  Empty media dict for {file_path.name}")
            return
        
        self._log_info(context, f"  Processing {len(game_metadata['media'])} media files for {file_path.name}")
        
        # Media type mapping to output directories
        media_dir_map = {
            "image": "titles",      # Title screens
            "boxart": "boxart",
            "screenshot": "screenshots",
            "mix": "mix",
            "video": "videos",
            "marquee": "marquees",
            "wheel": "wheels",
            "cartridge": "cartridges",
            "manual": "manuals",
        }
        
        base_name = file_path.stem
        media_base = context.output_dir / "media"
        
        for media_type, media_file in game_metadata["media"].items():
            # Use composed_target for media filtering if available
            # This is cleaner than hardcoding target names
            if context.composed_target:
                from romfarmer.config.frontend import MediaType
                # Map media_type string to MediaType enum
                media_type_map = {
                    "manual": MediaType.MANUAL,
                    "video": MediaType.VIDEO,
                    "marquee": MediaType.MARQUEE,
                }
                media_enum = media_type_map.get(media_type)
                if media_enum and not context.composed_target.supports_media(media_enum):
                    self._log_info(context, f"  Skipping {media_type} (not supported by target)")
                    continue
            else:
                # Legacy fallback: Skip manuals for RocknIX targets to save space
                if context.target_name == 'rocknix' and media_type == 'manual':
                    continue

            target_dir_name = media_dir_map.get(media_type)
            if not target_dir_name:
                continue
            
            target_dir = media_base / target_dir_name
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Source file in central storage
            source_path = Path(media_file.file_path)
            if not source_path.is_absolute():
                # file_path is already relative from rom-farmer-python root
                # (e.g., "metadata/media/video/b7/abc123.mp4")
                # Just resolve it relative to current directory
                source_path = Path.cwd() / source_path
            
            if not source_path.exists():
                self._log_info(context, f"  Media file not found: {source_path}")
                continue
            
            # For videos, use optimized version if converter is available
            actual_source = source_path
            if media_type == "video" and self.video_converter and self.video_profile:
                optimized_path = self.video_converter.get_optimized_video(
                    source_path, 
                    self.video_profile
                )
                if optimized_path != source_path:
                    actual_source = optimized_path
                    self._log_info(context, f"  Using optimized video: {optimized_path.name}")
            
            # For images, use optimized version if converter is available
            elif media_type in ("image", "cartridge", "boxart", "screenshot", "wheel"):
                if self.image_converter and self.image_profile:
                    optimized_path = self.image_converter.get_optimized_image(
                        source_path,
                        media_type,
                        self.image_profile
                    )
                    if optimized_path != source_path:
                        actual_source = optimized_path
                        self._log_info(context, f"  Using optimized image: {optimized_path.name}")
            
            # Target filename based on game file
            ext = actual_source.suffix
            target_path = target_dir / f"{base_name}{ext}"
            
            # Hardlink or copy the file
            if not target_path.exists():
                try:
                    # Try hardlink first (fast, saves disk space)
                    os.link(actual_source, target_path)
                    self._log_info(context, f"Linked {media_type}: {target_path.name}")
                except OSError:
                    # Fall back to copy if hardlink fails (cross-filesystem)
                    try:
                        shutil.copy2(actual_source, target_path)
                        self._log_info(context, f"Copied {media_type}: {target_path.name}")
                    except Exception as e:
                        self._log_info(context, f"Failed to copy {media_type}: {e}")
    
    def _get_inner_md5_from_zip(self, zip_path: Path) -> tuple[Optional[str], Optional[str]]:
        """Calculate MD5 of the largest file inside a ZIP.
        
        Note: This uses ARCHIVE_CONTENTS strategy (cartridge-style hashing)
        since we explicitly want the inner file's hash for metadata lookup.
        
        Args:
            zip_path: Path to ZIP file
            
        Returns:
            Tuple of (md5_hash, extension) or (None, None)
        """
        try:
            from ..core.hashing import calculate_hash, HashingStrategy
            
            # Force ARCHIVE_CONTENTS strategy to get inner file hash
            result = calculate_hash(zip_path, system_name=None)  # None = not arcade
            
            if result.strategy_used == HashingStrategy.ARCHIVE_CONTENTS:
                ext = Path(result.inner_filename).suffix.lower().lstrip('.') if result.inner_filename else ''
                return result.md5, ext
            else:
                # Fallback for non-archive files
                return result.md5, zip_path.suffix.lower().lstrip('.')
        except Exception:
            return None, None


# Example output for multi-disc game:
"""
<gameList>
  <!-- M3U: Visible in EmulationStation -->
  <game>
    <path>./Panzer Dragoon Saga (USA).m3u</path>
    <name>Panzer Dragoon Saga</name>
    <image>./images/Panzer Dragoon Saga (USA) (Disc 1).png</image>
  </game>
  
  <!-- Disc 1: HIDDEN -->
  <game>
    <path>./Panzer Dragoon Saga (USA) (Disc 1).chd</path>
    <name>Panzer Dragoon Saga (Disc 1)</name>
    <hidden>true</hidden>
  </game>
  
  <!-- Disc 2: HIDDEN -->
  <game>
    <path>./Panzer Dragoon Saga (USA) (Disc 2).chd</path>
    <name>Panzer Dragoon Saga (Disc 2)</name>
    <hidden>true</hidden>
  </game>
  
  <!-- Disc 3: HIDDEN -->
  <game>
    <path>./Panzer Dragoon Saga (USA) (Disc 3).chd</path>
    <name>Panzer Dragoon Saga (Disc 3)</name>
    <hidden>true</hidden>
  </game>
  
  <!-- Disc 4: HIDDEN -->
  <game>
    <path>./Panzer Dragoon Saga (USA) (Disc 4).chd</path>
    <name>Panzer Dragoon Saga (Disc 4)</name>
    <hidden>true</hidden>
  </game>
  
  <!-- Single-disc game: Visible -->
  <game>
    <path>./Daytona USA (USA).chd</path>
    <name>Daytona USA</name>
    <image>./images/Daytona USA (USA).png</image>
  </game>
</gameList>
"""
