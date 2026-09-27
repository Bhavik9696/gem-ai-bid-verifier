"""
Compliance Engine — Entity Matcher

Compares bidder-submitted identity information against extracted document
facts and source-verified data. Produces a list of MatchResult objects
describing how each identity field compared.

Design constraints:
    - Deterministic: same inputs always produce same outputs.
    - No database access, no HTTP calls, no side effects.
    - Fuzzy name matching NEVER establishes confirmed identity.
    - Missing values produce NOT_AVAILABLE, never inferred matches.
    - Multiple source records are handled deterministically.

Matching behaviour by field:
    PAN      → uppercase exact string comparison
    GSTIN    → uppercase exact string comparison
    Udyam    → normalise_identifier (strip dashes/whitespace), then exact
    CIN      → uppercase exact string comparison
    Name     → normalise_name, then exact. If normalised exact fails,
               similarity ≥ 0.85 flags for review (is_confirmed=False).
"""

from __future__ import annotations

from .schemas import (
    BidderProfile,
    ExtractedFact,
    ExtractedObservation,
    VerificationResult,
    VerificationObservation,
    MatchResult,
    MatchType,
)
from .utils import (
    normalise_name,
    normalise_identifier,
    name_similarity,
)


# ---------------------------------------------------------------------------
# Source-to-field mapping
# ---------------------------------------------------------------------------
# Maps connector source names to the verified_facts keys that contain
# the relevant identity values. This allows the matcher to extract
# the correct comparison value from each source's response.

_SOURCE_FIELD_MAP: dict[str, dict[str, str]] = {
    "PAN_DEMO": {
        "pan": "pan",
        "legalName": "name",
    },
    "GST_DEMO": {
        "gstin": "gstin",       # some GST responses include gstin in verified_facts
        "legalName": "legalName",
    },
    "UDYAM_DEMO": {
        "udyamNumber": "udyamNumber",
        "legalName": "enterpriseName",
        "pan": "pan",
    },
    "MCA_DEMO": {
        "cin": "cin",
        "legalName": "companyName",
    },
}

# Which source is the primary verifier for each identifier field
_PRIMARY_SOURCE: dict[str, str] = {
    "pan": "PAN_DEMO",
    "gstin": "GST_DEMO",
    "udyamNumber": "UDYAM_DEMO",
    "cin": "MCA_DEMO",
}

# Name comparison threshold: similarity at or above this triggers a review
# flag but never confirms identity.
_NAME_SIMILARITY_THRESHOLD = 0.85


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_bidder_value(bidder: BidderProfile, field: str) -> str | None:
    """Retrieve the bidder's value for a given identity field."""
    field_map = {
        "pan": bidder.pan,
        "gstin": bidder.gstin,
        "udyamNumber": bidder.udyam_number,
        "cin": bidder.cin,
        "legalName": bidder.legal_name,
    }
    return field_map.get(field)


def _get_extracted_value(
    facts: list[ExtractedFact], field: str
) -> str | None:
    """
    Find the extracted value for a field from document facts.
    If multiple facts exist for the same field, use the one with
    the highest confidence.
    """
    candidates = [f for f in facts if f.field == field and f.value is not None]
    if not candidates:
        return None
    best = max(candidates, key=lambda f: f.confidence)
    return best.value


def _get_source_value(
    verifications: list[VerificationResult],
    field: str,
    source_name: str,
) -> tuple[str | None, str]:
    """
    Find the source-verified value for a field from a specific source.

    Returns:
        (value, actual_source_name) — value may be None if not found.
    """
    for vr in verifications:
        if vr.source != source_name:
            continue
        if vr.status not in ("VERIFIED",):
            continue
        # Look up the key in verified_facts using the field map
        source_keys = _SOURCE_FIELD_MAP.get(source_name, {})
        fact_key = source_keys.get(field)
        if fact_key and fact_key in vr.verified_facts:
            raw = vr.verified_facts[fact_key]
            return (str(raw) if raw is not None else None, source_name)
    return (None, source_name)


# ---------------------------------------------------------------------------
# Provenance collection helpers
# ---------------------------------------------------------------------------

def _collect_extracted_observations(
    facts: list[ExtractedFact],
    field: str,
) -> list[ExtractedObservation]:
    """
    Collect ALL extracted facts for a field, preserving every observation
    including lower-confidence values and None values.

    Sorted by confidence descending, then document_id for deterministic output.
    """
    observations: list[ExtractedObservation] = []
    for f in facts:
        if f.field == field:
            observations.append(ExtractedObservation(
                value=f.value,
                confidence=f.confidence,
                document_id=f.document_id,
                page=f.page,
                document_type=f.document_type,
            ))
    # Deterministic sort: highest confidence first, then by document_id
    observations.sort(key=lambda o: (-o.confidence, o.document_id))
    return observations


def _collect_verification_observations(
    verifications: list[VerificationResult],
    source_name: str,
    field: str,
) -> list[VerificationObservation]:
    """
    Collect ALL verification results from a specific source for a field.

    Includes VERIFIED, NOT_FOUND, and ERROR results — all are preserved
    so that downstream phases (conflict detection) can distinguish
    between missing, unavailable, and conflicting evidence.

    Sorted by checked_at for deterministic output.
    """
    source_keys = _SOURCE_FIELD_MAP.get(source_name, {})
    fact_key = source_keys.get(field)

    observations: list[VerificationObservation] = []
    for vr in verifications:
        if vr.source != source_name:
            continue
        # Extract the specific field value if available
        value: str | None = None
        if fact_key and fact_key in vr.verified_facts:
            raw = vr.verified_facts[fact_key]
            value = str(raw) if raw is not None else None

        observations.append(VerificationObservation(
            source=vr.source,
            identifier=vr.identifier,
            status=vr.status,
            value=value,
            verified_facts=vr.verified_facts,
            checked_at=vr.checked_at,
            evidence_reference=vr.evidence_reference,
        ))
    # Deterministic sort by checked_at, then identifier
    observations.sort(key=lambda o: (o.checked_at or "", o.identifier))
    return observations


def _match_identifier(
    bid_value: str | None,
    source_value: str | None,
    field: str,
    source: str,
    use_normalise: bool = False,
) -> MatchResult:
    """
    Compare two identifier values (PAN, GSTIN, Udyam, CIN).

    For Udyam: uses normalise_identifier to strip dashes/whitespace.
    For others: uses simple uppercase comparison.
    """
    if bid_value is None and source_value is None:
        return MatchResult(
            field=field,
            bid_value=None,
            source_value=None,
            source=source,
            match_type=MatchType.NOT_AVAILABLE,
            is_confirmed=False,
            notes="Both bid and source values are missing.",
        )

    if bid_value is None:
        return MatchResult(
            field=field,
            bid_value=None,
            source_value=source_value,
            source=source,
            match_type=MatchType.NOT_AVAILABLE,
            is_confirmed=False,
            notes="Bidder did not provide this identifier.",
        )

    if source_value is None:
        return MatchResult(
            field=field,
            bid_value=bid_value,
            source_value=None,
            source=source,
            match_type=MatchType.NOT_AVAILABLE,
            is_confirmed=False,
            notes="Source verification did not return this value.",
        )

    # Normalise for comparison
    if use_normalise:
        norm_bid = normalise_identifier(bid_value)
        norm_src = normalise_identifier(source_value)
    else:
        norm_bid = bid_value.upper().strip()
        norm_src = source_value.upper().strip()

    if norm_bid == norm_src:
        return MatchResult(
            field=field,
            bid_value=bid_value,
            source_value=source_value,
            source=source,
            match_type=MatchType.EXACT,
            is_confirmed=True,
        )
    else:
        return MatchResult(
            field=field,
            bid_value=bid_value,
            source_value=source_value,
            source=source,
            match_type=MatchType.MISMATCH,
            is_confirmed=False,
            notes=f"Identifier mismatch: bid='{bid_value}' vs source='{source_value}'.",
        )


def _match_name(
    bid_value: str | None,
    source_value: str | None,
    source: str,
) -> MatchResult:
    """
    Compare legal/company names using normalisation and similarity.

    - Normalised exact match → NORMALISED_MATCH, is_confirmed=True.
    - Similarity ≥ 0.85 → MISMATCH, is_confirmed=False, with review note.
    - Similarity < 0.85 → MISMATCH, is_confirmed=False.
    - Missing value → NOT_AVAILABLE, is_confirmed=False.
    """
    field = "legalName"

    if bid_value is None and source_value is None:
        return MatchResult(
            field=field,
            bid_value=None,
            source_value=None,
            source=source,
            match_type=MatchType.NOT_AVAILABLE,
            is_confirmed=False,
            notes="Both bid and source names are missing.",
        )

    if bid_value is None:
        return MatchResult(
            field=field,
            bid_value=None,
            source_value=source_value,
            source=source,
            match_type=MatchType.NOT_AVAILABLE,
            is_confirmed=False,
            notes="Bidder name not available for comparison.",
        )

    if source_value is None:
        return MatchResult(
            field=field,
            bid_value=bid_value,
            source_value=None,
            source=source,
            match_type=MatchType.NOT_AVAILABLE,
            is_confirmed=False,
            notes="Source did not return a name for comparison.",
        )

    # Normalised exact comparison
    norm_bid = normalise_name(bid_value)
    norm_src = normalise_name(source_value)

    if norm_bid and norm_src and norm_bid == norm_src:
        return MatchResult(
            field=field,
            bid_value=bid_value,
            source_value=source_value,
            source=source,
            match_type=MatchType.NORMALISED_MATCH,
            is_confirmed=True,
        )

    # Fuzzy similarity — never confirms identity
    similarity = name_similarity(bid_value, source_value)

    if similarity >= _NAME_SIMILARITY_THRESHOLD:
        return MatchResult(
            field=field,
            bid_value=bid_value,
            source_value=source_value,
            source=source,
            match_type=MatchType.MISMATCH,
            is_confirmed=False,
            notes=(
                f"Names are similar (score={similarity:.2f}) but not a normalised "
                f"exact match. Flagged for officer review."
            ),
        )

    return MatchResult(
        field=field,
        bid_value=bid_value,
        source_value=source_value,
        source=source,
        match_type=MatchType.MISMATCH,
        is_confirmed=False,
        notes=f"Name mismatch (similarity={similarity:.2f}).",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def match_entities(
    bidder: BidderProfile,
    extracted_facts: list[ExtractedFact],
    verification_results: list[VerificationResult],
) -> list[MatchResult]:
    """
    Compare bidder-submitted identity information against extracted
    document facts and source-verified data.

    Evaluates: PAN, GSTIN, Udyam number, CIN, and legal name.

    For each identity field:
      1. Resolve the bid value from the bidder profile.
      2. Resolve the source value from the relevant verification result.
      3. Compare and classify the match.

    For name comparisons, checks are performed against each source
    that returns a name value, producing one MatchResult per source.

    Args:
        bidder: The bidder's submitted profile.
        extracted_facts: Facts extracted from the bidder's documents.
        verification_results: Responses from source connectors.

    Returns:
        List of MatchResult objects, one per field per source comparison.
    """
    results: list[MatchResult] = []

    # ---------------------------------------------------------------
    # 1. Identifier matching (PAN, GSTIN, Udyam, CIN)
    # ---------------------------------------------------------------
    identifier_fields = [
        ("pan", False),
        ("gstin", False),
        ("udyamNumber", True),   # use normalise_identifier for Udyam
        ("cin", False),
    ]

    for field, use_normalise in identifier_fields:
        bid_value = _get_bidder_value(bidder, field)
        primary_source = _PRIMARY_SOURCE.get(field, "UNKNOWN")

        # Try to get source value from the primary verification source
        source_value, source_name = _get_source_value(
            verification_results, field, primary_source
        )

        # If primary source didn't have the identifier in verified_facts,
        # also check if the identifier itself matches (for connectors
        # where the identifier IS the verified fact)
        if source_value is None and bid_value is not None:
            for vr in verification_results:
                if vr.source == primary_source and vr.status == "VERIFIED":
                    # The connector was queried with this identifier and
                    # returned VERIFIED — the identifier itself is confirmed
                    if use_normalise:
                        norm_bid = normalise_identifier(bid_value)
                        norm_id = normalise_identifier(vr.identifier)
                    else:
                        norm_bid = bid_value.upper().strip()
                        norm_id = vr.identifier.upper().strip()

                    if norm_bid == norm_id:
                        source_value = vr.identifier
                    break

        # Build the match result and attach evidence provenance
        match_result = _match_identifier(
            bid_value, source_value, field, source_name, use_normalise
        )
        extracted_obs = _collect_extracted_observations(extracted_facts, field)
        verification_obs = _collect_verification_observations(
            verification_results, source_name, field
        )
        results.append(match_result.model_copy(update={
            "extracted_observations": extracted_obs,
            "verification_observations": verification_obs,
        }))

    # ---------------------------------------------------------------
    # 2. Legal name matching (against each source that returns a name)
    # ---------------------------------------------------------------
    bid_name = _get_bidder_value(bidder, "legalName")
    name_sources_checked: set[str] = set()

    for source_name, field_map in _SOURCE_FIELD_MAP.items():
        name_key = field_map.get("legalName")
        if not name_key:
            continue

        # Find a VERIFIED result from this source
        source_name_value: str | None = None
        for vr in verification_results:
            if vr.source == source_name and vr.status == "VERIFIED":
                raw = vr.verified_facts.get(name_key)
                if raw is not None:
                    source_name_value = str(raw)
                break

        if source_name_value is None:
            # No name from this source — skip to avoid redundant NOT_AVAILABLE
            continue

        name_sources_checked.add(source_name)
        name_result = _match_name(bid_name, source_name_value, source_name)
        name_extracted_obs = _collect_extracted_observations(
            extracted_facts, "legalName"
        )
        name_verification_obs = _collect_verification_observations(
            verification_results, source_name, "legalName"
        )
        results.append(name_result.model_copy(update={
            "extracted_observations": name_extracted_obs,
            "verification_observations": name_verification_obs,
        }))

    # If no source returned a name at all, emit one NOT_AVAILABLE result
    if not name_sources_checked:
        name_extracted_obs = _collect_extracted_observations(
            extracted_facts, "legalName"
        )
        results.append(
            MatchResult(
                field="legalName",
                bid_value=bid_name,
                source_value=None,
                source="NONE",
                match_type=MatchType.NOT_AVAILABLE,
                is_confirmed=False,
                notes="No verification source returned a name for comparison.",
                extracted_observations=name_extracted_obs,
                verification_observations=[],
            )
        )

    return results
