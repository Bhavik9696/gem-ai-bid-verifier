import pytest
from app.services.document_ai.classifier import classify_document
from app.services.document_ai.schemas import DocumentType


def test_classify_pan_high_confidence():
    text = "INCOME TAX DEPARTMENT GOVT OF INDIA PAN ABCDE1234F"
    result = classify_document("unknown.pdf", text)
    assert result.document_type == DocumentType.PAN
    assert result.confidence > 0.9
    assert "pattern" in result.reason


def test_classify_pan_filename_fallback():
    text = "Some random text with ABCDE1234F in it."
    result = classify_document("user_pan_card.pdf", text)
    assert result.document_type == DocumentType.PAN
    assert result.confidence == 0.90
    assert "Filename" in result.reason


def test_classify_gst():
    text = "Registration Certificate GSTIN 33ABCDE1234F1Z5"
    result = classify_document("doc.pdf", text)
    assert result.document_type == DocumentType.GST
    assert result.confidence > 0.9


def test_classify_udyam():
    text = "UDYAM REGISTRATION CERTIFICATE UDYAM-TN-01-0001234"
    result = classify_document("doc.pdf", text)
    assert result.document_type == DocumentType.UDYAM
    assert result.confidence > 0.9


def test_classify_oem():
    text = "OEM AUTHORIZATION LETTER"
    result = classify_document("doc.pdf", text)
    assert result.document_type == DocumentType.OEM_AUTHORIZATION
    assert result.confidence > 0.9


def test_classify_mii():
    text = "MAKE IN INDIA DECLARATION Local Content: 60%"
    result = classify_document("doc.pdf", text)
    assert result.document_type == DocumentType.MAKE_IN_INDIA_DECLARATION
    assert result.confidence > 0.9


def test_classify_unknown():
    text = "Just a generic cover letter for the tender."
    result = classify_document("letter.pdf", text)
    assert result.document_type == DocumentType.UNKNOWN
    assert result.confidence < 0.5
