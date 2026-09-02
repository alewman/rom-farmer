"""Unit tests for Farm-Hand deployment system.

Tests the core logic — models, planner, deployer — with mocked SSH.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from romfarmer.farmhand.planner import SpacePlanner

from romfarmer.farmhand.models import (
    DeploymentPlan,
    DeploymentStatus,
    PlatformAllocation,
    PlatformSizeInfo,
    PlatformTier,
    SelectionAction,
    SystemInfo,
    TargetCapabilities,
    TargetProfile,
    TransferProgress,
    VolumeInfo,
    VolumeRole,
)


# =========================================================================
# Model tests
# =========================================================================


class TestVolumeInfo:
    def test_basic_properties(self) -> None:
        vol = VolumeInfo(
            mount_point="/userdata",
            total_bytes=2_000_000_000_000,  # ~2 TB
            used_bytes=1_800_000_000_000,
            available_bytes=200_000_000_000,
            use_percent=90.0,
        )
        assert vol.total_gb == pytest.approx(2000 / 1.073741824, rel=0.01)
        assert vol.available_gb == pytest.approx(200 / 1.073741824, rel=0.01)
        assert vol.role == VolumeRole.SYSTEM  # default

    def test_rom_volume(self) -> None:
        vol = VolumeInfo(
            mount_point="/userdata",
            total_bytes=2_000_000_000_000,
            used_bytes=0,
            available_bytes=2_000_000_000_000,
            use_percent=0.0,
            role=VolumeRole.PRIMARY,
            rom_path="/userdata/roms",
        )
        assert vol.rom_path == "/userdata/roms"
        assert vol.role == VolumeRole.PRIMARY


class TestTargetProfile:
    def test_get_rom_volumes(self) -> None:
        profile = TargetProfile(
            name="test",
            host="192.0.2.10",
            volumes=[
                VolumeInfo(
                    mount_point="/userdata",
                    total_bytes=2_000_000_000_000,
                    used_bytes=1_800_000_000_000,
                    available_bytes=200_000_000_000,
                    use_percent=90.0,
                    role=VolumeRole.PRIMARY,
                    rom_path="/userdata/roms",
                ),
                VolumeInfo(
                    mount_point="/media/int2tbhd",
                    total_bytes=2_000_000_000_000,
                    used_bytes=800_000_000_000,
                    available_bytes=1_200_000_000_000,
                    use_percent=40.0,
                    role=VolumeRole.SECONDARY,
                    rom_path="/media/int2tbhd/roms",
                ),
                VolumeInfo(
                    mount_point="/boot",
                    total_bytes=8_000_000_000,
                    used_bytes=4_000_000_000,
                    available_bytes=4_000_000_000,
                    use_percent=50.0,
                    role=VolumeRole.SYSTEM,
                ),
            ],
        )
        rom_vols = profile.get_rom_volumes()
        assert len(rom_vols) == 2
        assert rom_vols[0].mount_point == "/userdata"
        assert rom_vols[1].mount_point == "/media/int2tbhd"

    def test_total_available(self) -> None:
        profile = TargetProfile(
            name="test",
            host="192.0.2.10",
            volumes=[
                VolumeInfo(
                    mount_point="/userdata",
                    total_bytes=2_000_000_000_000,
                    used_bytes=1_800_000_000_000,
                    available_bytes=200_000_000_000,
                    use_percent=90.0,
                    role=VolumeRole.PRIMARY,
                    rom_path="/userdata/roms",
                ),
                VolumeInfo(
                    mount_point="/media/hdd",
                    total_bytes=2_000_000_000_000,
                    used_bytes=800_000_000_000,
                    available_bytes=1_200_000_000_000,
                    use_percent=40.0,
                    role=VolumeRole.SECONDARY,
                    rom_path="/media/hdd/roms",
                ),
            ],
        )
        total = profile.total_available_bytes()
        assert total == 200_000_000_000 + 1_200_000_000_000

    def test_get_primary_volume(self) -> None:
        profile = TargetProfile(
            name="test",
            host="192.0.2.10",
            volumes=[
                VolumeInfo(
                    mount_point="/userdata",
                    total_bytes=100,
                    used_bytes=50,
                    available_bytes=50,
                    use_percent=50.0,
                    role=VolumeRole.PRIMARY,
                    rom_path="/userdata/roms",
                ),
            ],
        )
        primary = profile.get_primary_volume()
        assert primary is not None
        assert primary.mount_point == "/userdata"

    def test_no_primary(self) -> None:
        profile = TargetProfile(name="test", host="192.0.2.10")
        assert profile.get_primary_volume() is None

    def test_serialization_roundtrip(self) -> None:
        profile = TargetProfile(
            name="test-nuc",
            host="192.0.2.10",
            user="root",
            frontend="batocera",
            system_info=SystemInfo(hostname="BATOCERA", os_name="Batocera", os_version="42"),
            volumes=[
                VolumeInfo(
                    mount_point="/userdata",
                    total_bytes=2_000_000_000_000,
                    used_bytes=1_000_000_000_000,
                    available_bytes=1_000_000_000_000,
                    use_percent=50.0,
                    role=VolumeRole.PRIMARY,
                    rom_path="/userdata/roms",
                ),
            ],
            capabilities=TargetCapabilities(binaries=["7z", "chdman"], has_7z=True, has_chdman=True),
        )
        json_str = profile.model_dump_json()
        restored = TargetProfile.model_validate_json(json_str)
        assert restored.name == "test-nuc"
        assert restored.system_info.hostname == "BATOCERA"
        assert len(restored.volumes) == 1
        assert restored.capabilities.has_7z is True


class TestDeploymentPlan:
    def test_summary(self) -> None:
        plan = DeploymentPlan(
            target_name="test",
            total_available_bytes=1_000_000_000_000,
            platforms_included=25,
            platforms_skipped=3,
            total_allocated_bytes=800_000_000_000,
        )
        s = plan.summary()
        assert "test" in s
        assert "25 included" in s

    def test_headroom(self) -> None:
        plan = DeploymentPlan(
            target_name="test",
            total_available_bytes=1_000_000_000_000,
            total_allocated_bytes=800_000_000_000,
        )
        assert plan.headroom_bytes == 200_000_000_000

    def test_get_allocations_for_volume(self) -> None:
        plan = DeploymentPlan(
            target_name="test",
            allocations=[
                PlatformAllocation(
                    platform="nes",
                    tier=PlatformTier.SMALL,
                    action=SelectionAction.INCLUDE_ALL,
                    target_volume="/userdata",
                ),
                PlatformAllocation(
                    platform="ps2",
                    tier=PlatformTier.MASSIVE,
                    action=SelectionAction.BUDGET_SELECT,
                    target_volume="/media/hdd",
                ),
                PlatformAllocation(
                    platform="snes",
                    tier=PlatformTier.SMALL,
                    action=SelectionAction.INCLUDE_ALL,
                    target_volume="/userdata",
                ),
            ],
        )
        userdata_allocs = plan.get_allocations_for_volume("/userdata")
        assert len(userdata_allocs) == 2
        hdd_allocs = plan.get_allocations_for_volume("/media/hdd")
        assert len(hdd_allocs) == 1
        assert hdd_allocs[0].platform == "ps2"


class TestTransferProgress:
    def test_percent(self) -> None:
        p = TransferProgress(bytes_total=1000, bytes_done=500)
        assert p.percent == 50.0

    def test_zero_total(self) -> None:
        p = TransferProgress(bytes_total=0, bytes_done=0)
        assert p.percent == 0.0

    def test_speed(self) -> None:
        p = TransferProgress(bytes_per_second=10 * 1024 * 1024)
        assert p.speed_mbps == pytest.approx(10.0)


# =========================================================================
# Planner tests
# =========================================================================


class TestPlatformTierClassification:
    def test_tiny(self) -> None:
        from romfarmer.farmhand.planner import classify_tier
        assert classify_tier(500_000_000) == PlatformTier.TINY  # 500 MB

    def test_small(self) -> None:
        from romfarmer.farmhand.planner import classify_tier
        assert classify_tier(5_000_000_000) == PlatformTier.SMALL  # 5 GB

    def test_medium(self) -> None:
        from romfarmer.farmhand.planner import classify_tier
        assert classify_tier(50_000_000_000) == PlatformTier.MEDIUM  # 50 GB

    def test_large(self) -> None:
        from romfarmer.farmhand.planner import classify_tier
        assert classify_tier(300_000_000_000) == PlatformTier.LARGE  # 300 GB

    def test_massive(self) -> None:
        from romfarmer.farmhand.planner import classify_tier
        assert classify_tier(3_000_000_000_000) == PlatformTier.MASSIVE  # 3 TB


class TestSpacePlanner:
    """Test the SpacePlanner with a mock size_data.json."""

    @pytest.fixture
    def mock_size_data(self, tmp_path: Path) -> Path:
        """Create a temporary size_data.json with representative platforms."""
        data = {
            "nes": [{"platform": "nes", "compression": "7z", "output_files": 7000, "output_size_bytes": 3_000_000_000}],
            "snes": [{"platform": "snes", "compression": "7z", "output_files": 5000, "output_size_bytes": 5_000_000_000}],
            "gb": [{"platform": "gb", "compression": "7z", "output_files": 7000, "output_size_bytes": 4_000_000_000}],
            "atarilynx": [{"platform": "atarilynx", "compression": "7z", "output_files": 2000, "output_size_bytes": 20_000_000}],
            "saturn": [{"platform": "saturn", "compression": "chd", "output_files": 4000, "output_size_bytes": 86_000_000_000}],
            "dreamcast": [{"platform": "dreamcast", "compression": "chd", "output_files": 3200, "output_size_bytes": 136_000_000_000}],
            "psx": [{"platform": "psx", "compression": "chd", "output_files": 21000, "output_size_bytes": 513_000_000_000}],
            "ps2": [{"platform": "ps2", "compression": "chd", "output_files": 13000, "output_size_bytes": 2_977_000_000_000}],
            "xbox360": [{"platform": "xbox360", "compression": "none", "output_files": 7000, "output_size_bytes": 5_865_000_000_000}],
        }
        path = tmp_path / "size_data.json"
        path.write_text(json.dumps(data))
        return path

    @pytest.fixture
    def planner(self, mock_size_data: Path) -> "SpacePlanner":
        from romfarmer.farmhand.planner import SpacePlanner
        return SpacePlanner(size_data_path=mock_size_data, workspace_root=mock_size_data.parent)

    @pytest.fixture
    def target_profile(self) -> TargetProfile:
        """Simulates the Batocera NUC with NVMe + HDD."""
        return TargetProfile(
            name="test-batocera",
            host="192.0.2.10",
            volumes=[
                VolumeInfo(
                    mount_point="/userdata",
                    total_bytes=1_800_000_000_000,
                    used_bytes=1_783_000_000_000,
                    available_bytes=17_000_000_000,  # ~17 GB free
                    use_percent=99.0,
                    role=VolumeRole.PRIMARY,
                    rom_path="/userdata/roms",
                ),
                VolumeInfo(
                    mount_point="/media/int2tbhd",
                    total_bytes=1_900_000_000_000,
                    used_bytes=743_000_000_000,
                    available_bytes=1_100_000_000_000,  # ~1.1 TB free
                    use_percent=40.0,
                    role=VolumeRole.SECONDARY,
                    rom_path="/media/int2tbhd/roms",
                ),
            ],
        )

    def test_load_size_data(self, planner: "SpacePlanner") -> None:
        sizes = planner.get_platform_sizes()
        assert len(sizes) == 9
        assert "nes" in sizes
        assert sizes["nes"].tier == PlatformTier.SMALL
        assert sizes["ps2"].tier == PlatformTier.MASSIVE

    def test_create_plan_includes_small(self, planner: "SpacePlanner", target_profile: TargetProfile) -> None:
        plan = planner.create_plan(target_profile)
        included = {a.platform for a in plan.allocations if a.action == SelectionAction.INCLUDE_ALL}
        # Small platforms should always be included
        assert "nes" in included
        assert "snes" in included
        assert "gb" in included
        assert "atarilynx" in included

    def test_create_plan_budgets_large(self, planner: "SpacePlanner", target_profile: TargetProfile) -> None:
        plan = planner.create_plan(target_profile)
        budgeted = {
            a.platform: a
            for a in plan.allocations
            if a.action == SelectionAction.BUDGET_SELECT
        }
        # PSX and PS2 should be budgeted (they're too large for full inclusion)
        assert "psx" in budgeted
        assert "ps2" in budgeted
        assert budgeted["psx"].selection_strategy == "rating_budget"

    def test_create_plan_skips_xbox360(self, planner: "SpacePlanner", target_profile: TargetProfile) -> None:
        plan = planner.create_plan(target_profile)
        skipped = {a.platform for a in plan.allocations if a.action == SelectionAction.SKIP}
        # Xbox360 at 5.87 TB with no default budget → skip
        assert "xbox360" in skipped

    def test_create_plan_respects_exclusions(self, planner: "SpacePlanner", target_profile: TargetProfile) -> None:
        plan = planner.create_plan(target_profile, exclude_platforms=["nes", "ps2"])
        platforms = {a.platform for a in plan.allocations}
        assert "nes" not in platforms
        assert "ps2" not in platforms

    def test_create_plan_respects_budget_overrides(self, planner: "SpacePlanner", target_profile: TargetProfile) -> None:
        plan = planner.create_plan(
            target_profile,
            budget_overrides={"ps2": 120, "xbox360": 50},
        )
        ps2 = next(a for a in plan.allocations if a.platform == "ps2")
        xbox360 = next(a for a in plan.allocations if a.platform == "xbox360")
        assert ps2.action == SelectionAction.BUDGET_SELECT
        assert ps2.selection_max_gb == 120
        assert xbox360.action == SelectionAction.BUDGET_SELECT
        assert xbox360.selection_max_gb == 50

    def test_create_plan_no_volumes(self, planner: "SpacePlanner") -> None:
        empty_target = TargetProfile(name="empty", host="192.0.2.1")
        plan = planner.create_plan(empty_target)
        assert plan.status == DeploymentStatus.FAILED

    def test_create_plan_summary_stats(self, planner: "SpacePlanner", target_profile: TargetProfile) -> None:
        plan = planner.create_plan(target_profile)
        assert plan.platforms_included > 0
        assert plan.total_allocated_bytes > 0
        assert plan.total_available_bytes > 0
        assert plan.headroom_bytes >= 0

    def test_estimate_platforms_count(self, planner: "SpacePlanner") -> None:
        result = planner.estimate_platforms_count(1100)
        assert result["available_gb"] == 1100
        assert result["guaranteed_platforms"] > 0
        assert "include_all" in result
        assert "budget_needed" in result
        assert "skip" in result

    def test_plan_spreads_across_volumes(self, planner: "SpacePlanner", target_profile: TargetProfile) -> None:
        """Saturn (86 GB) shouldn't fit on primary (17 GB free) — should go to secondary."""
        plan = planner.create_plan(target_profile)
        saturn = next(
            (a for a in plan.allocations if a.platform == "saturn"),
            None,
        )
        if saturn and saturn.action == SelectionAction.INCLUDE_ALL:
            # Saturn is 86 GB, primary only has 17 GB → must go to secondary
            assert saturn.target_volume == "/media/int2tbhd"


# =========================================================================
# SSH client tests (mocked)
# =========================================================================


class TestSSHClient:
    """Test SSH client with mocked paramiko."""

    @pytest.fixture
    def mock_paramiko(self) -> MagicMock:
        pytest.importorskip("paramiko", reason="requires romfarmer[farmhand]")
        with patch("romfarmer.farmhand.ssh.PARAMIKO_AVAILABLE", True):
            with patch("romfarmer.farmhand.ssh.paramiko") as mock_pkg:
                mock_client = MagicMock()
                mock_transport = MagicMock()
                mock_transport.is_active.return_value = True
                mock_client.get_transport.return_value = mock_transport
                mock_pkg.SSHClient.return_value = mock_client
                mock_pkg.AutoAddPolicy = MagicMock()
                yield mock_client

    def test_connect(self, mock_paramiko: MagicMock) -> None:
        from romfarmer.farmhand.ssh import SSHClient

        with patch("romfarmer.farmhand.ssh._ParamikoSSHClient", return_value=mock_paramiko):
            client = SSHClient("192.0.2.10", user="root", password="linux")
            client.connect()
            assert client.is_connected

    def test_run_command(self, mock_paramiko: MagicMock) -> None:
        from romfarmer.farmhand.ssh import SSHClient

        # Setup mock exec_command
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"BATOCERA\n"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_paramiko.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

        with patch("romfarmer.farmhand.ssh._ParamikoSSHClient", return_value=mock_paramiko):
            client = SSHClient("192.0.2.10", user="root", password="linux")
            client.connect()
            result = client.run("hostname")
            assert result.strip() == "BATOCERA"

    def test_close(self, mock_paramiko: MagicMock) -> None:
        from romfarmer.farmhand.ssh import SSHClient

        with patch("romfarmer.farmhand.ssh._ParamikoSSHClient", return_value=mock_paramiko):
            client = SSHClient("192.0.2.10", user="root", password="linux")
            client.connect()
            client.close()
            # After close, is_connected should be False
            assert not client.is_connected


# =========================================================================
# Analyzer tests (mocked SSH)
# =========================================================================


class TestTargetAnalyzer:

    @pytest.fixture
    def mock_ssh(self) -> MagicMock:
        ssh = MagicMock()
        ssh.host = "192.0.2.10"
        ssh.port = 22
        ssh.user = "root"
        ssh.key_file = None
        return ssh

    def test_scan_system_info(self, mock_ssh: MagicMock) -> None:
        from romfarmer.farmhand.analyzer import TargetAnalyzer

        mock_ssh.run.side_effect = [
            "BATOCERA\n",  # hostname
            "Linux 6.15.11 x86_64\n",  # uname
            "model name\t: AMD Ryzen 5 7430U\ncpu cores\t: 6\n",  # cpuinfo
            "12\n",  # nproc
            "MemTotal:     15754240 kB\nMemAvailable:  13106176 kB\n",  # meminfo
            "42\n",  # batocera version
            "1920x1080\n",  # display
        ]

        analyzer = TargetAnalyzer(mock_ssh)
        info = analyzer.scan_system_info()

        assert info.hostname == "BATOCERA"
        assert info.os_name == "Batocera"
        assert info.os_version == "42"
        assert info.architecture == "x86_64"
        assert info.cpu_cores == 6
        assert info.cpu_threads == 12
        assert info.memory_total_mb == pytest.approx(15754240 // 1024, abs=1)

    def test_scan_volumes(self, mock_ssh: MagicMock) -> None:
        from romfarmer.farmhand.analyzer import TargetAnalyzer

        mock_ssh.run.return_value = (
            "Filesystem     Type        1B-blocks          Used     Available Use% Mounted on\n"
            "/dev/nvme0n1p2 ext4  1932735283200 1915734122496   17001160704 100% /userdata\n"
            "/dev/sda1      ext4  2040109465600  797837721600 1200000000000  40% /media/int2tbhd\n"
        )

        analyzer = TargetAnalyzer(mock_ssh)
        volumes = analyzer.scan_volumes(frontend="batocera")

        assert len(volumes) == 2
        assert volumes[0].mount_point == "/userdata"
        assert volumes[0].role == VolumeRole.PRIMARY
        assert volumes[0].rom_path == "/userdata/roms"
        assert volumes[1].mount_point == "/media/int2tbhd"
        assert volumes[1].role == VolumeRole.SECONDARY
        assert volumes[1].rom_path == "/media/int2tbhd/roms"

    def test_scan_capabilities(self, mock_ssh: MagicMock) -> None:
        from romfarmer.farmhand.analyzer import TargetAnalyzer

        # which commands return paths for found binaries
        mock_ssh.run.side_effect = [
            "/usr/bin/retroarch\n/usr/bin/mame\n/usr/bin/7zr\n/usr/bin/chdman\n/usr/bin/rsync\n",
            "",  # configgen-defaults
            "mednafen_psx_libretro.so\nfbneo_libretro.so\nsnes9x_libretro.so\n",
        ]

        analyzer = TargetAnalyzer(mock_ssh)
        caps = analyzer.scan_capabilities()

        assert "retroarch" in caps.binaries
        assert "mame" in caps.binaries
        assert caps.has_7z is True
        assert caps.has_chdman is True
        assert "retroarch" in caps.emulators
        assert "mame" in caps.emulators


# =========================================================================
# Deployer tests (mocked SSH)
# =========================================================================


class TestDeployer:

    @pytest.fixture
    def mock_ssh(self) -> MagicMock:
        ssh = MagicMock()
        return ssh

    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        """Create a mock build output directory."""
        nes_dir = tmp_path / "nes"
        nes_dir.mkdir()
        (nes_dir / "Game1 (USA).7z").write_bytes(b"x" * 1000)
        (nes_dir / "Game2 (USA).7z").write_bytes(b"x" * 2000)

        snes_dir = tmp_path / "snes"
        snes_dir.mkdir()
        (snes_dir / "Game3 (USA).7z").write_bytes(b"x" * 3000)

        return tmp_path

    def test_deploy_dry_run(self, mock_ssh: MagicMock, output_dir: Path) -> None:
        from romfarmer.farmhand.deployer import Deployer

        deployer = Deployer(ssh=mock_ssh, output_root=output_dir)
        plan = DeploymentPlan(
            target_name="test",
            allocations=[
                PlatformAllocation(
                    platform="nes",
                    tier=PlatformTier.SMALL,
                    action=SelectionAction.INCLUDE_ALL,
                    target_volume="/userdata",
                ),
            ],
        )

        result = deployer.deploy(plan, dry_run=True)
        # Dry run: no uploads should have been called
        mock_ssh.upload.assert_not_called()
        assert result.status == DeploymentStatus.COMPLETED

    def test_deploy_cancellation(self, mock_ssh: MagicMock, output_dir: Path) -> None:
        from romfarmer.farmhand.deployer import Deployer

        deployer = Deployer(ssh=mock_ssh, output_root=output_dir)

        plan = DeploymentPlan(
            target_name="test",
            allocations=[
                PlatformAllocation(
                    platform="nes",
                    tier=PlatformTier.SMALL,
                    action=SelectionAction.INCLUDE_ALL,
                    target_volume="/userdata",
                ),
            ],
        )

        # Verify cancel() sets the flag
        deployer.cancel()
        assert deployer._cancelled is True

    def test_resolve_local_dir(self, mock_ssh: MagicMock, output_dir: Path) -> None:
        from romfarmer.farmhand.deployer import Deployer

        deployer = Deployer(ssh=mock_ssh, output_root=output_dir)
        nes_dir = deployer._resolve_local_dir("nes")
        assert nes_dir is not None
        assert nes_dir.exists()
        assert nes_dir.name == "nes"

    def test_resolve_local_dir_not_found(self, mock_ssh: MagicMock, output_dir: Path) -> None:
        from romfarmer.farmhand.deployer import Deployer

        deployer = Deployer(ssh=mock_ssh, output_root=output_dir)
        result = deployer._resolve_local_dir("n64")
        assert result is None

    def test_collect_local_files(self, mock_ssh: MagicMock, output_dir: Path) -> None:
        from romfarmer.farmhand.deployer import Deployer

        deployer = Deployer(ssh=mock_ssh, output_root=output_dir)
        files = deployer._collect_local_files(output_dir / "nes")
        assert len(files) == 2
        assert "Game1 (USA).7z" in files
        assert "Game2 (USA).7z" in files

    def test_skip_already_deployed(self, mock_ssh: MagicMock, output_dir: Path) -> None:
        from romfarmer.farmhand.deployer import Deployer

        plan = DeploymentPlan(
            target_name="test",
            allocations=[
                PlatformAllocation(
                    platform="nes",
                    tier=PlatformTier.SMALL,
                    action=SelectionAction.SKIP,  # Skipped platform
                    target_volume="/userdata",
                ),
            ],
        )

        deployer = Deployer(ssh=mock_ssh, output_root=output_dir)
        result = deployer.deploy(plan)
        # Nothing should be transferred for a skipped platform
        mock_ssh.upload.assert_not_called()
