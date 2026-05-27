"""LLM critic client — wraps the Copilot Router via OpenAI SDK.

Sends structured prompts to the local Copilot Router (``gcr``) and parses
the JSON response into a validated :class:`~.state.CriticDecision`.

Environment variables
---------------------
COPILOT_ROUTER_URL
    Base URL for the router.  Default: ``http://localhost:7318/v1``.
CRITIC_MODEL
    Model name to use.  Default: ``claude-haiku-4.5``.
CRITIC_TEMPERATURE
    Float in [0, 1].  Default: ``0.2`` (mostly deterministic).
CRITIC_MAX_RETRIES
    Number of JSON parse retries.  Default: ``3``.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict

from .state import CriticDecision

logger = logging.getLogger(__name__)

_ROUTER_URL = os.getenv("COPILOT_ROUTER_URL", "http://localhost:7318/v1")
_MODEL = os.getenv("CRITIC_MODEL", "claude-haiku-4.5")
_TEMPERATURE = float(os.getenv("CRITIC_TEMPERATURE", "0.2"))
_MAX_RETRIES = int(os.getenv("CRITIC_MAX_RETRIES", "3"))


def call_critic(system_prompt: str, user_payload: Dict[str, Any]) -> CriticDecision:
    """Call the LLM critic and return a validated :class:`CriticDecision`.

    Args:
        system_prompt: System prompt from :mod:`.prompts`.
        user_payload: Structured iteration data (thresholds, sizes, history).

    Returns:
        Parsed and validated :class:`CriticDecision`.

    Raises:
        RuntimeError: If the LLM returns malformed JSON after all retries.
    """
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "openai package is required for the budget optimizer. "
            "Install with: pip install 'romfarmer[optimizer]'"
        ) from exc

    client = OpenAI(base_url=_ROUTER_URL, api_key="not-required")

    user_message = (
        "Analyze the following build state and return your threshold adjustments "
        "as a JSON object.\n\n"
        + json.dumps(user_payload, indent=2)
    )

    last_exc: Exception = RuntimeError("no attempts made")
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=_MODEL,
                temperature=_TEMPERATURE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            raw = response.choices[0].message.content or ""
            decision = _parse_decision(raw)
            logger.debug(f"Critic response (attempt {attempt}): {decision.rationale[:120]}")
            return decision
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            last_exc = exc
            logger.warning(f"Critic parse error (attempt {attempt}/{_MAX_RETRIES}): {exc}")
            time.sleep(0.5 * attempt)

    raise RuntimeError(
        f"LLM critic returned invalid JSON after {_MAX_RETRIES} attempts: {last_exc}"
    ) from last_exc


def _parse_decision(raw: str) -> CriticDecision:
    """Extract JSON block from the LLM output and validate it."""
    # Strip markdown code fences if present
    text = raw.strip()
    if "```" in text:
        # Extract content between first ``` and last ```
        start = text.find("```") + 3
        if text[start:].startswith("json"):
            start += 4
        end = text.rfind("```")
        text = text[start:end].strip()

    data = json.loads(text)

    # Validate required keys
    if "thresholds" not in data:
        raise KeyError("Missing 'thresholds' key in critic response")
    if "rationale" not in data:
        raise KeyError("Missing 'rationale' key in critic response")

    direction = data.get("expected_direction", "hold")
    if direction not in ("grow", "shrink", "hold"):
        direction = "hold"

    # Coerce threshold values to float, clamp to [0.0, 1.0]
    thresholds = {
        str(k): max(0.0, min(1.0, float(v)))
        for k, v in data["thresholds"].items()
    }

    return CriticDecision(
        thresholds=thresholds,
        rationale=str(data["rationale"])[:1000],
        expected_direction=direction,
    )
