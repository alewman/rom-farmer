"""PassRunner — ordered pass execution with cumulative PassTrace list.

The runner owns the pass execution order.  Passes are invoked sequentially;
each receives the ``Catalog`` returned by the previous pass.

Usage::

    from romfarmer.planner.runner import PassRunner
    from romfarmer.planner import passes

    runner = PassRunner(
        passes=[passes.region, passes.dat_dedup, passes.one_g_one_r,
                passes.rating, passes.curated_lists, passes.budget],
        manifest=manifest,
        kb=kb,
        cost_model=cost_model,
    )
    final_catalog, traces = runner.run(initial_catalog)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from romfarmer.ir.catalog import Catalog, PassResult, PassTrace

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.manifest import BuildManifest
    from romfarmer.planner.costmodel import CostModel

logger = logging.getLogger(__name__)

# Type alias for the uniform pass signature
PassFn = Callable[
    [Catalog, "BuildManifest", "KnowledgeBase", "CostModel"],
    PassResult,
]


class PassRunner:
    """Execute a sequence of pure planner passes and collect their traces.

    Args:
        passes: Ordered list of pass callables.
        manifest: Resolved build config (shared by all passes).
        kb: Knowledge base (shared by all passes).
        cost_model: Cost model (shared by all passes).
    """

    def __init__(
        self,
        passes: list[PassFn],
        manifest: "BuildManifest",
        kb: "KnowledgeBase",
        cost_model: "CostModel",
    ) -> None:
        self._passes = passes
        self._manifest = manifest
        self._kb = kb
        self._cost_model = cost_model

    def run(self, catalog: Catalog) -> tuple[Catalog, list[PassTrace]]:
        """Run all passes in order.

        Returns:
            ``(final_catalog, [PassTrace, ...])`` — the trace list has one
            entry per pass, even for no-op passes (they produce empty traces).
        """
        traces: list[PassTrace] = []
        current = catalog

        for pass_fn in self._passes:
            name = getattr(pass_fn, "__module__", "<unknown>").rsplit(".", 1)[-1]
            before = len(current.units)
            result = pass_fn(current, self._manifest, self._kb, self._cost_model)
            after = len(result.catalog.units)
            delta = before - after
            if delta > 0:
                logger.info("pass %-20s removed %4d units (%d → %d)", name, delta, before, after)
            else:
                logger.debug("pass %-20s no-op (%d units)", name, before)
            traces.append(result.trace)
            current = result.catalog

        return current, traces
