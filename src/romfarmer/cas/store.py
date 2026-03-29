"""
Content-Addressable Store.

Stores files by their SHA-256 hash with 2-character prefix sharding.
Layout: {store_dir}/{hash[:2]}/{hash[2:]}.{ext}

On ZFS with 256 buckets, this handles millions of files efficiently.
Extensions are preserved so emulators/viewers can identify file types
without sniffing.
"""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple


class ContentStore:
    """
    Content-addressable blob store with SHA-256 hashing and 1-level sharding.

    Files are stored at: {store_dir}/{hash[:2]}/{hash[2:]}.{ext}

    Thread-safe for concurrent reads. Writes use atomic temp+rename
    to prevent partial files.
    """

    HASH_ALGO = "sha256"
    HASH_LENGTH = 64  # hex chars for SHA-256
    PREFIX_LENGTH = 2  # 256 buckets
    CHUNK_SIZE = 1_048_576  # 1MB - good throughput on ZFS

    def __init__(self, store_dir: str | Path = "store"):
        """
        Initialize content store.

        Args:
            store_dir: Root directory for the store. Can be relative
                       (paths returned will also be relative) or absolute.
        """
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def put(
        self,
        source: Path,
        *,
        file_hash: Optional[str] = None,
        move: bool = False,
    ) -> Tuple[str, Path]:
        """
        Store a file by its content hash.

        If the blob already exists, the source is left untouched
        (or deleted if move=True) and the existing path is returned.

        Args:
            source: Path to file to store.
            file_hash: Pre-computed SHA-256 hex digest. Computed if None.
            move: If True, rename source into store (atomic on same FS).
                  If False, copy with atomic temp+rename.

        Returns:
            (hash, blob_path) tuple.
        """
        source = Path(source)
        if file_hash is None:
            file_hash = self.hash_file(source)

        blob = self.blob_path(file_hash, source.suffix)

        if blob.exists():
            # Already stored — deduplicated
            if move:
                source.unlink()
            return file_hash, blob

        blob.parent.mkdir(parents=True, exist_ok=True)

        if move:
            # Atomic on same filesystem (ZFS pool)
            source.rename(blob)
        else:
            # Atomic: write to temp, then rename
            tmp = blob.with_suffix(blob.suffix + ".tmp")
            try:
                shutil.copy2(source, tmp)
                tmp.rename(blob)
            except BaseException:
                tmp.unlink(missing_ok=True)
                raise

        return file_hash, blob

    def blob_path(self, file_hash: str, ext: str = "") -> Path:
        """
        Get the store path for a given hash and extension.

        Args:
            file_hash: SHA-256 hex digest (64 chars).
            ext: File extension, with or without leading dot.

        Returns:
            Path like store/ab/cdef0123...{ext}
        """
        ext = self._normalize_ext(ext)
        return (
            self.store_dir
            / file_hash[: self.PREFIX_LENGTH]
            / (file_hash[self.PREFIX_LENGTH :] + ext)
        )

    def relative_path(self, file_hash: str, ext: str = "") -> str:
        """
        Get path as string, suitable for database storage.

        Returns the same path as blob_path() but as a string.
        If the store was initialized with a relative path, this
        will be relative (e.g., "store/ab/cdef...png").
        """
        return str(self.blob_path(file_hash, ext))

    def exists(self, file_hash: str, ext: str = "") -> bool:
        """Check if a blob exists in the store."""
        return self.blob_path(file_hash, ext).exists()

    def verify(self, file_hash: str, ext: str = "") -> bool:
        """
        Verify a blob's integrity by re-hashing.

        Returns False if the file is missing or the hash doesn't match.
        """
        blob = self.blob_path(file_hash, ext)
        if not blob.exists():
            return False
        return self.hash_file(blob) == file_hash

    def link_to(self, file_hash: str, ext: str, target: Path) -> None:
        """
        Hard-link a blob to target path.

        Creates parent directories as needed. Falls back to copy
        if hard-linking fails (cross-filesystem).

        Args:
            file_hash: SHA-256 hex digest.
            ext: File extension.
            target: Destination path for the link.

        Raises:
            FileNotFoundError: If the blob doesn't exist in the store.
        """
        source = self.blob_path(file_hash, ext)
        if not source.exists():
            raise FileNotFoundError(
                f"Blob not found: {file_hash[:12]}...{ext}"
            )
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(source, target)
        except OSError:
            shutil.copy2(source, target)

    def hash_file(self, path: Path) -> str:
        """
        Compute SHA-256 hex digest of a file.

        Uses 1MB chunks for good throughput on large files.
        """
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(self.CHUNK_SIZE):
                h.update(chunk)
        return h.hexdigest()

    def stats(self) -> dict:
        """
        Gather store statistics.

        Walks the store directory and counts files and bytes.
        Returns dict with: total_files, total_bytes, total_gb,
        buckets_used, buckets_total, avg_files_per_bucket.
        """
        total_files = 0
        total_bytes = 0
        buckets_used = 0

        for bucket in sorted(self.store_dir.iterdir()):
            if not bucket.is_dir() or len(bucket.name) != self.PREFIX_LENGTH:
                continue
            bucket_count = 0
            for blob in bucket.iterdir():
                if blob.is_file() and not blob.name.endswith(".tmp"):
                    total_files += 1
                    total_bytes += blob.stat().st_size
                    bucket_count += 1
            if bucket_count > 0:
                buckets_used += 1

        return {
            "total_files": total_files,
            "total_bytes": total_bytes,
            "total_gb": round(total_bytes / (1024**3), 2),
            "buckets_used": buckets_used,
            "buckets_total": 256,
            "avg_files_per_bucket": round(
                total_files / max(buckets_used, 1), 1
            ),
        }

    def gc(self, referenced_hashes: set[str]) -> dict:
        """
        Garbage-collect unreferenced blobs.

        For tree manifests, callers should expand tree hashes to include
        all blob hashes referenced by each manifest (using
        TreeStore.referenced_hashes()) before calling this method.

        Args:
            referenced_hashes: Set of SHA-256 hashes that are still
                               referenced (from the database). Must include
                               both single-file hashes and all blob hashes
                               from tree manifests.

        Returns:
            Dict with: removed_files, removed_bytes, kept_files.
        """
        removed_files = 0
        removed_bytes = 0
        kept_files = 0

        for bucket in sorted(self.store_dir.iterdir()):
            if not bucket.is_dir() or len(bucket.name) != self.PREFIX_LENGTH:
                continue
            for blob in bucket.iterdir():
                if not blob.is_file() or blob.name.endswith(".tmp"):
                    continue
                # Reconstruct hash: prefix dir + filename stem
                stem = blob.stem
                full_hash = bucket.name + stem
                if full_hash in referenced_hashes:
                    kept_files += 1
                else:
                    size = blob.stat().st_size
                    blob.unlink()
                    removed_files += 1
                    removed_bytes += size

            # Remove empty bucket dirs
            if not any(bucket.iterdir()):
                bucket.rmdir()

        return {
            "removed_files": removed_files,
            "removed_bytes": removed_bytes,
            "removed_gb": round(removed_bytes / (1024**3), 2),
            "kept_files": kept_files,
        }

    @staticmethod
    def _normalize_ext(ext: str) -> str:
        """Ensure extension starts with '.' or is empty."""
        if ext and not ext.startswith("."):
            return "." + ext
        return ext

    def __repr__(self) -> str:
        return f"ContentStore({self.store_dir!r})"
