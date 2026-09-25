import pytest

from app.services.document_ai import process_document
from app.services.document_ai.schemas import DocumentType


def test_process_pan_document():
    # Simulate a PAN card upload
    result = process_document("user_pan_card.pdf", b"dummy content")
    
    assert result.document_type == DocumentType.PAN
    assert result.classification_confidence > 0.9
    assert "pan_number" in result.extracted_fields
    assert result.extracted_fields["pan_number"].value == "ABCDE1234F"
    assert result.extracted_fields["pan_number"].confidence_score > 0.9
    assert result.extracted_fields["pan_number"].page_reference == 1


def test_process_gst_document():
    result = process_document("company_gst.pdf", b"dummy content")
    assert result.document_type == DocumentType.GST
    assert "gstin" in result.extracted_fields
    assert result.extracted_fields["gstin"].value == "33ABCDE1234F1Z5"


def test_process_invalid_file_type():
    with pytest.raises(ValueError, match="Unsupported file type"):
        process_document("malicious.exe", b"dummy content")


def test_process_large_file():
    # Generate a dummy file larger than 10MB
    large_content = b"0" * (11 * 1024 * 1024)
    with pytest.raises(ValueError, match="File size exceeds"):
        process_document("large_doc.pdf", large_content)


def test_process_unknown_document():
    result = process_document("random_letter.pdf", b"dummy content")
    assert result.document_type == DocumentType.UNKNOWN
    assert len(result.extracted_fields) == 0
