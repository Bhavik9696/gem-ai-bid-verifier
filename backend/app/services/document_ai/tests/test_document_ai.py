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


@patch("app.services.document_ai._ocr_orchestrator.perform_extraction")
def test_process_pan_document(mock_ocr):
    mock_ocr.return_value = OcrResult(
        document_id="doc-1",
        pages=[
            PageText(
                page_number=1,
                text=(
                    "INCOME TAX DEPARTMENT GOVT OF INDIA "
                    "PAN ABCDE1234F\n"
                    "Legal Name: Aster Tech"
                ),
                extraction_method=ExtractionMethod.TEXT_PDF,
            )
        ],
        total_pages=1,
    )

    result = process_document(
        "doc-1",
        "user_pan_card.pdf",
        b"dummy content",
    )

    assert result.document_type == DocumentType.PAN
    assert result.classification_confidence > 0.9
    assert result.processing_status == ProcessingStatus.SUCCESS
    assert "PAN" in result.extracted_fields
    assert result.extracted_fields["PAN"].value == "ABCDE1234F"
    assert result.validated_fields["PAN"].valid is True


@patch("app.services.document_ai._ocr_orchestrator.perform_extraction")
def test_process_gst_document(mock_ocr):
    mock_ocr.return_value = OcrResult(
        document_id="doc-2",
        pages=[
            PageText(
                page_number=1,
                text=(
                    "Form GST REG-06 Registration Certificate "
                    "GSTIN 33ABCDE1234F1Z5"
                ),
                extraction_method=ExtractionMethod.TEXT_PDF,
            )
        ],
        total_pages=1,
    )

    result = process_document(
        "doc-2",
        "company_gst.pdf",
        b"dummy content",
    )

    assert result.document_type == DocumentType.GST
    assert result.processing_status == ProcessingStatus.SUCCESS
    assert "GSTIN" in result.extracted_fields
    assert result.extracted_fields["GSTIN"].value == "33ABCDE1234F1Z5"


def test_process_invalid_file_type():
    result = process_document(
        "doc-x",
        "malicious.exe",
        b"dummy content",
    )

    assert result.processing_status == ProcessingStatus.FAILED
    assert result.document_type == DocumentType.UNKNOWN
    assert any(
        "Unsupported file type" in error
        for error in result.errors
    )


def test_process_large_file():
    large_content = b"0" * (11 * 1024 * 1024)

    result = process_document(
        "doc-y",
        "large_doc.pdf",
        large_content,
    )

    assert result.processing_status == ProcessingStatus.FAILED
    assert any(
        "size exceeds" in error
        for error in result.errors
    )


@patch("app.services.document_ai._ocr_orchestrator.perform_extraction")
def test_process_unknown_document(mock_ocr):
    mock_ocr.return_value = OcrResult(
        document_id="doc-3",
        pages=[
            PageText(
                page_number=1,
                text="random generic letter without ids",
                extraction_method=ExtractionMethod.TEXT_PDF,
            )
        ],
        total_pages=1,
    )

    result = process_document(
        "doc-3",
        "random_letter.pdf",
        b"dummy content",
    )

    assert result.document_type == DocumentType.UNKNOWN
    assert result.processing_status == ProcessingStatus.SUCCESS

    # Missing expected information should be represented explicitly.
    assert result.validated_fields["PAN"].valid is False
    assert (
        result.validated_fields["PAN"].status
        == ValidationStatus.MISSING
    )