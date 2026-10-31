"""Turn raw error messages into stable *signatures*.

A signature is a message with volatile parts (numbers, ids, addresses, paths,
timestamps, quoted values...) replaced by placeholders. Two messages that differ
only in such volatile parts collapse to the same signature, which is what makes
grouping and counting meaningful.
"""

from __future__ import annotations

import hashlib
import re
from typing import Tuple

__all__ = ["normalize_message", "signature_id", "compute_signature"]

# Order matters: more specific patterns run before the greedy numeric rule.
_RULES = (
    # Quoted strings -> <STR>
    (re.compile(r"'[^']*'"), "<STR>"),
    (re.compile(r'"[^"]*"'), "<STR>"),
    # URLs and emails
    (re.compile(r"\bhttps?://\S+", re.IGNORECASE), "<URL>"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "<EMAIL>"),
    # UUIDs
    (
        re.compile(
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
        ),
        "<UUID>",
    ),
    # Embedded ISO-ish timestamps
    (
        re.compile(
            r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d{1,6})?"
            r"(?:Z|[+-]\d{2}:?\d{2})?\b"
        ),
        "<TS>",
    ),
    # IPv4 addresses
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"), "<IP>"),
    # Hex literals and long hex blobs
    (re.compile(r"\b0x[0-9a-fA-F]+\b"), "<HEX>"),
    (re.compile(r"\b[0-9a-f]{16,}\b"), "<HEX>"),
    # file.ext:line references
    (re.compile(r"\b[\w./\\-]+\.[A-Za-z]\w*:\d+\b"), "<FILE>"),
    # Numbers (ints and floats, optional sign)
    (re.compile(r"\b\d+(?:\.\d+)?\b"), "<NUM>"),
)

_WHITESPACE = re.compile(r"\s+")


def normalize_message(message: str) -> str:
    """Return the placeholder-normalized form of ``message``."""
    result = message
    for pattern, replacement in _RULES:
        result = pattern.sub(replacement, result)
    return _WHITESPACE.sub(" ", result).strip()


def signature_id(signature: str) -> str:
    """Return a short, stable hash for a normalized signature."""
    digest = hashlib.sha1(signature.encode("utf-8")).hexdigest()
    return digest[:12]


def compute_signature(message: str) -> Tuple[str, str]:
    """Return ``(normalized_signature, id)`` for a raw message."""
    normalized = normalize_message(message)
    return normalized, signature_id(normalized)
