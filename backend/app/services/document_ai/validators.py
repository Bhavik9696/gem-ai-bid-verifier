import mimetypes
import re
from typing import Optional
from .schemas import ExtractedFact, ValidationResult, ValidationStatus

ALLOWED_MIME_TYPES = ["application/pdf", "image/jpeg", "image/png"]
MAX_FILE_SIZE_MB = 10


def validate_document(file_name: str, file_size_bytes: int, file_content: bytes) -> bool:
    """
    Validates the uploaded document prior to processing.
    """
    mime_type, _ = mimetypes.guess_type(file_name)
    
    if mime_type is None:
        if file_name.lower().endswith(".pdf"):
            mime_type = "application/pdf"
        elif file_name.lower().endswith(".jpg") or file_name.lower().endswith(".jpeg"):
            mime_type = "image/jpeg"
        elif file_name.lower().endswith(".png"):
            mime_type = "image/png"

    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"Unsupported file type: {mime_type}. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    if file_size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File size exceeds {MAX_FILE_SIZE_MB}MB limit.")
    
    return True


# Field Validation Patterns (Strict syntax bounding)
STRICT_REGEX_PAN = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')
STRICT_REGEX_GSTIN = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')
STRICT_REGEX_UDYAM = re.compile(r'^UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]+$')
STRICT_REGEX_CIN = re.compile(r'^[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$')
STRICT_REGEX_DATE = re.compile(r'^(\d{2}[-/]\d{2}[-/]\d{4}|\d{4}[-/]\d{2}[-/]\d{2})$')


def _check_missing(fact: Optional[ExtractedFact], field_name: str) -> Optional[ValidationResult]:
    if not fact or fact.value is None:
        return ValidationResult(
            valid=False, 
            status=ValidationStatus.MISSING, 
            value=None, 
            reason=f"Missing {field_name}"
        )
    return None


def _check_confidence(fact: ExtractedFact, threshold: float = 0.85) -> Optional[ValidationResult]:
    if fact.confidence < threshold:
        return ValidationResult(
            valid=False,
            status=ValidationStatus.NEEDS_REVIEW,
            value=fact.value,
            reason="Low extraction confidence"
        )
    return None


def validate_pan(fact: Optional[ExtractedFact]) -> ValidationResult:
    missing = _check_missing(fact, "PAN")
    if missing: return missing
    
    val = fact.value.strip()
    if not STRICT_REGEX_PAN.match(val):
        return ValidationResult(valid=False, status=ValidationStatus.INVALID, value=val, reason="Invalid PAN format")
        
    conf = _check_confidence(fact)
    if conf: return conf
    
    return ValidationResult(valid=True, status=ValidationStatus.VALID, value=val, reason="Valid PAN format")


def validate_gstin(fact: Optional[ExtractedFact]) -> ValidationResult:
    missing = _check_missing(fact, "GSTIN")
    if missing: return missing
    
    val = fact.value.strip()
    if not STRICT_REGEX_GSTIN.match(val):
        return ValidationResult(valid=False, status=ValidationStatus.INVALID, value=val, reason="Invalid GSTIN format")
        
    conf = _check_confidence(fact)
    if conf: return conf
    
    return ValidationResult(valid=True, status=ValidationStatus.VALID, value=val, reason="Valid GSTIN format")


def validate_udyam(fact: Optional[ExtractedFact]) -> ValidationResult:
    missing = _check_missing(fact, "Udyam number")
    if missing: return missing
    
    val = fact.value.strip()
    if not STRICT_REGEX_UDYAM.match(val):
        return ValidationResult(valid=False, status=ValidationStatus.INVALID, value=val, reason="Invalid Udyam format")
        
    conf = _check_confidence(fact)
    if conf: return conf
    
    return ValidationResult(valid=True, status=ValidationStatus.VALID, value=val, reason="Valid Udyam format")


def validate_cin(fact: Optional[ExtractedFact]) -> ValidationResult:
    missing = _check_missing(fact, "CIN")
    if missing: return missing
    
    val = fact.value.strip()
    if not STRICT_REGEX_CIN.match(val):
        return ValidationResult(valid=False, status=ValidationStatus.INVALID, value=val, reason="Invalid CIN format")
        
    conf = _check_confidence(fact)
    if conf: return conf
    
    return ValidationResult(valid=True, status=ValidationStatus.VALID, value=val, reason="Valid CIN format")


def validate_date(fact: Optional[ExtractedFact], field_name: str = "Date") -> ValidationResult:
    missing = _check_missing(fact, field_name)
    if missing: return missing
    
    val = fact.value.strip()
    if not STRICT_REGEX_DATE.match(val):
        return ValidationResult(valid=False, status=ValidationStatus.INVALID, value=val, reason=f"Invalid {field_name} format")
        
    conf = _check_confidence(fact)
    if conf: return conf
    
    return ValidationResult(valid=True, status=ValidationStatus.VALID, value=val, reason=f"Valid {field_name} format")


def validate_local_content_percentage(fact: Optional[ExtractedFact]) -> ValidationResult:
    missing = _check_missing(fact, "Local Content Percentage")
    if missing: return missing
    
    val = fact.value.strip()
    try:
        fval = float(val)
        if not (0 <= fval <= 100):
            return ValidationResult(valid=False, status=ValidationStatus.INVALID, value=val, reason="Percentage out of range (0-100)")
    except ValueError:
        return ValidationResult(valid=False, status=ValidationStatus.INVALID, value=val, reason="Invalid percentage format")
        
    conf = _check_confidence(fact)
    if conf: return conf
    
    return ValidationResult(valid=True, status=ValidationStatus.VALID, value=val, reason="Valid percentage")


def validate_generic_text(fact: Optional[ExtractedFact], field_name: str) -> ValidationResult:
    missing = _check_missing(fact, field_name)
    if missing: return missing
    
    val = fact.value.strip()
    if not val:
        return ValidationResult(valid=False, status=ValidationStatus.INVALID, value=val, reason=f"Empty {field_name}")
        
    conf = _check_confidence(fact)
    if conf: return conf
    
    return ValidationResult(valid=True, status=ValidationStatus.VALID, value=val, reason=f"Valid {field_name}")
