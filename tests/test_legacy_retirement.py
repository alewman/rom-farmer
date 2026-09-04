"""Retirement conditions with teeth: a superseded code path must actually go.

When this test fails, delete src/romfarmer/farmhand/optimizer/ (and the
`farmhand optimize` / pool commands in cli/farmhand.py) — the intent loop
(romfarmer.intent) replaced it.  Do not bump the date without a reason
recorded in the commit message.
"""

from __future__ import annotations

import datetime as dt

from romfarmer.farmhand.optimizer import LEGACY_RETIRE_AFTER, legacy_optimizer_status


def test_legacy_optimizer_has_not_outlived_its_retirement_date() -> None:
    assert dt.date.today() <= LEGACY_RETIRE_AFTER, (
        f"farmhand/optimizer was due for removal on {LEGACY_RETIRE_AFTER}: "
        "delete the package and its CLI commands (see module docstring)"
    )


def test_status_flips_after_the_date() -> None:
    assert legacy_optimizer_status(LEGACY_RETIRE_AFTER) == "deprecated"
    assert legacy_optimizer_status(LEGACY_RETIRE_AFTER + dt.timedelta(days=1)) == "retired"
