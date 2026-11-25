"""Public surface for the XML escaping exercise.

The eight functions below are implemented in :mod:`xmlesc.escape`.
"""

from __future__ import annotations

from .escape import (
    escape_attr,
    escape_batch,
    escape_once,
    escape_text,
    normalize_entity,
    roundtrip_ok,
    unescape,
    valid_codepoint,
)

__all__ = [
    "escape_text",
    "escape_attr",
    "unescape",
    "valid_codepoint",
    "normalize_entity",
    "escape_once",
    "roundtrip_ok",
    "escape_batch",
]