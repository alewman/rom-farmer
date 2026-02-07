"""Content-Addressable Store for ROM Farmer.

Unified store for all content-addressed blobs (media, ROMs, etc.).
Files are stored by SHA-256 hash with 1-level directory sharding.

Layout: {store_dir}/{hash[:2]}/{hash[2:]}.{ext}

Usage:
    from romfarmer.cas import ContentStore

    store = ContentStore("store")
    file_hash, path = store.put(Path("image.png"))
    store.link_to(file_hash, ".png", Path("output/boxart.png"))
"""

from .store import ContentStore

__all__ = ["ContentStore"]
