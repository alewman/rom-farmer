"""
Generation configuration loader.

Loads generation definitions from config/generations.yaml and provides
utilities for working with console generation configurations.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PlatformPriority:
    """Platform priority within a generation."""
    name: str
    label: str
    priority: int
    notes: str = ""


@dataclass
class Generation:
    """Console generation definition."""
    name: str
    label: str
    description: str
    years: List[int]
    platforms: List[PlatformPriority]
    enabled: bool
    notes: str = ""
    
    def get_platform_names(self) -> List[str]:
        """Get list of platform names in priority order."""
        return [p.name for p in sorted(self.platforms, key=lambda x: x.priority)]
    
    def get_priority(self, platform: str) -> Optional[int]:
        """Get priority for a platform (1 = highest)."""
        for p in self.platforms:
            if p.name == platform:
                return p.priority
        return None


class GenerationLoader:
    """Load and manage generation configurations."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize generation loader.
        
        Args:
            config_path: Path to generations.yaml (default: config/generations.yaml)
        """
        if config_path is None:
            # Try to find config relative to this file or workspace root
            # This module is in src/romfarmer/config/
            module_dir = Path(__file__).parent
            workspace_root = module_dir.parent.parent.parent
            config_path = workspace_root / "config" / "generations.yaml"
        
        self.config_path = config_path
        self.generations: Dict[str, Generation] = {}
        self._load_generations()
    
    def _load_generations(self):
        """Load generation definitions from YAML file."""
        if not self.config_path.exists():
            logger.warning(f"Generations config not found: {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data or 'generations' not in data:
                logger.error("Invalid generations.yaml: missing 'generations' key")
                return
            
            for gen_data in data['generations']:
                generation = self._parse_generation(gen_data)
                if generation:
                    self.generations[generation.name] = generation
            
            logger.info(f"Loaded {len(self.generations)} generation definitions")
            
        except Exception as e:
            logger.error(f"Error loading generations config: {e}")
    
    def _parse_generation(self, data: dict) -> Optional[Generation]:
        """Parse a generation definition from YAML data."""
        try:
            # Parse platform priorities
            platforms = []
            for platform_data in data.get('platforms', []):
                platform = PlatformPriority(
                    name=platform_data['name'],
                    label=platform_data.get('label', platform_data['name']),
                    priority=platform_data['priority'],
                    notes=platform_data.get('notes', '')
                )
                platforms.append(platform)
            
            generation = Generation(
                name=data['name'],
                label=data['label'],
                description=data['description'],
                years=data['years'],
                platforms=platforms,
                enabled=data.get('enabled', True),
                notes=data.get('notes', '')
            )
            
            return generation
            
        except Exception as e:
            logger.error(f"Error parsing generation {data.get('name')}: {e}")
            return None
    
    def get_generation(self, name: str) -> Optional[Generation]:
        """Get a generation by name.
        
        Args:
            name: Generation identifier (gen5, gen6, etc.)
            
        Returns:
            Generation object or None if not found
        """
        return self.generations.get(name)
    
    def get_enabled_generations(self) -> List[Generation]:
        """Get all enabled generations."""
        return [g for g in self.generations.values() if g.enabled]
    
    def get_generation_for_platform(self, platform: str) -> Optional[Generation]:
        """Find which generation a platform belongs to.
        
        Args:
            platform: Platform name (psx, ps2, saturn, etc.)
            
        Returns:
            Generation object or None if platform not in any generation
        """
        for generation in self.generations.values():
            if any(p.name == platform for p in generation.platforms):
                return generation
        return None


# Singleton instance
_generation_loader: Optional[GenerationLoader] = None


def get_generation_loader(config_path: Optional[Path] = None) -> GenerationLoader:
    """Get the singleton GenerationLoader instance.
    
    Args:
        config_path: Optional path to generations.yaml
        
    Returns:
        GenerationLoader instance
    """
    global _generation_loader
    if _generation_loader is None:
        _generation_loader = GenerationLoader(config_path)
    return _generation_loader


def load_generation(name: str) -> Optional[Generation]:
    """Load a generation by name.
    
    Args:
        name: Generation identifier (gen5, gen6, etc.)
        
    Returns:
        Generation object or None if not found
    """
    loader = get_generation_loader()
    return loader.get_generation(name)
