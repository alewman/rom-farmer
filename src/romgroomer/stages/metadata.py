"""Generate gamelist.xml metadata for EmulationStation.

This stage demonstrates how disc metadata from CreateM3UStage is used
to properly handle multi-disc games in the final gamelist.xml.
"""

from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

from .base import Stage, StageContext, StageResult, StageStatus
from .disc_models import DiscMetadata


class GenerateMetadataStage(Stage):
    """Generate gamelist.xml for EmulationStation/Batocera.
    
    Key Features:
    - For multi-disc games: Show M3U, hide individual CHDs
    - For single-disc games: Show CHD directly
    - Use first disc metadata for title, image, etc.
    - Support subdirectories from ApplyListsStage
    """
    
    def __init__(self):
        """Initialize metadata generation stage."""
        super().__init__("Generate Metadata")
    
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
        
        # Create gamelist.xml root
        gamelist = ET.Element("gameList")
        
        # Track files we've already processed
        processed_files = set()
        
        # Process disc-based games first (Saturn, PS1, etc.)
        if context.disc_metadata:
            self._add_disc_games(context, gamelist, processed_files)
        
        # Process remaining organized files (No-Intro, single-disc, etc.)
        self._add_regular_games(context, gamelist, processed_files)
        
        # Write gamelist.xml
        gamelist_path = context.output_dir / "gamelist.xml"
        tree = ET.ElementTree(gamelist)
        ET.indent(tree, space="  ")
        tree.write(gamelist_path, encoding="utf-8", xml_declaration=True)
        
        total_games = len(gamelist.findall("game"))
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
            # Add primary entry (M3U or single CHD)
            game_elem = self._create_game_element(
                context=context,
                file_path=metadata.primary_file,
                game_name=metadata.title,
                hidden=False,
                metadata=metadata,
            )
            gamelist.append(game_elem)
            processed_files.add(metadata.primary_file)
            
            # If M3U exists, hide individual disc CHDs
            if metadata.needs_m3u:
                for disc_path in metadata.all_discs:
                    # Create hidden entry for each disc
                    hidden_elem = self._create_game_element(
                        context=context,
                        file_path=disc_path,
                        game_name=f"{metadata.title} (Disc {self._get_disc_number(disc_path)})",
                        hidden=True,  # ← KEY: Hide individual discs!
                        metadata=None,  # No scraping for hidden entries
                    )
                    gamelist.append(hidden_elem)
                    processed_files.add(disc_path)
                
                self._log_info(
                    context,
                    f"Added M3U game: {game_base_name} "
                    f"({len(metadata.all_discs)} discs hidden)"
                )
            else:
                # Single disc game
                processed_files.add(metadata.first_disc_path)
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
        # Process organized files (from OrganizeStage)
        for subdir, files in context.organized_files.items():
            for file_path in files:
                if file_path not in processed_files:
                    # Extract clean game name
                    game_name = self._extract_game_name(file_path)
                    
                    game_elem = self._create_game_element(
                        context=context,
                        file_path=file_path,
                        game_name=game_name,
                        hidden=False,
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
    ) -> ET.Element:
        """Create <game> element for gamelist.xml.
        
        Args:
            context: Stage context
            file_path: Path to game file
            game_name: Display name
            hidden: Whether to hide in UI
            metadata: Optional disc metadata for images
            
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
        
        # Hidden (for individual discs in M3U games)
        if hidden:
            hidden_elem = ET.SubElement(game, "hidden")
            hidden_elem.text = "true"
        
        # Image (use first disc for multi-disc games)
        if metadata and metadata.first_disc_path:
            # Image path based on first disc name
            image_name = f"{metadata.first_disc_path.stem}.png"
            image_elem = ET.SubElement(game, "image")
            image_elem.text = f"./images/{image_name}"
        elif not hidden:
            # Regular game image
            image_name = f"{file_path.stem}.png"
            image_elem = ET.SubElement(game, "image")
            image_elem.text = f"./images/{image_name}"
        
        # Future: Add more metadata (developer, genre, rating, etc.)
        # This would come from scraping based on first disc
        
        return game
    
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
