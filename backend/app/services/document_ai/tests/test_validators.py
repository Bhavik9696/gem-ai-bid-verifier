import pytest
from app.services.document_ai.schemas import ExtractedFact, ValidationStatus
from app.services.document_ai.validators import (
    validate_pan, validate_gstin, validate_udyam,
    validate_cin, validate_date, validate_local_content_percentage,
    validate_generic_text
)


def build_fact(value, confidence=0.99):
    if value is None:
        return ExtractedFact(field="test", value=None, confidence=0.0, documentId="doc-1", page=1, evidence="Not found")
    return ExtractedFact(field="test", value=value, confidence=confidence, documentId="doc-1", page=1, evidence="Found")


def test_validate_pan():
    # Valid
    res = validate_pan(build_fact("ABCDE1234F"))
    assert res.valid is True
    assert res.status == ValidationStatus.VALID
    
    # Invalid format
    res = validate_pan(build_fact("ABCDE12345"))
    assert res.valid is False
    assert res.status == ValidationStatus.INVALID
    
    # Low confidence -> NEEDS_REVIEW
    res = validate_pan(build_fact("ABCDE1234F", 0.5))
    assert res.valid is False
    assert res.status == ValidationStatus.NEEDS_REVIEW
    
    # Missing
    res = validate_pan(build_fact(None))
    assert res.valid is False
    assert res.status == ValidationStatus.MISSING


def test_validate_gstin():
    res = validate_gstin(build_fact("33ABCDE1234F1Z5"))
    assert res.valid is True
    
    res = validate_gstin(build_fact("33ABCDE1234F1Z"))
    assert res.valid is False
    assert res.status == ValidationStatus.INVALID


def test_validate_udyam():
    res = validate_udyam(build_fact("UDYAM-TN-01-0001234"))
    assert res.valid is True
    
    res = validate_udyam(build_fact("UDYAM-TN-0001234"))
    assert res.valid is False


def test_validate_cin():
    res = validate_cin(build_fact("U12345TN2022PTC000001"))
    assert res.valid is True
    
    res = validate_cin(build_fact("Z12345TN2022PTC000001"))
    assert res.valid is False


def test_validate_percentage():
    res = validate_local_content_percentage(build_fact("60.5"))
    assert res.valid is True
    
    res = validate_local_content_percentage(build_fact("105"))
    assert res.valid is False
    assert res.status == ValidationStatus.INVALID
    
    res = validate_local_content_percentage(build_fact("abc"))
    assert res.valid is False


def test_validate_date():
    res = validate_date(build_fact("12-05-2025"))
    assert res.valid is True
    
    res = validate_date(build_fact("2025/12/05"))
    assert res.valid is True
    
    res = validate_date(build_fact("12th May 2025"))
    assert res.valid is False


def test_validate_generic():
    res = validate_generic_text(build_fact("Aster Tech"), "Company Name")
    assert res.valid is True
    
    res = validate_generic_text(build_fact("   "), "Company Name")
    assert res.valid is False
