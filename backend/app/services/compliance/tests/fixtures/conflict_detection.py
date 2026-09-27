"""
Test Fixtures — Conflict Detection

Reusable TenderContext, BidderProfile, ExtractedFact, VerificationResult,
and MatchResult instances for testing the Conflict Detector.

These fixtures are test-only data.
Do not import these into production compliance logic.
Do not hardcode Aster, Bharat, or Crest outcomes in production code.

Fixture naming convention:
    TENDER_*               → TenderContext instances
    BIDDER_CD_*            → BidderProfile instances (CD = conflict detection)
    FACTS_CD_*             → lists of ExtractedFact
    VERIFICATIONS_CD_*     → lists of VerificationResult
    MATCH_RESULTS_CD_*     → lists of MatchResult (from entity matcher)
"""

from __future__ import annotations

from backend.app.services.compliance.schemas import (
    BidderProfile,
    ExtractedFact,
    ExtractedObservation,
    MatchResult,
    MatchType,
    Severity,
    TenderContext,
    VerificationObservation,
    VerificationResult,
)


# ===================================================================
# Tender contexts
# ===================================================================

TENDER_DEFAULT = TenderContext(
    tender_id="TENDER-2026-IT-001",
    title="IT Equipment Procurement 2026",
    closing_date="2026-10-15",
    category="IT",
    rulebook_id="TENDER-2026-IT-001_v1",
    make_in_india_required=False,
    local_content_threshold=None,
    msme_mandatory=False,
)

TENDER_MSME_MANDATORY = TenderContext(
    tender_id="TENDER-2026-IT-001",
    title="IT Equipment Procurement 2026",
    closing_date="2026-10-15",
    category="IT",
    rulebook_id="TENDER-2026-IT-001_v1",
    make_in_india_required=False,
    local_content_threshold=None,
    msme_mandatory=True,
)

TENDER_MAKE_IN_INDIA = TenderContext(
    tender_id="TENDER-2026-IT-001",
    title="IT Equipment Procurement 2026",
    closing_date="2026-10-15",
    category="IT",
    rulebook_id="TENDER-2026-IT-001_v1",
    make_in_india_required=True,
    local_content_threshold=50.0,
    msme_mandatory=False,
)

TENDER_WITH_MANDATORY_DOCS = TenderContext(
    tender_id="TENDER-2026-IT-001",
    title="IT Equipment Procurement 2026",
    closing_date="2026-10-15",
    category="IT",
    rulebook_id="TENDER-2026-IT-001_v1",
    make_in_india_required=False,
    local_content_threshold=None,
    msme_mandatory=False,
    mandatory_documents=["GST_CERTIFICATE", "PAN_CARD", "UDYAM_CERTIFICATE"],
)


# ===================================================================
# Demo Story: Aster Tech — All clean, no conflicts
# ===================================================================

BIDDER_CD_ASTER = BidderProfile(
    bidder_id="BID-001",
    legal_name="Aster Tech Private Limited",
    pan="ABCDE1234F",
    gstin="33ABCDE1234F1Z5",
    udyam_number="UDYAM-TN-01-0001234",
    cin="U12345TN2022PTC000001",
)

FACTS_CD_ASTER = [
    ExtractedFact(
        field="pan", value="ABCDE1234F", confidence=0.97,
        document_id="doc-aster-pan", page=1, document_type="PAN_CARD",
    ),
    ExtractedFact(
        field="gstin", value="33ABCDE1234F1Z5", confidence=0.96,
        document_id="doc-aster-gst", page=1, document_type="GST_CERTIFICATE",
    ),
    ExtractedFact(
        field="legalName", value="Aster Tech Private Limited", confidence=0.95,
        document_id="doc-aster-gst", page=1, document_type="GST_CERTIFICATE",
    ),
    ExtractedFact(
        field="udyamNumber", value="UDYAM-TN-01-0001234", confidence=0.93,
        document_id="doc-aster-udyam", page=1, document_type="UDYAM_CERTIFICATE",
    ),
    ExtractedFact(
        field="cin", value="U12345TN2022PTC000001", confidence=0.94,
        document_id="doc-aster-mca", page=1, document_type="CIN_DOCUMENT",
    ),
]

VERIFICATIONS_CD_ASTER = [
    VerificationResult(
        source="PAN_DEMO", mode="DEMO", identifier="ABCDE1234F",
        status="VERIFIED",
        verified_facts={"pan": "ABCDE1234F", "name": "Aster Tech Private Limited", "status": "ACTIVE"},
        checked_at="2026-09-25T10:00:00Z", evidence_reference="PAN verification portal",
    ),
    VerificationResult(
        source="GST_DEMO", mode="DEMO", identifier="33ABCDE1234F1Z5",
        status="VERIFIED",
        verified_facts={
            "legalName": "Aster Tech Private Limited", "gstStatus": "ACTIVE",
            "registrationDate": "2022-04-10", "cancellationDate": None,
            "returnFilingStatus": "CURRENT", "lastReturnPeriod": "2026-08",
        },
        checked_at="2026-09-25T10:01:00Z", evidence_reference="GST portal lookup",
    ),
    VerificationResult(
        source="UDYAM_DEMO", mode="DEMO", identifier="UDYAM-TN-01-0001234",
        status="VERIFIED",
        verified_facts={
            "udyamNumber": "UDYAM-TN-01-0001234",
            "enterpriseName": "Aster Tech Private Limited",
            "status": "ACTIVE", "pan": "ABCDE1234F",
        },
        checked_at="2026-09-25T10:02:00Z", evidence_reference="Udyam registration portal",
    ),
    VerificationResult(
        source="MCA_DEMO", mode="DEMO", identifier="U12345TN2022PTC000001",
        status="VERIFIED",
        verified_facts={
            "cin": "U12345TN2022PTC000001",
            "companyName": "ASTER TECH PRIVATE LIMITED",
            "companyStatus": "ACTIVE",
        },
        checked_at="2026-09-25T10:03:00Z", evidence_reference="MCA company master",
    ),
]

# Pre-computed match results for Aster (all EXACT, all confirmed)
MATCH_RESULTS_CD_ASTER = [
    MatchResult(
        field="pan", bid_value="ABCDE1234F", source_value="ABCDE1234F",
        source="PAN_DEMO", match_type=MatchType.EXACT, is_confirmed=True,
        extracted_observations=[
            ExtractedObservation(
                value="ABCDE1234F", confidence=0.97,
                document_id="doc-aster-pan", page=1, document_type="PAN_CARD",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="PAN_DEMO", identifier="ABCDE1234F", status="VERIFIED",
                value="ABCDE1234F",
                verified_facts={"pan": "ABCDE1234F", "name": "Aster Tech Private Limited", "status": "ACTIVE"},
                checked_at="2026-09-25T10:00:00Z", evidence_reference="PAN verification portal",
            ),
        ],
    ),
    MatchResult(
        field="gstin", bid_value="33ABCDE1234F1Z5", source_value="33ABCDE1234F1Z5",
        source="GST_DEMO", match_type=MatchType.EXACT, is_confirmed=True,
        extracted_observations=[
            ExtractedObservation(
                value="33ABCDE1234F1Z5", confidence=0.96,
                document_id="doc-aster-gst", page=1, document_type="GST_CERTIFICATE",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="GST_DEMO", identifier="33ABCDE1234F1Z5", status="VERIFIED",
                value=None,
                verified_facts={
                    "legalName": "Aster Tech Private Limited", "gstStatus": "ACTIVE",
                },
                checked_at="2026-09-25T10:01:00Z", evidence_reference="GST portal lookup",
            ),
        ],
    ),
    MatchResult(
        field="udyamNumber", bid_value="UDYAM-TN-01-0001234",
        source_value="UDYAM-TN-01-0001234",
        source="UDYAM_DEMO", match_type=MatchType.EXACT, is_confirmed=True,
        extracted_observations=[
            ExtractedObservation(
                value="UDYAM-TN-01-0001234", confidence=0.93,
                document_id="doc-aster-udyam", page=1, document_type="UDYAM_CERTIFICATE",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="UDYAM_DEMO", identifier="UDYAM-TN-01-0001234", status="VERIFIED",
                value="UDYAM-TN-01-0001234",
                verified_facts={
                    "udyamNumber": "UDYAM-TN-01-0001234",
                    "enterpriseName": "Aster Tech Private Limited",
                    "status": "ACTIVE", "pan": "ABCDE1234F",
                },
                checked_at="2026-09-25T10:02:00Z", evidence_reference="Udyam registration portal",
            ),
        ],
    ),
    MatchResult(
        field="cin", bid_value="U12345TN2022PTC000001",
        source_value="U12345TN2022PTC000001",
        source="MCA_DEMO", match_type=MatchType.EXACT, is_confirmed=True,
        extracted_observations=[
            ExtractedObservation(
                value="U12345TN2022PTC000001", confidence=0.94,
                document_id="doc-aster-mca", page=1, document_type="CIN_DOCUMENT",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="MCA_DEMO", identifier="U12345TN2022PTC000001", status="VERIFIED",
                value="U12345TN2022PTC000001",
                verified_facts={
                    "cin": "U12345TN2022PTC000001",
                    "companyName": "ASTER TECH PRIVATE LIMITED",
                    "companyStatus": "ACTIVE",
                },
                checked_at="2026-09-25T10:03:00Z", evidence_reference="MCA company master",
            ),
        ],
    ),
    MatchResult(
        field="legalName", bid_value="Aster Tech Private Limited",
        source_value="Aster Tech Private Limited",
        source="GST_DEMO", match_type=MatchType.NORMALISED_MATCH, is_confirmed=True,
        extracted_observations=[
            ExtractedObservation(
                value="Aster Tech Private Limited", confidence=0.95,
                document_id="doc-aster-gst", page=1, document_type="GST_CERTIFICATE",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="GST_DEMO", identifier="33ABCDE1234F1Z5", status="VERIFIED",
                value=None,
                verified_facts={"legalName": "Aster Tech Private Limited", "gstStatus": "ACTIVE"},
                checked_at="2026-09-25T10:01:00Z", evidence_reference="GST portal lookup",
            ),
        ],
    ),
]


# ===================================================================
# Demo Story: Bharat Supplies — GST legal-name mismatch
# ===================================================================

BIDDER_CD_BHARAT = BidderProfile(
    bidder_id="BID-002",
    legal_name="Bharat Supplies Pvt Ltd",
    pan="FGHIJ5678K",
    gstin="29FGHIJ5678K1Z8",
    udyam_number=None,
    cin="U67890KA2020PTC000002",
)

FACTS_CD_BHARAT = [
    ExtractedFact(
        field="pan", value="FGHIJ5678K", confidence=0.95,
        document_id="doc-bharat-pan", page=1, document_type="PAN_CARD",
    ),
    ExtractedFact(
        field="gstin", value="29FGHIJ5678K1Z8", confidence=0.94,
        document_id="doc-bharat-gst", page=1, document_type="GST_CERTIFICATE",
    ),
    ExtractedFact(
        field="legalName", value="Bharat Supplies Pvt Ltd", confidence=0.93,
        document_id="doc-bharat-gst", page=1, document_type="GST_CERTIFICATE",
    ),
    ExtractedFact(
        field="cin", value="U67890KA2020PTC000002", confidence=0.92,
        document_id="doc-bharat-mca", page=1, document_type="CIN_DOCUMENT",
    ),
]

VERIFICATIONS_CD_BHARAT = [
    VerificationResult(
        source="PAN_DEMO", mode="DEMO", identifier="FGHIJ5678K",
        status="VERIFIED",
        verified_facts={
            "pan": "FGHIJ5678K", "name": "Bharat Supplies Private Limited",
            "status": "ACTIVE",
        },
        checked_at="2026-09-25T10:04:00Z", evidence_reference="PAN verification portal",
    ),
    VerificationResult(
        source="GST_DEMO", mode="DEMO", identifier="29FGHIJ5678K1Z8",
        status="VERIFIED",
        verified_facts={
            # Intentional name mismatch
            "legalName": "Bharat Trading Corp", "gstStatus": "ACTIVE",
            "registrationDate": "2020-06-15", "cancellationDate": None,
            "returnFilingStatus": "CURRENT",
        },
        checked_at="2026-09-25T10:05:00Z", evidence_reference="GST portal lookup",
    ),
    VerificationResult(
        source="MCA_DEMO", mode="DEMO", identifier="U67890KA2020PTC000002",
        status="VERIFIED",
        verified_facts={
            "cin": "U67890KA2020PTC000002",
            "companyName": "BHARAT SUPPLIES PRIVATE LIMITED",
            "companyStatus": "ACTIVE",
        },
        checked_at="2026-09-25T10:06:00Z", evidence_reference="MCA company master",
    ),
]

# Match results for Bharat: GST legalName is MISMATCH
MATCH_RESULTS_CD_BHARAT = [
    MatchResult(
        field="pan", bid_value="FGHIJ5678K", source_value="FGHIJ5678K",
        source="PAN_DEMO", match_type=MatchType.EXACT, is_confirmed=True,
        extracted_observations=[
            ExtractedObservation(
                value="FGHIJ5678K", confidence=0.95,
                document_id="doc-bharat-pan", page=1, document_type="PAN_CARD",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="PAN_DEMO", identifier="FGHIJ5678K", status="VERIFIED",
                value="FGHIJ5678K",
                verified_facts={"pan": "FGHIJ5678K", "name": "Bharat Supplies Private Limited", "status": "ACTIVE"},
                checked_at="2026-09-25T10:04:00Z", evidence_reference="PAN verification portal",
            ),
        ],
    ),
    MatchResult(
        field="gstin", bid_value="29FGHIJ5678K1Z8", source_value="29FGHIJ5678K1Z8",
        source="GST_DEMO", match_type=MatchType.EXACT, is_confirmed=True,
        extracted_observations=[
            ExtractedObservation(
                value="29FGHIJ5678K1Z8", confidence=0.94,
                document_id="doc-bharat-gst", page=1, document_type="GST_CERTIFICATE",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="GST_DEMO", identifier="29FGHIJ5678K1Z8", status="VERIFIED",
                value=None,
                verified_facts={"legalName": "Bharat Trading Corp", "gstStatus": "ACTIVE"},
                checked_at="2026-09-25T10:05:00Z", evidence_reference="GST portal lookup",
            ),
        ],
    ),
    MatchResult(
        field="cin", bid_value="U67890KA2020PTC000002",
        source_value="U67890KA2020PTC000002",
        source="MCA_DEMO", match_type=MatchType.EXACT, is_confirmed=True,
        extracted_observations=[
            ExtractedObservation(
                value="U67890KA2020PTC000002", confidence=0.92,
                document_id="doc-bharat-mca", page=1, document_type="CIN_DOCUMENT",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="MCA_DEMO", identifier="U67890KA2020PTC000002", status="VERIFIED",
                value="U67890KA2020PTC000002",
                verified_facts={"cin": "U67890KA2020PTC000002", "companyName": "BHARAT SUPPLIES PRIVATE LIMITED"},
                checked_at="2026-09-25T10:06:00Z", evidence_reference="MCA company master",
            ),
        ],
    ),
    # GST name mismatch — this is the key Bharat finding
    MatchResult(
        field="legalName", bid_value="Bharat Supplies Pvt Ltd",
        source_value="Bharat Trading Corp",
        source="GST_DEMO", match_type=MatchType.MISMATCH, is_confirmed=False,
        notes="Name mismatch (similarity=0.53).",
        extracted_observations=[
            ExtractedObservation(
                value="Bharat Supplies Pvt Ltd", confidence=0.93,
                document_id="doc-bharat-gst", page=1, document_type="GST_CERTIFICATE",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="GST_DEMO", identifier="29FGHIJ5678K1Z8", status="VERIFIED",
                value=None,
                verified_facts={"legalName": "Bharat Trading Corp", "gstStatus": "ACTIVE"},
                checked_at="2026-09-25T10:05:00Z", evidence_reference="GST portal lookup",
            ),
        ],
    ),
]


# ===================================================================
# Demo Story: Crest Systems — Missing Udyam + Expired OEM
# ===================================================================

BIDDER_CD_CREST = BidderProfile(
    bidder_id="BID-003",
    legal_name="Crest Systems Pvt Ltd",
    pan="KLMNO9012P",
    gstin="27KLMNO9012P1Z3",
    udyam_number=None,  # Missing Udyam
    cin="U54321MH2021PTC000003",
)

FACTS_CD_CREST = [
    ExtractedFact(
        field="pan", value="KLMNO9012P", confidence=0.96,
        document_id="doc-crest-pan", page=1, document_type="PAN_CARD",
    ),
    ExtractedFact(
        field="gstin", value="27KLMNO9012P1Z3", confidence=0.95,
        document_id="doc-crest-gst", page=1, document_type="GST_CERTIFICATE",
    ),
    ExtractedFact(
        field="legalName", value="Crest Systems Pvt Ltd", confidence=0.94,
        document_id="doc-crest-gst", page=1, document_type="GST_CERTIFICATE",
    ),
    ExtractedFact(
        field="cin", value="U54321MH2021PTC000003", confidence=0.93,
        document_id="doc-crest-mca", page=1, document_type="CIN_DOCUMENT",
    ),
    # OEM authorisation expiry — BEFORE tender closing date
    ExtractedFact(
        field="oem_expiry_date", value="2026-09-01", confidence=0.91,
        document_id="doc-crest-oem", page=2, document_type="OEM_AUTHORISATION",
    ),
]

VERIFICATIONS_CD_CREST = [
    VerificationResult(
        source="PAN_DEMO", mode="DEMO", identifier="KLMNO9012P",
        status="VERIFIED",
        verified_facts={"pan": "KLMNO9012P", "name": "Crest Systems Private Limited", "status": "ACTIVE"},
        checked_at="2026-09-25T10:07:00Z", evidence_reference="PAN verification portal",
    ),
    VerificationResult(
        source="GST_DEMO", mode="DEMO", identifier="27KLMNO9012P1Z3",
        status="VERIFIED",
        verified_facts={
            "legalName": "Crest Systems Private Limited", "gstStatus": "ACTIVE",
            "registrationDate": "2021-03-20", "cancellationDate": None,
            "returnFilingStatus": "CURRENT",
        },
        checked_at="2026-09-25T10:08:00Z", evidence_reference="GST portal lookup",
    ),
    VerificationResult(
        source="MCA_DEMO", mode="DEMO", identifier="U54321MH2021PTC000003",
        status="VERIFIED",
        verified_facts={
            "cin": "U54321MH2021PTC000003",
            "companyName": "CREST SYSTEMS PRIVATE LIMITED",
            "companyStatus": "ACTIVE",
        },
        checked_at="2026-09-25T10:09:00Z", evidence_reference="MCA company master",
    ),
    # No UDYAM_DEMO verification — missing
]

MATCH_RESULTS_CD_CREST = [
    MatchResult(
        field="pan", bid_value="KLMNO9012P", source_value="KLMNO9012P",
        source="PAN_DEMO", match_type=MatchType.EXACT, is_confirmed=True,
        extracted_observations=[
            ExtractedObservation(
                value="KLMNO9012P", confidence=0.96,
                document_id="doc-crest-pan", page=1, document_type="PAN_CARD",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="PAN_DEMO", identifier="KLMNO9012P", status="VERIFIED",
                value="KLMNO9012P",
                verified_facts={"pan": "KLMNO9012P", "name": "Crest Systems Private Limited", "status": "ACTIVE"},
                checked_at="2026-09-25T10:07:00Z", evidence_reference="PAN verification portal",
            ),
        ],
    ),
    MatchResult(
        field="gstin", bid_value="27KLMNO9012P1Z3", source_value="27KLMNO9012P1Z3",
        source="GST_DEMO", match_type=MatchType.EXACT, is_confirmed=True,
        extracted_observations=[
            ExtractedObservation(
                value="27KLMNO9012P1Z3", confidence=0.95,
                document_id="doc-crest-gst", page=1, document_type="GST_CERTIFICATE",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="GST_DEMO", identifier="27KLMNO9012P1Z3", status="VERIFIED",
                value=None,
                verified_facts={"legalName": "Crest Systems Private Limited", "gstStatus": "ACTIVE"},
                checked_at="2026-09-25T10:08:00Z", evidence_reference="GST portal lookup",
            ),
        ],
    ),
    MatchResult(
        field="udyamNumber", bid_value=None, source_value=None,
        source="UDYAM_DEMO", match_type=MatchType.NOT_AVAILABLE, is_confirmed=False,
        notes="Bidder did not provide this identifier.",
    ),
    MatchResult(
        field="cin", bid_value="U54321MH2021PTC000003",
        source_value="U54321MH2021PTC000003",
        source="MCA_DEMO", match_type=MatchType.EXACT, is_confirmed=True,
        extracted_observations=[
            ExtractedObservation(
                value="U54321MH2021PTC000003", confidence=0.93,
                document_id="doc-crest-mca", page=1, document_type="CIN_DOCUMENT",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="MCA_DEMO", identifier="U54321MH2021PTC000003", status="VERIFIED",
                value="U54321MH2021PTC000003",
                verified_facts={"cin": "U54321MH2021PTC000003", "companyName": "CREST SYSTEMS PRIVATE LIMITED"},
                checked_at="2026-09-25T10:09:00Z", evidence_reference="MCA company master",
            ),
        ],
    ),
    MatchResult(
        field="legalName", bid_value="Crest Systems Pvt Ltd",
        source_value="Crest Systems Private Limited",
        source="GST_DEMO", match_type=MatchType.NORMALISED_MATCH, is_confirmed=True,
        extracted_observations=[
            ExtractedObservation(
                value="Crest Systems Pvt Ltd", confidence=0.94,
                document_id="doc-crest-gst", page=1, document_type="GST_CERTIFICATE",
            ),
        ],
        verification_observations=[
            VerificationObservation(
                source="GST_DEMO", identifier="27KLMNO9012P1Z3", status="VERIFIED",
                value=None,
                verified_facts={"legalName": "Crest Systems Private Limited", "gstStatus": "ACTIVE"},
                checked_at="2026-09-25T10:08:00Z", evidence_reference="GST portal lookup",
            ),
        ],
    ),
]


# ===================================================================
# Edge-case fixtures for individual conflict categories
# ===================================================================

# GST INACTIVE — status cancelled before closing date
VERIFICATION_GST_INACTIVE = VerificationResult(
    source="GST_DEMO", mode="DEMO", identifier="29FGHIJ5678K1Z8",
    status="VERIFIED",
    verified_facts={
        "legalName": "Some Company", "gstStatus": "CANCELLED",
        "registrationDate": "2020-06-15", "cancellationDate": "2026-08-01",
    },
    checked_at="2026-09-25T12:00:00Z", evidence_reference="GST portal lookup",
)

VERIFICATION_GST_CANCELLED_AFTER_CLOSING = VerificationResult(
    source="GST_DEMO", mode="DEMO", identifier="29FGHIJ5678K1Z8",
    status="VERIFIED",
    verified_facts={
        "legalName": "Some Company", "gstStatus": "ACTIVE",
        "registrationDate": "2020-06-15", "cancellationDate": "2026-12-01",
    },
    checked_at="2026-09-25T12:00:00Z", evidence_reference="GST portal lookup",
)

# BLACKLIST HIT
VERIFICATION_BLACKLIST_HIT = VerificationResult(
    source="BLACKLIST_DEMO", mode="DEMO", identifier="ABCDE1234F",
    status="VERIFIED",
    verified_facts={"isBlacklisted": True, "reason": "Debarred by CVC"},
    checked_at="2026-09-25T12:00:00Z", evidence_reference="Blacklist registry",
)

VERIFICATION_BLACKLIST_CLEAR = VerificationResult(
    source="BLACKLIST_DEMO", mode="DEMO", identifier="ABCDE1234F",
    status="VERIFIED",
    verified_facts={"isBlacklisted": False},
    checked_at="2026-09-25T12:00:00Z", evidence_reference="Blacklist registry",
)

VERIFICATION_BLACKLIST_ERROR = VerificationResult(
    source="BLACKLIST_DEMO", mode="DEMO", identifier="ABCDE1234F",
    status="ERROR",
    verified_facts={},
    checked_at="2026-09-25T12:00:00Z", evidence_reference="Blacklist registry",
)

# LOCAL CONTENT — below threshold
FACT_LOCAL_CONTENT_LOW = ExtractedFact(
    field="localContentPercentage", value="35.0", confidence=0.90,
    document_id="doc-local-content", page=3, document_type="MAKE_IN_INDIA_CERT",
)

FACT_LOCAL_CONTENT_HIGH = ExtractedFact(
    field="localContentPercentage", value="65.0", confidence=0.92,
    document_id="doc-local-content", page=3, document_type="MAKE_IN_INDIA_CERT",
)

# PAN MISMATCH — verification returns different PAN
MATCH_RESULT_PAN_MISMATCH = MatchResult(
    field="pan", bid_value="ABCDE1234F", source_value="XXXXX9999Y",
    source="PAN_DEMO", match_type=MatchType.MISMATCH, is_confirmed=False,
    notes="Identifier mismatch: bid='ABCDE1234F' vs source='XXXXX9999Y'.",
    extracted_observations=[
        ExtractedObservation(
            value="ABCDE1234F", confidence=0.97,
            document_id="doc-pan", page=1, document_type="PAN_CARD",
        ),
    ],
    verification_observations=[
        VerificationObservation(
            source="PAN_DEMO", identifier="ABCDE1234F", status="VERIFIED",
            value="XXXXX9999Y",
            verified_facts={"pan": "XXXXX9999Y", "name": "Some Other Company"},
            checked_at="2026-09-25T10:12:00Z", evidence_reference="PAN verification portal",
        ),
    ],
)

# LOW CONFIDENCE fact
FACT_LOW_CONFIDENCE_PAN = ExtractedFact(
    field="pan", value="ABCDE1234F", confidence=0.55,
    document_id="doc-low-conf", page=1, document_type="PAN_CARD",
)

# SOURCE ERROR
VERIFICATION_SOURCE_ERROR = VerificationResult(
    source="UDYAM_DEMO", mode="DEMO", identifier="UDYAM-XX-00-0000000",
    status="ERROR",
    verified_facts={},
    checked_at="2026-09-25T12:00:00Z", evidence_reference="Udyam portal",
)

# OEM authorisation — not expired (valid date is after closing)
FACT_OEM_EXPIRY_VALID = ExtractedFact(
    field="oem_expiry_date", value="2027-03-15", confidence=0.92,
    document_id="doc-oem-valid", page=1, document_type="OEM_AUTHORISATION",
)

FACT_OEM_EXPIRY_EXPIRED = ExtractedFact(
    field="oem_expiry_date", value="2026-09-01", confidence=0.91,
    document_id="doc-oem-expired", page=2, document_type="OEM_AUTHORISATION",
)


# ===================================================================
# Phase 3 Correctness Review — Additional Fixtures
# ===================================================================

# --- Tender contexts with OEM required ---

TENDER_OEM_REQUIRED = TenderContext(
    tender_id="TENDER-2026-IT-001",
    title="IT Equipment Procurement 2026",
    closing_date="2026-10-15",
    category="IT",
    rulebook_id="TENDER-2026-IT-001_v1",
    oem_required=True,
)

TENDER_MSME_OEM = TenderContext(
    tender_id="TENDER-2026-IT-001",
    title="IT Equipment Procurement 2026",
    closing_date="2026-10-15",
    category="IT",
    rulebook_id="TENDER-2026-IT-001_v1",
    msme_mandatory=True,
    oem_required=True,
)


# --- GST: currently inactive but no cancellation date ---

VERIFICATION_GST_INACTIVE_NO_DATE = VerificationResult(
    source="GST_DEMO", mode="DEMO", identifier="29FGHIJ5678K1Z8",
    status="VERIFIED",
    verified_facts={
        "legalName": "Some Company", "gstStatus": "SUSPENDED",
        "registrationDate": "2020-06-15",
        # No cancellationDate field — timing cannot be established
    },
    checked_at="2026-09-25T12:00:00Z", evidence_reference="GST portal lookup",
)


# --- Local content: malformed value ---

FACT_LOCAL_CONTENT_MALFORMED = ExtractedFact(
    field="localContentPercentage", value="not_a_number", confidence=0.85,
    document_id="doc-local-malformed", page=1, document_type="MAKE_IN_INDIA_CERT",
)


# --- OEM: malformed expiry date ---

FACT_OEM_EXPIRY_MALFORMED = ExtractedFact(
    field="oem_expiry_date", value="invalid-date-xyz", confidence=0.88,
    document_id="doc-oem-malformed", page=1, document_type="OEM_AUTHORISATION",
)


# --- Udyam: bidder has Udyam number but no verification (unverified state) ---

BIDDER_CD_UDYAM_UNVERIFIED = BidderProfile(
    bidder_id="BID-UDYAM-UNVERIFIED",
    legal_name="Unverified Udyam Corp",
    pan="ABCDE1234F",
    gstin="33ABCDE1234F1Z5",
    udyam_number="UDYAM-TN-01-0009999",
)

