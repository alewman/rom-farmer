"""Configuration management with YAML support and profile system."""

from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from pydantic import BaseModel, Field, field_validator


class OrganizationProfile(BaseModel):
    """Configuration profile for ROM organization."""
    
    name: str = Field(description="Profile name")
    regions: List[str] = Field(default_factory=lambda: ["usa"], description="Regions to keep")
    organize_languages: bool = Field(default=False, description="Create language symlinks")
    exclude_language_regions: List[str] = Field(
        default_factory=list,
        description="Regions to exclude from language symlinks"
    )
    organize_kinds: bool = Field(default=True, description="Organize by kind (Applications, etc)")
    keep_in_root_regions: List[str] = Field(
        default_factory=list,
        description="Regions to keep in root without subfolders"
    )
    keep_in_root_kinds: List[str] = Field(
        default_factory=list,
        description="Kinds to keep in root without subfolders"
    )
    
    @field_validator("regions", "exclude_language_regions", "keep_in_root_regions")
    @classmethod
    def lowercase_regions(cls, v: List[str]) -> List[str]:
        """Ensure regions are lowercase."""
        return [r.lower() for r in v]


class DatabaseConfig(BaseModel):
    """Database configuration."""
    
    path: Path = Field(
        default_factory=lambda: Path("catalog/database/catalog.db"),
        description="Database file path"
    )
    echo: bool = Field(default=False, description="Echo SQL statements")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max connection overflow")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: str = Field(default="INFO", description="Logging level")
    log_dir: Optional[Path] = Field(
        default=None,
        description="Log directory (default: ./logs in project root)"
    )
    enable_file_logging: bool = Field(default=True, description="Enable file logging")
    
    @field_validator("level")
    @classmethod
    def uppercase_level(cls, v: str) -> str:
        """Ensure level is uppercase."""
        return v.upper()


class RomGroomerConfig(BaseModel):
    """
    Main configuration for ROM Groomer.
    
    Configuration is loaded from:
    1. ~/.config/romgroomer/config.yaml (user config)
    2. /etc/romgroomer/config.yaml (system config)
    3. Environment variables (ROMGROOMER_*)
    4. Command-line arguments
    """
    
    version: str = Field(default="2.0.0", description="Config version")
    profiles: Dict[str, OrganizationProfile] = Field(
        default_factory=dict,
        description="Organization profiles"
    )
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig,
        description="Database configuration"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration"
    )
    
    # Global settings
    parallel_workers: int = Field(default=4, description="Number of parallel workers")
    verify_hashes: bool = Field(default=True, description="Verify file hashes")
    case_insensitive_check: bool = Field(
        default=True,
        description="Check for case-insensitive filename collisions"
    )
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "RomGroomerConfig":
        """
        Load configuration from file.
        
        Args:
            config_path: Path to config file (default: ~/.config/romgroomer/config.yaml)
            
        Returns:
            RomGroomerConfig instance
        """
        if config_path is None:
            config_path = Path.home() / ".config" / "romgroomer" / "config.yaml"
        
        if not config_path.exists():
            # Return default configuration
            return cls()
        
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    def save(self, config_path: Optional[Path] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            config_path: Path to config file (default: ~/.config/romgroomer/config.yaml)
        """
        if config_path is None:
            config_path = Path.home() / ".config" / "romgroomer" / "config.yaml"
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w") as f:
            yaml.safe_dump(
                self.model_dump(mode="json", exclude_none=True),
                f,
                default_flow_style=False,
                sort_keys=False,
            )
    
    def get_profile(self, name: str) -> Optional[OrganizationProfile]:
        """Get profile by name."""
        return self.profiles.get(name)
    
    def add_profile(self, profile: OrganizationProfile) -> None:
        """Add or update a profile."""
        self.profiles[profile.name] = profile
    
    @classmethod
    def create_default_config(cls) -> "RomGroomerConfig":
        """Create default configuration with example profiles."""
        config = cls()
        
        # NES USA profile
        config.add_profile(OrganizationProfile(
            name="nes-usa",
            regions=["usa", "world"],
            organize_languages=False,
            organize_kinds=True,
        ))
        
        # NES English profile
        config.add_profile(OrganizationProfile(
            name="nes-eng",
            regions=["europe", "australia", "world"],
            organize_languages=True,
            exclude_language_regions=["usa"],
            organize_kinds=True,
        ))
        
        # Saturn USA profile
        config.add_profile(OrganizationProfile(
            name="saturn-usa",
            regions=["usa"],
            organize_languages=False,
            organize_kinds=True,
        ))
        
        # Saturn English profile
        config.add_profile(OrganizationProfile(
            name="saturn-eng",
            regions=["europe", "usa"],
            organize_languages=True,
            exclude_language_regions=["usa"],
            organize_kinds=True,
        ))
        
        # All regions profile
        config.add_profile(OrganizationProfile(
            name="all",
            regions=["*"],  # Special marker for all regions
            organize_languages=True,
            exclude_language_regions=[],
            organize_kinds=True,
        ))
        
        return config
