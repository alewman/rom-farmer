"""Emit extras stage — organize DLC/updates into destination subdirs + install scripts.

This stage handles "extras" platforms — content that doesn't go into the ROM
folder directly but needs to be installed on the target system (e.g., DLC WADs
installed to Dolphin NAND, PS3 DLC copied to dev_hdd0, etc.).

The wii-extras platform config defines:
  extras:
    destinations:
      nand: "(DLC)"           # filename pattern → subfolder
    install_scripts:
      batocera:
        template: wii-nand-install-batocera
      retrobat:
        template: wii-nand-install-retrobat

Output structure:
  output/.../wii-extras/
    nand/
      Mega Man 9 (USA) (WiiWare) (DLC).wad
      ...
    install.sh        (Batocera)
    install.bat       (RetroBat)
"""

import logging
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Stage, StageContext, StageResult, StageStatus, StagePhase

logger = logging.getLogger(__name__)

# Template directory relative to project root
# Resolve from package location to handle any CWD
TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"


class EmitExtrasStage(Stage):
    PHASE = StagePhase.FINALIZE

    """Organize extras into destination subdirs and emit install scripts.

    This stage:
    1. Reads extras config from platform_config
    2. Sorts source_files into destination subdirectories by filename pattern
    3. Copies install script templates to output, renamed per frontend
    """

    def __init__(self, extras_config: Optional[Dict[str, Any]] = None):
        """Initialize extras stage.

        Args:
            extras_config: The 'extras' section from platform YAML config.
                           Contains 'destinations' and 'install_scripts'.
        """
        super().__init__("Emit Extras")
        self.extras_config = extras_config or {}

    def should_skip(self, context: StageContext) -> bool:
        """Skip if no extras config or no files."""
        if not self.extras_config:
            return True
        # Prefer filtered_files (CAS-backed after ingest), fall back to source_files
        files = context.filtered_files or context.source_files
        if not files:
            return True
        return False

    def execute(self, context: StageContext) -> StageResult:
        """Execute extras organization and script emission."""
        start = time.time()

        destinations = self.extras_config.get("destinations", {})
        install_scripts = self.extras_config.get("install_scripts", {})

        if not destinations:
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No destination mappings configured",
            )

        output_dir = context.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use filtered_files if available (CAS-backed after ingest stage),
        # otherwise fall back to source_files for backwards compatibility
        files_to_sort = context.filtered_files or context.source_files

        # ── 1. Sort files into destination subdirs ────────────────────────
        sorted_count = 0
        unmatched: List[Path] = []

        for src_file in files_to_sort:
            placed = False
            for dest_subdir, pattern in destinations.items():
                if pattern in src_file.name:
                    dest_dir = output_dir / dest_subdir
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    dest_file = dest_dir / src_file.name
                    if not dest_file.exists():
                        # Hardlink if same filesystem, else copy
                        try:
                            dest_file.hardlink_to(src_file)
                        except OSError:
                            shutil.copy2(src_file, dest_file)
                    sorted_count += 1
                    placed = True
                    break

            if not placed:
                unmatched.append(src_file)

        self._log(
            context,
            f"Sorted {sorted_count} files into "
            f"{len(destinations)} destination(s)",
        )

        if unmatched:
            self._log_warning(
                context,
                f"{len(unmatched)} files didn't match any destination pattern",
            )

        # ── 2. Emit install scripts ───────────────────────────────────────
        scripts_emitted = 0
        target_name = context.target_name

        # Determine which frontend we're building for
        frontend = None
        if context.composed_target:
            fe = getattr(context.composed_target, "frontend", None)
            if fe:
                frontend = getattr(fe, "name", None)
        if not frontend:
            # Infer from target name
            target_lower = target_name.lower()
            if "batocera" in target_lower:
                frontend = "batocera"
            elif "retrobat" in target_lower:
                frontend = "retrobat"

        if frontend and frontend in install_scripts:
            script_config = install_scripts[frontend]
            template_name = script_config.get("template", "")

            if template_name:
                scripts_emitted = self._emit_script(
                    context, output_dir, template_name, frontend
                )

        duration = time.time() - start

        return StageResult(
            status=StageStatus.SUCCESS,
            message=(
                f"Organized {sorted_count} extras, "
                f"emitted {scripts_emitted} install script(s)"
            ),
            files_processed=sorted_count,
            files_matched=sorted_count,
            files_skipped=len(unmatched),
            duration_seconds=duration,
            details={
                "sorted": sorted_count,
                "unmatched": len(unmatched),
                "scripts_emitted": scripts_emitted,
                "frontend": frontend,
            },
        )

    def _emit_script(
        self,
        context: StageContext,
        output_dir: Path,
        template_name: str,
        frontend: str,
    ) -> int:
        """Copy install script template to output directory.

        Returns:
            Number of scripts emitted (0 or 1).
        """
        # Determine script extension from frontend
        ext = ".bat" if frontend == "retrobat" else ".sh"
        template_file = TEMPLATE_DIR / f"{template_name}{ext}"

        if not template_file.exists():
            self._log_warning(
                context,
                f"Template not found: {template_file}",
            )
            return 0

        dest_script = output_dir / f"install{ext}"
        shutil.copy2(template_file, dest_script)

        # Make shell scripts executable
        if ext == ".sh":
            dest_script.chmod(0o755)

        self._log(context, f"Emitted install script: {dest_script.name}")
        return 1
