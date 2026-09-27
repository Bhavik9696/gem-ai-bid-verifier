from enum import Enum
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    PAN = "PAN"
    GST = "GST"
    UDYAM = "UDYAM"
    OEM_AUTHORIZATION = "OEM_AUTHORIZATION"
    MAKE_IN_INDIA_DECLARATION = "MAKE_IN_INDIA_DECLARATION"
    UNKNOWN = "UNKNOWN"


class ExtractionMethod(str, Enum):
    TEXT_PDF = "TEXT_PDF"
    OCR_DOCTR = "OCR_DOCTR"
    OCR_PADDLE = "OCR_PADDLE"
    UNKNOWN = "UNKNOWN"


class PageText(BaseModel):
    page_number: int
    text: str
    extraction_method: ExtractionMethod
    confidence: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)


class OcrResult(BaseModel):
    document_id: str
    pages: List[PageText]
    total_pages: int
    global_errors: List[str] = Field(default_factory=list)


class ClassificationResult(BaseModel):
    document_type: DocumentType
    confidence: float
    reason: str


class ExtractedFact(BaseModel):
    field: str
    value: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    documentId: str
    page: int = 1
    evidence: str


class ValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    MISSING = "MISSING"


class ValidationResult(BaseModel):
    valid: bool
    status: ValidationStatus
    value: Optional[str] = None
    reason: str


class ProcessingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"


class DocumentResult(BaseModel):
    document_id: str
    document_type: DocumentType
    classification_confidence: float
    classification_reason: Optional[str] = None
    extracted_fields: Dict[str, ExtractedFact]
    validated_fields: Dict[str, ValidationResult]
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    processing_status: ProcessingStatus
    ocr_result: Optional[OcrResult] = None
    raw_text_excerpt: Optional[str] = None
