"""
Tree Manifests for Content-Addressable Store.

Extends the CAS to handle folder-based outputs (PS3 JB folders, daphne,
scummvm, Xbox 360 GOD, Wii U NUS, PS Vita, OpenBOR).

A TreeManifest is a JSON document listing every file in a folder output,
each with its relative path, SHA-256 hash, size, and permissions. The
manifest itself is content-addressed — its SHA-256 (the "tree hash")
serves as the cache key.

Architecture:
    - Individual files are stored in the same CAS blob store as single files
    - The manifest JSON is also stored as a CAS blob (.manifest extension)
    - Restoring a tree = read manifest → hardlink each blob to its relative path

This gives us full deduplication across folder outputs (shared DLLs, firmware
files, etc.) while supporting atomic restore and garbage collection.
"""

import hashlib
import json
import logging
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from .store import ContentStore

logger = logging.getLogger(__name__)


@dataclass
class TreeEntry:
    """A single file within a tree manifest."""

    relative_path: str  # e.g., "PS3_GAME/USRDIR/EBOOT.BIN"
    sha256: str  # SHA-256 of file contents
    size: int  # File size in bytes
    executable: bool = False  # Preserve +x permission

    def to_dict(self) -> dict:
        d = {
            "path": self.relative_path,
            "sha256": self.sha256,
            "size": self.size,
        }
        if self.executable:
            d["executable"] = True
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TreeEntry":
        return cls(
            relative_path=d["path"],
            sha256=d["sha256"],
            size=d["size"],
            executable=d.get("executable", False),
        )


@dataclass
class TreeManifest:
    """
    Manifest describing all files in a folder-based output.

    The tree_hash is computed from the sorted manifest content, making
    it deterministic — identical folder contents always produce the
    same tree hash regardless of creation order.
    """

    entries: List[TreeEntry] = field(default_factory=list)
    tree_hash: str = ""  # Computed after all entries are added
    total_size: int = 0  # Sum of all entry sizes
    total_files: int = 0  # Number of entries

    # Optional metadata (not included in hash computation)
    source_name: str = ""  # e.g., "Borderlands 2 (USA)"
    platform: str = ""  # e.g., "ps3", "daphne", "scummvm"
    format: str = ""  # e.g., "ps3-jb", "daphne-folder"
    tool: str = ""  # e.g., "ps3dec+7z", "extract"
    tool_version: str = ""

    def compute_hash(self) -> str:
        """Compute tree hash from sorted entry data.

        The hash is deterministic: same files → same hash, regardless
        of insertion order. Only file paths, hashes, and sizes are
        included (not metadata like permissions).
        """
        # Sort by path for determinism
        sorted_entries = sorted(self.entries, key=lambda e: e.relative_path)

        # Build canonical representation
        canonical = []
        for entry in sorted_entries:
            canonical.append(f"{entry.relative_path}\t{entry.sha256}\t{entry.size}")

        content = "\n".join(canonical).encode("utf-8", "surrogateescape")
        self.tree_hash = hashlib.sha256(content).hexdigest()
        self.total_size = sum(e.size for e in self.entries)
        self.total_files = len(self.entries)
        return self.tree_hash

    def to_json(self) -> str:
        """Serialize manifest to JSON (for CAS storage)."""
        data = {
            "version": 1,
            "tree_hash": self.tree_hash,
            "total_size": self.total_size,
            "total_files": self.total_files,
            "metadata": {
                "source_name": self.source_name,
                "platform": self.platform,
                "format": self.format,
                "tool": self.tool,
                "tool_version": self.tool_version,
            },
            "entries": [e.to_dict() for e in sorted(
                self.entries, key=lambda e: e.relative_path
            )],
        }
        return json.dumps(data, indent=2, ensure_ascii=True)

    @classmethod
    def from_json(cls, json_str: str) -> "TreeManifest":
        """Deserialize manifest from JSON."""
        data = json.loads(json_str)

        if data.get("version", 1) != 1:
            raise ValueError(f"Unsupported manifest version: {data['version']}")

        metadata = data.get("metadata", {})
        entries = [TreeEntry.from_dict(e) for e in data["entries"]]

        manifest = cls(
            entries=entries,
            tree_hash=data["tree_hash"],
            total_size=data["total_size"],
            total_files=data["total_files"],
            source_name=metadata.get("source_name", ""),
            platform=metadata.get("platform", ""),
            format=metadata.get("format", ""),
            tool=metadata.get("tool", ""),
            tool_version=metadata.get("tool_version", ""),
        )
        return manifest

    def __repr__(self) -> str:
        h = self.tree_hash[:12] if self.tree_hash else "uncomputed"
        return f"<TreeManifest({h}..., {self.total_files} files, {self.total_size} bytes)>"


class TreeStore:
    """
    Manages tree manifests on top of the ContentStore.

    Provides store_tree() to ingest a folder, and restore_tree() to
    recreate it. Individual files go into the regular CAS blob store;
    the manifest JSON is stored as a .manifest blob.
    """

    MANIFEST_EXT = ".manifest"

    def __init__(self, content_store: ContentStore):
        self.store = content_store

    def ingest(
        self,
        folder: Path,
        *,
        platform: str = "",
        format: str = "",
        source_name: str = "",
        tool: str = "",
        tool_version: str = "",
        hardlink: bool = False,
    ) -> TreeManifest:
        """
        Ingest a folder into the CAS, returning its tree manifest.

        Every file in the folder is hashed and stored in the CAS.
        A manifest JSON is created and also stored as a CAS blob.

        Args:
            folder: Root folder to ingest (e.g., "BLUS30455.ps3/")
            platform: Platform identifier (e.g., "ps3")
            format: Output format (e.g., "ps3-jb")
            source_name: Human-readable source name
            tool: Tool used for transformation
            tool_version: Tool version string
            hardlink: If True, use hardlinks instead of copies (zero-copy
                      on same filesystem). Source files become linked to
                      CAS blobs — same inode, no extra space.

        Returns:
            TreeManifest with computed tree_hash
        """
        folder = Path(folder)
        if not folder.is_dir():
            raise NotADirectoryError(f"Not a directory: {folder}")

        manifest = TreeManifest(
            source_name=source_name,
            platform=platform,
            format=format,
            tool=tool,
            tool_version=tool_version,
        )

        # Walk the folder and store each file
        file_count = 0
        for file_path in sorted(folder.rglob("*")):
            if not file_path.is_file():
                continue

            # Compute relative path from folder root
            # Handle surrogate escapes from non-UTF-8 filenames (common in
            # PS3 game data) by encoding via filesystem codec then decoding
            # with replacement so the path is safe for JSON/UTF-8.
            rel_path = str(file_path.relative_to(folder))
            try:
                rel_path.encode("utf-8")
            except UnicodeEncodeError:
                # Convert surrogates to raw bytes, then back to safe UTF-8
                raw = os.fsencode(rel_path)
                rel_path = raw.decode("utf-8", "surrogateescape")
                # Re-encode with backslashreplace for JSON-safe storage
                rel_path = raw.decode("utf-8", "replace")

            # Check if file is executable
            is_exec = os.access(file_path, os.X_OK)

            # Store in CAS (deduplicates automatically)
            if hardlink:
                file_hash, _blob_path = self.store.put_hardlink(file_path)
            else:
                file_hash, _blob_path = self.store.put(file_path)

            entry = TreeEntry(
                relative_path=rel_path,
                sha256=file_hash,
                size=file_path.stat().st_size,
                executable=is_exec,
            )
            manifest.entries.append(entry)
            file_count += 1

        # Compute tree hash
        manifest.compute_hash()

        # Store the manifest itself as a CAS blob
        self._store_manifest(manifest)

        logger.info(
            f"Ingested tree: {folder.name} → {manifest.tree_hash[:12]}... "
            f"({file_count} files, {manifest.total_size / (1024**2):.1f} MB)"
        )

        return manifest

    def restore(
        self,
        tree_hash: str,
        target: Path,
        *,
        use_hardlinks: bool = True,
    ) -> TreeManifest:
        """
        Restore a tree from the CAS to a target directory.

        Reads the manifest, then hardlinks (or copies) each blob
        to its relative path under target.

        Args:
            tree_hash: Tree manifest hash
            target: Root directory to restore into
            use_hardlinks: Use hardlinks (True) or copies (False)

        Returns:
            The TreeManifest that was restored

        Raises:
            FileNotFoundError: If manifest or any blob is missing
        """
        manifest = self.load_manifest(tree_hash)
        target = Path(target)

        restored = 0
        for entry in manifest.entries:
            dest = target / entry.relative_path
            dest.parent.mkdir(parents=True, exist_ok=True)

            blob = self.store.blob_path(entry.sha256, Path(entry.relative_path).suffix)
            if not blob.exists():
                # Try without extension (some files may have been stored differently)
                blob = self.store.blob_path(entry.sha256, "")
                if not blob.exists():
                    raise FileNotFoundError(
                        f"Blob missing for {entry.relative_path}: {entry.sha256[:12]}..."
                    )

            if dest.exists():
                dest.unlink()

            if use_hardlinks:
                try:
                    os.link(blob, dest)
                except OSError:
                    shutil.copy2(blob, dest)
            else:
                shutil.copy2(blob, dest)

            # Restore executable permission
            if entry.executable:
                dest.chmod(dest.stat().st_mode | 0o111)

            restored += 1

        logger.info(
            f"Restored tree: {tree_hash[:12]}... → {target} "
            f"({restored} files)"
        )

        return manifest

    def exists(self, tree_hash: str) -> bool:
        """Check if a tree manifest exists in the store."""
        return self.store.exists(tree_hash, self.MANIFEST_EXT)

    def load_manifest(self, tree_hash: str) -> TreeManifest:
        """Load a tree manifest from the CAS.

        Args:
            tree_hash: SHA-256 of the manifest

        Returns:
            TreeManifest

        Raises:
            FileNotFoundError: If manifest doesn't exist
        """
        manifest_path = self.store.blob_path(tree_hash, self.MANIFEST_EXT)
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Tree manifest not found: {tree_hash[:12]}..."
            )

        json_str = manifest_path.read_text(encoding="utf-8")
        manifest = TreeManifest.from_json(json_str)

        # Verify tree hash matches
        if manifest.tree_hash != tree_hash:
            raise ValueError(
                f"Manifest hash mismatch: expected {tree_hash[:12]}..., "
                f"got {manifest.tree_hash[:12]}..."
            )

        return manifest

    def verify(self, tree_hash: str) -> Tuple[int, int, List[str]]:
        """Verify all blobs for a tree exist and match.

        Returns:
            (valid_count, missing_count, missing_paths)
        """
        manifest = self.load_manifest(tree_hash)

        valid = 0
        missing = []

        for entry in manifest.entries:
            blob = self.store.blob_path(entry.sha256, Path(entry.relative_path).suffix)
            if blob.exists():
                valid += 1
            else:
                # Check without extension
                blob_noext = self.store.blob_path(entry.sha256, "")
                if blob_noext.exists():
                    valid += 1
                else:
                    missing.append(entry.relative_path)

        return valid, len(missing), missing

    def referenced_hashes(self, tree_hash: str) -> set[str]:
        """Get all blob hashes referenced by a tree manifest.

        Useful for garbage collection — these hashes must be kept.

        Args:
            tree_hash: SHA-256 of the manifest

        Returns:
            Set of SHA-256 hashes (including the manifest hash itself)
        """
        manifest = self.load_manifest(tree_hash)
        hashes = {entry.sha256 for entry in manifest.entries}
        hashes.add(tree_hash)  # The manifest blob itself
        return hashes

    def _store_manifest(self, manifest: TreeManifest) -> Path:
        """Store a manifest JSON as a CAS blob.

        The manifest is written to a temp file, then stored via
        the normal CAS put() flow.
        """
        import tempfile

        json_str = manifest.to_json()

        # Write to temp file, then store via CAS
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=self.MANIFEST_EXT,
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(json_str)
            tmp_path = Path(tmp.name)

        try:
            # Store manifest blob — use the tree_hash as the content hash
            # (not the hash of the JSON text, since we want to look up by tree_hash)
            blob_path = self.store.blob_path(manifest.tree_hash, self.MANIFEST_EXT)
            blob_path.parent.mkdir(parents=True, exist_ok=True)

            if not blob_path.exists():
                shutil.copy2(tmp_path, blob_path)

            return blob_path
        finally:
            tmp_path.unlink(missing_ok=True)

    def __repr__(self) -> str:
        return f"TreeStore({self.store!r})"
