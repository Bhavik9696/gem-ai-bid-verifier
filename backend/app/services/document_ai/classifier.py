from .schemas import DocumentType


def classify_document(text: str) -> tuple[DocumentType, float]:
    """
    Classifies the document based on its extracted text content.
    
    In a real implementation, this could use an LLM (e.g., via OpenAI API) 
    with a structured output, or a trained ML classifier like Naive Bayes/FastText.
    """
    text_lower = text.lower()
    
    if "income tax department" in text_lower or "pan" in text_lower:
        return DocumentType.PAN, 0.95
    elif "gst reg" in text_lower or "gstin" in text_lower:
        return DocumentType.GST, 0.98
    elif "udyam registration" in text_lower or "udyam-" in text_lower:
        return DocumentType.UDYAM, 0.99
    elif "oem authorisation" in text_lower or "manufacturer authorization" in text_lower:
        return DocumentType.OEM_AUTHORISATION, 0.90
    elif "make in india" in text_lower or "local content" in text_lower:
        return DocumentType.MAKE_IN_INDIA, 0.92
        
    return DocumentType.UNKNOWN, 0.50
