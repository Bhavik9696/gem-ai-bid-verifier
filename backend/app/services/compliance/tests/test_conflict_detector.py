"""
Phase 3 Tests — Conflict Detector

Tests the conflict detection logic for all conflict categories:
    GST_LEGAL_NAME_MISMATCH, PAN_MISMATCH, GST_INACTIVE_AT_CLOSING,
    UDYAM_CERTIFICATE_MISSING, UDYAM_CERTIFICATE_UNVERIFIED,
    OEM_AUTH_EXPIRED, BLACKLIST_DEBARMENT_HIT,
    LOCAL_CONTENT_THRESHOLD_FAILED, MANDATORY_DOCUMENT_MISSING,
    SOURCE_UNAVAILABLE, LOW_CONFIDENCE_MATERIAL_FACT,
    CONFLICTING_SOURCE_EVIDENCE.

Uses reusable fixtures from tests/fixtures/conflict_detection.py.
Does not test rule evaluation, scoring, or recommendation.
"""

from __future__ import annotations

import pytest

from backend.app.services.compliance.schemas import (
    BidderProfile,
    ExtractedFact,
    ExtractedObservation,
    Finding,
    MatchResult,
    MatchType,
    Severity,
    TenderContext,
    VerificationObservation,
    VerificationResult,
)
from backend.app.services.compliance.conflict_detector import detect_conflicts

from backend.app.services.compliance.tests.fixtures.conflict_detection import (
    # Tender contexts
    TENDER_DEFAULT,
    TENDER_MSME_MANDATORY,
    TENDER_MAKE_IN_INDIA,
    TENDER_WITH_MANDATORY_DOCS,
    TENDER_OEM_REQUIRED,
    TENDER_MSME_OEM,
    # Aster (all clean)
    BIDDER_CD_ASTER,
    FACTS_CD_ASTER,
    VERIFICATIONS_CD_ASTER,
    MATCH_RESULTS_CD_ASTER,
    # Bharat (GST name mismatch)
    BIDDER_CD_BHARAT,
    FACTS_CD_BHARAT,
    VERIFICATIONS_CD_BHARAT,
    MATCH_RESULTS_CD_BHARAT,
    # Crest (missing Udyam + expired OEM)
    BIDDER_CD_CREST,
    FACTS_CD_CREST,
    VERIFICATIONS_CD_CREST,
    MATCH_RESULTS_CD_CREST,
    # Edge cases
    VERIFICATION_GST_INACTIVE,
    VERIFICATION_GST_CANCELLED_AFTER_CLOSING,
    VERIFICATION_GST_INACTIVE_NO_DATE,
    VERIFICATION_BLACKLIST_HIT,
    VERIFICATION_BLACKLIST_CLEAR,
    VERIFICATION_BLACKLIST_ERROR,
    FACT_LOCAL_CONTENT_LOW,
    FACT_LOCAL_CONTENT_HIGH,
    FACT_LOCAL_CONTENT_MALFORMED,
    MATCH_RESULT_PAN_MISMATCH,
    FACT_LOW_CONFIDENCE_PAN,
    VERIFICATION_SOURCE_ERROR,
    FACT_OEM_EXPIRY_VALID,
    FACT_OEM_EXPIRY_EXPIRED,
    FACT_OEM_EXPIRY_MALFORMED,
    BIDDER_CD_UDYAM_UNVERIFIED,
)


# ===================================================================
# Helper functions
# ===================================================================

def _find_finding(findings: list[Finding], finding_type: str) -> Finding | None:
    """Find the first finding with a specific type."""
    for f in findings:
        if f.type == finding_type:
            return f
    return None


def _find_all_findings(findings: list[Finding], finding_type: str) -> list[Finding]:
    """Find all findings with a specific type."""
    return [f for f in findings if f.type == finding_type]


# ===================================================================
# Demo Story: Aster Tech — No material conflicts
# ===================================================================


class TestAsterNoConflicts:
    """Aster Tech: all clean data, should produce no material conflict findings."""

    def test_no_identity_conflicts(self):
        """Aster should have no GST name mismatch, PAN mismatch, or blacklist hits."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        conflict_types = {f.type for f in findings}
        assert "GST_LEGAL_NAME_MISMATCH" not in conflict_types
        assert "PAN_MISMATCH" not in conflict_types
        assert "BLACKLIST_DEBARMENT_HIT" not in conflict_types
        assert "GST_INACTIVE_AT_CLOSING" not in conflict_types

    def test_no_missing_document_without_requirement(self):
        """Aster with default tender (no mandatory_documents list) should not flag missing docs."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        assert _find_finding(findings, "MANDATORY_DOCUMENT_MISSING") is None

    def test_no_udyam_finding_when_not_mandatory(self):
        """Aster with msme_mandatory=False should not flag missing Udyam."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        assert _find_finding(findings, "UDYAM_CERTIFICATE_MISSING") is None
        assert _find_finding(findings, "UDYAM_CERTIFICATE_UNVERIFIED") is None

    def test_matching_evidence_preserved_in_no_conflict(self):
        """Even with no conflicts, the function should return an empty findings list."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        # Should have no BLOCKER or HIGH findings
        blockers = [f for f in findings if f.severity == Severity.BLOCKER]
        highs = [f for f in findings if f.severity == Severity.HIGH]
        assert len(blockers) == 0
        assert len(highs) == 0


# ===================================================================
# Demo Story: Bharat Supplies — GST legal-name mismatch
# ===================================================================


class TestBharatGstNameMismatch:
    """Bharat Supplies: GST legal name differs from bidder name."""

    def test_gst_name_mismatch_detected(self):
        """GST_LEGAL_NAME_MISMATCH finding should be present."""
        findings = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "GST_LEGAL_NAME_MISMATCH")
        assert finding is not None

    def test_finding_has_rule_id_and_severity(self):
        """The finding must have rule_id, severity, and message."""
        findings = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "GST_LEGAL_NAME_MISMATCH")
        assert finding is not None
        assert finding.rule_id == "GST_LEGAL_NAME_MISMATCH"
        assert finding.severity == Severity.HIGH
        assert finding.source == "GST_DEMO"
        assert len(finding.message) > 0

    def test_finding_preserves_both_names(self):
        """The evidence should contain both submitted and verified names."""
        findings = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "GST_LEGAL_NAME_MISMATCH")
        assert finding is not None
        assert finding.evidence is not None
        assert finding.evidence["bidder_legal_name"] == "Bharat Supplies Pvt Ltd"
        assert finding.evidence["gst_verified_name"] == "Bharat Trading Corp"

    def test_finding_has_evidence_reference(self):
        """Evidence should include source provenance."""
        findings = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "GST_LEGAL_NAME_MISMATCH")
        assert finding is not None
        assert finding.evidence is not None
        assert finding.evidence.get("checked_at") is not None
        assert finding.evidence.get("evidence_reference") is not None

    def test_pan_match_does_not_suppress_gst_mismatch(self):
        """PAN matching should not suppress the GST legal-name discrepancy."""
        findings = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        gst_finding = _find_finding(findings, "GST_LEGAL_NAME_MISMATCH")
        pan_finding = _find_finding(findings, "PAN_MISMATCH")
        assert gst_finding is not None
        assert pan_finding is None  # PAN matches, so no PAN mismatch

    def test_no_duplicate_gst_name_findings(self):
        """Only one GST_LEGAL_NAME_MISMATCH finding per bidder."""
        findings = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        gst_findings = _find_all_findings(findings, "GST_LEGAL_NAME_MISMATCH")
        assert len(gst_findings) == 1


# ===================================================================
# Demo Story: Crest Systems — Missing Udyam + Expired OEM
# ===================================================================


class TestCrestMissingUdyam:
    """Crest Systems: missing mandatory Udyam certificate."""

    def test_udyam_missing_detected_when_mandatory(self):
        """UDYAM_CERTIFICATE_MISSING should be detected when msme_mandatory=True."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_MSME_MANDATORY,
        )
        finding = _find_finding(findings, "UDYAM_CERTIFICATE_MISSING")
        assert finding is not None
        assert finding.severity == Severity.HIGH
        assert finding.rule_id == "UDYAM_CERTIFICATE_MISSING"

    def test_udyam_not_flagged_when_not_mandatory(self):
        """UDYAM_CERTIFICATE_MISSING should NOT appear when msme_mandatory=False."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "UDYAM_CERTIFICATE_MISSING")
        assert finding is None

    def test_finding_evidence_shows_missing_state(self):
        """Evidence should show that bidder did not provide Udyam."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_MSME_MANDATORY,
        )
        finding = _find_finding(findings, "UDYAM_CERTIFICATE_MISSING")
        assert finding is not None
        assert finding.evidence is not None
        assert finding.evidence["msme_mandatory"] is True
        assert finding.evidence["bidder_udyam_number"] is None


class TestCrestExpiredOem:
    """Crest Systems: OEM authorisation expired before tender closing."""

    def test_oem_expired_detected(self):
        """OEM_AUTH_EXPIRED should be detected when oem_required and expiry < closing date."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_OEM_REQUIRED,
        )
        finding = _find_finding(findings, "OEM_AUTH_EXPIRED")
        assert finding is not None
        assert finding.severity == Severity.HIGH

    def test_oem_finding_preserves_dates(self):
        """Evidence should contain both expiry and closing dates."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_OEM_REQUIRED,
        )
        finding = _find_finding(findings, "OEM_AUTH_EXPIRED")
        assert finding is not None
        assert finding.evidence is not None
        assert finding.evidence["oem_expiry_date"] == "2026-09-01"
        assert finding.evidence["tender_closing_date"] == "2026-10-15"
        assert finding.evidence["document_id"] == "doc-crest-oem"

    def test_oem_not_expired_valid(self):
        """OEM with future expiry should NOT produce a finding."""
        valid_facts = FACTS_CD_CREST[:4] + [FACT_OEM_EXPIRY_VALID]
        findings = detect_conflicts(
            BIDDER_CD_CREST, valid_facts, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_OEM_REQUIRED,
        )
        finding = _find_finding(findings, "OEM_AUTH_EXPIRED")
        assert finding is None


# ===================================================================
# Category: GST Inactive at Closing
# ===================================================================


class TestGstInactiveAtClosing:
    """Test GST inactive/cancelled detection."""

    def test_gst_cancelled_with_date_before_closing_is_blocker(self):
        """CANCELLED GST with cancellation date before closing → BLOCKER."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER,
            [VERIFICATION_GST_INACTIVE],
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "GST_INACTIVE_AT_CLOSING")
        assert finding is not None
        assert finding.severity == Severity.BLOCKER
        assert finding.evidence is not None
        assert finding.evidence["gst_status"] == "CANCELLED"
        assert finding.evidence["status_confirmed_historical"] is True

    def test_gst_cancellation_after_closing_no_finding(self):
        """Cancellation after closing date should not produce a finding."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER,
            [VERIFICATION_GST_CANCELLED_AFTER_CLOSING],
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        # Status is ACTIVE and cancellation is after closing — no finding
        finding = _find_finding(findings, "GST_INACTIVE_AT_CLOSING")
        assert finding is None

    def test_gst_active_no_finding(self):
        """Active GST with no cancellation date should produce no finding."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "GST_INACTIVE_AT_CLOSING")
        assert finding is None

    def test_gst_inactive_no_cancellation_date_is_high(self):
        """Currently inactive GST without cancellation date → HIGH (not BLOCKER)."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER,
            [VERIFICATION_GST_INACTIVE_NO_DATE],
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "GST_INACTIVE_AT_CLOSING")
        assert finding is not None
        assert finding.severity == Severity.HIGH  # not BLOCKER
        assert finding.evidence is not None
        assert finding.evidence["gst_status"] == "SUSPENDED"
        assert finding.evidence["status_confirmed_historical"] is False

    def test_gst_inactive_no_date_message_notes_uncertainty(self):
        """Message should explain that timing cannot be established."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER,
            [VERIFICATION_GST_INACTIVE_NO_DATE],
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "GST_INACTIVE_AT_CLOSING")
        assert finding is not None
        msg_lower = finding.message.lower()
        assert "confirm" in msg_lower or "establish" in msg_lower

    def test_gst_confirmed_cancelled_preserves_evidence(self):
        """Confirmed cancelled finding preserves cancellation date and source."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER,
            [VERIFICATION_GST_INACTIVE],
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "GST_INACTIVE_AT_CLOSING")
        assert finding is not None
        assert finding.evidence["cancellation_date"] == "2026-08-01"
        assert finding.evidence["tender_closing_date"] == "2026-10-15"
        assert finding.evidence["identifier"] is not None
        assert finding.evidence["checked_at"] is not None


# ===================================================================
# Category: PAN Mismatch
# ===================================================================


class TestPanMismatch:
    """Test PAN mismatch detection."""

    def test_pan_mismatch_detected(self):
        """PAN mismatch in match results should produce a BLOCKER finding."""
        match_results = [MATCH_RESULT_PAN_MISMATCH]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER,
            VERIFICATIONS_CD_ASTER,
            match_results, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "PAN_MISMATCH")
        assert finding is not None
        assert finding.severity == Severity.BLOCKER
        assert finding.evidence is not None
        assert finding.evidence["bidder_pan"] == "ABCDE1234F"
        assert finding.evidence["source_verified_pan"] == "XXXXX9999Y"

    def test_pan_match_no_finding(self):
        """Matching PAN should produce no PAN_MISMATCH finding."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "PAN_MISMATCH")
        assert finding is None

    def test_pan_provenance_preserved_in_mismatch(self):
        """PAN mismatch finding should preserve verification observations."""
        match_results = [MATCH_RESULT_PAN_MISMATCH]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER,
            VERIFICATIONS_CD_ASTER,
            match_results, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "PAN_MISMATCH")
        assert finding is not None
        assert finding.evidence is not None
        assert "verification_observations" in finding.evidence
        assert len(finding.evidence["verification_observations"]) >= 1


# ===================================================================
# Category: Blacklist/Debarment
# ===================================================================


class TestBlacklistDebarment:
    """Test blacklist/debarment detection."""

    def test_blacklist_hit_detected(self):
        """Blacklisted bidder should produce a BLOCKER finding."""
        verifications = list(VERIFICATIONS_CD_ASTER) + [VERIFICATION_BLACKLIST_HIT]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, verifications,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "BLACKLIST_DEBARMENT_HIT")
        assert finding is not None
        assert finding.severity == Severity.BLOCKER
        assert finding.evidence is not None
        assert finding.evidence["is_blacklisted"] is True

    def test_blacklist_clear_no_finding(self):
        """Non-blacklisted bidder should produce no finding."""
        verifications = list(VERIFICATIONS_CD_ASTER) + [VERIFICATION_BLACKLIST_CLEAR]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, verifications,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "BLACKLIST_DEBARMENT_HIT")
        assert finding is None

    def test_blacklist_error_not_treated_as_hit(self):
        """ERROR from blacklist source should NOT produce a blacklist hit."""
        verifications = list(VERIFICATIONS_CD_ASTER) + [VERIFICATION_BLACKLIST_ERROR]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, verifications,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        # Should NOT be treated as blacklist hit
        assert _find_finding(findings, "BLACKLIST_DEBARMENT_HIT") is None
        # But should be flagged as SOURCE_UNAVAILABLE
        assert _find_finding(findings, "SOURCE_UNAVAILABLE") is not None


# ===================================================================
# Category: Local Content Threshold
# ===================================================================


class TestLocalContentThreshold:
    """Test Make in India local-content threshold detection."""

    def test_local_content_below_threshold(self):
        """Declared 35% < threshold 50% should produce a finding."""
        facts = list(FACTS_CD_ASTER) + [FACT_LOCAL_CONTENT_LOW]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, facts, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_MAKE_IN_INDIA,
        )
        finding = _find_finding(findings, "LOCAL_CONTENT_THRESHOLD_FAILED")
        assert finding is not None
        assert finding.severity == Severity.HIGH
        assert finding.evidence is not None
        assert finding.evidence["declared_percentage"] == 35.0
        assert finding.evidence["local_content_threshold"] == 50.0

    def test_local_content_above_threshold(self):
        """Declared 65% > threshold 50% should produce no finding."""
        facts = list(FACTS_CD_ASTER) + [FACT_LOCAL_CONTENT_HIGH]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, facts, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_MAKE_IN_INDIA,
        )
        finding = _find_finding(findings, "LOCAL_CONTENT_THRESHOLD_FAILED")
        assert finding is None

    def test_local_content_missing_when_required(self):
        """Missing local content declaration when required should produce a finding."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_MAKE_IN_INDIA,
        )
        finding = _find_finding(findings, "LOCAL_CONTENT_THRESHOLD_FAILED")
        assert finding is not None
        assert finding.evidence["declared_percentage"] is None

    def test_local_content_not_checked_when_not_required(self):
        """No local content check when make_in_india_required=False."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "LOCAL_CONTENT_THRESHOLD_FAILED")
        assert finding is None

    def test_local_content_malformed_produces_finding(self):
        """Malformed local content value should produce explicit finding, not silent skip."""
        facts = list(FACTS_CD_ASTER) + [FACT_LOCAL_CONTENT_MALFORMED]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, facts, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_MAKE_IN_INDIA,
        )
        finding = _find_finding(findings, "LOCAL_CONTENT_THRESHOLD_FAILED")
        assert finding is not None
        assert finding.severity == Severity.HIGH
        assert finding.evidence is not None
        assert finding.evidence["parse_error"] is True
        assert finding.evidence["raw_value"] == "not_a_number"

    def test_local_content_meeting_threshold_no_finding(self):
        """Local content exactly at threshold should produce no finding."""
        fact_exact = ExtractedFact(
            field="localContentPercentage", value="50.0", confidence=0.90,
            document_id="doc-lc-exact", page=1, document_type="MAKE_IN_INDIA_CERT",
        )
        facts = list(FACTS_CD_ASTER) + [fact_exact]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, facts, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_MAKE_IN_INDIA,
        )
        finding = _find_finding(findings, "LOCAL_CONTENT_THRESHOLD_FAILED")
        assert finding is None


# ===================================================================
# Category: Missing Mandatory Documents
# ===================================================================


class TestMissingMandatoryDocuments:
    """Test missing mandatory document detection."""

    def test_missing_udyam_certificate_document(self):
        """When UDYAM_CERTIFICATE is mandatory but absent, should flag it."""
        # Crest has no UDYAM_CERTIFICATE in extracted facts
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_WITH_MANDATORY_DOCS,
        )
        doc_findings = _find_all_findings(findings, "MANDATORY_DOCUMENT_MISSING")
        missing_types = {f.evidence["required_document_type"] for f in doc_findings}
        assert "UDYAM_CERTIFICATE" in missing_types

    def test_present_documents_not_flagged(self):
        """Documents that are present should NOT be flagged as missing."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_WITH_MANDATORY_DOCS,
        )
        doc_findings = _find_all_findings(findings, "MANDATORY_DOCUMENT_MISSING")
        missing_types = {f.evidence["required_document_type"] for f in doc_findings}
        assert "PAN_CARD" not in missing_types
        assert "GST_CERTIFICATE" not in missing_types

    def test_no_mandatory_docs_no_finding(self):
        """When no mandatory_documents in tender, no missing-doc findings."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_DEFAULT,
        )
        doc_findings = _find_all_findings(findings, "MANDATORY_DOCUMENT_MISSING")
        assert len(doc_findings) == 0

    def test_message_does_not_claim_no_submission(self):
        """Message should not claim document was not submitted — only no extraction evidence."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_WITH_MANDATORY_DOCS,
        )
        doc_findings = _find_all_findings(findings, "MANDATORY_DOCUMENT_MISSING")
        for f in doc_findings:
            assert "not found in the bid submission" not in f.message
            assert "extracted evidence" in f.message.lower() or "processed" in f.message.lower()

    def test_evidence_records_what_was_checked(self):
        """Evidence should record that we checked extracted_facts."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_WITH_MANDATORY_DOCS,
        )
        doc_findings = _find_all_findings(findings, "MANDATORY_DOCUMENT_MISSING")
        for f in doc_findings:
            assert f.evidence["checked_against"] == "extracted_facts"


# ===================================================================
# Category: Source Unavailable
# ===================================================================


class TestSourceUnavailable:
    """Test source unavailability detection."""

    def test_error_source_detected(self):
        """ERROR verification should produce SOURCE_UNAVAILABLE finding."""
        verifications = list(VERIFICATIONS_CD_ASTER) + [VERIFICATION_SOURCE_ERROR]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, verifications,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "SOURCE_UNAVAILABLE")
        assert finding is not None
        assert finding.severity == Severity.MEDIUM
        assert finding.evidence["source"] == "UDYAM_DEMO"

    def test_no_error_no_finding(self):
        """No ERROR verifications should produce no SOURCE_UNAVAILABLE finding."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "SOURCE_UNAVAILABLE")
        assert finding is None

    def test_no_duplicate_source_findings(self):
        """Same source ERROR appearing twice should produce only one finding."""
        error_dup = VerificationResult(
            source="UDYAM_DEMO", mode="DEMO", identifier="UDYAM-XX-00-0000001",
            status="ERROR", verified_facts={},
            checked_at="2026-09-25T12:01:00Z", evidence_reference="Udyam portal",
        )
        verifications = list(VERIFICATIONS_CD_ASTER) + [
            VERIFICATION_SOURCE_ERROR, error_dup
        ]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, verifications,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        source_findings = _find_all_findings(findings, "SOURCE_UNAVAILABLE")
        udyam_findings = [f for f in source_findings if f.evidence["source"] == "UDYAM_DEMO"]
        assert len(udyam_findings) == 1  # deduplicated by source


# ===================================================================
# Category: Low Confidence Material Fact
# ===================================================================


class TestLowConfidenceMaterialFact:
    """Test low-confidence material fact detection."""

    def test_low_confidence_pan_flagged(self):
        """PAN with confidence < 0.70 should produce a finding."""
        facts = list(FACTS_CD_ASTER) + [FACT_LOW_CONFIDENCE_PAN]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, facts, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "LOW_CONFIDENCE_MATERIAL_FACT")
        assert finding is not None
        assert finding.severity == Severity.MEDIUM
        assert finding.evidence["field"] == "pan"
        assert finding.evidence["confidence"] == 0.55

    def test_high_confidence_not_flagged(self):
        """Facts above threshold should not produce low-confidence findings."""
        # All Aster facts are high confidence
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "LOW_CONFIDENCE_MATERIAL_FACT")
        assert finding is None


# ===================================================================
# Determinism and Duplicate Prevention
# ===================================================================


class TestDeterminism:
    """Verify deterministic output and duplicate prevention."""

    def test_identical_inputs_same_output(self):
        """Same inputs should produce same number and types of findings."""
        findings_1 = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        findings_2 = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        assert len(findings_1) == len(findings_2)
        types_1 = [f.type for f in findings_1]
        types_2 = [f.type for f in findings_2]
        assert types_1 == types_2

    def test_no_duplicate_findings_for_same_issue(self):
        """Each finding type should not appear more times than justified."""
        findings = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        gst_findings = _find_all_findings(findings, "GST_LEGAL_NAME_MISMATCH")
        assert len(gst_findings) <= 1


# ===================================================================
# Finding Structure Validation
# ===================================================================


class TestFindingStructure:
    """Verify all findings have required fields populated."""

    def test_all_findings_have_required_fields(self):
        """Every finding must have finding_id, type, severity, message."""
        # Use Bharat + mandatory Udyam + expired OEM to generate multiple finding types
        all_facts = FACTS_CD_BHARAT + [FACT_LOW_CONFIDENCE_PAN, FACT_OEM_EXPIRY_EXPIRED]
        all_verifications = list(VERIFICATIONS_CD_BHARAT) + [VERIFICATION_SOURCE_ERROR]
        findings = detect_conflicts(
            BIDDER_CD_BHARAT, all_facts, all_verifications,
            MATCH_RESULTS_CD_BHARAT, TENDER_MSME_OEM,
        )
        assert len(findings) > 0
        for f in findings:
            assert f.finding_id is not None and len(f.finding_id) > 0
            assert f.type is not None and len(f.type) > 0
            assert f.severity is not None
            assert f.message is not None and len(f.message) > 0
            assert f.rule_id is not None

    def test_findings_have_stable_rule_ids(self):
        """Rule IDs should be from the defined set."""
        valid_rule_ids = {
            "GST_LEGAL_NAME_MISMATCH", "PAN_MISMATCH",
            "GST_INACTIVE_AT_CLOSING", "UDYAM_CERTIFICATE_MISSING",
            "UDYAM_CERTIFICATE_UNVERIFIED",
            "OEM_AUTH_EXPIRED", "BLACKLIST_DEBARMENT_HIT",
            "LOCAL_CONTENT_THRESHOLD_FAILED", "MANDATORY_DOCUMENT_MISSING",
            "SOURCE_UNAVAILABLE", "LOW_CONFIDENCE_MATERIAL_FACT",
            "CONFLICTING_SOURCE_EVIDENCE",
        }
        # Generate findings from all three demo stories
        for bidder, facts, verifications, matches in [
            (BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER, MATCH_RESULTS_CD_ASTER),
            (BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT, MATCH_RESULTS_CD_BHARAT),
            (BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST, MATCH_RESULTS_CD_CREST),
        ]:
            findings = detect_conflicts(
                bidder, facts, verifications, matches, TENDER_MSME_MANDATORY,
            )
            for f in findings:
                assert f.rule_id in valid_rule_ids, (
                    f"Unexpected rule_id '{f.rule_id}' in finding '{f.type}'"
                )


# ===================================================================
# Conflicting Source Evidence
# ===================================================================


class TestConflictingSourceEvidence:
    """Test detection of conflicting values from the same source."""

    def test_conflicting_verified_values_detected(self):
        """Two VERIFIED observations with different values should flag conflict."""
        mr_with_conflict = MatchResult(
            field="pan", bid_value="ABCDE1234F", source_value="ABCDE1234F",
            source="PAN_DEMO", match_type=MatchType.EXACT, is_confirmed=True,
            verification_observations=[
                VerificationObservation(
                    source="PAN_DEMO", identifier="ABCDE1234F", status="VERIFIED",
                    value="ABCDE1234F",
                    verified_facts={"pan": "ABCDE1234F"},
                    checked_at="2026-09-25T10:00:00Z",
                ),
                VerificationObservation(
                    source="PAN_DEMO", identifier="ABCDE1234F", status="VERIFIED",
                    value="XXXXX9999Y",  # conflicting
                    verified_facts={"pan": "XXXXX9999Y"},
                    checked_at="2026-09-25T10:01:00Z",
                ),
            ],
        )
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            [mr_with_conflict], TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "CONFLICTING_SOURCE_EVIDENCE")
        assert finding is not None
        assert finding.severity == Severity.MEDIUM
        assert finding.evidence is not None
        assert len(finding.evidence["conflicting_values"]) == 2

    def test_consistent_observations_no_conflict(self):
        """Matching observations should NOT produce a conflict finding."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        finding = _find_finding(findings, "CONFLICTING_SOURCE_EVIDENCE")
        assert finding is None


# ===================================================================
# Combined Scenarios
# ===================================================================


class TestCombinedScenarios:
    """Test that multiple conflict categories can coexist correctly."""

    def test_crest_msme_oem_required_both_findings(self):
        """Crest with msme+oem required should have both Udyam and OEM findings."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_MSME_OEM,
        )
        udyam = _find_finding(findings, "UDYAM_CERTIFICATE_MISSING")
        oem = _find_finding(findings, "OEM_AUTH_EXPIRED")
        assert udyam is not None
        assert oem is not None

    def test_bharat_with_blacklist_has_both(self):
        """Bharat with blacklist hit should have both GST mismatch and blacklist."""
        verifications = list(VERIFICATIONS_CD_BHARAT) + [VERIFICATION_BLACKLIST_HIT]
        findings = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, verifications,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        assert _find_finding(findings, "GST_LEGAL_NAME_MISMATCH") is not None
        assert _find_finding(findings, "BLACKLIST_DEBARMENT_HIT") is not None


# ===================================================================
# FIX 1 REGRESSION: GST Status and Tender Closing Date
# ===================================================================


class TestGstStatusCorrectness:
    """Regression tests for GST status / closing-date correctness."""

    def test_inactive_with_date_before_closing_confirmed_blocker(self):
        """Confirmed historical: cancellation date <= closing → BLOCKER."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER,
            [VERIFICATION_GST_INACTIVE],
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        f = _find_finding(findings, "GST_INACTIVE_AT_CLOSING")
        assert f is not None
        assert f.severity == Severity.BLOCKER
        assert f.evidence["status_confirmed_historical"] is True

    def test_inactive_no_date_uncertain_high(self):
        """Uncertain timing: no cancellation date → HIGH, not BLOCKER."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER,
            [VERIFICATION_GST_INACTIVE_NO_DATE],
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        f = _find_finding(findings, "GST_INACTIVE_AT_CLOSING")
        assert f is not None
        assert f.severity == Severity.HIGH
        assert f.evidence["status_confirmed_historical"] is False
        # Evidence must still include source provenance
        assert f.evidence["checked_at"] is not None
        assert f.evidence["identifier"] is not None

    def test_cancellation_after_closing_no_finding(self):
        """Cancellation after closing → no finding (was active at closing)."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER,
            [VERIFICATION_GST_CANCELLED_AFTER_CLOSING],
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        assert _find_finding(findings, "GST_INACTIVE_AT_CLOSING") is None

    def test_active_status_no_finding(self):
        """Active GST → no finding."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        assert _find_finding(findings, "GST_INACTIVE_AT_CLOSING") is None


# ===================================================================
# FIX 2 REGRESSION: OEM Authorization Requirement
# ===================================================================


class TestOemRequirement:
    """Regression tests for OEM requirement gating."""

    def test_oem_not_required_no_finding(self):
        """When oem_required=False, no OEM finding even with expired date in facts."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_DEFAULT,  # oem_required=False
        )
        assert _find_finding(findings, "OEM_AUTH_EXPIRED") is None

    def test_oem_required_expired(self):
        """When required and expiry < closing → OEM_AUTH_EXPIRED."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_OEM_REQUIRED,
        )
        f = _find_finding(findings, "OEM_AUTH_EXPIRED")
        assert f is not None
        assert f.severity == Severity.HIGH
        assert f.evidence["oem_expiry_date"] == "2026-09-01"

    def test_oem_required_valid(self):
        """When required and expiry > closing → no finding."""
        valid_facts = FACTS_CD_CREST[:4] + [FACT_OEM_EXPIRY_VALID]
        findings = detect_conflicts(
            BIDDER_CD_CREST, valid_facts, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_OEM_REQUIRED,
        )
        assert _find_finding(findings, "OEM_AUTH_EXPIRED") is None

    def test_oem_required_missing_evidence(self):
        """When required but no OEM facts at all → explicit finding."""
        # Remove all OEM facts (use only first 4 Crest facts)
        no_oem_facts = FACTS_CD_CREST[:4]
        findings = detect_conflicts(
            BIDDER_CD_CREST, no_oem_facts, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_OEM_REQUIRED,
        )
        f = _find_finding(findings, "OEM_AUTH_EXPIRED")
        assert f is not None
        assert f.evidence["expiry_evidence_found"] is False

    def test_oem_required_malformed_date(self):
        """When required but expiry date is unparseable → explicit finding."""
        malformed_facts = FACTS_CD_CREST[:4] + [FACT_OEM_EXPIRY_MALFORMED]
        findings = detect_conflicts(
            BIDDER_CD_CREST, malformed_facts, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_OEM_REQUIRED,
        )
        f = _find_finding(findings, "OEM_AUTH_EXPIRED")
        assert f is not None
        assert f.evidence["parse_error"] is True
        assert f.evidence["raw_expiry_value"] == "invalid-date-xyz"


# ===================================================================
# FIX 3 REGRESSION: Mandatory Document Evidence
# ===================================================================


class TestMandatoryDocumentCorrectness:
    """Regression: document evidence wording and provenance."""

    def test_finding_does_not_claim_no_submission(self):
        """Message must not claim the document was not submitted."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_WITH_MANDATORY_DOCS,
        )
        doc_findings = _find_all_findings(findings, "MANDATORY_DOCUMENT_MISSING")
        assert len(doc_findings) > 0
        for f in doc_findings:
            # Must NOT claim "not found in the bid submission"
            assert "not found in the bid submission" not in f.message

    def test_evidence_indicates_extraction_check(self):
        """Evidence should record that extracted_facts was the basis."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_WITH_MANDATORY_DOCS,
        )
        doc_findings = _find_all_findings(findings, "MANDATORY_DOCUMENT_MISSING")
        for f in doc_findings:
            assert f.evidence["checked_against"] == "extracted_facts"

    def test_extracted_document_not_flagged(self):
        """A document with extracted evidence should not be flagged as missing."""
        # PAN_CARD is present in Crest facts
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_WITH_MANDATORY_DOCS,
        )
        doc_findings = _find_all_findings(findings, "MANDATORY_DOCUMENT_MISSING")
        missing = {f.evidence["required_document_type"] for f in doc_findings}
        assert "PAN_CARD" not in missing

    def test_absent_document_flagged(self):
        """A document with no extracted evidence should be flagged."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_WITH_MANDATORY_DOCS,
        )
        doc_findings = _find_all_findings(findings, "MANDATORY_DOCUMENT_MISSING")
        missing = {f.evidence["required_document_type"] for f in doc_findings}
        assert "UDYAM_CERTIFICATE" in missing


# ===================================================================
# FIX 4 REGRESSION: Udyam Missing vs Unverified
# ===================================================================


class TestUdyamMissingVsUnverified:
    """Regression: distinguish missing from unverified Udyam."""

    def test_no_evidence_is_missing(self):
        """No bidder Udyam, no extracted, no verification → MISSING."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_MSME_MANDATORY,
        )
        assert _find_finding(findings, "UDYAM_CERTIFICATE_MISSING") is not None
        assert _find_finding(findings, "UDYAM_CERTIFICATE_UNVERIFIED") is None

    def test_bidder_declared_but_unverified(self):
        """Bidder has Udyam number but no verification → UNVERIFIED."""
        # BIDDER_CD_UDYAM_UNVERIFIED has udyam_number set
        # Use verifications WITHOUT UDYAM_DEMO to simulate unverified state
        verifications_no_udyam = [
            vr for vr in VERIFICATIONS_CD_ASTER if vr.source != "UDYAM_DEMO"
        ]
        findings = detect_conflicts(
            BIDDER_CD_UDYAM_UNVERIFIED, FACTS_CD_ASTER,
            verifications_no_udyam,
            MATCH_RESULTS_CD_ASTER, TENDER_MSME_MANDATORY,
        )
        assert _find_finding(findings, "UDYAM_CERTIFICATE_UNVERIFIED") is not None
        assert _find_finding(findings, "UDYAM_CERTIFICATE_MISSING") is None

    def test_verified_udyam_no_finding(self):
        """Verified Udyam → no Udyam finding at all."""
        # Aster has verified Udyam via UDYAM_DEMO
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_MSME_MANDATORY,
        )
        assert _find_finding(findings, "UDYAM_CERTIFICATE_MISSING") is None
        assert _find_finding(findings, "UDYAM_CERTIFICATE_UNVERIFIED") is None

    def test_not_mandatory_no_finding(self):
        """When msme_mandatory=False, no Udyam finding regardless of state."""
        findings = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_DEFAULT,
        )
        assert _find_finding(findings, "UDYAM_CERTIFICATE_MISSING") is None
        assert _find_finding(findings, "UDYAM_CERTIFICATE_UNVERIFIED") is None

    def test_unverified_finding_preserves_evidence(self):
        """UNVERIFIED finding should preserve bidder Udyam number in evidence."""
        verifications_no_udyam = [
            vr for vr in VERIFICATIONS_CD_ASTER if vr.source != "UDYAM_DEMO"
        ]
        findings = detect_conflicts(
            BIDDER_CD_UDYAM_UNVERIFIED, FACTS_CD_ASTER,
            verifications_no_udyam,
            MATCH_RESULTS_CD_ASTER, TENDER_MSME_MANDATORY,
        )
        f = _find_finding(findings, "UDYAM_CERTIFICATE_UNVERIFIED")
        assert f is not None
        assert f.evidence["bidder_udyam_number"] == "UDYAM-TN-01-0009999"
        assert f.evidence["has_verified_udyam"] is False


# ===================================================================
# FIX 5 REGRESSION: Local Content Evidence
# ===================================================================


class TestLocalContentCorrectness:
    """Regression: malformed and edge-case local content handling."""

    def test_malformed_value_explicit_finding(self):
        """Malformed local content must NOT be silently skipped."""
        facts = list(FACTS_CD_ASTER) + [FACT_LOCAL_CONTENT_MALFORMED]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, facts, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_MAKE_IN_INDIA,
        )
        f = _find_finding(findings, "LOCAL_CONTENT_THRESHOLD_FAILED")
        assert f is not None
        assert f.evidence["parse_error"] is True

    def test_missing_evidence_explicit_finding(self):
        """Missing local content evidence when required → explicit finding."""
        findings = detect_conflicts(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_MAKE_IN_INDIA,
        )
        f = _find_finding(findings, "LOCAL_CONTENT_THRESHOLD_FAILED")
        assert f is not None
        assert f.evidence["declared_percentage"] is None

    def test_valid_below_threshold(self):
        """Valid 35% < 50% threshold → finding with declared_percentage."""
        facts = list(FACTS_CD_ASTER) + [FACT_LOCAL_CONTENT_LOW]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, facts, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_MAKE_IN_INDIA,
        )
        f = _find_finding(findings, "LOCAL_CONTENT_THRESHOLD_FAILED")
        assert f is not None
        assert f.evidence["declared_percentage"] == 35.0

    def test_valid_above_threshold_no_finding(self):
        """Valid 65% > 50% threshold → no finding."""
        facts = list(FACTS_CD_ASTER) + [FACT_LOCAL_CONTENT_HIGH]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, facts, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_MAKE_IN_INDIA,
        )
        assert _find_finding(findings, "LOCAL_CONTENT_THRESHOLD_FAILED") is None

    def test_not_required_no_finding(self):
        """When make_in_india_required=False, no local content finding."""
        facts = list(FACTS_CD_ASTER) + [FACT_LOCAL_CONTENT_LOW]
        findings = detect_conflicts(
            BIDDER_CD_ASTER, facts, VERIFICATIONS_CD_ASTER,
            MATCH_RESULTS_CD_ASTER, TENDER_DEFAULT,
        )
        assert _find_finding(findings, "LOCAL_CONTENT_THRESHOLD_FAILED") is None


# ===================================================================
# FIX 6 REGRESSION: Deterministic Finding IDs
# ===================================================================


class TestDeterministicFindingIds:
    """Regression: finding IDs must be deterministic and unique."""

    def test_identical_inputs_produce_identical_ids(self):
        """Same inputs must produce the exact same finding IDs."""
        findings_1 = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        findings_2 = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        ids_1 = [f.finding_id for f in findings_1]
        ids_2 = [f.finding_id for f in findings_2]
        assert ids_1 == ids_2

    def test_distinct_findings_have_distinct_ids(self):
        """Different findings in the same assessment must have different IDs."""
        all_facts = FACTS_CD_BHARAT + [FACT_LOW_CONFIDENCE_PAN, FACT_OEM_EXPIRY_EXPIRED]
        all_verifications = list(VERIFICATIONS_CD_BHARAT) + [VERIFICATION_SOURCE_ERROR]
        findings = detect_conflicts(
            BIDDER_CD_BHARAT, all_facts, all_verifications,
            MATCH_RESULTS_CD_BHARAT, TENDER_MSME_OEM,
        )
        ids = [f.finding_id for f in findings]
        assert len(ids) == len(set(ids)), "Finding IDs must be unique"

    def test_finding_ids_start_with_fnd_prefix(self):
        """All finding IDs should have the FND- prefix."""
        findings = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        for f in findings:
            assert f.finding_id.startswith("FND-")

    def test_different_inputs_produce_different_ids(self):
        """Different evidence inputs must produce different finding IDs."""
        findings_bharat = detect_conflicts(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            MATCH_RESULTS_CD_BHARAT, TENDER_DEFAULT,
        )
        findings_crest = detect_conflicts(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            MATCH_RESULTS_CD_CREST, TENDER_MSME_OEM,
        )
        bharat_ids = {f.finding_id for f in findings_bharat}
        crest_ids = {f.finding_id for f in findings_crest}
        # Different bidders/evidence should produce different IDs
        assert len(bharat_ids & crest_ids) == 0
