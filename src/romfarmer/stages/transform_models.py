"""Models for tracking file transformations through complex pipelines."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class TransformStatus(str, Enum):
    """Status of a transformation."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class TransformType(str, Enum):
    """Types of transformations."""
    
    # Archive operations
    UNZIP = "unzip"
    EXTRACT_7Z = "extract_7z"
    EXTRACT_RAR = "extract_rar"
    
    # Disc operations
    EXTRACT_ISO = "extract_iso"
    REBUILD_ISO = "rebuild_iso"
    
    # Xbox 360 specific
    DECRYPT_XBOX360 = "decrypt_xbox360"
    EXTRACT_XISO = "extract_xiso"
    REBUILD_XISO = "rebuild_xiso"
    
    # Compression
    COMPRESS_CHD = "compress_chd"
    COMPRESS_CSO = "compress_cso"
    COMPRESS_XISO = "compress_xiso"
    COMPRESS_ZSO = "compress_zso"
    COMPRESS_RVZ = "compress_rvz"
    
    # Wii/GameCube
    DECRYPT_WII = "decrypt_wii"
    EXTRACT_WBFS = "extract_wbfs"
    
    # PS3
    DECRYPT_PS3 = "decrypt_ps3"
    EXTRACT_PKG = "extract_pkg"
    
    # Other
    CONVERT_FORMAT = "convert_format"
    PATCH = "patch"
    CUSTOM = "custom"


@dataclass
class TransformStep:
    """Single transformation step in a multi-step process.
    
    Example: Unzipping an archive is one step in the Xbox 360 pipeline.
    """
    
    step_type: TransformType
    """Type of transformation"""
    
    input_file: Path
    """Input file for this step"""
    
    output_file: Optional[Path] = None
    """Output file from this step (None if failed)"""
    
    tool: Optional[str] = None
    """Tool/command used (e.g., 'zipfile', 'xbox360_decrypt', 'chdman')"""
    
    status: TransformStatus = TransformStatus.PENDING
    """Status of this step"""
    
    duration_seconds: float = 0.0
    """Time taken for this step"""
    
    error: Optional[str] = None
    """Error message if failed"""
    
    details: dict = field(default_factory=dict)
    """Additional details (file sizes, compression ratio, etc.)"""
    
    def __repr__(self) -> str:
        """Human-readable representation."""
        status_icon = {
            TransformStatus.SUCCESS: "✓",
            TransformStatus.FAILED: "✗",
            TransformStatus.IN_PROGRESS: "⋯",
            TransformStatus.PENDING: "○",
            TransformStatus.SKIPPED: "⊘",
        }
        icon = status_icon.get(self.status, "?")
        
        if self.output_file:
            return f"{icon} {self.step_type.value}: {self.input_file.name} → {self.output_file.name}"
        else:
            return f"{icon} {self.step_type.value}: {self.input_file.name}"


@dataclass
class FileTransformation:
    """Complete transformation record for a single file.
    
    Tracks a file's journey through multiple transformation steps.
    
    Example Xbox 360:
        Source: Halo 3.zip
        Steps:
          1. Unzip → Halo 3.iso (encrypted)
          2. Decrypt → Halo 3.iso (raw)
          3. Extract → Halo 3/ (folder)
          4. Rebuild → Halo 3.iso (optimized)
          5. Compress → Halo 3.xiso
        Final: Halo 3.xiso
    """
    
    source_file: Path
    """Original input file"""
    
    final_file: Optional[Path] = None
    """Final output file (None if transformation incomplete/failed)"""
    
    steps: List[TransformStep] = field(default_factory=list)
    """All transformation steps in order"""
    
    status: TransformStatus = TransformStatus.PENDING
    """Overall transformation status"""
    
    duration_seconds: float = 0.0
    """Total time for all steps"""
    
    error: Optional[str] = None
    """Error message if transformation failed"""
    
    intermediate_files: List[Path] = field(default_factory=list)
    """Intermediate files created (for cleanup tracking)"""
    
    def add_step(self, step: TransformStep):
        """Add a transformation step.
        
        Args:
            step: Transformation step to add
        """
        self.steps.append(step)
        self.duration_seconds += step.duration_seconds
        
        # Track intermediate files
        if step.output_file and step.output_file != self.final_file:
            self.intermediate_files.append(step.output_file)
        
        # Update overall status
        if step.status == TransformStatus.FAILED:
            self.status = TransformStatus.FAILED
            self.error = step.error
    
    def get_step(self, step_type: TransformType) -> Optional[TransformStep]:
        """Get step by type.
        
        Args:
            step_type: Type of step to find
            
        Returns:
            Step if found, None otherwise
        """
        for step in self.steps:
            if step.step_type == step_type:
                return step
        return None
    
    def get_compression_ratio(self) -> Optional[float]:
        """Calculate compression ratio if applicable.
        
        Returns:
            Ratio (0.0-1.0) or None if not compressible
        """
        if not self.source_file.exists() or not self.final_file or not self.final_file.exists():
            return None
        
        source_size = self.source_file.stat().st_size
        final_size = self.final_file.stat().st_size
        
        if source_size == 0:
            return None
        
        return final_size / source_size
    
    def get_summary(self) -> str:
        """Get human-readable summary.
        
        Returns:
            Summary string
        """
        if self.status == TransformStatus.SUCCESS:
            ratio = self.get_compression_ratio()
            ratio_str = f" ({ratio:.1%} of original)" if ratio else ""
            return f"✓ {self.source_file.name} → {self.final_file.name}{ratio_str} ({self.duration_seconds:.1f}s)"
        elif self.status == TransformStatus.FAILED:
            failed_step = next((s for s in self.steps if s.status == TransformStatus.FAILED), None)
            step_name = failed_step.step_type.value if failed_step else "unknown"
            return f"✗ {self.source_file.name} (failed at {step_name}): {self.error}"
        else:
            return f"⋯ {self.source_file.name} ({self.status.value})"
    
    def __repr__(self) -> str:
        """Human-readable representation."""
        return self.get_summary()


# Example usage:
"""
# Xbox 360 transformation
transformation = FileTransformation(source_file=Path("Halo 3.zip"))

# Step 1: Unzip
transformation.add_step(TransformStep(
    step_type=TransformType.UNZIP,
    input_file=Path("Halo 3.zip"),
    output_file=Path("Halo 3.iso"),
    tool="zipfile",
    status=TransformStatus.SUCCESS,
    duration_seconds=2.3,
))

# Step 2: Decrypt
transformation.add_step(TransformStep(
    step_type=TransformType.DECRYPT_XBOX360,
    input_file=Path("Halo 3.iso"),
    output_file=Path("Halo 3_decrypted.iso"),
    tool="xbox360_decrypt",
    status=TransformStatus.SUCCESS,
    duration_seconds=15.7,
))

# Step 3: Extract
transformation.add_step(TransformStep(
    step_type=TransformType.EXTRACT_XISO,
    input_file=Path("Halo 3_decrypted.iso"),
    output_file=Path("Halo 3/"),
    tool="extract-xiso",
    status=TransformStatus.SUCCESS,
    duration_seconds=8.2,
))

# Step 4: Rebuild
transformation.add_step(TransformStep(
    step_type=TransformType.REBUILD_XISO,
    input_file=Path("Halo 3/"),
    output_file=Path("Halo 3_rebuilt.iso"),
    tool="xdvdfs",
    status=TransformStatus.SUCCESS,
    duration_seconds=12.1,
))

# Step 5: Compress
transformation.add_step(TransformStep(
    step_type=TransformType.COMPRESS_XISO,
    input_file=Path("Halo 3_rebuilt.iso"),
    output_file=Path("Halo 3.xiso"),
    tool="maxcso",
    status=TransformStatus.SUCCESS,
    duration_seconds=45.3,
))

transformation.final_file = Path("Halo 3.xiso")
transformation.status = TransformStatus.SUCCESS

print(transformation.get_summary())
# Output: ✓ Halo 3.zip → Halo 3.xiso (45% of original) (83.6s)

# Print each step
for step in transformation.steps:
    print(f"  {step}")
# Output:
#   ✓ unzip: Halo 3.zip → Halo 3.iso
#   ✓ decrypt_xbox360: Halo 3.iso → Halo 3_decrypted.iso
#   ✓ extract_xiso: Halo 3_decrypted.iso → Halo 3/
#   ✓ rebuild_xiso: Halo 3/ → Halo 3_rebuilt.iso
#   ✓ compress_xiso: Halo 3_rebuilt.iso → Halo 3.xiso
"""
