from enum import Enum
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    PAN = "PAN"
    GST = "GST"
    UDYAM = "UDYAM"
    OEM_AUTHORISATION = "OEM_AUTHORISATION"
    MAKE_IN_INDIA = "MAKE_IN_INDIA"
    UNKNOWN = "UNKNOWN"


class ExtractedField(BaseModel):
    value: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    page_reference: int = 1


class DocumentResult(BaseModel):
    document_type: DocumentType
    classification_confidence: float
    extracted_fields: Dict[str, ExtractedField]
    raw_text_excerpt: Optional[str] = None
