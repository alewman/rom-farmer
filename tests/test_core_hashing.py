"""
Tests for the centralized hashing module.

These tests verify that the hashing logic correctly distinguishes between:
- Arcade systems (hash the ZIP file itself)
- Cartridge systems (hash contents inside ZIP)
- Direct files (hash the file itself)
"""

import hashlib
import zipfile
from pathlib import Path

from src.romfarmer.core.hashing import (
    ARCADE_SYSTEMS,
    DIRECT_HASH_EXTENSIONS,
    HashingStrategy,
    HashResult,
    calculate_hash,
    calculate_md5,
    calculate_md5_with_auto_detect,
    detect_system_from_path,
    get_hashing_strategy,
    is_arcade_system,
)


class TestArcadeSystemDetection:
    """Tests for arcade system identification."""

    def test_fbneo_is_arcade(self):
        assert is_arcade_system("fbneo") is True

    def test_mame_is_arcade(self):
        assert is_arcade_system("mame") is True

    def test_naomi_is_arcade(self):
        assert is_arcade_system("naomi") is True

    def test_atomiswave_is_arcade(self):
        assert is_arcade_system("atomiswave") is True

    def test_model2_is_arcade(self):
        assert is_arcade_system("model2") is True

    def test_model3_is_arcade(self):
        assert is_arcade_system("model3") is True

    def test_triforce_is_arcade(self):
        assert is_arcade_system("triforce") is True

    def test_neogeo_is_arcade(self):
        assert is_arcade_system("neogeo") is True

    def test_hbmame_is_arcade(self):
        assert is_arcade_system("hbmame") is True

    def test_nes_is_not_arcade(self):
        assert is_arcade_system("nes") is False

    def test_snes_is_not_arcade(self):
        assert is_arcade_system("snes") is False

    def test_psx_is_not_arcade(self):
        assert is_arcade_system("psx") is False

    def test_genesis_is_not_arcade(self):
        assert is_arcade_system("genesis") is False

    def test_n64_is_not_arcade(self):
        assert is_arcade_system("n64") is False

    def test_case_insensitive(self):
        assert is_arcade_system("FBNEO") is True
        assert is_arcade_system("FbNeO") is True
        assert is_arcade_system("MAME") is True

    def test_empty_string(self):
        assert is_arcade_system("") is False

    def test_none(self):
        assert is_arcade_system(None) is False


class TestHashingStrategy:
    """Tests for hashing strategy determination."""

    def test_arcade_zip_uses_archive_as_file(self, tmp_path):
        test_zip = tmp_path / "test.zip"
        test_zip.touch()

        strategy = get_hashing_strategy(test_zip, "fbneo")
        assert strategy == HashingStrategy.ARCHIVE_AS_FILE

    def test_arcade_7z_uses_archive_as_file(self, tmp_path):
        test_7z = tmp_path / "test.7z"
        test_7z.touch()

        strategy = get_hashing_strategy(test_7z, "mame")
        assert strategy == HashingStrategy.ARCHIVE_AS_FILE

    def test_arcade_chd_uses_direct(self, tmp_path):
        test_chd = tmp_path / "test.chd"
        test_chd.touch()

        # CHD files are always hashed directly, even in arcade context
        strategy = get_hashing_strategy(test_chd, "naomi")
        assert strategy == HashingStrategy.DIRECT

    def test_console_zip_uses_archive_contents(self, tmp_path):
        test_zip = tmp_path / "test.zip"
        test_zip.touch()

        strategy = get_hashing_strategy(test_zip, "nes")
        assert strategy == HashingStrategy.ARCHIVE_CONTENTS

    def test_console_7z_uses_archive_contents(self, tmp_path):
        test_7z = tmp_path / "test.7z"
        test_7z.touch()

        strategy = get_hashing_strategy(test_7z, "snes")
        assert strategy == HashingStrategy.ARCHIVE_CONTENTS

    def test_direct_extensions_always_direct(self, tmp_path):
        for ext in [".nes", ".sfc", ".chd", ".iso", ".bin", ".rvz"]:
            test_file = tmp_path / f"test{ext}"
            test_file.touch()

            strategy = get_hashing_strategy(test_file, "nes")
            assert strategy == HashingStrategy.DIRECT, f"Expected DIRECT for {ext}"

    def test_no_system_defaults_to_contents(self, tmp_path):
        test_zip = tmp_path / "test.zip"
        test_zip.touch()

        # Without system context, assume console behavior
        strategy = get_hashing_strategy(test_zip, None)
        assert strategy == HashingStrategy.ARCHIVE_CONTENTS


class TestCalculateMd5:
    """Tests for MD5 calculation."""

    def test_direct_file_hash(self, tmp_path):
        """Test hashing a plain file."""
        test_file = tmp_path / "test.nes"
        content = b"test rom content"
        test_file.write_bytes(content)

        expected = hashlib.md5(content).hexdigest()
        result = calculate_md5(test_file, "nes")

        assert result == expected

    def test_arcade_zip_hashes_archive(self, tmp_path):
        """Arcade ZIP should hash the ZIP file itself."""
        zip_path = tmp_path / "game.zip"

        # Create a ZIP with some content
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("rom.bin", b"rom contents")

        # Expected: hash of the ZIP file
        expected = hashlib.md5(zip_path.read_bytes()).hexdigest()
        result = calculate_md5(zip_path, "fbneo")

        assert result == expected

    def test_console_zip_hashes_contents(self, tmp_path):
        """Console ZIP should hash the ROM inside."""
        zip_path = tmp_path / "game.zip"
        rom_content = b"rom contents inside zip"

        # Create a ZIP with some content
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("game.nes", rom_content)

        # Expected: hash of the ROM content, not the ZIP
        expected = hashlib.md5(rom_content).hexdigest()
        result = calculate_md5(zip_path, "nes")

        assert result == expected

    def test_same_content_different_systems(self, tmp_path):
        """Same ZIP should produce different hashes for arcade vs console."""
        zip_path = tmp_path / "game.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("rom.bin", b"some rom data")

        arcade_hash = calculate_md5(zip_path, "fbneo")
        console_hash = calculate_md5(zip_path, "nes")

        # These must be different!
        assert arcade_hash != console_hash

    def test_zip_with_multiple_files_uses_largest(self, tmp_path):
        """For consoles, hash the largest file in the archive."""
        zip_path = tmp_path / "game.zip"
        small_content = b"small"
        large_content = b"this is the larger rom file content"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("small.txt", small_content)
            zf.writestr("game.nes", large_content)

        # Should hash the larger file
        expected = hashlib.md5(large_content).hexdigest()
        result = calculate_md5(zip_path, "nes")

        assert result == expected


class TestCalculateHash:
    """Tests for full hash calculation with multiple algorithms."""

    def test_returns_hash_result(self, tmp_path):
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test content")

        result = calculate_hash(test_file, "nes")

        assert isinstance(result, HashResult)
        assert result.md5 is not None
        assert result.sha1 is not None

    def test_sha1_optional(self, tmp_path):
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test content")

        result = calculate_hash(test_file, "nes", include_sha1=False)

        assert result.md5 is not None
        assert result.sha1 is None

    def test_strategy_recorded(self, tmp_path):
        zip_path = tmp_path / "game.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("rom.bin", b"content")

        arcade_result = calculate_hash(zip_path, "fbneo")
        console_result = calculate_hash(zip_path, "nes")

        assert arcade_result.strategy_used == HashingStrategy.ARCHIVE_AS_FILE
        assert console_result.strategy_used == HashingStrategy.ARCHIVE_CONTENTS

    def test_inner_filename_recorded_for_contents(self, tmp_path):
        zip_path = tmp_path / "game.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("game.nes", b"content")

        result = calculate_hash(zip_path, "nes")

        assert result.inner_filename == "game.nes"


class TestDetectSystemFromPath:
    """Tests for automatic system detection from path."""

    def test_detects_fbneo(self):
        path = Path("/path/to/roms/fbneo/kinst.zip")
        assert detect_system_from_path(path) == "fbneo"

    def test_detects_mame(self):
        path = Path("/path/to/output/arcade/mame/kinst.zip")
        assert detect_system_from_path(path) == "mame"

    def test_detects_naomi(self):
        path = Path("/path/to/roms/naomi/game.zip")
        assert detect_system_from_path(path) == "naomi"

    def test_returns_none_for_unknown(self):
        path = Path("/path/to/roms/nes/game.nes")
        # NES is not an arcade system, so returns None
        assert detect_system_from_path(path) is None

    def test_returns_none_for_random_path(self):
        path = Path("/home/user/downloads/game.zip")
        assert detect_system_from_path(path) is None


class TestAutoDetectHashing:
    """Tests for automatic detection combined with hashing."""

    def test_auto_detect_arcade(self, tmp_path):
        """Should detect arcade system from path and hash accordingly."""
        fbneo_dir = tmp_path / "fbneo"
        fbneo_dir.mkdir()
        zip_path = fbneo_dir / "game.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("rom.bin", b"arcade rom")

        # Auto-detect should find "fbneo" in path
        result = calculate_md5_with_auto_detect(zip_path)

        # Should match archive hash (arcade style)
        expected = hashlib.md5(zip_path.read_bytes()).hexdigest()
        assert result == expected

    def test_auto_detect_fallback_to_contents(self, tmp_path):
        """Unknown path should default to contents hashing."""
        random_dir = tmp_path / "games"
        random_dir.mkdir()
        zip_path = random_dir / "game.zip"
        rom_content = b"console rom"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("game.nes", rom_content)

        result = calculate_md5_with_auto_detect(zip_path)

        # Should match contents hash (no arcade detected)
        expected = hashlib.md5(rom_content).hexdigest()
        assert result == expected


class TestArcadeSystemsConstant:
    """Verify ARCADE_SYSTEMS includes expected systems."""

    def test_core_arcade_systems_present(self):
        expected = {"fbneo", "mame", "hbmame", "naomi", "atomiswave", "model2", "model3"}
        assert expected.issubset(ARCADE_SYSTEMS)

    def test_is_frozen_set(self):
        # Should be immutable
        assert isinstance(ARCADE_SYSTEMS, frozenset)


class TestDirectHashExtensions:
    """Verify DIRECT_HASH_EXTENSIONS includes expected types."""

    def test_disc_formats_present(self):
        expected = {".chd", ".iso", ".cue", ".bin", ".rvz", ".wbfs"}
        assert expected.issubset(DIRECT_HASH_EXTENSIONS)

    def test_rom_formats_present(self):
        expected = {".nes", ".sfc", ".gb", ".gba", ".n64", ".nds"}
        assert expected.issubset(DIRECT_HASH_EXTENSIONS)

    def test_is_frozen_set(self):
        assert isinstance(DIRECT_HASH_EXTENSIONS, frozenset)
