"""
Phase 8 Tests — DB Adapter (build_compliance_input only)

Tests the conversion from mock DB model objects to Member 5 Pydantic inputs.
Does NOT test persist_compliance_assessment since that requires the actual
SQLAlchemy models and a DB session.
"""

from __future__ import annotations

import pytest
from types import SimpleNamespace

from backend.app.services.compliance.adapters import build_compliance_input
from backend.app.services.compliance.schemas import (
    BidComplianceInput,
    BidderProfile,
    ExtractedFact,
    TenderContext,
    VerificationResult,
)


# ===================================================================
# Mock DB rows using SimpleNamespace
# ===================================================================

def _mock_tender(**overrides):
    defaults = dict(
        tender_id="TENDER-GEM-2026-001",
        title="Supply of IT Equipment",
        bid_closing_date="2026-09-30",
        category="IT Equipment",
        rulebook_version="v1.0",
        eligibility_conditions={
            "msmeRequired": True,
            "makeInIndiaRequired": True,
            "localContentThreshold": 50,
            "oemRequired": True,
        },
        mandatory_documents=[
            "GST Registration Certificate",
            "PAN Card",
        ],
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _mock_bidder(**overrides):
    defaults = dict(
        bidder_id="BID-001",
        legal_name="Aster Tech Private Limited",
        pan="ABCDE1234F",
        gstin="33ABCDE1234F1Z5",
        udyam_number="UDYAM-TN-01-0001234",
        cin="U12345TN2022PTC000001",
        authorised_signatory="Aster Signatory",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _mock_bid(**overrides):
    defaults = dict(
        bid_id="GEM-BID-2026-001",
        tender_id="TENDER-GEM-2026-001",
        bidder_id="BID-001",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _mock_extracted_fact(**overrides):
    defaults = dict(
        field="pan",
        value="ABCDE1234F",
        confidence=0.98,
        document_id="DOC-001-01",
        page=1,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _mock_verification(**overrides):
    defaults = dict(
        source="GST_DEMO",
        mode="DEMO",
        identifier="33ABCDE1234F1Z5",
        status="VERIFIED",
        verified_facts={"legalName": "Aster Tech Private Limited", "gstStatus": "ACTIVE"},
        checked_at="2026-09-25T10:01:00Z",
        evidence_reference="demo-data/gst-records.json",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ===================================================================
# Tests
# ===================================================================


class TestBuildComplianceInput:

    def test_returns_bid_compliance_input(self):
        result = build_compliance_input(
            _mock_bid(), _mock_bidder(), _mock_tender(),
            [_mock_extracted_fact()], [_mock_verification()],
        )
        assert isinstance(result, BidComplianceInput)

    def test_bid_id_mapped(self):
        result = build_compliance_input(
            _mock_bid(bid_id="BID-TEST-42"), _mock_bidder(), _mock_tender(),
            [], [],
        )
        assert result.bid_id == "BID-TEST-42"

    def test_tender_context_fields(self):
        result = build_compliance_input(
            _mock_bid(), _mock_bidder(), _mock_tender(),
            [], [],
        )
        assert result.tender.tender_id == "TENDER-GEM-2026-001"
        assert result.tender.title == "Supply of IT Equipment"
        assert result.tender.closing_date == "2026-09-30"
        assert result.tender.category == "IT Equipment"
        assert result.tender.msme_mandatory is True
        assert result.tender.oem_required is True
        assert result.tender.make_in_india_required is True
        assert result.tender.local_content_threshold == 50.0

    def test_bidder_profile_fields(self):
        result = build_compliance_input(
            _mock_bid(), _mock_bidder(), _mock_tender(),
            [], [],
        )
        assert result.bidder.bidder_id == "BID-001"
        assert result.bidder.legal_name == "Aster Tech Private Limited"
        assert result.bidder.pan == "ABCDE1234F"
        assert result.bidder.gstin == "33ABCDE1234F1Z5"

    def test_extracted_facts_mapped(self):
        facts = [
            _mock_extracted_fact(field="pan", value="ABCDE1234F"),
            _mock_extracted_fact(field="gstin", value="33ABCDE1234F1Z5"),
        ]
        result = build_compliance_input(
            _mock_bid(), _mock_bidder(), _mock_tender(),
            facts, [],
        )
        assert len(result.extracted_facts) == 2
        assert result.extracted_facts[0].field == "pan"
        assert result.extracted_facts[1].field == "gstin"

    def test_verifications_mapped(self):
        verifs = [
            _mock_verification(source="GST_DEMO"),
            _mock_verification(source="PAN_DEMO", identifier="ABCDE1234F"),
        ]
        result = build_compliance_input(
            _mock_bid(), _mock_bidder(), _mock_tender(),
            [], verifs,
        )
        assert len(result.verification_results) == 2
        assert result.verification_results[0].source == "GST_DEMO"
        assert result.verification_results[1].source == "PAN_DEMO"

    def test_null_eligibility_conditions(self):
        """Handles tender with no eligibility conditions gracefully."""
        result = build_compliance_input(
            _mock_bid(), _mock_bidder(),
            _mock_tender(eligibility_conditions=None),
            [], [],
        )
        assert result.tender.msme_mandatory is False
        assert result.tender.oem_required is False

    def test_null_optional_bidder_fields(self):
        """Handles bidder with missing optional fields."""
        result = build_compliance_input(
            _mock_bid(),
            _mock_bidder(gstin=None, udyam_number=None, cin=None, authorised_signatory=None),
            _mock_tender(),
            [], [],
        )
        assert result.bidder.gstin is None
        assert result.bidder.udyam_number is None

    def test_empty_facts_and_verifications(self):
        result = build_compliance_input(
            _mock_bid(), _mock_bidder(), _mock_tender(),
            [], [],
        )
        assert result.extracted_facts == []
        assert result.verification_results == []
