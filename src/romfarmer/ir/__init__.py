"""romfarmer.ir — the typed Intermediate Representation for the ROM Farmer compiler.

Five-phase pipeline:
  RESOLVE → CATALOG → PLAN → EXECUTE → EMIT

Each phase boundary is a frozen, serialisable IR artifact defined here.
The bridge to the legacy ``StageContext`` lives in ``romfarmer.ir.bridge``
(temporary — deleted in Phase 5).
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
)

__all__ = [
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
]
