"""
Compliance Engine — Conflict Detector

Consumes structured bidder information, extracted document facts,
verification responses, Entity Matcher results, and tender context to
produce explainable compliance findings.

This is Phase 3 of the compliance engine. It does not calculate scores,
generate recommendations, or make final procurement decisions.

Design constraints:
    - Deterministic: same inputs always produce same outputs.
    - No database access, no HTTP calls, no LLM calls, no side effects.
    - Every finding includes explainable evidence and provenance.
    - Duplicate findings for the same underlying issue are prevented.
    - Missing evidence is never treated as a confirmed match.
    - ERROR/NOT_FOUND are never treated as positive confirmations.
    - Finding IDs are deterministic: identical input evidence produces
      identical finding IDs (via SHA-256 hashing).

Conflict categories:
    GST_LEGAL_NAME_MISMATCH       — GST verified name ≠ bidder/PAN name
    PAN_MISMATCH                  — PAN discrepancy across sources
    GST_INACTIVE_AT_CLOSING       — GST inactive/cancelled before closing
    UDYAM_CERTIFICATE_MISSING     — No Udyam certificate evidence found
    UDYAM_CERTIFICATE_UNVERIFIED  — Udyam evidence present but not verified
    OEM_AUTH_EXPIRED              — OEM authorisation expired before closing
    BLACKLIST_DEBARMENT_HIT       — Blacklist/debarment hit detected
    LOCAL_CONTENT_THRESHOLD_FAILED — Local content below tender threshold
    MANDATORY_DOCUMENT_MISSING    — No extracted evidence for required document
    SOURCE_UNAVAILABLE            — Verification source returned ERROR
    LOW_CONFIDENCE_MATERIAL_FACT  — Material fact below confidence threshold
    CONFLICTING_SOURCE_EVIDENCE   — Sources provide conflicting values
"""

from __future__ import annotations

from .schemas import (
    BidderProfile,
    ExtractedFact,
    Finding,
    MatchResult,
    MatchType,
    Severity,
    TenderContext,
    VerificationResult,
)
from .utils import (
    generate_deterministic_finding_id,
    normalise_name,
    parse_date,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Material identity fields whose low confidence warrants a finding
_MATERIAL_FIELDS = frozenset({"pan", "gstin", "udyamNumber", "cin", "legalName"})

# Confidence threshold below which a material fact is flagged
_LOW_CONFIDENCE_THRESHOLD = 0.70

# Source field-key mapping for extracting specific values from verified_facts
_GST_NAME_KEY = "legalName"
_PAN_KEY = "pan"
_PAN_NAME_KEY = "name"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_match_result(
    match_results: list[MatchResult], field: str, source: str | None = None
) -> MatchResult | None:
    """Find a MatchResult by field and optionally by source."""
    for mr in match_results:
        if mr.field == field:
            if source is None or mr.source == source:
                return mr
    return None


def _find_verification(
    verifications: list[VerificationResult], source: str
) -> VerificationResult | None:
    """Find the first verification result from a specific source."""
    for vr in verifications:
        if vr.source == source:
            return vr
    return None


def _find_verifications_by_source(
    verifications: list[VerificationResult], source: str
) -> list[VerificationResult]:
    """Find all verification results from a specific source."""
    return [vr for vr in verifications if vr.source == source]


def _find_extracted_facts(
    facts: list[ExtractedFact], field: str
) -> list[ExtractedFact]:
    """Find all extracted facts for a given field."""
    return [f for f in facts if f.field == field]


def _best_extracted_value(facts: list[ExtractedFact], field: str) -> str | None:
    """Get the highest-confidence extracted value for a field."""
    candidates = [f for f in facts if f.field == field and f.value is not None]
    if not candidates:
        return None
    best = max(candidates, key=lambda f: f.confidence)
    return best.value


# ---------------------------------------------------------------------------
# Individual conflict detectors
# ---------------------------------------------------------------------------

def _detect_gst_legal_name_mismatch(
    bidder: BidderProfile,
    match_results: list[MatchResult],
    verification_results: list[VerificationResult],
) -> Finding | None:
    """
    A. Detect when the GST-verified legal name differs from the bidder's
    submitted legal name.

    Uses normalised name comparison. Does not treat fuzzy similarity as
    identity proof.
    """
    gst_name_match = _find_match_result(match_results, "legalName", "GST_DEMO")
    if gst_name_match is None:
        return None

    # Only flag actual mismatches, not NOT_AVAILABLE
    if gst_name_match.match_type not in (MatchType.MISMATCH,):
        return None

    # The GST source returned a name that doesn't match the bidder
    gst_vr = _find_verification(verification_results, "GST_DEMO")
    evidence: dict = {
        "bidder_legal_name": bidder.legal_name,
        "gst_verified_name": gst_name_match.source_value,
        "normalised_bidder_name": normalise_name(bidder.legal_name),
        "normalised_gst_name": normalise_name(gst_name_match.source_value),
    }
    if gst_vr:
        evidence["source"] = gst_vr.source
        evidence["identifier"] = gst_vr.identifier
        evidence["checked_at"] = gst_vr.checked_at
        evidence["evidence_reference"] = gst_vr.evidence_reference

    return Finding(
        finding_id=generate_deterministic_finding_id(
            "GST_LEGAL_NAME_MISMATCH",
            bidder.legal_name or "",
            gst_name_match.source_value or "",
        ),
        type="GST_LEGAL_NAME_MISMATCH",
        severity=Severity.HIGH,
        message=(
            f"GST-verified legal name '{gst_name_match.source_value}' does not match "
            f"the bidder's submitted name '{bidder.legal_name}'. "
            f"This discrepancy requires officer review."
        ),
        rule_id="GST_LEGAL_NAME_MISMATCH",
        tender_clause=None,
        source="GST_DEMO",
        evidence=evidence,
    )


def _detect_pan_mismatch(
    bidder: BidderProfile,
    extracted_facts: list[ExtractedFact],
    match_results: list[MatchResult],
    verification_results: list[VerificationResult],
) -> list[Finding]:
    """
    B. Detect PAN discrepancies between bidder, extracted, and verified values.

    Produces findings for:
    - Bidder PAN vs verified PAN mismatch
    - Extracted PAN vs bidder PAN mismatch (preserved from provenance)
    """
    findings: list[Finding] = []
    seen_types: set[str] = set()

    pan_match = _find_match_result(match_results, "pan")
    if pan_match is None:
        return findings

    # Check bidder PAN vs source-verified PAN
    if pan_match.match_type == MatchType.MISMATCH:
        key = f"PAN_MISMATCH:bid_vs_source:{pan_match.source}"
        if key not in seen_types:
            seen_types.add(key)
            evidence: dict = {
                "bidder_pan": pan_match.bid_value,
                "source_verified_pan": pan_match.source_value,
                "source": pan_match.source,
            }
            # Attach provenance if available
            if pan_match.verification_observations:
                evidence["verification_observations"] = [
                    {
                        "source": vo.source,
                        "identifier": vo.identifier,
                        "status": vo.status,
                        "value": vo.value,
                        "checked_at": vo.checked_at,
                        "evidence_reference": vo.evidence_reference,
                    }
                    for vo in pan_match.verification_observations
                ]
            if pan_match.extracted_observations:
                evidence["extracted_observations"] = [
                    {
                        "value": eo.value,
                        "confidence": eo.confidence,
                        "document_id": eo.document_id,
                        "page": eo.page,
                        "document_type": eo.document_type,
                    }
                    for eo in pan_match.extracted_observations
                ]

            findings.append(Finding(
                finding_id=generate_deterministic_finding_id(
                    "PAN_MISMATCH",
                    pan_match.bid_value or "",
                    pan_match.source_value or "",
                    pan_match.source or "",
                ),
                type="PAN_MISMATCH",
                severity=Severity.BLOCKER,
                message=(
                    f"Bidder PAN '{pan_match.bid_value}' does not match "
                    f"source-verified PAN '{pan_match.source_value}' from {pan_match.source}. "
                    f"This is a material identity discrepancy."
                ),
                rule_id="PAN_MISMATCH",
                tender_clause=None,
                source=pan_match.source,
                evidence=evidence,
            ))

    # Check if extracted PAN differs from bidder PAN (provenance-based)
    if bidder.pan and pan_match.extracted_observations:
        bidder_pan_upper = bidder.pan.upper().strip()
        for eo in pan_match.extracted_observations:
            if eo.value and eo.value.upper().strip() != bidder_pan_upper:
                key = f"PAN_MISMATCH:extracted_vs_bid:{eo.document_id}"
                if key not in seen_types:
                    seen_types.add(key)
                    findings.append(Finding(
                        finding_id=generate_deterministic_finding_id(
                            "CONFLICTING_SOURCE_EVIDENCE",
                            "pan",
                            eo.document_id or "",
                            eo.value or "",
                            bidder.pan,
                        ),
                        type="CONFLICTING_SOURCE_EVIDENCE",
                        severity=Severity.MEDIUM,
                        message=(
                            f"Document-extracted PAN '{eo.value}' "
                            f"(from {eo.document_id}, page {eo.page}, "
                            f"confidence {eo.confidence:.2f}) differs from "
                            f"bidder-submitted PAN '{bidder.pan}'. "
                            f"This may indicate an OCR error or document discrepancy."
                        ),
                        rule_id="CONFLICTING_SOURCE_EVIDENCE",
                        tender_clause=None,
                        source=eo.document_type,
                        evidence={
                            "bidder_pan": bidder.pan,
                            "extracted_pan": eo.value,
                            "document_id": eo.document_id,
                            "page": eo.page,
                            "confidence": eo.confidence,
                            "document_type": eo.document_type,
                        },
                    ))

    return findings


def _detect_gst_inactive(
    tender: TenderContext,
    verification_results: list[VerificationResult],
) -> Finding | None:
    """
    C. Detect when GST was inactive or cancelled on or before the
    tender closing date.

    Correctness rules:
        - If current status is ACTIVE, no GST-inactivity concern.
        - If status is non-ACTIVE AND a cancellation date before/at the
          tender closing date is available → BLOCKER (confirmed historical).
        - If status is non-ACTIVE AND the cancellation date is after the
          tender closing date → no finding (was active at closing).
        - If status is non-ACTIVE AND no cancellation date is available →
          HIGH severity (current status is concerning but the timing
          relative to the tender closing date cannot be established).
        - Missing or null gstStatus → no finding (cannot determine).
    """
    gst_results = _find_verifications_by_source(verification_results, "GST_DEMO")
    if not gst_results:
        return None

    for gst_vr in gst_results:
        if gst_vr.status != "VERIFIED":
            continue

        gst_status = gst_vr.verified_facts.get("gstStatus")
        cancellation_date_str = gst_vr.verified_facts.get("cancellationDate")

        # No status information → cannot determine, skip
        if not gst_status:
            continue

        # ACTIVE status → no inactivity concern
        if gst_status.upper() == "ACTIVE":
            continue

        # --- Status is NOT ACTIVE (e.g. CANCELLED, SUSPENDED) ---

        # If a cancellation date is available, compare to closing date
        if cancellation_date_str:
            cancellation_date = parse_date(cancellation_date_str)
            closing_date = parse_date(tender.closing_date)
            if cancellation_date and closing_date:
                if cancellation_date <= closing_date:
                    # CONFIRMED: registration was cancelled by the closing date
                    return Finding(
                        finding_id=generate_deterministic_finding_id(
                            "GST_INACTIVE_AT_CLOSING",
                            gst_status,
                            cancellation_date_str,
                            tender.closing_date,
                            gst_vr.identifier or "",
                        ),
                        type="GST_INACTIVE_AT_CLOSING",
                        severity=Severity.BLOCKER,
                        message=(
                            f"GST registration was cancelled on {cancellation_date_str}, "
                            f"which is on or before the tender closing date "
                            f"{tender.closing_date}. "
                            f"This confirms the bidder's GST was not active at bid closing."
                        ),
                        rule_id="GST_INACTIVE_AT_CLOSING",
                        tender_clause=None,
                        source="GST_DEMO",
                        evidence={
                            "gst_status": gst_status,
                            "cancellation_date": cancellation_date_str,
                            "tender_closing_date": tender.closing_date,
                            "status_confirmed_historical": True,
                            "identifier": gst_vr.identifier,
                            "checked_at": gst_vr.checked_at,
                            "evidence_reference": gst_vr.evidence_reference,
                        },
                    )
                else:
                    # Cancellation is AFTER closing date — was active at closing
                    continue

        # Status is not ACTIVE but no usable cancellation date to confirm
        # timing. Flag with HIGH severity (not BLOCKER) since we cannot
        # confirm historical inactivity at the specific closing date.
        return Finding(
            finding_id=generate_deterministic_finding_id(
                "GST_INACTIVE_AT_CLOSING",
                gst_status,
                "no_historical_date",
                gst_vr.identifier or "",
            ),
            type="GST_INACTIVE_AT_CLOSING",
            severity=Severity.HIGH,
            message=(
                f"GST registration is currently '{gst_status}' (not ACTIVE). "
                f"No cancellation or effective date was provided to confirm "
                f"whether the registration was inactive at the tender closing date "
                f"({tender.closing_date}). Officer review is required to "
                f"establish the historical status."
            ),
            rule_id="GST_INACTIVE_AT_CLOSING",
            tender_clause=None,
            source="GST_DEMO",
            evidence={
                "gst_status": gst_status,
                "cancellation_date": cancellation_date_str,
                "tender_closing_date": tender.closing_date,
                "status_confirmed_historical": False,
                "identifier": gst_vr.identifier,
                "checked_at": gst_vr.checked_at,
                "evidence_reference": gst_vr.evidence_reference,
            },
        )

    return None


def _detect_missing_udyam(
    tender: TenderContext,
    bidder: BidderProfile,
    extracted_facts: list[ExtractedFact],
    verification_results: list[VerificationResult],
    match_results: list[MatchResult],
) -> Finding | None:
    """
    D. Detect when Udyam documentation is mandatory for the tender
    but required evidence is absent or cannot be verified.

    Only flags when msme_mandatory=True in the tender context.

    Distinguishes three states:
        - VERIFIED: Udyam evidence is verified → no finding.
        - UNVERIFIED: Udyam evidence exists (bidder declared or document
          extracted) but verification is unavailable or failed.
        - MISSING: No Udyam evidence found at all.
    """
    if not tender.msme_mandatory:
        return None

    # Check if bidder provided Udyam
    has_bidder_udyam = bidder.udyam_number is not None

    # Check if any extracted fact for udyamNumber exists
    udyam_facts = _find_extracted_facts(extracted_facts, "udyamNumber")
    has_extracted_udyam = any(f.value for f in udyam_facts)

    # Check if any verification exists for UDYAM_DEMO
    udyam_verifications = _find_verifications_by_source(
        verification_results, "UDYAM_DEMO"
    )
    has_verified_udyam = any(
        vr.status == "VERIFIED" for vr in udyam_verifications
    )

    # State 1: Verified — no finding needed
    if has_verified_udyam:
        return None

    # Build evidence about what IS available
    evidence: dict = {
        "msme_mandatory": True,
        "bidder_udyam_number": bidder.udyam_number,
        "has_extracted_udyam": has_extracted_udyam,
        "has_verified_udyam": has_verified_udyam,
    }

    if udyam_verifications:
        evidence["udyam_verification_statuses"] = [
            {"source": vr.source, "status": vr.status, "identifier": vr.identifier}
            for vr in udyam_verifications
        ]

    # State 2: Evidence exists but not verified
    if has_bidder_udyam or has_extracted_udyam:
        udyam_ref = bidder.udyam_number or "extracted"
        if has_bidder_udyam and not has_extracted_udyam:
            message = (
                "This tender requires MSME/Udyam registration. "
                f"Bidder submitted Udyam number '{bidder.udyam_number}', "
                "but verification could not confirm it. "
                "The certificate may be valid but could not be verified "
                "from the available sources."
            )
        elif has_extracted_udyam and not has_bidder_udyam:
            message = (
                "This tender requires MSME/Udyam registration. "
                "A Udyam certificate was found in the uploaded documents, "
                "but the bidder did not declare a Udyam number and "
                "verification could not confirm the certificate. "
                "Officer review is required."
            )
        else:
            message = (
                "This tender requires MSME/Udyam registration. "
                f"Bidder submitted Udyam number '{bidder.udyam_number}' "
                "and a certificate was found in the documents, "
                "but verification could not confirm it."
            )

        return Finding(
            finding_id=generate_deterministic_finding_id(
                "UDYAM_CERTIFICATE_UNVERIFIED",
                bidder.bidder_id,
                bidder.udyam_number or "",
            ),
            type="UDYAM_CERTIFICATE_UNVERIFIED",
            severity=Severity.HIGH,
            message=message,
            rule_id="UDYAM_CERTIFICATE_UNVERIFIED",
            tender_clause=None,
            source="UDYAM_DEMO",
            evidence=evidence,
        )

    # State 3: No evidence at all
    return Finding(
        finding_id=generate_deterministic_finding_id(
            "UDYAM_CERTIFICATE_MISSING",
            bidder.bidder_id,
        ),
        type="UDYAM_CERTIFICATE_MISSING",
        severity=Severity.HIGH,
        message=(
            "This tender requires MSME/Udyam registration, but the bidder "
            "did not submit a Udyam number and no Udyam certificate was found "
            "in the uploaded documents."
        ),
        rule_id="UDYAM_CERTIFICATE_MISSING",
        tender_clause=None,
        source="UDYAM_DEMO",
        evidence=evidence,
    )


def _detect_expired_oem(
    tender: TenderContext,
    extracted_facts: list[ExtractedFact],
) -> Finding | None:
    """
    E. Detect when OEM authorisation expired before the tender closing date.

    Only runs when tender.oem_required is True. If OEM is not required by
    the tender, no OEM-related findings are produced.

    When required:
        - No oem_expiry_date facts → finding noting missing evidence.
        - Unparseable date value → finding noting invalid evidence.
        - Expiry before closing → OEM_AUTH_EXPIRED finding.
        - Expiry on or after closing → no finding (valid).
    """
    if not tender.oem_required:
        return None

    oem_expiry_facts = _find_extracted_facts(extracted_facts, "oem_expiry_date")

    if not oem_expiry_facts:
        # OEM required but no expiry evidence found at all
        return Finding(
            finding_id=generate_deterministic_finding_id(
                "OEM_AUTH_EXPIRED",
                "missing_evidence",
                tender.tender_id,
            ),
            type="OEM_AUTH_EXPIRED",
            severity=Severity.HIGH,
            message=(
                "OEM authorisation is required by this tender, but no OEM "
                "expiry date evidence was found in the bid documents. "
                "Officer review is required to determine OEM validity."
            ),
            rule_id="OEM_AUTH_EXPIRED",
            tender_clause=None,
            source=None,
            evidence={
                "oem_required": True,
                "expiry_evidence_found": False,
                "tender_closing_date": tender.closing_date,
            },
        )

    closing_date = parse_date(tender.closing_date)
    if closing_date is None:
        return None

    for fact in oem_expiry_facts:
        if fact.value is None:
            continue

        expiry_date = parse_date(fact.value)
        if expiry_date is None:
            # Malformed / unparseable date — produce explicit finding
            return Finding(
                finding_id=generate_deterministic_finding_id(
                    "OEM_AUTH_EXPIRED",
                    "invalid_evidence",
                    fact.document_id or "",
                    fact.value,
                ),
                type="OEM_AUTH_EXPIRED",
                severity=Severity.HIGH,
                message=(
                    f"OEM authorisation is required, but the extracted expiry "
                    f"date '{fact.value}' (from document '{fact.document_id}') "
                    f"could not be parsed. Officer review is required to "
                    f"determine OEM validity."
                ),
                rule_id="OEM_AUTH_EXPIRED",
                tender_clause=None,
                source=fact.document_type,
                evidence={
                    "oem_required": True,
                    "raw_expiry_value": fact.value,
                    "parse_error": True,
                    "tender_closing_date": tender.closing_date,
                    "document_id": fact.document_id,
                    "page": fact.page,
                    "confidence": fact.confidence,
                    "document_type": fact.document_type,
                },
            )

        if expiry_date < closing_date:
            return Finding(
                finding_id=generate_deterministic_finding_id(
                    "OEM_AUTH_EXPIRED",
                    fact.value,
                    tender.closing_date,
                    fact.document_id or "",
                ),
                type="OEM_AUTH_EXPIRED",
                severity=Severity.HIGH,
                message=(
                    f"OEM authorisation expiry date ({fact.value}) is before "
                    f"the tender closing date ({tender.closing_date}). "
                    f"The authorisation was not valid at bid closing."
                ),
                rule_id="OEM_AUTH_EXPIRED",
                tender_clause=None,
                source=fact.document_type,
                evidence={
                    "oem_expiry_date": fact.value,
                    "tender_closing_date": tender.closing_date,
                    "document_id": fact.document_id,
                    "page": fact.page,
                    "confidence": fact.confidence,
                    "document_type": fact.document_type,
                },
            )

    # Check if all facts had None values (submitted but empty)
    if all(f.value is None for f in oem_expiry_facts):
        return Finding(
            finding_id=generate_deterministic_finding_id(
                "OEM_AUTH_EXPIRED",
                "null_evidence",
                tender.tender_id,
            ),
            type="OEM_AUTH_EXPIRED",
            severity=Severity.HIGH,
            message=(
                "OEM authorisation is required. Document evidence for "
                "OEM expiry was found but contains no usable date value. "
                "Officer review is required."
            ),
            rule_id="OEM_AUTH_EXPIRED",
            tender_clause=None,
            source=None,
            evidence={
                "oem_required": True,
                "expiry_evidence_found": True,
                "usable_date_found": False,
                "tender_closing_date": tender.closing_date,
            },
        )

    return None


def _detect_blacklist_hit(
    verification_results: list[VerificationResult],
) -> Finding | None:
    """
    F. Detect an explicit blacklist or debarment hit from verification evidence.

    Does not treat ERROR or NOT_FOUND as a blacklist hit.
    """
    blacklist_results = _find_verifications_by_source(
        verification_results, "BLACKLIST_DEMO"
    )
    if not blacklist_results:
        return None

    for bl_vr in blacklist_results:
        if bl_vr.status != "VERIFIED":
            continue

        is_blacklisted = bl_vr.verified_facts.get("isBlacklisted")
        if is_blacklisted is True or str(is_blacklisted).lower() == "true":
            return Finding(
                finding_id=generate_deterministic_finding_id(
                    "BLACKLIST_DEBARMENT_HIT",
                    bl_vr.identifier or "",
                    bl_vr.source,
                ),
                type="BLACKLIST_DEBARMENT_HIT",
                severity=Severity.BLOCKER,
                message=(
                    f"Bidder is flagged as blacklisted/debarred by source "
                    f"'{bl_vr.source}'. Identifier: '{bl_vr.identifier}'. "
                    f"This requires immediate officer review."
                ),
                rule_id="BLACKLIST_DEBARMENT_HIT",
                tender_clause=None,
                source="BLACKLIST_DEMO",
                evidence={
                    "is_blacklisted": True,
                    "identifier": bl_vr.identifier,
                    "verified_facts": bl_vr.verified_facts,
                    "checked_at": bl_vr.checked_at,
                    "evidence_reference": bl_vr.evidence_reference,
                },
            )

    return None


def _detect_local_content_failure(
    tender: TenderContext,
    extracted_facts: list[ExtractedFact],
) -> Finding | None:
    """
    G. Compare declared/extracted local-content percentage against the
    tender-specific threshold.

    Does not hardcode a universal threshold.
    Does not silently skip malformed or unusable evidence.
    """
    if not tender.make_in_india_required:
        return None
    if tender.local_content_threshold is None:
        return None

    lc_facts = _find_extracted_facts(extracted_facts, "localContentPercentage")
    if not lc_facts:
        # Missing local content declaration when required
        return Finding(
            finding_id=generate_deterministic_finding_id(
                "LOCAL_CONTENT_THRESHOLD_FAILED",
                "missing_evidence",
                str(tender.local_content_threshold),
            ),
            type="LOCAL_CONTENT_THRESHOLD_FAILED",
            severity=Severity.HIGH,
            message=(
                f"This tender requires Make in India compliance with a minimum "
                f"local content of {tender.local_content_threshold}%, but no "
                f"local content declaration was found in the bid documents."
            ),
            rule_id="LOCAL_CONTENT_THRESHOLD_FAILED",
            tender_clause=None,
            source=None,
            evidence={
                "make_in_india_required": True,
                "local_content_threshold": tender.local_content_threshold,
                "declared_percentage": None,
            },
        )

    # Use the highest-confidence extracted value
    best_fact = max(
        [f for f in lc_facts if f.value is not None],
        key=lambda f: f.confidence,
        default=None,
    )

    # All facts have None values — evidence exists but no usable value
    if best_fact is None:
        return Finding(
            finding_id=generate_deterministic_finding_id(
                "LOCAL_CONTENT_THRESHOLD_FAILED",
                "null_evidence",
                str(tender.local_content_threshold),
            ),
            type="LOCAL_CONTENT_THRESHOLD_FAILED",
            severity=Severity.HIGH,
            message=(
                f"This tender requires Make in India compliance with a minimum "
                f"local content of {tender.local_content_threshold}%, but the "
                f"extracted local content evidence contains no usable value. "
                f"Officer review is required."
            ),
            rule_id="LOCAL_CONTENT_THRESHOLD_FAILED",
            tender_clause=None,
            source=None,
            evidence={
                "make_in_india_required": True,
                "local_content_threshold": tender.local_content_threshold,
                "declared_percentage": None,
                "evidence_present_but_unusable": True,
            },
        )

    # Attempt to parse the value as a number
    try:
        declared_pct = float(best_fact.value)
    except (ValueError, TypeError):
        # Malformed local-content value — produce explicit finding
        return Finding(
            finding_id=generate_deterministic_finding_id(
                "LOCAL_CONTENT_THRESHOLD_FAILED",
                "malformed_evidence",
                best_fact.value or "",
                best_fact.document_id or "",
            ),
            type="LOCAL_CONTENT_THRESHOLD_FAILED",
            severity=Severity.HIGH,
            message=(
                f"This tender requires Make in India compliance with a minimum "
                f"local content of {tender.local_content_threshold}%, but the "
                f"extracted value '{best_fact.value}' could not be parsed as "
                f"a percentage. Officer review is required."
            ),
            rule_id="LOCAL_CONTENT_THRESHOLD_FAILED",
            tender_clause=None,
            source=best_fact.document_type,
            evidence={
                "make_in_india_required": True,
                "local_content_threshold": tender.local_content_threshold,
                "raw_value": best_fact.value,
                "parse_error": True,
                "document_id": best_fact.document_id,
                "page": best_fact.page,
                "confidence": best_fact.confidence,
            },
        )

    if declared_pct < tender.local_content_threshold:
        return Finding(
            finding_id=generate_deterministic_finding_id(
                "LOCAL_CONTENT_THRESHOLD_FAILED",
                str(declared_pct),
                str(tender.local_content_threshold),
                best_fact.document_id or "",
            ),
            type="LOCAL_CONTENT_THRESHOLD_FAILED",
            severity=Severity.HIGH,
            message=(
                f"Declared local content ({declared_pct}%) is below the "
                f"tender threshold ({tender.local_content_threshold}%). "
                f"Make in India compliance is not met."
            ),
            rule_id="LOCAL_CONTENT_THRESHOLD_FAILED",
            tender_clause=None,
            source=best_fact.document_type,
            evidence={
                "declared_percentage": declared_pct,
                "local_content_threshold": tender.local_content_threshold,
                "document_id": best_fact.document_id,
                "page": best_fact.page,
                "confidence": best_fact.confidence,
            },
        )

    return None


def _detect_missing_mandatory_documents(
    tender: TenderContext,
    extracted_facts: list[ExtractedFact],
) -> list[Finding]:
    """
    H. Detect when no extracted evidence exists for a tender-mandatory
    document type.

    Does not claim the document was not submitted — only that no extracted
    evidence is available. The document may have been submitted but not
    yet processed, or extraction may have failed.
    """
    findings: list[Finding] = []

    if not tender.mandatory_documents:
        return findings

    # Build set of document types with extracted evidence
    present_doc_types: set[str] = set()
    for fact in extracted_facts:
        if fact.document_type:
            present_doc_types.add(fact.document_type)

    for required_doc in tender.mandatory_documents:
        if required_doc not in present_doc_types:
            findings.append(Finding(
                finding_id=generate_deterministic_finding_id(
                    "MANDATORY_DOCUMENT_MISSING",
                    required_doc,
                    tender.tender_id,
                ),
                type="MANDATORY_DOCUMENT_MISSING",
                severity=Severity.HIGH,
                message=(
                    f"No extracted evidence was found for mandatory document "
                    f"type '{required_doc}'. The document may not have been "
                    f"submitted, or it may not yet have been processed for "
                    f"extraction. Officer review is required."
                ),
                rule_id="MANDATORY_DOCUMENT_MISSING",
                tender_clause=None,
                source=None,
                evidence={
                    "required_document_type": required_doc,
                    "present_document_types": sorted(present_doc_types),
                    "checked_against": "extracted_facts",
                },
            ))

    return findings


def _detect_source_unavailable(
    verification_results: list[VerificationResult],
) -> list[Finding]:
    """
    I (part 1). Identify verification sources that returned ERROR status.

    Does not treat ERROR as a positive confirmation or a negative finding
    about the bidder. It is a finding about evidence quality.
    """
    findings: list[Finding] = []
    seen_sources: set[str] = set()

    for vr in verification_results:
        if vr.status == "ERROR" and vr.source not in seen_sources:
            seen_sources.add(vr.source)
            findings.append(Finding(
                finding_id=generate_deterministic_finding_id(
                    "SOURCE_UNAVAILABLE",
                    vr.source,
                    vr.identifier or "",
                ),
                type="SOURCE_UNAVAILABLE",
                severity=Severity.MEDIUM,
                message=(
                    f"Verification source '{vr.source}' returned an error "
                    f"for identifier '{vr.identifier}'. "
                    f"The compliance status for this source could not be "
                    f"established. Officer should review manually."
                ),
                rule_id="SOURCE_UNAVAILABLE",
                tender_clause=None,
                source=vr.source,
                evidence={
                    "source": vr.source,
                    "identifier": vr.identifier,
                    "status": vr.status,
                    "checked_at": vr.checked_at,
                    "evidence_reference": vr.evidence_reference,
                },
            ))

    return findings


def _detect_low_confidence_facts(
    extracted_facts: list[ExtractedFact],
) -> list[Finding]:
    """
    I (part 2). Identify material facts with confidence below the threshold.

    Only flags material identity fields, not every extracted fact.
    """
    findings: list[Finding] = []
    seen: set[str] = set()

    for fact in extracted_facts:
        if fact.field not in _MATERIAL_FIELDS:
            continue
        if fact.value is None:
            continue
        if fact.confidence >= _LOW_CONFIDENCE_THRESHOLD:
            continue

        key = f"{fact.field}:{fact.document_id}:{fact.page}"
        if key in seen:
            continue
        seen.add(key)

        findings.append(Finding(
            finding_id=generate_deterministic_finding_id(
                "LOW_CONFIDENCE_MATERIAL_FACT",
                fact.field,
                fact.document_id or "",
                str(fact.page),
                fact.value,
            ),
            type="LOW_CONFIDENCE_MATERIAL_FACT",
            severity=Severity.MEDIUM,
            message=(
                f"Material fact '{fact.field}' extracted with low confidence "
                f"({fact.confidence:.2f}) from document '{fact.document_id}' "
                f"(page {fact.page}). "
                f"The extracted value '{fact.value}' may not be reliable."
            ),
            rule_id="LOW_CONFIDENCE_MATERIAL_FACT",
            tender_clause=None,
            source=fact.document_type,
            evidence={
                "field": fact.field,
                "value": fact.value,
                "confidence": fact.confidence,
                "threshold": _LOW_CONFIDENCE_THRESHOLD,
                "document_id": fact.document_id,
                "page": fact.page,
                "document_type": fact.document_type,
            },
        ))

    return findings


def _detect_conflicting_source_evidence(
    match_results: list[MatchResult],
) -> list[Finding]:
    """
    I (part 3). Identify fields where multiple verification sources
    provide conflicting values.

    Examines verification_observations on match results.
    """
    findings: list[Finding] = []
    seen: set[str] = set()

    for mr in match_results:
        if not mr.verification_observations:
            continue

        # Check for conflicting values among VERIFIED observations
        verified_obs = [
            vo for vo in mr.verification_observations
            if vo.status == "VERIFIED" and vo.value is not None
        ]
        if len(verified_obs) < 2:
            continue

        unique_values = {vo.value.upper().strip() for vo in verified_obs}
        if len(unique_values) <= 1:
            continue

        key = f"CONFLICTING:{mr.field}:{mr.source}"
        if key in seen:
            continue
        seen.add(key)

        sorted_values = sorted(unique_values)
        findings.append(Finding(
            finding_id=generate_deterministic_finding_id(
                "CONFLICTING_SOURCE_EVIDENCE",
                mr.field,
                mr.source or "",
                *sorted_values,
            ),
            type="CONFLICTING_SOURCE_EVIDENCE",
            severity=Severity.MEDIUM,
            message=(
                f"Multiple verification responses for field '{mr.field}' "
                f"from source '{mr.source}' provide conflicting values: "
                f"{sorted_values}. Officer review is required."
            ),
            rule_id="CONFLICTING_SOURCE_EVIDENCE",
            tender_clause=None,
            source=mr.source,
            evidence={
                "field": mr.field,
                "conflicting_values": sorted_values,
                "observations": [
                    {
                        "source": vo.source,
                        "identifier": vo.identifier,
                        "status": vo.status,
                        "value": vo.value,
                        "checked_at": vo.checked_at,
                    }
                    for vo in verified_obs
                ],
            },
        ))

    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_conflicts(
    bidder: BidderProfile,
    extracted_facts: list[ExtractedFact],
    verification_results: list[VerificationResult],
    match_results: list[MatchResult],
    tender: TenderContext,
) -> list[Finding]:
    """
    Detect evidence-backed compliance conflicts and discrepancies.

    Consumes structured inputs from the Entity Matcher (Phase 2) and
    source data, producing a list of explainable findings for the
    Procurement Officer.

    This function is deterministic: identical inputs always produce
    identical outputs, including stable finding IDs.

    Does not calculate scores, generate recommendations, or make
    final procurement decisions.

    Args:
        bidder: The bidder's submitted profile.
        extracted_facts: Facts extracted from the bidder's documents.
        verification_results: Responses from source connectors.
        match_results: Entity matching results from Phase 2.
        tender: Tender metadata including closing date and requirements.

    Returns:
        List of Finding objects, each with full provenance and explanation.
    """
    findings: list[Finding] = []

    # A. GST legal-name mismatch
    gst_name_finding = _detect_gst_legal_name_mismatch(
        bidder, match_results, verification_results
    )
    if gst_name_finding:
        findings.append(gst_name_finding)

    # B. PAN mismatch
    pan_findings = _detect_pan_mismatch(
        bidder, extracted_facts, match_results, verification_results
    )
    findings.extend(pan_findings)

    # C. GST inactive or cancelled before tender closing
    gst_inactive_finding = _detect_gst_inactive(tender, verification_results)
    if gst_inactive_finding:
        findings.append(gst_inactive_finding)

    # D. Missing or unverified mandatory Udyam certificate
    udyam_finding = _detect_missing_udyam(
        tender, bidder, extracted_facts, verification_results, match_results
    )
    if udyam_finding:
        findings.append(udyam_finding)

    # E. Expired OEM authorisation (only when tender requires OEM)
    oem_finding = _detect_expired_oem(tender, extracted_facts)
    if oem_finding:
        findings.append(oem_finding)

    # F. Blacklist/debarment hit
    blacklist_finding = _detect_blacklist_hit(verification_results)
    if blacklist_finding:
        findings.append(blacklist_finding)

    # G. Local content threshold failure
    local_content_finding = _detect_local_content_failure(
        tender, extracted_facts
    )
    if local_content_finding:
        findings.append(local_content_finding)

    # H. Missing mandatory documents (based on extraction evidence)
    doc_findings = _detect_missing_mandatory_documents(tender, extracted_facts)
    findings.extend(doc_findings)

    # I. Source unavailable, low confidence, conflicting evidence
    source_findings = _detect_source_unavailable(verification_results)
    findings.extend(source_findings)

    low_conf_findings = _detect_low_confidence_facts(extracted_facts)
    findings.extend(low_conf_findings)

    conflict_findings = _detect_conflicting_source_evidence(match_results)
    findings.extend(conflict_findings)

    return findings
