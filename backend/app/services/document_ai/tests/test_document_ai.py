import pytest
from unittest.mock import patch

from app.services.document_ai import process_document
from app.services.document_ai.schemas import DocumentType, OcrResult, PageText, ExtractionMethod


@patch('app.services.document_ai._ocr_orchestrator.perform_extraction')
def test_process_pan_document(mock_ocr):
    mock_ocr.return_value = OcrResult(
        document_id="doc-1",
        pages=[PageText(page_number=1, text="INCOME TAX DEPARTMENT GOVT OF INDIA PAN ABCDE1234F Name: Aster Tech", extraction_method=ExtractionMethod.TEXT_PDF)],
        total_pages=1
    )
    result = process_document("doc-1", "user_pan_card.pdf", b"dummy content")
    
    assert result.document_type == DocumentType.PAN
    assert result.classification_confidence > 0.9
    assert "pan_number" in result.extracted_fields
    assert result.extracted_fields["pan_number"].value == "ABCDE1234F"
    assert result.extracted_fields["pan_number"].confidence_score > 0.9
    assert result.extracted_fields["pan_number"].page_reference == 1


@patch('app.services.document_ai._ocr_orchestrator.perform_extraction')
def test_process_gst_document(mock_ocr):
    mock_ocr.return_value = OcrResult(
        document_id="doc-2",
        pages=[PageText(page_number=1, text="Form GST REG-06 Registration Certificate GSTIN 33ABCDE1234F1Z5", extraction_method=ExtractionMethod.TEXT_PDF)],
        total_pages=1
    )
    result = process_document("doc-2", "company_gst.pdf", b"dummy content")
    
    assert result.document_type == DocumentType.GST
    assert "gstin" in result.extracted_fields
    assert result.extracted_fields["gstin"].value == "33ABCDE1234F1Z5"


def test_process_invalid_file_type():
    with pytest.raises(ValueError, match="Unsupported file type"):
        process_document("doc-x", "malicious.exe", b"dummy content")


def test_process_large_file():
    large_content = b"0" * (11 * 1024 * 1024)
    with pytest.raises(ValueError, match="File size exceeds"):
        process_document("doc-y", "large_doc.pdf", large_content)


@patch('app.services.document_ai._ocr_orchestrator.perform_extraction')
def test_process_unknown_document(mock_ocr):
    mock_ocr.return_value = OcrResult(
        document_id="doc-3",
        pages=[PageText(page_number=1, text="random generic letter without ids", extraction_method=ExtractionMethod.TEXT_PDF)],
        total_pages=1
    )
    result = process_document("doc-3", "random_letter.pdf", b"dummy content")
    
    assert result.document_type == DocumentType.UNKNOWN
    assert len(result.extracted_fields) == 0
