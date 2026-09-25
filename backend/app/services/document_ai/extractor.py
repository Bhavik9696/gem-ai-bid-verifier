import re
from typing import Dict
from .schemas import DocumentType, ExtractedField


def extract_fields(document_type: DocumentType, text: str) -> Dict[str, ExtractedField]:
    """
    Extracts structured data fields (like PAN, GSTIN, Udyam Number) from the document text.
    
    In a production system, this could be achieved through precise Regex patterns 
    or by prompting an LLM (e.g. GPT-4o-mini or Gemini) to extract values into JSON.
    """
    fields: Dict[str, ExtractedField] = {}
    
    if document_type == DocumentType.PAN:
        pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', text)
        if pan_match:
            fields["pan_number"] = ExtractedField(
                value=pan_match.group(0),
                confidence_score=0.99,
                page_reference=1
            )
            
    elif document_type == DocumentType.GST:
        gstin_match = re.search(r'[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}', text)
        if gstin_match:
            fields["gstin"] = ExtractedField(
                value=gstin_match.group(0),
                confidence_score=0.98,
                page_reference=1
            )
            
    elif document_type == DocumentType.UDYAM:
        udyam_match = re.search(r'UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]+', text)
        if udyam_match:
            fields["udyam_number"] = ExtractedField(
                value=udyam_match.group(0),
                confidence_score=0.96,
                page_reference=1
            )
            
    elif document_type == DocumentType.OEM_AUTHORIZATION:
        auth_match = re.search(r'Auth No:\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        if auth_match:
            fields["authorisation_number"] = ExtractedField(
                value=auth_match.group(1),
                confidence_score=0.90,
                page_reference=1
            )
            
    elif document_type == DocumentType.MAKE_IN_INDIA_DECLARATION:
        content_match = re.search(r'Local Content:\s*([0-9]+)%', text, re.IGNORECASE)
        if content_match:
            fields["local_content_percentage"] = ExtractedField(
                value=content_match.group(1),
                confidence_score=0.95,
                page_reference=1
            )

    return fields
