"""
Compliance Engine — Utility Helpers

Pure helper functions for normalisation, comparison, date parsing,
and ID generation. No business logic — only data transformation.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import date, datetime
from difflib import SequenceMatcher


# ---------------------------------------------------------------------------
# Name normalisation
# ---------------------------------------------------------------------------

# Words stripped during legal-name normalisation (order doesn't matter).
_LEGAL_SUFFIXES = re.compile(
    r"\b(private|pvt|limited|ltd|llp|inc|incorporated|corporation|corp)\b",
    re.IGNORECASE,
)

# Collapse multiple whitespace / punctuation noise.
_WHITESPACE = re.compile(r"\s+")
_PUNCTUATION = re.compile(r"[.\-,()&]")


def normalise_name(name: str | None) -> str:
    """
    Normalise a legal / company name for comparison.

    Steps:
      1. Lowercase.
      2. Remove common legal suffixes (Pvt, Private, Ltd, Limited, etc.).
      3. Strip punctuation (dots, dashes, commas, parens, ampersand).
      4. Collapse whitespace.
      5. Strip leading/trailing whitespace.

    Returns an empty string if input is None or blank.
    """
    if not name:
        return ""
    result = name.lower()
    result = _LEGAL_SUFFIXES.sub("", result)
    result = _PUNCTUATION.sub(" ", result)
    result = _WHITESPACE.sub(" ", result).strip()
    return result


# ---------------------------------------------------------------------------
# Identifier normalisation
# ---------------------------------------------------------------------------

_NON_ALNUM = re.compile(r"[^A-Z0-9]")


def normalise_identifier(value: str | None) -> str:
    """
    Normalise a PAN, GSTIN, CIN, Udyam number, or similar identifier.

    Steps:
      1. Uppercase.
      2. Strip all non-alphanumeric characters (spaces, dashes, dots).

    Returns an empty string if input is None or blank.
    """
    if not value:
        return ""
    return _NON_ALNUM.sub("", value.upper())


# ---------------------------------------------------------------------------
# Name similarity
# ---------------------------------------------------------------------------

def name_similarity(a: str, b: str) -> float:
    """
    Compute similarity ratio between two names after normalisation.
    Uses stdlib ``difflib.SequenceMatcher`` — no external fuzzy library needed.

    Returns a float in [0.0, 1.0].
    """
    norm_a = normalise_name(a)
    norm_b = normalise_name(b)
    if not norm_a or not norm_b:
        return 0.0
    if norm_a == norm_b:
        return 1.0
    return SequenceMatcher(None, norm_a, norm_b).ratio()


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

# Supported date formats, tried in order.
_DATE_FORMATS = [
    "%Y-%m-%d",       # ISO 8601: 2026-09-30
    "%d/%m/%Y",       # Indian common: 30/09/2026
    "%d-%m-%Y",       # 30-09-2026
    "%d-%b-%Y",       # 30-Sep-2026
    "%d %b %Y",       # 30 Sep 2026
    "%Y-%m-%dT%H:%M:%S",     # ISO with time
    "%Y-%m-%dT%H:%M:%S.%f",  # ISO with microseconds
    "%Y-%m-%dT%H:%M:%SZ",    # ISO with Z suffix
]


def parse_date(value: str | None) -> date | None:
    """
    Parse a date string into a ``datetime.date``.

    Tries ISO 8601 first, then common Indian formats. Returns ``None``
    if the value is empty or cannot be parsed.
    """
    if not value or not value.strip():
        return None

    clean = value.strip()

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(clean, fmt).date()
        except ValueError:
            continue

    return None


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def generate_finding_id() -> str:
    """Generate a unique finding ID using UUID v4."""
    return f"FND-{uuid.uuid4().hex[:12].upper()}"


def generate_deterministic_finding_id(finding_type: str, *key_parts: str) -> str:
    """
    Generate a deterministic finding ID from the finding type and key
    evidence components.

    Same inputs always produce the same ID. Uses SHA-256 to ensure
    uniqueness for distinct inputs while remaining collision-resistant.

    Args:
        finding_type: The finding type code (e.g. ``'PAN_MISMATCH'``).
        *key_parts: Evidence strings that distinguish this finding from
                    others of the same type (e.g. field values, source IDs).

    Returns:
        A ``FND-`` prefixed 12-character hex digest.
    """
    content = "|".join([finding_type] + [str(p) for p in key_parts])
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12].upper()
    return f"FND-{digest}"


def generate_id(prefix: str = "ID") -> str:
    """Generate a prefixed unique ID using UUID v4."""
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
