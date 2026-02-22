"""Target system analyzer — introspects remote hosts via SSH.

Discovers volumes, existing ROMs, installed binaries, emulator capabilities,
and system information. Populates a TargetProfile with everything the
planner needs to make deployment decisions.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import PurePosixPath
from typing import Optional

from romfarmer.farmhand.models import (
    SystemInfo,
    TargetCapabilities,
    TargetProfile,
    VolumeInfo,
    VolumeRole,
)
from romfarmer.farmhand.ssh import SSHClient

logger = logging.getLogger(__name__)

# Default Batocera ROM path on the primary data partition
BATOCERA_ROM_PATH = "/userdata/roms"
# Batocera secondary storage convention — ROMs can live under /media/*/roms
BATOCERA_MEDIA_PREFIX = "/media"

# Common emulator-related binaries to check for
_EMULATOR_BINARIES = [
    "retroarch",
    "mame",
    "dolphin-emu",
    "dolphin-emu-nogui",
    "ppsspp",
    "pcsx2",
    "rpcs3",
    "duckstation",
    "flycast",
    "mednafen",
    "mupen64plus",
    "citra",
    "yuzu",
    "ryujinx",
    "xemu",
    "cemu",
]

# Utility binaries relevant to ROM format support
_UTILITY_BINARIES = [
    "7z",
    "7zr",
    "7za",
    "unzip",
    "zip",
    "chdman",
    "extract-xiso",
    "maxcso",
    "rsync",
    "md5sum",
    "sha1sum",
]


class TargetAnalyzer:
    """Analyzes a remote target system to build a complete TargetProfile.

    Usage:
        analyzer = TargetAnalyzer(ssh_client)
        profile = analyzer.full_scan(name="batocera-nuc", frontend="batocera")
    """

    def __init__(self, ssh: SSHClient) -> None:
        self.ssh = ssh

    # ------------------------------------------------------------------
    # Full scan — combines all the sub-scans
    # ------------------------------------------------------------------

    def full_scan(
        self,
        name: str,
        frontend: str = "batocera",
        device_type: str = "pc",
    ) -> TargetProfile:
        """Run a full analysis of the target and return a populated TargetProfile."""
        logger.info("Starting full scan of %s (%s)", self.ssh.host, frontend)

        profile = TargetProfile(
            name=name,
            host=self.ssh.host,
            port=self.ssh.port,
            user=self.ssh.user,
            auth_method="key_file" if self.ssh.key_file else "password",
            key_file=self.ssh.key_file,
            frontend=frontend,
            device_type=device_type,
        )

        profile.system_info = self.scan_system_info()
        profile.volumes = self.scan_volumes(frontend=frontend)
        profile.capabilities = self.scan_capabilities()
        profile.existing_roms = self.scan_existing_roms(profile.volumes)
        profile.last_scanned = datetime.now()

        logger.info(
            "Scan complete: %d volumes, %d platforms with existing ROMs, %d binaries",
            len(profile.volumes),
            len(profile.existing_roms),
            len(profile.capabilities.binaries) if profile.capabilities else 0,
        )
        return profile

    # ------------------------------------------------------------------
    # System information
    # ------------------------------------------------------------------

    def scan_system_info(self) -> SystemInfo:
        """Gather system information from the target."""
        info = SystemInfo()

        # Hostname
        try:
            info.hostname = self.ssh.run("hostname").strip()
        except Exception:
            pass

        # Kernel / architecture
        try:
            uname = self.ssh.run("uname -srm").strip()
            parts = uname.split()
            if len(parts) >= 1:
                info.os_name = parts[0]  # Linux
            if len(parts) >= 2:
                info.kernel_version = parts[1]
            if len(parts) >= 3:
                info.architecture = parts[2]
        except Exception:
            pass

        # CPU info
        try:
            cpu_out = self.ssh.run("cat /proc/cpuinfo | head -30").strip()
            for line in cpu_out.splitlines():
                if line.startswith("model name"):
                    info.cpu_model = line.split(":", 1)[1].strip()
                elif line.startswith("cpu cores"):
                    try:
                        info.cpu_cores = int(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass
            # Thread count
            nproc = self.ssh.run("nproc 2>/dev/null").strip()
            try:
                info.cpu_threads = int(nproc)
            except ValueError:
                pass
        except Exception:
            pass

        # Memory
        try:
            mem_out = self.ssh.run("cat /proc/meminfo | head -3").strip()
            for line in mem_out.splitlines():
                if line.startswith("MemTotal"):
                    kb = int(re.search(r"(\d+)", line).group(1))  # type: ignore[union-attr]
                    info.memory_total_mb = kb // 1024
                elif line.startswith("MemAvailable"):
                    kb = int(re.search(r"(\d+)", line).group(1))  # type: ignore[union-attr]
                    info.memory_available_mb = kb // 1024
        except Exception:
            pass

        # Batocera-specific: OS version
        try:
            batocera_version = self.ssh.run(
                "cat /usr/share/batocera/batocera.version 2>/dev/null"
            ).strip()
            if batocera_version:
                info.os_name = "Batocera"
                info.os_version = batocera_version
        except Exception:
            pass

        # Display resolution
        try:
            xrandr = self.ssh.run(
                "cat /sys/class/drm/card*/modes 2>/dev/null | head -1"
            ).strip()
            if xrandr:
                info.display_resolution = xrandr
        except Exception:
            pass

        logger.info(
            "System: %s %s, %s, %s, %d MB RAM",
            info.os_name,
            info.os_version,
            info.architecture,
            info.cpu_model,
            info.memory_total_mb,
        )
        return info

    # ------------------------------------------------------------------
    # Volume discovery
    # ------------------------------------------------------------------

    def scan_volumes(self, frontend: str = "batocera") -> list[VolumeInfo]:
        """Discover and classify storage volumes on the target."""
        raw_df = self.ssh.run("df -B1 --output=source,fstype,size,used,avail,pcent,target")
        volumes: list[VolumeInfo] = []

        for line in raw_df.strip().splitlines()[1:]:  # skip header
            parts = line.split()
            if len(parts) < 7:
                continue

            device = parts[0]
            fstype = parts[1]
            mount_point = parts[-1]

            # Skip pseudo-filesystems
            if fstype in ("tmpfs", "devtmpfs", "overlay", "squashfs", "none"):
                continue
            if mount_point in ("/", "/boot"):
                continue

            try:
                total = int(parts[2])
                used = int(parts[3])
                avail = int(parts[4])
                pct_str = parts[5].rstrip("%")
                pct = float(pct_str)
            except (ValueError, IndexError):
                continue

            # Classify the volume's role
            role = self._classify_volume(mount_point, frontend)
            rom_path = self._infer_rom_path(mount_point, role, frontend)

            vol = VolumeInfo(
                mount_point=mount_point,
                filesystem=fstype,
                device=device,
                total_bytes=total,
                used_bytes=used,
                available_bytes=avail,
                use_percent=pct,
                role=role,
                rom_path=rom_path,
            )
            volumes.append(vol)
            logger.info(
                "Volume %s: %.1f GB total, %.1f GB free, role=%s, rom_path=%s",
                mount_point,
                vol.total_gb,
                vol.available_gb,
                role.value,
                rom_path or "none",
            )

        return volumes

    def _classify_volume(self, mount_point: str, frontend: str) -> VolumeRole:
        """Determine the role of a volume based on its mount point."""
        if frontend == "batocera":
            if mount_point == "/userdata":
                return VolumeRole.PRIMARY
            elif mount_point.startswith("/media/"):
                return VolumeRole.SECONDARY
        elif frontend == "rocknix":
            if mount_point in ("/storage", "/userdata"):
                return VolumeRole.PRIMARY
            elif mount_point.startswith("/media/") or mount_point.startswith("/mnt/"):
                return VolumeRole.SECONDARY
        # Generic fallback
        if mount_point == "/":
            return VolumeRole.SYSTEM
        return VolumeRole.SECONDARY

    def _infer_rom_path(
        self, mount_point: str, role: VolumeRole, frontend: str
    ) -> Optional[str]:
        """Infer where ROMs should be stored on a given volume."""
        if role == VolumeRole.SYSTEM:
            return None

        if frontend == "batocera":
            if mount_point == "/userdata":
                return "/userdata/roms"
            elif mount_point.startswith("/media/"):
                # Secondary drives: ROMs go in a roms/ subdirectory
                return f"{mount_point}/roms"
        elif frontend == "rocknix":
            if mount_point in ("/storage", "/userdata"):
                return f"{mount_point}/roms"
            else:
                return f"{mount_point}/roms"

        return f"{mount_point}/roms"

    # ------------------------------------------------------------------
    # Capability detection
    # ------------------------------------------------------------------

    def scan_capabilities(self) -> TargetCapabilities:
        """Detect available binaries and emulator capabilities on the target."""
        caps = TargetCapabilities()

        # Check for utility binaries
        all_binaries = _EMULATOR_BINARIES + _UTILITY_BINARIES
        which_cmd = " && ".join(f"which {b} 2>/dev/null || true" for b in all_binaries)
        output = self.ssh.run(which_cmd, timeout=15)

        found_paths = [line.strip() for line in output.splitlines() if line.strip()]
        for path in found_paths:
            binary_name = PurePosixPath(path).name
            caps.binaries.append(binary_name)
            if binary_name in _EMULATOR_BINARIES:
                caps.emulators.append(binary_name)

        caps.has_7z = any(b in caps.binaries for b in ("7z", "7zr", "7za"))
        caps.has_chdman = "chdman" in caps.binaries

        # Try to discover Batocera emulator configuration
        try:
            es_systems = self.ssh.run(
                "cat /usr/share/batocera/configgen/configgen-defaults.yml 2>/dev/null | head -100",
                timeout=10,
            )
            if es_systems.strip():
                logger.info("Found Batocera configgen defaults — can parse emulator assignments")
                # We could parse this deeply; for now just note it exists
        except Exception:
            pass

        # Detect RetroArch cores if available
        try:
            cores_output = self.ssh.run(
                "ls /usr/lib/libretro/ 2>/dev/null | head -50", timeout=10
            )
            if cores_output.strip():
                cores = [
                    line.strip().replace("_libretro.so", "").replace(".so", "")
                    for line in cores_output.splitlines()
                    if line.strip()
                ]
                caps.emulators.extend(cores[:50])  # cap at 50 to avoid bloat
        except Exception:
            pass

        logger.info(
            "Capabilities: %d binaries, %d emulators, 7z=%s, chdman=%s",
            len(caps.binaries),
            len(caps.emulators),
            caps.has_7z,
            caps.has_chdman,
        )
        return caps

    # ------------------------------------------------------------------
    # Existing ROM discovery
    # ------------------------------------------------------------------

    def scan_existing_roms(
        self,
        volumes: list[VolumeInfo],
        max_files_per_platform: int = 10000,
    ) -> dict[str, list[str]]:
        """Scan target volumes for existing ROMs, organized by platform folder.

        Returns:
            Dict mapping platform folder name -> list of ROM filenames.
            e.g., {"psx": ["Final Fantasy VII (USA).chd", ...], "nes": [...]}
        """
        existing: dict[str, list[str]] = {}

        for vol in volumes:
            if not vol.rom_path:
                continue

            # Check if the roms directory exists
            try:
                entries = self.ssh.run(
                    f"ls -1 {vol.rom_path}/ 2>/dev/null", timeout=15
                ).strip()
                if not entries:
                    continue
            except Exception:
                continue

            platform_dirs = [d.strip() for d in entries.splitlines() if d.strip()]

            for platform_dir in platform_dirs:
                platform_path = f"{vol.rom_path}/{platform_dir}"
                try:
                    # Get file listing (just names, not directories)
                    files_output = self.ssh.run(
                        f"find {platform_path} -maxdepth 1 -type f -printf '%f\\n' "
                        f"2>/dev/null | head -{max_files_per_platform}",
                        timeout=30,
                    )
                    files = [f.strip() for f in files_output.splitlines() if f.strip()]
                    if files:
                        # Accumulate across volumes
                        if platform_dir in existing:
                            existing[platform_dir].extend(files)
                        else:
                            existing[platform_dir] = files
                except Exception as exc:
                    logger.warning("Failed to scan %s: %s", platform_path, exc)
                    continue

        total_roms = sum(len(v) for v in existing.values())
        logger.info(
            "Found existing ROMs: %d platforms, %d files total",
            len(existing),
            total_roms,
        )
        return existing

    # ------------------------------------------------------------------
    # Utility: quick probe
    # ------------------------------------------------------------------

    def quick_probe(self) -> dict:
        """Fast probe — just hostname, OS, and disk space. No ROM scanning."""
        hostname = self.ssh.run("hostname").strip()
        df_output = self.ssh.run("df -h")
        uname = self.ssh.run("uname -srm").strip()
        return {
            "hostname": hostname,
            "uname": uname,
            "disk_usage": df_output,
            "connected": True,
        }
