"""
Phase 7 Tests — Integration + Three Demo Story Tests

End-to-end tests that exercise the full compliance pipeline:
    entity_matcher → conflict_detector → rule_engine → scoring → recommendation

Uses the three demo scenarios:
    Aster Tech   — Compliant / Low Risk
    Bharat       — GST Name Mismatch / High Risk
    Crest        — Missing Udyam + Expired OEM / Clarification or Review
"""

from __future__ import annotations

import pytest

from backend.app.services.compliance import evaluate_bid_compliance
from backend.app.services.compliance.schemas import (
    BidComplianceInput,
    ComplianceAssessment,
    RECOMMENDATION_CLARIFICATION,
    RECOMMENDATION_COMPLIANT,
    RECOMMENDATION_HIGH_RISK,
    ALLOWED_RECOMMENDATIONS,
    RiskLevel,
    RuleResultStatus,
    RulePriority,
    Severity,
)

from backend.app.services.compliance.tests.fixtures.conflict_detection import (
    TENDER_DEFAULT,
    TENDER_MSME_MANDATORY,
    TENDER_OEM_REQUIRED,
    TENDER_MSME_OEM,
    BIDDER_CD_ASTER,
    FACTS_CD_ASTER,
    VERIFICATIONS_CD_ASTER,
    BIDDER_CD_BHARAT,
    FACTS_CD_BHARAT,
    VERIFICATIONS_CD_BHARAT,
    BIDDER_CD_CREST,
    FACTS_CD_CREST,
    VERIFICATIONS_CD_CREST,
)


# ===================================================================
# Helpers
# ===================================================================

def _build_input(
    bidder,
    facts,
    verifications,
    tender,
    bid_id: str = "BID-TEST-001",
) -> BidComplianceInput:
    return BidComplianceInput(
        bid_id=bid_id,
        tender=tender,
        bidder=bidder,
        extracted_facts=facts,
        verification_results=verifications,
    )


def _find_rule(assessment: ComplianceAssessment, rule_id: str):
    for r in assessment.rule_results:
        if r.rule_id == rule_id:
            return r
    return None


def _find_finding(assessment: ComplianceAssessment, finding_type: str):
    for f in assessment.findings:
        if f.type == finding_type:
            return f
    return None


# ===================================================================
# Demo Story 1: Aster Tech — Compliant / Low Risk
# ===================================================================


class TestAsterIntegration:
    """
    Aster Tech: all facts match, all sources ACTIVE/VALID.

    Expected:
        - Score ~100, Risk LOW
        - "Compliant — Ready for Officer Confirmation"
        - No BLOCKER findings
        - has_mandatory_failure = False
    """

    @pytest.fixture()
    def assessment(self) -> ComplianceAssessment:
        inp = _build_input(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            TENDER_DEFAULT, bid_id="BID-ASTER-001",
        )
        return evaluate_bid_compliance(inp)

    def test_recommendation_compliant(self, assessment):
        assert assessment.recommendation == RECOMMENDATION_COMPLIANT

    def test_no_mandatory_failure(self, assessment):
        assert assessment.has_mandatory_failure is False

    def test_risk_level_low(self, assessment):
        assert assessment.risk_level in (RiskLevel.LOW, RiskLevel.MODERATE)

    def test_no_blocker_findings(self, assessment):
        blockers = [
            f for f in assessment.findings if f.severity == Severity.BLOCKER
        ]
        assert len(blockers) == 0

    def test_entity_matches_present(self, assessment):
        assert len(assessment.match_results) > 0

    def test_rule_results_present(self, assessment):
        assert len(assessment.rule_results) > 0

    def test_gst_active_passes(self, assessment):
        r = _find_rule(assessment, "GST_ACTIVE_ON_CLOSING_DATE")
        assert r is not None
        assert r.result == RuleResultStatus.PASS

    def test_pan_match_passes(self, assessment):
        r = _find_rule(assessment, "PAN_ENTITY_MATCH")
        assert r is not None
        assert r.result == RuleResultStatus.PASS

    def test_score_breakdown_present(self, assessment):
        assert len(assessment.score_breakdown) > 0

    def test_evaluated_at_present(self, assessment):
        assert assessment.evaluated_at is not None
        assert len(assessment.evaluated_at) > 0

    def test_output_is_valid_model(self, assessment):
        """ComplianceAssessment must be a valid Pydantic model."""
        assert isinstance(assessment, ComplianceAssessment)
        assert assessment.bid_id == "BID-ASTER-001"
        assert assessment.bidder_id == "BID-001"
        assert assessment.tender_id == "TENDER-2026-IT-001"


# ===================================================================
# Demo Story 2: Bharat — GST Legal-Name Mismatch / High Risk
# ===================================================================


class TestBharatIntegration:
    """
    Bharat Supplies: GST legal name 'Bharat Trading Corp' ≠
    bid entity name 'Bharat Supplies Pvt Ltd'.

    Expected:
        - GST_LEGAL_NAME_MISMATCH finding present
        - Finding has evidence, severity, source
        - Recommendation is High-Risk or Clarification
        - No unsupported identity confirmation
    """

    @pytest.fixture()
    def assessment(self) -> ComplianceAssessment:
        inp = _build_input(
            BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
            TENDER_DEFAULT, bid_id="BID-BHARAT-001",
        )
        return evaluate_bid_compliance(inp)

    def test_gst_name_mismatch_finding_present(self, assessment):
        f = _find_finding(assessment, "GST_LEGAL_NAME_MISMATCH")
        assert f is not None

    def test_finding_has_evidence(self, assessment):
        f = _find_finding(assessment, "GST_LEGAL_NAME_MISMATCH")
        assert f is not None
        assert f.evidence is not None
        assert f.evidence["bidder_legal_name"] == "Bharat Supplies Pvt Ltd"
        assert f.evidence["gst_verified_name"] == "Bharat Trading Corp"

    def test_finding_severity(self, assessment):
        f = _find_finding(assessment, "GST_LEGAL_NAME_MISMATCH")
        assert f is not None
        assert f.severity == Severity.HIGH

    def test_finding_source(self, assessment):
        f = _find_finding(assessment, "GST_LEGAL_NAME_MISMATCH")
        assert f is not None
        assert f.source == "GST_DEMO"

    def test_recommendation_not_compliant(self, assessment):
        """Mismatch must not produce a compliant recommendation."""
        assert assessment.recommendation != RECOMMENDATION_COMPLIANT

    def test_recommendation_is_valid(self, assessment):
        assert assessment.recommendation in ALLOWED_RECOMMENDATIONS

    def test_mismatch_cannot_be_hidden_by_score(self, assessment):
        """Even if compliance score is decent, the mismatch is visible."""
        f = _find_finding(assessment, "GST_LEGAL_NAME_MISMATCH")
        assert f is not None
        # The finding persists regardless of score
        assert f.message is not None and len(f.message) > 0

    def test_no_unsupported_identity_confirmation(self, assessment):
        """Fuzzy match must not set is_confirmed=True for legalName."""
        for mr in assessment.match_results:
            if mr.field == "legalName" and mr.match_type.value == "MISMATCH":
                assert mr.is_confirmed is False

    def test_has_mandatory_failure_or_elevated_risk(self, assessment):
        """Must have either mandatory failure or elevated risk."""
        assert (
            assessment.has_mandatory_failure
            or assessment.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
            or assessment.recommendation in (
                RECOMMENDATION_HIGH_RISK,
                RECOMMENDATION_CLARIFICATION,
            )
        )


# ===================================================================
# Demo Story 3: Crest — Missing Udyam + Expired OEM
# ===================================================================


class TestCrestIntegration:
    """
    Crest Systems: no Udyam (MSME mandatory), OEM expired (OEM required).

    Expected:
        - UDYAM_CERTIFICATE_MISSING finding present
        - OEM_AUTH_EXPIRED finding present
        - UDYAM_VALID rule = NEEDS_CLARIFICATION
        - OEM_AUTH_VALID rule = FAIL
        - Recommendation is Clarification or High-Risk
        - has_mandatory_failure reflects mandatory FAILs
    """

    @pytest.fixture()
    def assessment(self) -> ComplianceAssessment:
        inp = _build_input(
            BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
            TENDER_MSME_OEM, bid_id="BID-CREST-001",
        )
        return evaluate_bid_compliance(inp)

    def test_udyam_missing_finding(self, assessment):
        f = _find_finding(assessment, "UDYAM_CERTIFICATE_MISSING")
        assert f is not None
        assert f.severity == Severity.HIGH
        assert f.evidence is not None
        assert f.evidence["msme_mandatory"] is True

    def test_oem_expired_finding(self, assessment):
        f = _find_finding(assessment, "OEM_AUTH_EXPIRED")
        assert f is not None
        assert f.severity == Severity.HIGH

    def test_udyam_rule_needs_clarification(self, assessment):
        r = _find_rule(assessment, "UDYAM_VALID")
        assert r is not None
        assert r.result == RuleResultStatus.NEEDS_CLARIFICATION

    def test_oem_rule_fails(self, assessment):
        r = _find_rule(assessment, "OEM_AUTH_VALID")
        assert r is not None
        assert r.result == RuleResultStatus.FAIL

    def test_has_mandatory_failure(self, assessment):
        """OEM FAIL is mandatory → has_mandatory_failure must be True."""
        assert assessment.has_mandatory_failure is True

    def test_recommendation_not_compliant(self, assessment):
        assert assessment.recommendation != RECOMMENDATION_COMPLIANT

    def test_recommendation_is_valid(self, assessment):
        assert assessment.recommendation in ALLOWED_RECOMMENDATIONS

    def test_mandatory_failure_not_hidden_by_score(self, assessment):
        """Compliance score must not mask mandatory failure."""
        assert assessment.has_mandatory_failure is True
        assert assessment.recommendation != RECOMMENDATION_COMPLIANT

    def test_evidence_preserved(self, assessment):
        """Findings and rule results must have evidence/provenance."""
        for f in assessment.findings:
            assert f.finding_id is not None
            assert f.type is not None
            assert f.severity is not None
            assert f.message is not None

        for r in assessment.rule_results:
            assert r.rule_id is not None
            assert r.result is not None
            assert r.message is not None

    def test_output_model_structure(self, assessment):
        assert isinstance(assessment, ComplianceAssessment)
        assert assessment.bid_id == "BID-CREST-001"
        assert assessment.bidder_id == "BID-003"
        assert assessment.tender_id == "TENDER-2026-IT-001"
        assert assessment.compliance_score >= 0.0
        assert assessment.risk_score >= 0.0
        assert assessment.evaluated_at is not None


# ===================================================================
# Cross-cutting integration tests
# ===================================================================


class TestIntegrationCrossCutting:
    """Additional integration assertions across all scenarios."""

    def test_all_assessments_have_valid_recommendations(self):
        """Every assessment recommendation must be from the allowed set."""
        for bidder, facts, verifs, tender, bid_id in [
            (BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
             TENDER_DEFAULT, "BID-A"),
            (BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT,
             TENDER_DEFAULT, "BID-B"),
            (BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST,
             TENDER_MSME_OEM, "BID-C"),
        ]:
            inp = _build_input(bidder, facts, verifs, tender, bid_id)
            a = evaluate_bid_compliance(inp)
            assert a.recommendation in ALLOWED_RECOMMENDATIONS

    def test_deterministic_across_calls(self):
        """Same input must produce same output."""
        inp = _build_input(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            TENDER_DEFAULT, "BID-DET",
        )
        a1 = evaluate_bid_compliance(inp)
        a2 = evaluate_bid_compliance(inp)
        assert a1.compliance_score == a2.compliance_score
        assert a1.risk_score == a2.risk_score
        assert a1.risk_level == a2.risk_level
        assert a1.recommendation == a2.recommendation
        assert a1.has_mandatory_failure == a2.has_mandatory_failure
        assert len(a1.findings) == len(a2.findings)
        assert len(a1.rule_results) == len(a2.rule_results)

    def test_every_finding_has_required_fields(self):
        """Every finding across all stories must have ID, type, severity, message."""
        for bidder, facts, verifs, tender in [
            (BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER, TENDER_DEFAULT),
            (BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT, TENDER_DEFAULT),
            (BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST, TENDER_MSME_OEM),
        ]:
            inp = _build_input(bidder, facts, verifs, tender)
            a = evaluate_bid_compliance(inp)
            for f in a.findings:
                assert f.finding_id is not None
                assert f.type is not None
                assert f.severity is not None
                assert f.message is not None and len(f.message) > 0

    def test_every_rule_result_has_required_fields(self):
        """Every rule result must have ID, name, result, priority, message."""
        inp = _build_input(
            BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER,
            TENDER_DEFAULT,
        )
        a = evaluate_bid_compliance(inp)
        for r in a.rule_results:
            assert r.rule_id is not None
            assert r.rule_name is not None
            assert r.result is not None
            assert r.priority is not None
            assert r.message is not None and len(r.message) > 0

    def test_score_within_bounds(self):
        """Scores must be within 0–100."""
        for bidder, facts, verifs, tender in [
            (BIDDER_CD_ASTER, FACTS_CD_ASTER, VERIFICATIONS_CD_ASTER, TENDER_DEFAULT),
            (BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT, TENDER_DEFAULT),
            (BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST, TENDER_MSME_OEM),
        ]:
            inp = _build_input(bidder, facts, verifs, tender)
            a = evaluate_bid_compliance(inp)
            assert 0.0 <= a.compliance_score <= 100.0
            assert 0.0 <= a.risk_score <= 100.0

    def test_mandatory_failure_prevents_compliant(self):
        """No assessment with has_mandatory_failure=True can be Compliant."""
        for bidder, facts, verifs, tender in [
            (BIDDER_CD_BHARAT, FACTS_CD_BHARAT, VERIFICATIONS_CD_BHARAT, TENDER_DEFAULT),
            (BIDDER_CD_CREST, FACTS_CD_CREST, VERIFICATIONS_CD_CREST, TENDER_MSME_OEM),
        ]:
            inp = _build_input(bidder, facts, verifs, tender)
            a = evaluate_bid_compliance(inp)
            if a.has_mandatory_failure:
                assert a.recommendation != RECOMMENDATION_COMPLIANT
