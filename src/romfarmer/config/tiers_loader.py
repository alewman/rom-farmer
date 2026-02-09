"""Loader for platform tiers configuration.

Provides functions to load and cache the platform tiers config.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

from .models import PlatformTiersConfig

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_platform_tiers(config_root: Optional[Path] = None) -> PlatformTiersConfig:
    """Load the platform tiers configuration.
    
    The tiers config is loaded from config/platform_tiers.yaml.
    Results are cached after first load.
    
    Args:
        config_root: Root config directory. Defaults to 'config/' in current directory.
        
    Returns:
        PlatformTiersConfig instance
        
    Raises:
        FileNotFoundError: If platform_tiers.yaml doesn't exist
    """
    if config_root is None:
        config_root = Path("config")
    
    config_path = config_root / "platform_tiers.yaml"
    
    if not config_path.exists():
        logger.warning(f"Platform tiers config not found: {config_path}")
        logger.warning("Using empty default tiers config")
        return PlatformTiersConfig()
    
    logger.debug(f"Loading platform tiers config: {config_path}")
    
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    
    # Parse the YAML structure into our models
    config = PlatformTiersConfig.model_validate(data)
    
    logger.info(f"Loaded platform tiers: "
                f"{len(config.tier_1.platforms)} T1, "
                f"{len(config.tier_2.platforms)} T2, "
                f"{len(config.tier_3.platforms)} T3, "
                f"{len(config.tier_4.platforms)} T4, "
                f"{len(config.tier_5.platforms)} T5")
    
    return config


def clear_tiers_cache():
    """Clear the cached tiers config.
    
    Useful for testing or when config files change.
    """
    load_platform_tiers.cache_clear()
