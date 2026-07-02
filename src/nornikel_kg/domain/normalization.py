from __future__ import annotations

import re

_DASH_VARIANTS_RE = re.compile(r"[‐‑‒–—―−_]")
_WHITESPACE_RE = re.compile(r"\s+")


def canonical_key(value: str) -> str:
    """Normalize an entity mention into its canonical resolution key.

    Rules fixed by the entity-resolution contract: lowercase, strip, unify
    every dash variant to "-", fold "ё" to "е", collapse whitespace runs.
    """
    normalized = _DASH_VARIANTS_RE.sub("-", value.strip().lower())
    normalized = normalized.replace("ё", "е")
    return _WHITESPACE_RE.sub(" ", normalized)
