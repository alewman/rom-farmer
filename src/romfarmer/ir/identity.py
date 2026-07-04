"""Identity — content-addressing primitives for the ROM Farmer IR.

An Identity may be *partial* (only some fields populated) everywhere except
inside the Executor, which is the ONLY component that requires
``is_complete`` and the ONLY writer of alias records to the database.
"""

from __future__ import annotations

from dataclasses import dataclass


class IdentityConflict(ValueError):
    """Raised by ``Identity.merged()`` when two populated fields disagree."""


@dataclass(frozen=True, slots=True)
class ZipIdentity:
    """The in-archive identity of the dominant member of a ZIP.

    "Dominant member" means the largest file, or the ``.cue`` sheet for
    multi-track disc images.
    """

    member_crc32: int   # CRC32 of the dominant member
    member_size: int    # uncompressed size of that member
    member_name: str    # filename of that member

    def serialized(self) -> str:
        """Canonical string form used as a cache-key alias: ``crc32:size:name``."""
        return f"{self.member_crc32}:{self.member_size}:{self.member_name}"


@dataclass(frozen=True, slots=True)
class Identity:
    """Accumulated content-addressing knowledge for one file.

    Fields are optional because knowledge accumulates incrementally:
    - Source scanning produces ``zip_identity`` (pre-extraction).
    - DAT matching adds ``md5`` (and sometimes ``size``).
    - The Executor, after computing or verifying, fills in ``sha256`` and
      writes all aliases atomically — fixing the MD5-vs-CRC32 divergence
      described in the system briefing §3.9.
    """

    size: int | None = None
    sha256: str | None = None           # primary CAS key; REQUIRED by Executor
    md5: str | None = None              # DAT-matching alias
    zip_identity: ZipIdentity | None = None  # pre-extraction alias

    @property
    def is_complete(self) -> bool:
        """True iff ``sha256`` is populated (Executor precondition)."""
        return self.sha256 is not None

    def merged(self, other: "Identity") -> "Identity":
        """Return the union of knowledge from ``self`` and ``other``.

        Raises:
            IdentityConflict: if any field is populated in *both* instances
                with different values.
        """

        def _merge(a: object, b: object, name: str) -> object:
            if a is None:
                return b
            if b is None:
                return a
            if a != b:
                raise IdentityConflict(
                    f"Identity conflict on field '{name}': {a!r} != {b!r}"
                )
            return a

        return Identity(
            size=_merge(self.size, other.size, "size"),  # type: ignore[arg-type]
            sha256=_merge(self.sha256, other.sha256, "sha256"),  # type: ignore[arg-type]
            md5=_merge(self.md5, other.md5, "md5"),  # type: ignore[arg-type]
            zip_identity=_merge(  # type: ignore[arg-type]
                self.zip_identity, other.zip_identity, "zip_identity"
            ),
        )

    def best_key(self) -> tuple[str, str]:
        """Return the strongest available ``(kind, value)`` pair.

        Precedence: ``sha256`` > ``md5`` > ``zip_identity`` (serialized as
        ``"crc32:size:name"``).

        Raises:
            ValueError: if all hash fields are ``None``.
        """
        if self.sha256 is not None:
            return ("sha256", self.sha256)
        if self.md5 is not None:
            return ("md5", self.md5)
        if self.zip_identity is not None:
            return ("zip_identity", self.zip_identity.serialized())
        raise ValueError(
            "Identity has no hash fields set — cannot determine best_key"
        )
