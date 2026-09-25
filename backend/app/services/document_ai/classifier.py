import re
from .schemas import DocumentType, ClassificationResult

def classify_document(filename: str, text: str) -> ClassificationResult:
    """
    Classifies the document based on filename keywords, extracted text keywords, and specific identifiers.
    Avoids LLM usage for speed, deterministic behavior, and robustness.
    """
    filename_lower = filename.lower()
    text_upper = text.upper()
    
    # 1. PAN Classification
    pan_pattern = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')
    if "INCOME TAX DEPARTMENT" in text_upper or "GOVT OF INDIA" in text_upper:
        if pan_pattern.search(text_upper):
            return ClassificationResult(
                document_type=DocumentType.PAN,
                confidence=0.98,
                reason="Found Income Tax Department keywords and valid PAN pattern in text."
            )
        return ClassificationResult(
            document_type=DocumentType.PAN,
            confidence=0.80,
            reason="Found PAN-related keywords but no valid PAN pattern."
        )
    if re.search(r'(?:^|[^a-z])pan(?:[^a-z]|$)', filename_lower):
        if pan_pattern.search(text_upper):
            return ClassificationResult(
                document_type=DocumentType.PAN,
                confidence=0.90,
                reason="Filename suggests PAN and valid PAN pattern found in text."
            )
        return ClassificationResult(
            document_type=DocumentType.PAN,
            confidence=0.60,
            reason="Filename suggests PAN, but no pattern or keywords found."
        )
            
    # 2. GST Classification
    gstin_pattern = re.compile(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b')
    if "GST" in text_upper or "GOODS AND SERVICES TAX" in text_upper:
        if gstin_pattern.search(text_upper):
            return ClassificationResult(
                document_type=DocumentType.GST,
                confidence=0.98,
                reason="Found GST keywords and valid GSTIN pattern in text."
            )
        return ClassificationResult(
            document_type=DocumentType.GST,
            confidence=0.80,
            reason="Found GST keywords but no valid GSTIN pattern."
        )
    if re.search(r'(?:^|[^a-z])gst(?:[^a-z]|$)', filename_lower):
        if gstin_pattern.search(text_upper):
            return ClassificationResult(
                document_type=DocumentType.GST,
                confidence=0.90,
                reason="Filename suggests GST and valid GSTIN pattern found in text."
            )
        return ClassificationResult(
            document_type=DocumentType.GST,
            confidence=0.60,
            reason="Filename suggests GST, but no pattern or keywords found."
        )

    # 3. UDYAM Classification
    udyam_pattern = re.compile(r'\bUDYAM-[A-Z]{2}-[0-9]{2}-[0-9]+\b')
    if "UDYAM" in text_upper or "MSME" in text_upper:
        if udyam_pattern.search(text_upper):
            return ClassificationResult(
                document_type=DocumentType.UDYAM,
                confidence=0.98,
                reason="Found Udyam/MSME keywords and valid Udyam pattern."
            )
        return ClassificationResult(
            document_type=DocumentType.UDYAM,
            confidence=0.80,
            reason="Found Udyam keywords but no valid pattern."
        )
    if re.search(r'(?:^|[^a-z])udyam(?:[^a-z]|$)', filename_lower):
        if udyam_pattern.search(text_upper):
            return ClassificationResult(
                document_type=DocumentType.UDYAM,
                confidence=0.90,
                reason="Filename suggests Udyam and valid pattern found in text."
            )
        return ClassificationResult(
            document_type=DocumentType.UDYAM,
            confidence=0.60,
            reason="Filename suggests Udyam, but no pattern or keywords found."
        )

    # 4. OEM Authorization Classification
    if "OEM AUTHORISATION" in text_upper or "MANUFACTURER AUTHORIZATION" in text_upper or "OEM AUTHORIZATION" in text_upper:
        return ClassificationResult(
            document_type=DocumentType.OEM_AUTHORIZATION,
            confidence=0.95,
            reason="Found explicit OEM authorization keywords in text."
        )
    if re.search(r'(?:^|[^a-z])oem(?:[^a-z]|$)', filename_lower) and ("AUTHORISATION" in text_upper or "AUTHORIZATION" in text_upper or "AUTH" in filename_lower):
        return ClassificationResult(
            document_type=DocumentType.OEM_AUTHORIZATION,
            confidence=0.85,
            reason="Filename suggests OEM and text contains authorization terms."
        )

    # 5. Make in India Declaration
    if "MAKE IN INDIA" in text_upper or "LOCAL CONTENT" in text_upper or "CLASS I LOCAL SUPPLIER" in text_upper:
        return ClassificationResult(
            document_type=DocumentType.MAKE_IN_INDIA_DECLARATION,
            confidence=0.95,
            reason="Found explicit Make in India or local content keywords in text."
        )
    if re.search(r'(?:^|[^a-z])mii(?:[^a-z]|$)', filename_lower) or "make_in_india" in filename_lower:
        return ClassificationResult(
            document_type=DocumentType.MAKE_IN_INDIA_DECLARATION,
            confidence=0.85,
            reason="Filename suggests Make in India declaration."
        )
        
    # Default Unknown
    return ClassificationResult(
        document_type=DocumentType.UNKNOWN,
        confidence=0.40,
        reason="Document does not match any known keywords, patterns, or filenames."
    )
