"""romfarmer.ir — the typed Intermediate Representation for the ROM Farmer compiler.

Five-phase pipeline:
  RESOLVE → CATALOG → PLAN → EXECUTE → EMIT

Each phase boundary is a frozen, serialisable IR artifact defined here.
"""

from .actions import (
    Action,
    ActionId,
    ActionKey,
    ArtifactDecl,
    BuildPlan,
    ContentRef,
    InputRef,
    PendingRef,
    Retention,
    SizePrediction,
    UnitPlan,
    resolve_key,
)
from .catalog import (
    Catalog,
    CatalogWarning,
    DiscRef,
    GameUnit,
    PassResult,
    PassTrace,
    PlatformId,
    SourceRef,
    UnitId,
)
from .chain import FormatChain
from .identity import (
    Identity,
    IdentityConflict,
    ZipIdentity,
)
from .layout import (
    LayoutConstraints,
    LayoutEntry,
    LayoutPlan,
    MediaPolicy,
    MetadataDialect,
    OutputSet,
    PlatformCapability,
)
from .manifest import BuildManifest

__all__ = [
    # chain
    "FormatChain",
    # identity
    "Identity",
    "IdentityConflict",
    "ZipIdentity",
    # catalog
    "Catalog",
    "CatalogWarning",
    "DiscRef",
    "GameUnit",
    "PassResult",
    "PassTrace",
    "PlatformId",
    "SourceRef",
    "UnitId",
    # actions
    "Action",
    "ActionId",
    "ActionKey",
    "ArtifactDecl",
    "BuildPlan",
    "ContentRef",
    "InputRef",
    "PendingRef",
    "Retention",
    "SizePrediction",
    "UnitPlan",
    "resolve_key",
    # layout
    "LayoutConstraints",
    "LayoutEntry",
    "LayoutPlan",
    "MediaPolicy",
    "MetadataDialect",
    "OutputSet",
    "PlatformCapability",
    # manifest
    "BuildManifest",
]
