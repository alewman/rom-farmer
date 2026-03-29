"""Content-Addressable Store for ROM Farmer.

Unified store for all content-addressed blobs (media, ROMs, etc.).
Files are stored by SHA-256 hash with 1-level directory sharding.

Layout: {store_dir}/{hash[:2]}/{hash[2:]}.{ext}

Usage:
    from romfarmer.cas import ContentStore, TreeStore, TreeManifest

    store = ContentStore("store")
    file_hash, path = store.put(Path("image.png"))
    store.link_to(file_hash, ".png", Path("output/boxart.png"))

    # Folder-based outputs (PS3, daphne, scummvm, etc.)
    trees = TreeStore(store)
    manifest = trees.ingest(Path("BLUS30455.ps3"), platform="ps3")
    trees.restore(manifest.tree_hash, Path("output/ps3/BLUS30455"))
"""

from .store import ContentStore
from .tree import TreeEntry, TreeManifest, TreeStore

__all__ = ["ContentStore", "TreeEntry", "TreeManifest", "TreeStore"]
