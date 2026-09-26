"""
Identifier format validators for the Connector Service.

All validation uses regex patterns matching official Indian government formats.
Invalid format → 422 Unprocessable Entity with a clear error message.
"""

import re
from fastapi import HTTPException

# ── Regex patterns ─────────────────────────────────────────────────────────────

# GSTIN: 15 chars — 2-digit state code + 10-char PAN + 1 entity code + 1 check + Z
_GSTIN_RE = re.compile(r"^[0-3][0-9][A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")

# PAN: 10 chars — AAAAA9999A (5 letters, 4 digits, 1 letter)
_PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")

# Udyam: UDYAM-XX-00-0000000
_UDYAM_RE = re.compile(r"^UDYAM-[A-Z]{2}-\d{2}-\d{7}$")

# CIN: U/L + 5 digits + 2-letter state + 4-digit year + PTC/LLP + 6 digits
_CIN_RE = re.compile(r"^[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$")

# OEM authorisation: any non-empty printable string (no strict format)
_OEM_RE = re.compile(r"^[\w\-/\.]{3,60}$")


# ── Validator functions ────────────────────────────────────────────────────────

def validate_gstin(gstin: str) -> str:
    """Validate and normalise a GSTIN. Raises HTTP 422 on failure."""
    val = gstin.upper().strip()
    if not _GSTIN_RE.match(val):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_GSTIN_FORMAT",
                "message": (
                    f"'{gstin}' is not a valid GSTIN. "
                    "Expected 15-character format: 2-digit state code + 10-char PAN + 3 chars. "
                    "Example: 33AABCA1234F1Z5"
                ),
            },
        )
    return val


def validate_pan(pan: str) -> str:
    """Validate and normalise a PAN. Raises HTTP 422 on failure."""
    val = pan.upper().strip()
    if not _PAN_RE.match(val):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_PAN_FORMAT",
                "message": (
                    f"'{pan}' is not a valid PAN. "
                    "Expected 10-character format: AAAAA9999A (5 letters, 4 digits, 1 letter). "
                    "Example: AABCA1234F"
                ),
            },
        )
    return val


def validate_udyam(udyam_number: str) -> str:
    """Validate and normalise a Udyam registration number. Raises HTTP 422 on failure."""
    val = udyam_number.upper().strip()
    if not _UDYAM_RE.match(val):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_UDYAM_FORMAT",
                "message": (
                    f"'{udyam_number}' is not a valid Udyam number. "
                    "Expected format: UDYAM-XX-00-0000000. "
                    "Example: UDYAM-TN-01-0001234"
                ),
            },
        )
    return val


def validate_cin(cin: str) -> str:
    """Validate and normalise a CIN. Raises HTTP 422 on failure."""
    val = cin.upper().strip()
    if not _CIN_RE.match(val):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_CIN_FORMAT",
                "message": (
                    f"'{cin}' is not a valid CIN. "
                    "Expected format: U/L + 5 digits + 2-letter state + 4-digit year + PTC/LLP + 6 digits. "
                    "Example: U72900TN2018PTC122345"
                ),
            },
        )
    return val


def validate_oem_ref(ref: str) -> str:
    """Validate an OEM authorisation reference number. Raises HTTP 422 on failure."""
    val = ref.strip()
    if not val or not _OEM_RE.match(val):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INVALID_OEM_REFERENCE",
                "message": (
                    f"'{ref}' is not a valid OEM authorisation reference. "
                    "Must be 3–60 alphanumeric/dash/dot characters. "
                    "Example: OEM-DELL-ASTER-2024-001"
                ),
            },
        )
    return val
