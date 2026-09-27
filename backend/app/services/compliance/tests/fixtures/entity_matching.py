"""
Test Fixtures — Entity Matching

Reusable BidderProfile, ExtractedFact, and VerificationResult instances
for testing the entity matcher. These fixtures are test-only data.

Do not import these into production compliance logic.
Do not hardcode bidder outcomes here — the matcher derives results
from the data it receives.

Fixture naming convention:
    BIDDER_*       → BidderProfile instances
    FACTS_*        → lists of ExtractedFact
    VERIFICATIONS_* → lists of VerificationResult
"""

from __future__ import annotations

from backend.app.services.compliance.schemas import (
    BidderProfile,
    ExtractedFact,
    VerificationResult,
)


# ===================================================================
# Bidder profiles
# ===================================================================

BIDDER_ASTER = BidderProfile(
    bidder_id="BID-001",
    legal_name="Aster Tech Private Limited",
    pan="ABCDE1234F",
    gstin="33ABCDE1234F1Z5",
    udyam_number="UDYAM-TN-01-0001234",
    cin="U12345TN2022PTC000001",
    authorised_signatory="Arun Kumar",
)

BIDDER_BHARAT = BidderProfile(
    bidder_id="BID-002",
    legal_name="Bharat Supplies Pvt Ltd",
    pan="FGHIJ5678K",
    gstin="29FGHIJ5678K1Z8",
    udyam_number=None,
    cin="U67890KA2020PTC000002",
    authorised_signatory="Suresh Patel",
)

BIDDER_CREST = BidderProfile(
    bidder_id="BID-003",
    legal_name="Crest Systems Pvt Ltd",
    pan="KLMNO9012P",
    gstin="27KLMNO9012P1Z3",
    udyam_number=None,  # Missing Udyam — demo scenario
    cin="U54321MH2021PTC000003",
    authorised_signatory="Priya Sharma",
)

BIDDER_MINIMAL = BidderProfile(
    bidder_id="BID-MINIMAL",
    legal_name="Minimal Corp",
    # All optional identifiers missing
)

BIDDER_NONE_IDENTIFIERS = BidderProfile(
    bidder_id="BID-NONE",
    legal_name="No Identifiers Corp",
    pan=None,
    gstin=None,
    udyam_number=None,
    cin=None,
)


# ===================================================================
# Extracted facts — Aster Tech (all fields present, high confidence)
# ===================================================================

FACTS_ASTER = [
    ExtractedFact(
        field="pan",
        value="ABCDE1234F",
        confidence=0.97,
        document_id="doc-aster-pan",
        page=1,
        document_type="PAN_CARD",
    ),
    ExtractedFact(
        field="gstin",
        value="33ABCDE1234F1Z5",
        confidence=0.96,
        document_id="doc-aster-gst",
        page=1,
        document_type="GST_CERTIFICATE",
    ),
    ExtractedFact(
        field="legalName",
        value="Aster Tech Private Limited",
        confidence=0.95,
        document_id="doc-aster-gst",
        page=1,
        document_type="GST_CERTIFICATE",
    ),
    ExtractedFact(
        field="udyamNumber",
        value="UDYAM-TN-01-0001234",
        confidence=0.93,
        document_id="doc-aster-udyam",
        page=1,
        document_type="UDYAM_CERTIFICATE",
    ),
    ExtractedFact(
        field="cin",
        value="U12345TN2022PTC000001",
        confidence=0.94,
        document_id="doc-aster-mca",
        page=1,
        document_type="CIN_DOCUMENT",
    ),
]


# ===================================================================
# Extracted facts — Bharat Supplies (GST name mismatch scenario)
# ===================================================================

FACTS_BHARAT = [
    ExtractedFact(
        field="pan",
        value="FGHIJ5678K",
        confidence=0.95,
        document_id="doc-bharat-pan",
        page=1,
        document_type="PAN_CARD",
    ),
    ExtractedFact(
        field="gstin",
        value="29FGHIJ5678K1Z8",
        confidence=0.94,
        document_id="doc-bharat-gst",
        page=1,
        document_type="GST_CERTIFICATE",
    ),
    ExtractedFact(
        field="legalName",
        value="Bharat Supplies Pvt Ltd",
        confidence=0.93,
        document_id="doc-bharat-gst",
        page=1,
        document_type="GST_CERTIFICATE",
    ),
    ExtractedFact(
        field="cin",
        value="U67890KA2020PTC000002",
        confidence=0.92,
        document_id="doc-bharat-mca",
        page=1,
        document_type="CIN_DOCUMENT",
    ),
]


# ===================================================================
# Extracted facts — Crest Systems (missing Udyam)
# ===================================================================

FACTS_CREST = [
    ExtractedFact(
        field="pan",
        value="KLMNO9012P",
        confidence=0.96,
        document_id="doc-crest-pan",
        page=1,
        document_type="PAN_CARD",
    ),
    ExtractedFact(
        field="gstin",
        value="27KLMNO9012P1Z3",
        confidence=0.95,
        document_id="doc-crest-gst",
        page=1,
        document_type="GST_CERTIFICATE",
    ),
    ExtractedFact(
        field="legalName",
        value="Crest Systems Pvt Ltd",
        confidence=0.94,
        document_id="doc-crest-gst",
        page=1,
        document_type="GST_CERTIFICATE",
    ),
    # Note: No udyamNumber fact — this is the "missing Udyam" scenario
    ExtractedFact(
        field="cin",
        value="U54321MH2021PTC000003",
        confidence=0.93,
        document_id="doc-crest-mca",
        page=1,
        document_type="CIN_DOCUMENT",
    ),
]


# ===================================================================
# Verification results — Aster Tech (all matching)
# ===================================================================

VERIFICATIONS_ASTER = [
    VerificationResult(
        source="PAN_DEMO",
        mode="DEMO",
        identifier="ABCDE1234F",
        status="VERIFIED",
        verified_facts={
            "pan": "ABCDE1234F",
            "name": "Aster Tech Private Limited",
            "status": "ACTIVE",
        },
        checked_at="2026-09-25T10:00:00Z",
        evidence_reference="PAN verification portal",
    ),
    VerificationResult(
        source="GST_DEMO",
        mode="DEMO",
        identifier="33ABCDE1234F1Z5",
        status="VERIFIED",
        verified_facts={
            "legalName": "Aster Tech Private Limited",
            "gstStatus": "ACTIVE",
            "registrationDate": "2022-04-10",
            "cancellationDate": None,
            "returnFilingStatus": "CURRENT",
            "lastReturnPeriod": "2026-08",
        },
        checked_at="2026-09-25T10:01:00Z",
        evidence_reference="GST portal lookup",
    ),
    VerificationResult(
        source="UDYAM_DEMO",
        mode="DEMO",
        identifier="UDYAM-TN-01-0001234",
        status="VERIFIED",
        verified_facts={
            "udyamNumber": "UDYAM-TN-01-0001234",
            "enterpriseName": "Aster Tech Private Limited",
            "status": "ACTIVE",
            "pan": "ABCDE1234F",
        },
        checked_at="2026-09-25T10:02:00Z",
        evidence_reference="Udyam registration portal",
    ),
    VerificationResult(
        source="MCA_DEMO",
        mode="DEMO",
        identifier="U12345TN2022PTC000001",
        status="VERIFIED",
        verified_facts={
            "cin": "U12345TN2022PTC000001",
            "companyName": "ASTER TECH PRIVATE LIMITED",
            "companyStatus": "ACTIVE",
        },
        checked_at="2026-09-25T10:03:00Z",
        evidence_reference="MCA company master",
    ),
]


# ===================================================================
# Verification results — Bharat Supplies (GST name mismatch)
# ===================================================================

VERIFICATIONS_BHARAT = [
    VerificationResult(
        source="PAN_DEMO",
        mode="DEMO",
        identifier="FGHIJ5678K",
        status="VERIFIED",
        verified_facts={
            "pan": "FGHIJ5678K",
            "name": "Bharat Supplies Private Limited",
            "status": "ACTIVE",
        },
        checked_at="2026-09-25T10:04:00Z",
        evidence_reference="PAN verification portal",
    ),
    VerificationResult(
        source="GST_DEMO",
        mode="DEMO",
        identifier="29FGHIJ5678K1Z8",
        status="VERIFIED",
        verified_facts={
            # Intentional name mismatch — demo scenario
            "legalName": "Bharat Trading Corp",
            "gstStatus": "ACTIVE",
            "registrationDate": "2020-06-15",
            "cancellationDate": None,
            "returnFilingStatus": "CURRENT",
        },
        checked_at="2026-09-25T10:05:00Z",
        evidence_reference="GST portal lookup",
    ),
    VerificationResult(
        source="MCA_DEMO",
        mode="DEMO",
        identifier="U67890KA2020PTC000002",
        status="VERIFIED",
        verified_facts={
            "cin": "U67890KA2020PTC000002",
            "companyName": "BHARAT SUPPLIES PRIVATE LIMITED",
            "companyStatus": "ACTIVE",
        },
        checked_at="2026-09-25T10:06:00Z",
        evidence_reference="MCA company master",
    ),
]


# ===================================================================
# Verification results — Crest Systems (matching identifiers)
# ===================================================================

VERIFICATIONS_CREST = [
    VerificationResult(
        source="PAN_DEMO",
        mode="DEMO",
        identifier="KLMNO9012P",
        status="VERIFIED",
        verified_facts={
            "pan": "KLMNO9012P",
            "name": "Crest Systems Private Limited",
            "status": "ACTIVE",
        },
        checked_at="2026-09-25T10:07:00Z",
        evidence_reference="PAN verification portal",
    ),
    VerificationResult(
        source="GST_DEMO",
        mode="DEMO",
        identifier="27KLMNO9012P1Z3",
        status="VERIFIED",
        verified_facts={
            "legalName": "Crest Systems Private Limited",
            "gstStatus": "ACTIVE",
            "registrationDate": "2021-03-20",
            "cancellationDate": None,
            "returnFilingStatus": "CURRENT",
        },
        checked_at="2026-09-25T10:08:00Z",
        evidence_reference="GST portal lookup",
    ),
    VerificationResult(
        source="MCA_DEMO",
        mode="DEMO",
        identifier="U54321MH2021PTC000003",
        status="VERIFIED",
        verified_facts={
            "cin": "U54321MH2021PTC000003",
            "companyName": "CREST SYSTEMS PRIVATE LIMITED",
            "companyStatus": "ACTIVE",
        },
        checked_at="2026-09-25T10:09:00Z",
        evidence_reference="MCA company master",
    ),
]


# ===================================================================
# Special-case verification results for edge-case tests
# ===================================================================

VERIFICATION_NOT_FOUND = VerificationResult(
    source="PAN_DEMO",
    mode="DEMO",
    identifier="ZZZZZ9999Z",
    status="NOT_FOUND",
    verified_facts={},
    checked_at="2026-09-25T10:10:00Z",
    evidence_reference="PAN verification portal",
)

VERIFICATION_ERROR = VerificationResult(
    source="GST_DEMO",
    mode="DEMO",
    identifier="99ZZZZZ9999Z1Z9",
    status="ERROR",
    verified_facts={},
    checked_at="2026-09-25T10:11:00Z",
    evidence_reference="GST portal lookup",
)

# A verification result with conflicting PAN value
VERIFICATION_PAN_CONFLICT = VerificationResult(
    source="PAN_DEMO",
    mode="DEMO",
    identifier="ABCDE1234F",
    status="VERIFIED",
    verified_facts={
        "pan": "XXXXX9999Y",  # Different PAN in verified facts
        "name": "Some Other Company",
        "status": "ACTIVE",
    },
    checked_at="2026-09-25T10:12:00Z",
    evidence_reference="PAN verification portal",
)


# ===================================================================
# Provenance test fixtures
# ===================================================================

# Bidder for provenance testing
BIDDER_PROVENANCE = BidderProfile(
    bidder_id="BID-PROV",
    legal_name="Provenance Test Corp",
    pan="ABCDE1234F",
    gstin="33ABCDE1234F1Z5",
)

# Extracted PAN differs from bidder PAN (OCR misread)
FACTS_DIVERGENT_PAN = [
    ExtractedFact(
        field="pan",
        value="ABCDE1234G",  # different from bidder PAN (ABCDE1234F)
        confidence=0.88,
        document_id="doc-prov-pan-ocr",
        page=1,
        document_type="PAN_CARD",
    ),
    ExtractedFact(
        field="gstin",
        value="33ABCDE1234F1Z5",
        confidence=0.95,
        document_id="doc-prov-gst",
        page=1,
        document_type="GST_CERTIFICATE",
    ),
]

# Verification matches the BIDDER PAN, not the extracted one
VERIFICATIONS_MATCH_BIDDER_PAN = [
    VerificationResult(
        source="PAN_DEMO",
        mode="DEMO",
        identifier="ABCDE1234F",
        status="VERIFIED",
        verified_facts={
            "pan": "ABCDE1234F",
            "name": "Provenance Test Corp",
            "status": "ACTIVE",
        },
        checked_at="2026-09-25T11:00:00Z",
        evidence_reference="PAN portal verification",
    ),
    VerificationResult(
        source="GST_DEMO",
        mode="DEMO",
        identifier="33ABCDE1234F1Z5",
        status="VERIFIED",
        verified_facts={
            "legalName": "Provenance Test Corp",
            "gstStatus": "ACTIVE",
        },
        checked_at="2026-09-25T11:01:00Z",
        evidence_reference="GST portal lookup",
    ),
]

# Multiple extracted facts for PAN with different confidences and values
FACTS_MULTI_CONFIDENCE_PAN = [
    ExtractedFact(
        field="pan",
        value="ABCDE1234F",
        confidence=0.95,
        document_id="doc-pan-high",
        page=1,
        document_type="PAN_CARD",
    ),
    ExtractedFact(
        field="pan",
        value="ABCDE1234F",
        confidence=0.72,
        document_id="doc-pan-low",
        page=2,
        document_type="GST_CERTIFICATE",
    ),
    ExtractedFact(
        field="pan",
        value="ABCDE1234G",  # different value, lowest confidence
        confidence=0.60,
        document_id="doc-pan-diff",
        page=1,
        document_type="UNKNOWN",
    ),
]

# Two verification results from same source — one VERIFIED, one NOT_FOUND
VERIFICATIONS_MIXED_STATUS = [
    VerificationResult(
        source="PAN_DEMO",
        mode="DEMO",
        identifier="ABCDE1234F",
        status="VERIFIED",
        verified_facts={
            "pan": "ABCDE1234F",
            "name": "Provenance Test Corp",
            "status": "ACTIVE",
        },
        checked_at="2026-09-25T11:00:00Z",
        evidence_reference="PAN portal verification",
    ),
    VerificationResult(
        source="PAN_DEMO",
        mode="DEMO",
        identifier="XXXXX9999Z",
        status="NOT_FOUND",
        verified_facts={},
        checked_at="2026-09-25T11:02:00Z",
        evidence_reference="PAN portal verification",
    ),
]

