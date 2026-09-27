"""
Data loader for demo source records.

All data is loaded at startup from the backend/demo-data directory.
Connectors look up identifiers dynamically — they never branch on bidder name.
"""

import json
import os
from pathlib import Path
from typing import Any

# Resolve path to demo-data regardless of where the process is started from.
# connector-service/ is a sibling of backend/, so we go two levels up from this file
# to reach the repo root, then into backend/demo-data.
_REPO_ROOT = Path(__file__).resolve().parents[3]  # connector-service/app/data -> repo root
_DEMO_DATA = _REPO_ROOT / "backend" / "demo-data"


def _load(filename: str) -> Any:
    filepath = _DEMO_DATA / filename
    if not filepath.exists():
        raise FileNotFoundError(
            f"Demo data file not found: {filepath}. "
            "Ensure backend/demo-data/ exists and is populated."
        )
    with open(filepath, encoding="utf-8") as fh:
        return json.load(fh)


# ── Cached source records ──────────────────────────────────────────────────────

GST_RECORDS: list[dict] = _load("gst-records.json")
PAN_RECORDS: list[dict] = _load("pan-records.json")
UDYAM_RECORDS: list[dict] = _load("udyam-records.json")
MCA_RECORDS: list[dict] = _load("mca-records.json")
OEM_RECORDS: list[dict] = _load("oem-authorisations.json")
DIGILOCKER_RECORDS: list[dict] = _load("digilocker-records.json")
BLACKLIST_RECORDS: list[dict] = _load("blacklist-records.json")
STATUTORY_RECORDS: list[dict] = _load("statutory-records.json")


# ── Lookup helpers ─────────────────────────────────────────────────────────────

def find_gst(gstin: str) -> dict | None:
    gstin = gstin.upper().strip()
    return next((r for r in GST_RECORDS if r["gstin"].upper() == gstin), None)


def find_pan(pan: str) -> dict | None:
    pan = pan.upper().strip()
    return next((r for r in PAN_RECORDS if r["pan"].upper() == pan), None)


def find_udyam(udyam_number: str) -> dict | None:
    num = udyam_number.upper().strip()
    return next((r for r in UDYAM_RECORDS if r["udyamNumber"].upper() == num), None)


def find_mca(cin: str) -> dict | None:
    cin = cin.upper().strip()
    return next((r for r in MCA_RECORDS if r["cin"].upper() == cin), None)


def find_oem(authorisation_number: str) -> dict | None:
    num = authorisation_number.strip()
    return next(
        (r for r in OEM_RECORDS if r["authorisationNumber"] == num), None
    )


def find_digilocker(document_id: str) -> dict | None:
    return next(
        (r for r in DIGILOCKER_RECORDS if r["documentId"] == document_id), None
    )


def find_blacklist_by_pan(pan: str) -> dict | None:
    pan = pan.upper().strip()
    return next((r for r in BLACKLIST_RECORDS if r["pan"].upper() == pan), None)


def find_statutory(source: str, identifier: str) -> list[dict]:
    source = source.upper().strip()
    identifier = identifier.upper().strip()
    return [
        r for r in STATUTORY_RECORDS
        if r["source"].upper() == source and r["identifier"].upper() == identifier
    ]
