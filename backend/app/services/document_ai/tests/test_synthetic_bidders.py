from unittest.mock import patch

from app.services.document_ai import process_document
from app.services.document_ai.schemas import (
    DocumentType,
    ExtractionMethod,
    OcrResult,
    PageText,
    ProcessingStatus,
    ValidationStatus,
)


# ==============================
# Synthetic bidder documents
# ==============================

# Bidder 1: Aster Tech Private Limited
# Documents contain consistent identity information.

FIXTURE_BIDDER_1_PAN = """
INCOME TAX DEPARTMENT GOVT OF INDIA
Legal Name: Aster Tech Private Limited
PAN ABCDE1234F
"""

FIXTURE_BIDDER_1_GST = """
Form GST REG-06 Registration Certificate
Legal Name: Aster Tech Private Limited
GSTIN 33ABCDE1234F1Z5
"""

FIXTURE_BIDDER_1_UDYAM = (
    "UDYAM REGISTRATION CERTIFICATE "
    "UDYAM-TN-01-0001234\n"
    "Enterprise Name: Aster Tech Private Limited"
)

FIXTURE_BIDDER_1_CIN = (
    "Certificate of Incorporation "
    "CIN U12345TN2022PTC000001\n"
    "Legal Name: Aster Tech Private Limited"
)

FIXTURE_BIDDER_1_OEM = """
OEM AUTHORIZATION LETTER
Manufacturer: Cisco Systems
Valid Until: 31-12-2026
Auth No: OEM-2026-991
"""

FIXTURE_BIDDER_1_MII = """
MAKE IN INDIA DECLARATION
Local Content: 60%
Class I Local Supplier
"""


# Bidder 2: Bharat Supplies Pvt Ltd
# PAN and GST documents contain different legal names.
# Document AI should extract the names as written.
# Cross-document mismatch evaluation belongs to the compliance layer.

FIXTURE_BIDDER_2_PAN = """
INCOME TAX DEPARTMENT GOVT OF INDIA
Legal Name: Bharat Supplies Pvt Ltd
PAN XYZDE5678G
"""

FIXTURE_BIDDER_2_GST = """
Form GST REG-06 Registration Certificate
Legal Name: Bharat Trading Company
GSTIN 07XYZDE5678G1Z9
"""


# Bidder 3: Crest Systems Pvt Ltd
# Includes an OEM authorization with a past expiry date.
# Document AI extracts and validates the date's format.
# Tender-date-based expiry evaluation belongs to the compliance layer.

FIXTURE_BIDDER_3_OEM = """
OEM AUTHORIZATION LETTER
Manufacturer: Dell Inc
Valid Until: 01-01-2023
Auth No: OEM-EXPIRED-01
"""


# ==============================
# Mock OCR helper
# ==============================

def _mock_ocr(document_id: str, text: str) -> OcrResult:
    return OcrResult(
        document_id=document_id,
        pages=[
            PageText(
                page_number=1,
                text=text,
                extraction_method=ExtractionMethod.TEXT_PDF,
            )
        ],
        total_pages=1,
        global_errors=[],
    )


# ==============================
# Synthetic bidder tests
# ==============================

@patch("app.services.document_ai._ocr_orchestrator.perform_extraction")
def test_bidder_1_valid_documents(mock_ocr_engine):
    """Verify extraction of the valid bidder's document fields."""

    # PAN
    mock_ocr_engine.return_value = _mock_ocr(
        "doc-1",
        FIXTURE_BIDDER_1_PAN,
    )
    res_pan = process_document("doc-1", "pan.pdf", b"dummy")

    assert res_pan.processing_status == ProcessingStatus.SUCCESS
    assert res_pan.document_type == DocumentType.PAN
    assert res_pan.extracted_fields["PAN"].value == "ABCDE1234F"
    assert (
        res_pan.extracted_fields["Legal/Company Name"].value
        == "Aster Tech Private Limited"
    )

    # GST
    mock_ocr_engine.return_value = _mock_ocr(
        "doc-2",
        FIXTURE_BIDDER_1_GST,
    )
    res_gst = process_document("doc-2", "gst.pdf", b"dummy")

    assert res_gst.document_type == DocumentType.GST
    assert res_gst.extracted_fields["GSTIN"].value == "33ABCDE1234F1Z5"
    assert (
        res_gst.extracted_fields["Legal/Company Name"].value
        == "Aster Tech Private Limited"
    )

    # Udyam
    mock_ocr_engine.return_value = _mock_ocr(
        "doc-3",
        FIXTURE_BIDDER_1_UDYAM,
    )
    res_udyam = process_document("doc-3", "udyam.pdf", b"dummy")

    assert (
        res_udyam.extracted_fields["Udyam Number"].value
        == "UDYAM-TN-01-0001234"
    )

    # CIN
    mock_ocr_engine.return_value = _mock_ocr(
        "doc-4",
        FIXTURE_BIDDER_1_CIN,
    )
    res_cin = process_document("doc-4", "cin.pdf", b"dummy")

    assert (
        res_cin.extracted_fields["CIN"].value
        == "U12345TN2022PTC000001"
    )

    # OEM authorization
    mock_ocr_engine.return_value = _mock_ocr(
        "doc-5",
        FIXTURE_BIDDER_1_OEM,
    )
    res_oem = process_document("doc-5", "oem.pdf", b"dummy")

    assert res_oem.extracted_fields["OEM Name"].value == "Cisco Systems"
    assert res_oem.extracted_fields["Expiry Date"].value == "31-12-2026"
    assert res_oem.validated_fields["Expiry Date"].valid is True

    # Make in India declaration
    mock_ocr_engine.return_value = _mock_ocr(
        "doc-6",
        FIXTURE_BIDDER_1_MII,
    )
    res_mii = process_document("doc-6", "mii.pdf", b"dummy")

    assert (
        res_mii.extracted_fields["Local Content Percentage"].value
        == "60"
    )


@patch("app.services.document_ai._ocr_orchestrator.perform_extraction")
def test_bidder_2_gst_name_mismatch(mock_ocr_engine):
    """
    Verify that document extraction preserves names from each document.

    Cross-document identity matching is left to the compliance engine.
    """

    # PAN
    mock_ocr_engine.return_value = _mock_ocr(
        "doc-21",
        FIXTURE_BIDDER_2_PAN,
    )
    res_pan = process_document("doc-21", "pan.pdf", b"dummy")
    pan_name = res_pan.extracted_fields["Legal/Company Name"].value

    # GST
    mock_ocr_engine.return_value = _mock_ocr(
        "doc-22",
        FIXTURE_BIDDER_2_GST,
    )
    res_gst = process_document("doc-22", "gst.pdf", b"dummy")
    gst_name = res_gst.extracted_fields["Legal/Company Name"].value

    assert pan_name == "Bharat Supplies Pvt Ltd"
    assert gst_name == "Bharat Trading Company"
    assert pan_name != gst_name


@patch("app.services.document_ai._ocr_orchestrator.perform_extraction")
def test_bidder_3_missing_and_expired(mock_ocr_engine):
    """
    Verify missing-field handling and extraction of an OEM expiry date.

    Date-format validation is distinct from checking whether the document
    is expired relative to a tender's relevant date.
    """

    # Missing Udyam information
    mock_ocr_engine.return_value = _mock_ocr(
        "doc-31",
        "Just a generic random letter without Udyam",
    )
    res_missing = process_document(
        "doc-31",
        "udyam_missing.pdf",
        b"dummy",
    )

    assert res_missing.extracted_fields["Udyam Number"].value is None
    assert (
        res_missing.validated_fields["Udyam Number"].status
        == ValidationStatus.MISSING
    )
    assert res_missing.validated_fields["Udyam Number"].valid is False

    # OEM authorization with a past expiry date
    mock_ocr_engine.return_value = _mock_ocr(
        "doc-32",
        FIXTURE_BIDDER_3_OEM,
    )
    res_expired = process_document("doc-32", "oem.pdf", b"dummy")

    assert res_expired.extracted_fields["Expiry Date"].value == "01-01-2023"

    # The date is syntactically valid. Whether it is expired for a
    # particular tender is evaluated by the downstream compliance rules.
    assert (
        res_expired.validated_fields["Expiry Date"].status
        == ValidationStatus.VALID
    )
    assert res_expired.validated_fields["Expiry Date"].valid is True