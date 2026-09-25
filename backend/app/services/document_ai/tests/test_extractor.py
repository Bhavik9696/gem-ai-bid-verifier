import pytest
from app.services.document_ai.extractor import extract_fields
from app.services.document_ai.schemas import DocumentType, PageText, ExtractionMethod


def create_mock_pages(text: str) -> list[PageText]:
    return [PageText(page_number=1, text=text, extraction_method=ExtractionMethod.TEXT_PDF)]


def test_valid_fields_pan_gstin():
    text = "Company Legal Name: Aster Tech\nPAN ABCDE1234F and GSTIN 33ABCDE1234F1Z5 are valid."
    pages = create_mock_pages(text)
    result = extract_fields("doc-1", DocumentType.UNKNOWN, pages)
    
    assert result["PAN"].value == "ABCDE1234F"
    assert result["PAN"].confidence == 0.99
    
    assert result["GSTIN"].value == "33ABCDE1234F1Z5"
    assert result["GSTIN"].confidence == 0.99
    
    assert result["Legal/Company Name"].value == "Aster Tech"
    assert result["Legal/Company Name"].confidence == 0.85


def test_missing_fields():
    pages = create_mock_pages("Just some random generic text without identifiers.")
    result = extract_fields("doc-2", DocumentType.UNKNOWN, pages)
    
    assert result["PAN"].value is None
    assert result["PAN"].confidence == 0.0
    assert "Not found" in result["PAN"].evidence
    assert result["GSTIN"].value is None
    assert result["Udyam Number"].value is None


def test_malformed_fields():
    # 9-char PAN (malformed), invalid percentage > 100
    pages = create_mock_pages("PAN ABCDE123F Local Content: 150%")
    result = extract_fields("doc-3", DocumentType.UNKNOWN, pages)
    
    assert result["PAN"].value is None  # Since it won't match the strict 10-char regex
    assert result["Local Content Percentage"].value is None # > 100 is rejected


def test_multiple_identifiers_low_confidence():
    pages = create_mock_pages("PAN ABCDE1234F and also another PAN XXXXX9999X")
    result = extract_fields("doc-4", DocumentType.UNKNOWN, pages)
    
    assert result["PAN"].value == "ABCDE1234F"
    assert result["PAN"].confidence == 0.80  # Confidence drops because of ambiguity
    assert "Multiple" in result["PAN"].evidence


def test_other_valid_fields():
    text = (
        "CIN U12345TN2022PTC000001 UDYAM-MH-18-0000123\n"
        "Date of Issue: 15-08-2025\n"
        "Valid Until: 2026-12-31\n"
        "Manufacturer: Cisco Systems\n"
    )
    pages = create_mock_pages(text)
    result = extract_fields("doc-5", DocumentType.UNKNOWN, pages)
    
    assert result["CIN"].value == "U12345TN2022PTC000001"
    assert result["Udyam Number"].value == "UDYAM-MH-18-0000123"
    assert result["Issue Date"].value == "15-08-2025"
    assert result["Expiry Date"].value == "2026-12-31"
    assert result["OEM Name"].value == "Cisco Systems"
