from enum import Enum
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    PAN = "PAN"
    GST = "GST"
    UDYAM = "UDYAM"
    OEM_AUTHORISATION = "OEM_AUTHORISATION"
    MAKE_IN_INDIA = "MAKE_IN_INDIA"
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


class ExtractedField(BaseModel):
    value: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    page_reference: int = 1


class DocumentResult(BaseModel):
    document_id: str
    document_type: DocumentType
    classification_confidence: float
    extracted_fields: Dict[str, ExtractedField]
    ocr_result: OcrResult
    raw_text_excerpt: Optional[str] = None
