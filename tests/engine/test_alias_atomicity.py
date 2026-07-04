"""§3.9 regression tests — artifact alias atomicity.

Gate 2 from docs/compiler-refactor/03-migration-roadmap.md Phase 2:

  Store via zip-identity path, then query by MD5 → hit (and vice versa).
  Both aliases written in one transaction, asserted.

Previously, CAS ingest and DAT matching each wrote their own alias
independently.  A file stored via its ZIP CRC32 path would miss on a
subsequent MD5 lookup, causing redundant re-processing.

ActionCache.record_aliases() is the SOLE WRITER of artifact_aliases and
writes all known aliases atomically, fixing this.
"""

import pytest

from romfarmer.engine.actioncache import ActionCache
from romfarmer.ir.actions import ActionKey
from romfarmer.ir.identity import Identity, ZipIdentity


@pytest.fixture
def cache(tmp_path):
    db = tmp_path / "romfarmer.db"
    with ActionCache(db) as ac:
        yield ac


class TestAliasAtomicity:
    """§3.9: all aliases for a sha256 are written in one transaction."""

    def test_store_via_zip_then_lookup_by_md5(self, cache: ActionCache) -> None:
        """Store with full identity (zip + md5 + sha256) → MD5 lookup hits."""
        identity = Identity(
            sha256="a" * 64,
            md5="deadbeef" * 4,
            size=1024,
            zip_identity=ZipIdentity(
                member_crc32=0x12345678,
                member_size=1024,
                member_name="game.bin",
            ),
        )
        cache.record_aliases(identity)

        # Query by MD5 — must find the same sha256
        result = cache.lookup_by_md5("deadbeef" * 4)
        assert result is not None
        assert result.sha256 == "a" * 64

    def test_store_via_md5_then_lookup_by_zip(self, cache: ActionCache) -> None:
        """Store with full identity → ZIP identity lookup hits."""
        identity = Identity(
            sha256="b" * 64,
            md5="cafebabe" * 4,
            size=2048,
            zip_identity=ZipIdentity(
                member_crc32=0xDEADBEEF,
                member_size=2048,
                member_name="disc.iso",
            ),
        )
        cache.record_aliases(identity)

        result = cache.lookup_by_zip(0xDEADBEEF, 2048)
        assert result is not None
        assert result.sha256 == "b" * 64
        assert result.md5 == "cafebabe" * 4

    def test_bidirectional_after_single_write(self, cache: ActionCache) -> None:
        """Single record_aliases call → both directions work immediately."""
        identity = Identity(
            sha256="c" * 64,
            md5="11223344" * 4,
            zip_identity=ZipIdentity(0xABCD, 512, "rom.nes"),
        )
        cache.record_aliases(identity)

        by_md5 = cache.lookup_by_md5("11223344" * 4)
        by_zip = cache.lookup_by_zip(0xABCD, 512, "rom.nes")

        assert by_md5 is not None and by_md5.sha256 == "c" * 64
        assert by_zip is not None and by_zip.sha256 == "c" * 64

    def test_record_aliases_requires_sha256(self, cache: ActionCache) -> None:
        """record_aliases raises ValueError if sha256 is None."""
        partial = Identity(md5="abc123" * 5)
        with pytest.raises(ValueError, match="sha256"):
            cache.record_aliases(partial)

    def test_no_cross_contamination(self, cache: ActionCache) -> None:
        """Two different sha256s stored independently don't bleed into each other."""
        a = Identity(sha256="a" * 64, md5="aaaa" * 8)
        b = Identity(sha256="b" * 64, md5="bbbb" * 8)
        cache.record_aliases(a)
        cache.record_aliases(b)

        ra = cache.lookup_by_md5("aaaa" * 8)
        rb = cache.lookup_by_md5("bbbb" * 8)
        assert ra is not None and ra.sha256 == "a" * 64
        assert rb is not None and rb.sha256 == "b" * 64

    def test_update_adds_missing_alias(self, cache: ActionCache) -> None:
        """Second record_aliases call fills in a previously-unknown alias."""
        # First: only sha256 + md5 known
        first = Identity(sha256="d" * 64, md5="firstmd5" + "0" * 24)
        cache.record_aliases(first)

        # Later: zip identity becomes known
        second = Identity(
            sha256="d" * 64,
            zip_identity=ZipIdentity(0x99, 256, "file.rom"),
        )
        cache.record_aliases(second)

        # Both lookups should now work
        by_md5 = cache.lookup_by_md5("firstmd5" + "0" * 24)
        by_zip = cache.lookup_by_zip(0x99, 256, "file.rom")
        assert by_md5 is not None and by_md5.sha256 == "d" * 64
        assert by_zip is not None and by_zip.sha256 == "d" * 64

    def test_unknown_md5_returns_none(self, cache: ActionCache) -> None:
        assert cache.lookup_by_md5("0" * 32) is None

    def test_unknown_zip_returns_none(self, cache: ActionCache) -> None:
        assert cache.lookup_by_zip(0xFFFF, 9999) is None


class TestActionCacheGetStore:
    def test_get_miss_returns_none(self, cache: ActionCache) -> None:
        assert cache.get(ActionKey("no_such_key")) is None

    def test_store_and_get_roundtrip(self, cache: ActionCache) -> None:
        key = ActionKey("k" * 64)
        outputs = (Identity(sha256="e" * 64, size=100),)
        cache.store(key, outputs, "chdman", "0.263")

        result = cache.get(key)
        assert result is not None
        assert len(result) == 1
        assert result[0].sha256 == "e" * 64
        assert result[0].size == 100

    def test_store_idempotent(self, cache: ActionCache) -> None:
        """Storing the same key twice is a no-op (INSERT OR IGNORE)."""
        key = ActionKey("f" * 64)
        outputs_v1 = (Identity(sha256="1" * 64, size=1),)
        outputs_v2 = (Identity(sha256="2" * 64, size=2),)
        cache.store(key, outputs_v1, "chdman", "0.263")
        cache.store(key, outputs_v2, "chdman", "0.263")  # should be ignored

        result = cache.get(key)
        assert result is not None
        assert result[0].sha256 == "1" * 64  # first value kept

    def test_store_records_aliases(self, cache: ActionCache) -> None:
        """store() calls record_aliases for each output with a sha256."""
        key = ActionKey("g" * 64)
        outputs = (
            Identity(sha256="h" * 64, md5="iiiiiiii" * 4, size=50),
        )
        cache.store(key, outputs, "unzip", "6.0")

        by_md5 = cache.lookup_by_md5("iiiiiiii" * 4)
        assert by_md5 is not None
        assert by_md5.sha256 == "h" * 64
