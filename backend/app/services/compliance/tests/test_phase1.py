"""
Phase 1 Tests — Schemas, Utils, and Façade Validation

Verifies that:
  1. All Pydantic input/output models can be instantiated and validated.
  2. Normalisation utilities produce correct results.
  3. Date parsing handles ISO and Indian formats.
  4. Name similarity scores are sensible.
  5. The public façade returns a valid ComplianceAssessment stub.
"""

from __future__ import annotations

import pytest
from datetime import date

from backend.app.services.compliance.schemas import (
    ExtractedFact,
    VerificationResult,
    BidderProfile,
    TenderContext,
    BidComplianceInput,
    MatchResult,
    MatchType,
    Finding,
    Severity,
    RuleResult,
    RuleResultStatus,
    RulePriority,
    RuleCategory,
    ScoreBreakdown,
    ComplianceAssessment,
    RiskLevel,
    RECOMMENDATION_COMPLIANT,
    RECOMMENDATION_CLARIFICATION,
    RECOMMENDATION_HIGH_RISK,
    ALLOWED_RECOMMENDATIONS,
)
from backend.app.services.compliance.utils import (
    normalise_name,
    normalise_identifier,
    name_similarity,
    parse_date,
    generate_finding_id,
    generate_id,
)
from backend.app.services.compliance import evaluate_bid_compliance


# ===================================================================
# Schema validation tests
# ===================================================================


class TestExtractedFact:
    """Validate ExtractedFact model construction and constraints."""

    def test_valid_fact(self):
        fact = ExtractedFact(
            field="gstin",
            value="33ABCDE1234F1Z5",
            confidence=0.96,
            document_id="doc-001",
            page=1,
            document_type="GST_CERTIFICATE",
        )
        assert fact.field == "gstin"
        assert fact.value == "33ABCDE1234F1Z5"
        assert fact.confidence == 0.96
        assert fact.page == 1

    def test_fact_with_none_value(self):
        fact = ExtractedFact(
            field="udyamNumber",
            value=None,
            confidence=0.0,
            document_id="doc-003",
        )
        assert fact.value is None
        assert fact.page is None
        assert fact.document_type is None

    def test_confidence_bounds(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ExtractedFact(
                field="pan",
                value="ABCDE1234F",
                confidence=1.5,  # out of range
                document_id="doc-001",
            )
        with pytest.raises(ValidationError):
            ExtractedFact(
                field="pan",
                value="ABCDE1234F",
                confidence=-0.1,  # out of range
                document_id="doc-001",
            )


class TestVerificationResult:
    """Validate VerificationResult model."""

    def test_valid_result(self):
        result = VerificationResult(
            source="GST_DEMO",
            mode="DEMO",
            identifier="33ABCDE1234F1Z5",
            status="VERIFIED",
            verified_facts={
                "legalName": "Aster Tech Private Limited",
                "gstStatus": "ACTIVE",
            },
            checked_at="2026-09-25T10:06:00Z",
            evidence_reference="GST portal lookup",
        )
        assert result.source == "GST_DEMO"
        assert result.verified_facts["gstStatus"] == "ACTIVE"

    def test_default_mode(self):
        result = VerificationResult(
            source="PAN_DEMO",
            identifier="ABCDE1234F",
            status="VERIFIED",
            checked_at="2026-09-25T10:06:00Z",
        )
        assert result.mode == "DEMO"
        assert result.verified_facts == {}


class TestBidderProfile:
    """Validate BidderProfile model."""

    def test_full_profile(self):
        bidder = BidderProfile(
            bidder_id="BID-001",
            legal_name="Aster Tech Private Limited",
            pan="ABCDE1234F",
            gstin="33ABCDE1234F1Z5",
            udyam_number="UDYAM-TN-01-0001234",
            cin="U12345TN2022PTC000001",
            authorised_signatory="Arun Kumar",
        )
        assert bidder.bidder_id == "BID-001"
        assert bidder.pan == "ABCDE1234F"

    def test_minimal_profile(self):
        bidder = BidderProfile(
            bidder_id="BID-002",
            legal_name="Bharat Supplies Pvt Ltd",
        )
        assert bidder.pan is None
        assert bidder.cin is None


class TestTenderContext:
    """Validate TenderContext model."""

    def test_full_context(self):
        tender = TenderContext(
            tender_id="TENDER-2026-IT-001",
            title="Supply of IT Equipment",
            closing_date="2026-09-30",
            category="IT Hardware",
            rulebook_id="TENDER-2026-IT-001_v1",
            make_in_india_required=False,
            local_content_threshold=None,
            msme_mandatory=True,
        )
        assert tender.tender_id == "TENDER-2026-IT-001"
        assert tender.msme_mandatory is True

    def test_defaults(self):
        tender = TenderContext(
            tender_id="T-001",
            title="Test",
            closing_date="2026-09-30",
            rulebook_id="T-001_v1",
        )
        assert tender.make_in_india_required is False
        assert tender.msme_mandatory is False
        assert tender.local_content_threshold is None


class TestBidComplianceInput:
    """Validate the full input bundle."""

    def test_full_input(self):
        inp = BidComplianceInput(
            bid_id="bid-001",
            tender=TenderContext(
                tender_id="T-001",
                title="Test Tender",
                closing_date="2026-09-30",
                rulebook_id="T-001_v1",
            ),
            bidder=BidderProfile(
                bidder_id="BID-001",
                legal_name="Aster Tech Private Limited",
                pan="ABCDE1234F",
            ),
            extracted_facts=[
                ExtractedFact(
                    field="pan",
                    value="ABCDE1234F",
                    confidence=0.95,
                    document_id="doc-001",
                ),
            ],
            verification_results=[
                VerificationResult(
                    source="PAN_DEMO",
                    identifier="ABCDE1234F",
                    status="VERIFIED",
                    checked_at="2026-09-25T10:00:00Z",
                ),
            ],
        )
        assert inp.bid_id == "bid-001"
        assert len(inp.extracted_facts) == 1
        assert len(inp.verification_results) == 1

    def test_empty_facts_and_results(self):
        inp = BidComplianceInput(
            bid_id="bid-002",
            tender=TenderContext(
                tender_id="T-001",
                title="Test",
                closing_date="2026-09-30",
                rulebook_id="T-001_v1",
            ),
            bidder=BidderProfile(
                bidder_id="BID-002",
                legal_name="Test Corp",
            ),
        )
        assert inp.extracted_facts == []
        assert inp.verification_results == []


class TestOutputModels:
    """Validate output model construction."""

    def test_match_result(self):
        mr = MatchResult(
            field="pan",
            bid_value="ABCDE1234F",
            source_value="ABCDE1234F",
            source="PAN_DEMO",
            match_type=MatchType.EXACT,
            is_confirmed=True,
        )
        assert mr.is_confirmed is True
        assert mr.match_type == MatchType.EXACT

    def test_finding(self):
        f = Finding(
            finding_id="FND-ABC123",
            type="ENTITY_NAME_MISMATCH",
            severity=Severity.HIGH,
            message="GST legal name does not match bidder legal name.",
            rule_id="PAN_ENTITY_MATCH",
            tender_clause="Clause 4.1, Page 6",
            source="GST_DEMO",
            evidence={"extractedValue": "Bharat Trading Corp", "sourceValue": "Bharat Supplies Pvt Ltd"},
        )
        assert f.severity == Severity.HIGH
        assert f.rule_id == "PAN_ENTITY_MATCH"

    def test_rule_result(self):
        rr = RuleResult(
            rule_id="GST_ACTIVE_ON_CLOSING_DATE",
            rule_name="GST must be active",
            result=RuleResultStatus.PASS,
            priority=RulePriority.MANDATORY,
            category=RuleCategory.MANDATORY_ELIGIBILITY,
            tender_clause="Clause 4.2, Page 7",
            message="GST is active on bid closing date.",
        )
        assert rr.result == RuleResultStatus.PASS
        assert rr.severity is None  # only set on FAIL

    def test_score_breakdown(self):
        sb = ScoreBreakdown(
            category=RuleCategory.MANDATORY_ELIGIBILITY,
            weight=0.60,
            fulfilled=1.0,
            rules_passed=5,
            rules_total=5,
            details=["GST: PASS", "PAN: PASS"],
        )
        assert sb.weight == 0.60
        assert sb.rules_passed == sb.rules_total

    def test_compliance_assessment(self):
        ca = ComplianceAssessment(
            bid_id="bid-001",
            bidder_id="BID-001",
            tender_id="T-001",
            compliance_score=92.0,
            risk_score=10.0,
            risk_level=RiskLevel.LOW,
            recommendation=RECOMMENDATION_COMPLIANT,
            recommendation_summary="All mandatory checks passed.",
            match_results=[],
            findings=[],
            rule_results=[],
            score_breakdown=[],
            has_mandatory_failure=False,
            evaluated_at="2026-09-25T10:10:00Z",
        )
        assert ca.compliance_score == 92.0
        assert ca.recommendation in ALLOWED_RECOMMENDATIONS


class TestEnums:
    """Verify enum values match the product specification."""

    def test_rule_result_statuses(self):
        expected = {"PASS", "FAIL", "NEEDS_CLARIFICATION", "SOURCE_UNAVAILABLE", "NOT_APPLICABLE"}
        actual = {s.value for s in RuleResultStatus}
        assert actual == expected

    def test_severity_levels(self):
        expected = {"BLOCKER", "HIGH", "MEDIUM", "LOW", "INFO"}
        actual = {s.value for s in Severity}
        assert actual == expected

    def test_risk_levels(self):
        expected = {"LOW", "MODERATE", "HIGH", "CRITICAL"}
        actual = {r.value for r in RiskLevel}
        assert actual == expected

    def test_allowed_recommendations(self):
        assert len(ALLOWED_RECOMMENDATIONS) == 3
        assert RECOMMENDATION_COMPLIANT in ALLOWED_RECOMMENDATIONS
        assert RECOMMENDATION_CLARIFICATION in ALLOWED_RECOMMENDATIONS
        assert RECOMMENDATION_HIGH_RISK in ALLOWED_RECOMMENDATIONS


# ===================================================================
# Utils tests
# ===================================================================


class TestNormaliseName:
    """Test legal name normalisation."""

    def test_basic(self):
        assert normalise_name("Aster Tech Private Limited") == "aster tech"

    def test_pvt_ltd(self):
        assert normalise_name("Aster Tech Pvt. Ltd.") == "aster tech"

    def test_case_insensitive(self):
        assert normalise_name("ASTER TECH PVT LTD") == "aster tech"

    def test_punctuation(self):
        assert normalise_name("A.B.C. Corp.") == "a b c"

    def test_none(self):
        assert normalise_name(None) == ""

    def test_empty_string(self):
        assert normalise_name("") == ""

    def test_whitespace_collapse(self):
        assert normalise_name("  Aster   Tech   ") == "aster tech"

    def test_llp(self):
        assert normalise_name("Tech Solutions LLP") == "tech solutions"


class TestNormaliseIdentifier:
    """Test identifier normalisation."""

    def test_pan(self):
        assert normalise_identifier("ABCDE1234F") == "ABCDE1234F"

    def test_gstin_with_spaces(self):
        assert normalise_identifier("33 ABCDE 1234F 1Z5") == "33ABCDE1234F1Z5"

    def test_udyam_with_dashes(self):
        assert normalise_identifier("UDYAM-TN-01-0001234") == "UDYAMTN010001234"

    def test_lowercase_input(self):
        assert normalise_identifier("abcde1234f") == "ABCDE1234F"

    def test_none(self):
        assert normalise_identifier(None) == ""

    def test_empty(self):
        assert normalise_identifier("") == ""


class TestNameSimilarity:
    """Test name similarity scoring."""

    def test_identical_names(self):
        assert name_similarity("Aster Tech", "Aster Tech") == 1.0

    def test_normalised_identical(self):
        score = name_similarity("Aster Tech Pvt Ltd", "Aster Tech Private Limited")
        assert score == 1.0

    def test_completely_different(self):
        score = name_similarity("Aster Tech", "Bharat Supplies")
        assert score < 0.5

    def test_partial_match(self):
        score = name_similarity("Bharat Supplies Pvt Ltd", "Bharat Trading Corp")
        assert 0.0 < score < 0.85  # similar but not a confirmed match

    def test_none_input(self):
        assert name_similarity(None, "Aster Tech") == 0.0
        assert name_similarity("Aster Tech", None) == 0.0

    def test_both_none(self):
        assert name_similarity(None, None) == 0.0


class TestParseDate:
    """Test date parsing across multiple formats."""

    def test_iso_format(self):
        assert parse_date("2026-09-30") == date(2026, 9, 30)

    def test_indian_slash(self):
        assert parse_date("30/09/2026") == date(2026, 9, 30)

    def test_indian_dash(self):
        assert parse_date("30-09-2026") == date(2026, 9, 30)

    def test_month_abbrev(self):
        assert parse_date("30-Sep-2026") == date(2026, 9, 30)

    def test_month_abbrev_space(self):
        assert parse_date("30 Sep 2026") == date(2026, 9, 30)

    def test_iso_with_time(self):
        assert parse_date("2026-09-30T10:00:00") == date(2026, 9, 30)

    def test_iso_with_z(self):
        assert parse_date("2026-09-30T10:00:00Z") == date(2026, 9, 30)

    def test_none(self):
        assert parse_date(None) is None

    def test_empty(self):
        assert parse_date("") is None

    def test_whitespace(self):
        assert parse_date("  ") is None

    def test_invalid(self):
        assert parse_date("not-a-date") is None

    def test_whitespace_padding(self):
        assert parse_date("  2026-09-30  ") == date(2026, 9, 30)


class TestIdGeneration:
    """Test unique ID generation."""

    def test_finding_id_format(self):
        fid = generate_finding_id()
        assert fid.startswith("FND-")
        assert len(fid) == 16  # FND- + 12 hex chars

    def test_finding_id_uniqueness(self):
        ids = {generate_finding_id() for _ in range(100)}
        assert len(ids) == 100

    def test_custom_prefix(self):
        cid = generate_id("RULE")
        assert cid.startswith("RULE-")

    def test_id_uniqueness(self):
        ids = {generate_id("TEST") for _ in range(100)}
        assert len(ids) == 100


# ===================================================================
# Façade stub test
# ===================================================================


class TestEvaluateBidComplianceStub:
    """Verify the Phase 1 stub returns a valid ComplianceAssessment."""

    def _make_input(self) -> BidComplianceInput:
        return BidComplianceInput(
            bid_id="bid-001",
            tender=TenderContext(
                tender_id="TENDER-2026-IT-001",
                title="Supply of IT Equipment",
                closing_date="2026-09-30",
                rulebook_id="TENDER-2026-IT-001_v1",
                msme_mandatory=True,
            ),
            bidder=BidderProfile(
                bidder_id="BID-001",
                legal_name="Aster Tech Private Limited",
                pan="ABCDE1234F",
                gstin="33ABCDE1234F1Z5",
            ),
            extracted_facts=[
                ExtractedFact(
                    field="pan",
                    value="ABCDE1234F",
                    confidence=0.95,
                    document_id="doc-001",
                ),
            ],
            verification_results=[
                VerificationResult(
                    source="PAN_DEMO",
                    identifier="ABCDE1234F",
                    status="VERIFIED",
                    verified_facts={"name": "Aster Tech Private Limited"},
                    checked_at="2026-09-25T10:00:00Z",
                ),
            ],
        )

    def test_returns_valid_assessment(self):
        result = evaluate_bid_compliance(self._make_input())
        assert isinstance(result, ComplianceAssessment)

    def test_ids_propagated(self):
        result = evaluate_bid_compliance(self._make_input())
        assert result.bid_id == "bid-001"
        assert result.bidder_id == "BID-001"
        assert result.tender_id == "TENDER-2026-IT-001"

    def test_recommendation_is_allowed(self):
        result = evaluate_bid_compliance(self._make_input())
        assert result.recommendation in ALLOWED_RECOMMENDATIONS

    def test_evaluated_at_present(self):
        result = evaluate_bid_compliance(self._make_input())
        assert result.evaluated_at is not None
        assert len(result.evaluated_at) > 0

    def test_scores_are_valid_range(self):
        result = evaluate_bid_compliance(self._make_input())
        assert 0.0 <= result.compliance_score <= 100.0
        assert 0.0 <= result.risk_score <= 100.0
