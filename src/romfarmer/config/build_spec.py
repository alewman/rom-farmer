"""Build specification — declarative build intent.

A BuildSpec declares WHAT to build: which recipes, which target, what
constraints. It's intentionally small and declarative.

Compare with the old BuildConfig god object (30+ Optional fields):
a BuildSpec is ~10 fields that express pure intent.

Examples:
    # Full production build: ~10 lines
    name: batocera-1tb
    target: batocera-pc
    recipes:
      - nointro-7z
      - redump-chd
      - nintendo-disc-rvz
      - arcade-fbneo
    
    # Test build: 6 lines  
    name: test-saturn-10
    target: batocera-pc
    recipes: [redump-chd, test-10]
    platforms: [saturn]
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from .models import (
    GenerationFilterConfig,
    SelectionConfig,
)


class DeployConfig(BaseModel):
    """Deployment configuration for build outputs."""
    
    method: str = Field(
        default="rsync",
        description="Deployment method: rsync, copy, symlink"
    )
    destination: str = Field(
        description="Deployment destination path or host:path"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Method-specific options (e.g., rsync flags)"
    )


class PostBuildHook(BaseModel):
    """A post-build action to run after all platforms complete."""
    
    name: str = Field(description="Hook identifier")
    command: Optional[str] = Field(
        None, description="Shell command to run"
    )
    type: str = Field(
        default="command",
        description="Hook type: command, jdupes, generation_filter"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Hook-specific options"
    )


class BuildSpec(BaseModel):
    """Declarative build specification.
    
    A BuildSpec is intentionally small. It declares:
    1. WHERE: target (frontend + device)
    2. HOW: recipes (processing templates)
    3. WHAT: platform list (optional filters/overrides)
    4. CONSTRAINTS: budget, generation filter
    
    Everything else is derived by the resolver.
    """
    
    # Identity
    name: str = Field(description="Build identifier (e.g., 'batocera-1tb')")
    description: str = Field(
        default="",
        description="Human-readable description"
    )
    
    # WHERE — deployment target
    target: str = Field(
        description="Target name (e.g., 'batocera-pc', 'rocknix-r36s'). "
                    "Must match a file in config/targets/."
    )
    
    # HOW — processing recipes (applied in order)
    recipes: List[str] = Field(
        description="Recipe names to apply, in order. Later recipes override earlier "
                    "ones for overlapping platforms. Must match files in config/recipes/."
    )
    
    # WHAT — platform selection (optional)
    platforms: Optional[List[str]] = Field(
        None,
        description="Explicit platform list. None = union of all recipe platform lists."
    )
    exclude: List[str] = Field(
        default_factory=list,
        description="Platforms to exclude from the build"
    )
    
    # Global overrides (rarely needed)
    selection: Optional[SelectionConfig] = Field(
        None,
        description="Global selection override for all platforms (e.g., limit to 10 games)"
    )
    
    # Cross-platform deduplication
    generation_filter: Optional[GenerationFilterConfig] = Field(
        None,
        description="Cross-platform generation deduplication (1G1Gen)"
    )
    
    # Storage constraints
    storage_budget: Optional[str] = Field(
        None,
        description="Total storage budget: '512gb', '1tb', 'unlimited', or None (unlimited)"
    )
    platform_budgets: Dict[str, str] = Field(
        default_factory=dict,
        description="Per-platform storage budgets (e.g., {'psx': '80gb', '3ds': '50gb'})"
    )
    
    # Output path override (rarely needed — usually derived from target + build name)
    output_base: Optional[str] = Field(
        None,
        description="Override output base directory. Default: 'output/{build_name}/'"
    )
    
    # Post-build hooks
    post_build: List[PostBuildHook] = Field(
        default_factory=list,
        description="Actions to run after all platforms complete (jdupes, deploy, etc.)"
    )
    
    # Deployment
    deploy: Optional[DeployConfig] = Field(
        None,
        description="Deployment configuration (rsync to target device)"
    )
    
    @model_validator(mode="after")
    def validate_build_spec(self) -> "BuildSpec":
        """Validate build spec consistency."""
        if not self.recipes:
            raise ValueError("BuildSpec requires at least one recipe")
        
        # Default storage_budget to unlimited
        if self.storage_budget is None:
            object.__setattr__(self, "storage_budget", "unlimited")
        
        return self
    
    def get_output_base(self) -> Path:
        """Get the output base directory for this build.
        
        Returns:
            Path to output base (e.g., output/batocera-1tb/)
        """
        if self.output_base:
            return Path(self.output_base)
        return Path("output") / self.name
    
    def has_budget_constraint(self) -> bool:
        """Check if this build has a storage budget."""
        return (
            self.storage_budget is not None 
            and self.storage_budget != "unlimited"
        )
