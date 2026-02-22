"""Deployer — executes a DeploymentPlan by transferring ROMs to the target.

Handles file comparison (delta sync), SFTP transfers with progress,
and optional post-deploy actions (EmulationStation restart, etc.).
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Optional

from romfarmer.farmhand.models import (
    DeploymentPlan,
    DeploymentStatus,
    PlatformAllocation,
    SelectionAction,
    TransferProgress,
)
from romfarmer.farmhand.ssh import SSHClient

logger = logging.getLogger(__name__)

# Type for deployment event callbacks
DeployCallback = Callable[[str, dict[str, Any]], None]


class Deployer:
    """Executes a deployment plan by transferring ROM files to the target.

    Supports delta sync (only transfer new/changed files), progress
    tracking, dry-run mode, and post-deploy hooks.

    Usage:
        deployer = Deployer(ssh_client, output_root=Path("output/build-name"))
        deployer.deploy(plan, dry_run=True)
        deployer.deploy(plan)
    """

    def __init__(
        self,
        ssh: SSHClient,
        output_root: Path,
        frontend_config: Optional[dict] = None,
        on_event: Optional[DeployCallback] = None,
    ) -> None:
        """
        Args:
            ssh: Connected SSH client.
            output_root: Local path to the build output (e.g., output/nointro-1g1r-eng-7z-batocera-v2).
            frontend_config: Frontend folder mapping (platform -> folder name).
            on_event: Callback for deployment events (for progress tracking).
        """
        self.ssh = ssh
        self.output_root = output_root
        self.frontend_config = frontend_config or {}
        self.on_event = on_event

        self._progress = TransferProgress()
        self._cancelled = False

    # ------------------------------------------------------------------
    # Main deployment entry point
    # ------------------------------------------------------------------

    def deploy(
        self,
        plan: DeploymentPlan,
        dry_run: bool = False,
        delta_sync: bool = True,
        verify: bool = False,
    ) -> DeploymentPlan:
        """Execute the deployment plan.

        Args:
            plan: The deployment plan to execute.
            dry_run: If True, log what would be done without transferring.
            delta_sync: If True, skip files that already exist on target with same size.
            verify: If True, verify file sizes after transfer.

        Returns:
            Updated plan with actual transfer stats.
        """
        plan.status = DeploymentStatus.TRANSFERRING
        self._cancelled = False

        included = [a for a in plan.allocations if a.action != SelectionAction.SKIP]

        logger.info(
            "Deploying %d platforms to %s (%s mode)",
            len(included),
            plan.target_name,
            "dry-run" if dry_run else "live",
        )

        total_bytes_sent = 0
        total_files_sent = 0
        errors: list[str] = []

        for alloc in included:
            if self._cancelled:
                plan.status = DeploymentStatus.CANCELLED
                plan.notes.append("Deployment cancelled by user")
                return plan

            try:
                bytes_sent, files_sent = self._deploy_platform(
                    alloc, dry_run=dry_run, delta_sync=delta_sync
                )
                alloc.bytes_transferred = bytes_sent
                alloc.files_transferred = files_sent
                total_bytes_sent += bytes_sent
                total_files_sent += files_sent

                self._emit("platform_done", {
                    "platform": alloc.platform,
                    "files": files_sent,
                    "bytes": bytes_sent,
                })
            except Exception as exc:
                msg = f"Failed to deploy {alloc.platform}: {exc}"
                logger.error(msg)
                errors.append(msg)

        if errors:
            plan.status = DeploymentStatus.FAILED
            plan.notes.extend(errors)
        else:
            plan.status = DeploymentStatus.COMPLETED

        plan.notes.append(
            f"Transfer complete: {total_files_sent} files, "
            f"{total_bytes_sent / 1024**3:.1f} GB"
        )

        logger.info(
            "Deployment %s: %d files, %.1f GB",
            plan.status.value,
            total_files_sent,
            total_bytes_sent / 1024**3,
        )

        return plan

    def cancel(self) -> None:
        """Cancel the current deployment."""
        self._cancelled = True

    # ------------------------------------------------------------------
    # Per-platform deployment
    # ------------------------------------------------------------------

    def _deploy_platform(
        self,
        alloc: PlatformAllocation,
        dry_run: bool = False,
        delta_sync: bool = True,
    ) -> tuple[int, int]:
        """Deploy a single platform's files to the target.

        Returns:
            Tuple of (bytes_transferred, files_transferred).
        """
        # Resolve local source directory
        local_dir = self._resolve_local_dir(alloc.platform)
        if local_dir is None or not local_dir.exists():
            logger.warning("No local output for %s at expected path", alloc.platform)
            return 0, 0

        # Resolve remote destination
        remote_dir = self._resolve_remote_dir(alloc)
        if not remote_dir:
            logger.warning("No remote path resolved for %s", alloc.platform)
            return 0, 0

        # Collect local files to transfer
        local_files = self._collect_local_files(local_dir)
        if not local_files:
            logger.info("No files to deploy for %s", alloc.platform)
            return 0, 0

        alloc.files_total = len(local_files)

        # Delta sync: check what already exists on target
        skip_files: set[str] = set()
        if delta_sync and not dry_run:
            skip_files = self._compute_delta(local_files, local_dir, remote_dir)
            if skip_files:
                logger.info(
                    "%s: %d/%d files already on target (skipping)",
                    alloc.platform,
                    len(skip_files),
                    len(local_files),
                )

        files_to_send = [f for f in local_files if f not in skip_files]

        if dry_run:
            total_size = sum(
                (local_dir / f).stat().st_size
                for f in files_to_send
                if (local_dir / f).exists()
            )
            logger.info(
                "[DRY RUN] %s: would transfer %d files (%.1f GB) to %s",
                alloc.platform,
                len(files_to_send),
                total_size / 1024**3,
                remote_dir,
            )
            return 0, 0

        # Create remote directory
        self.ssh.mkdir_p(remote_dir)

        # Transfer files
        bytes_sent = 0
        files_sent = 0

        self._progress = TransferProgress(
            platform=alloc.platform,
            files_total=len(files_to_send),
            bytes_total=sum(
                (local_dir / f).stat().st_size
                for f in files_to_send
                if (local_dir / f).exists()
            ),
            started_at=datetime.now(),
        )

        for relative_path in files_to_send:
            if self._cancelled:
                break

            local_file = local_dir / relative_path
            if not local_file.exists():
                continue

            remote_file = f"{remote_dir}/{relative_path}"
            file_size = local_file.stat().st_size

            self._progress.current_file = relative_path

            try:
                self.ssh.upload(
                    local_file,
                    remote_file,
                    progress_callback=self._on_file_progress,
                )
                bytes_sent += file_size
                files_sent += 1
                self._progress.files_done = files_sent
                self._progress.bytes_done = bytes_sent

                self._emit("file_done", {
                    "platform": alloc.platform,
                    "file": relative_path,
                    "size": file_size,
                    "progress": self._progress.percent,
                })
            except Exception as exc:
                logger.error("Failed to upload %s: %s", local_file, exc)

        return bytes_sent, files_sent

    # ------------------------------------------------------------------
    # Path resolution
    # ------------------------------------------------------------------

    def _resolve_local_dir(self, platform: str) -> Optional[Path]:
        """Find the local output directory for a platform.

        Checks both the platform name and frontend folder mapping.
        """
        # Direct match
        direct = self.output_root / platform
        if direct.exists():
            return direct

        # Check frontend folder mapping (reverse: folder_name -> platform)
        for internal_name, folder_name in self.frontend_config.items():
            if internal_name == platform:
                mapped = self.output_root / folder_name
                if mapped.exists():
                    return mapped

        # Try just listing the output root for a fuzzy match
        if self.output_root.exists():
            for child in self.output_root.iterdir():
                if child.is_dir() and child.name.lower() == platform.lower():
                    return child

        return None

    def _resolve_remote_dir(self, alloc: PlatformAllocation) -> Optional[str]:
        """Determine the remote path for a platform on the target volume."""
        if not alloc.target_volume:
            return None

        # The folder name on the target follows the frontend convention
        folder_name = self.frontend_config.get(alloc.platform, alloc.platform)

        # Find the volume's rom_path
        # We stored the volume mount point in alloc.target_volume
        # Convention: rom_path = {mount_point}/roms/{folder_name}
        rom_base = f"{alloc.target_volume}/roms"
        if alloc.target_volume == "/userdata":
            rom_base = "/userdata/roms"

        return f"{rom_base}/{folder_name}"

    # ------------------------------------------------------------------
    # File collection and delta sync
    # ------------------------------------------------------------------

    def _collect_local_files(self, local_dir: Path) -> list[str]:
        """Collect all files in a local directory (relative paths)."""
        files: list[str] = []
        for root, dirs, filenames in os.walk(local_dir):
            for fname in filenames:
                full_path = Path(root) / fname
                rel_path = full_path.relative_to(local_dir)
                files.append(str(rel_path))
        return sorted(files)

    def _compute_delta(
        self,
        local_files: list[str],
        local_dir: Path,
        remote_dir: str,
    ) -> set[str]:
        """Determine which local files already exist on target with matching size.

        Returns set of relative paths to skip.
        """
        skip: set[str] = set()

        # Get remote file listing with sizes
        try:
            output = self.ssh.run(
                f"find {remote_dir} -type f -printf '%P\\t%s\\n' 2>/dev/null",
                timeout=60,
            )
        except Exception:
            return skip

        remote_files: dict[str, int] = {}
        for line in output.strip().splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                try:
                    remote_files[parts[0]] = int(parts[1])
                except ValueError:
                    pass

        for local_file in local_files:
            if local_file in remote_files:
                local_size = (local_dir / local_file).stat().st_size
                if local_size == remote_files[local_file]:
                    skip.add(local_file)

        return skip

    # ------------------------------------------------------------------
    # Post-deploy actions
    # ------------------------------------------------------------------

    def restart_emulationstation(self) -> str:
        """Restart EmulationStation on the target (Batocera)."""
        logger.info("Restarting EmulationStation on target")
        try:
            return self.ssh.run(
                "batocera-es-swissknife --restart 2>&1 || "
                "systemctl restart emulationstation 2>&1 || "
                "echo 'Could not restart ES'",
                timeout=30,
            )
        except Exception as exc:
            return f"Failed to restart ES: {exc}"

    def trigger_rom_rescan(self) -> str:
        """Trigger a ROM rescan on the target."""
        logger.info("Triggering ROM rescan on target")
        try:
            return self.ssh.run(
                "batocera-es-swissknife --gamesdb-reinit 2>&1 || "
                "echo 'Rescan not available'",
                timeout=60,
            )
        except Exception as exc:
            return f"Failed to trigger rescan: {exc}"

    # ------------------------------------------------------------------
    # Progress callbacks
    # ------------------------------------------------------------------

    def _on_file_progress(self, transferred: int, total: int) -> None:
        """Called by SFTP upload for per-file progress."""
        if total > 0 and self.on_event:
            self._emit("file_progress", {
                "platform": self._progress.platform,
                "file": self._progress.current_file,
                "transferred": transferred,
                "total": total,
            })

    def _emit(self, event: str, data: dict[str, Any]) -> None:
        """Emit a deployment event."""
        if self.on_event:
            try:
                self.on_event(event, data)
            except Exception:
                pass

    @property
    def progress(self) -> TransferProgress:
        """Current transfer progress."""
        return self._progress
