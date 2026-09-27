from .schemas import DocumentType, DocumentResult, ExtractedFact, ProcessingStatus, ValidationStatus
from .validators import (
    validate_document, validate_pan, validate_gstin, 
    validate_udyam, validate_cin, validate_date, 
    validate_local_content_percentage, validate_generic_text
)
from .ocr import OcrOrchestrator
from .classifier import classify_document
from .extractor import extract_fields

# Create a singleton instance of the orchestrator to reuse models/adapters if needed
_ocr_orchestrator = OcrOrchestrator()

__all__ = ["process_document"]

def process_document(document_id: str, file_name: str, file_content: bytes) -> DocumentResult:
    """
    Main orchestration pipeline for the Document Intelligence module.
    Exposes a clean public interface that Core API orchestration can securely call.
    """
    warnings = []
    errors = []
    
    try:
        # 1. File Validation (Catches unreadable formats/giant sizes gracefully)
        validate_document(
            file_name=file_name, 
            file_size_bytes=len(file_content), 
            file_content=file_content
        )
    except ValueError as e:
        errors.append(f"Validation Error: {str(e)}")
        return DocumentResult(
            document_id=document_id,
            document_type=DocumentType.UNKNOWN,
            classification_confidence=0.0,
            extracted_fields={},
            validated_fields={},
            warnings=warnings,
            errors=errors,
            processing_status=ProcessingStatus.FAILED
        )
    
    try:
        # 2. Text Extraction with seamless OCR fallback
        ocr_result = _ocr_orchestrator.perform_extraction(document_id, file_content)
        
        # Propagate underlying extraction errors to the top level
        if ocr_result.global_errors:
            errors.extend(ocr_result.global_errors)
        for page in ocr_result.pages:
            warnings.extend(page.warnings)
            
        if not ocr_result.pages and errors:
            # Complete failure to read ANY text from ANY page
            return DocumentResult(
                document_id=document_id,
                document_type=DocumentType.UNKNOWN,
                classification_confidence=0.0,
                extracted_fields={},
                validated_fields={},
                warnings=warnings,
                errors=errors,
                processing_status=ProcessingStatus.FAILED,
                ocr_result=ocr_result
            )
        
        # Prepare content for analysis
        full_text = "\n".join([p.text for p in ocr_result.pages])
        
        # 3. Deterministic Document Classification
        classification = classify_document(file_name, full_text)
        
        # 4. Schema-First Deterministic Field Extraction
        extracted_fields = extract_fields(document_id, classification.document_type, ocr_result.pages)
        
        # 5. Semantic Validation of extracted facts
        validated_fields = {
            "PAN": validate_pan(extracted_fields.get("PAN")),
            "GSTIN": validate_gstin(extracted_fields.get("GSTIN")),
            "Udyam Number": validate_udyam(extracted_fields.get("Udyam Number")),
            "CIN": validate_cin(extracted_fields.get("CIN")),
            "Issue Date": validate_date(extracted_fields.get("Issue Date"), "Issue Date"),
            "Expiry Date": validate_date(extracted_fields.get("Expiry Date"), "Expiry Date"),
            "Local Content Percentage": validate_local_content_percentage(extracted_fields.get("Local Content Percentage")),
            "Legal/Company Name": validate_generic_text(extracted_fields.get("Legal/Company Name"), "Legal/Company Name"),
            "OEM Name": validate_generic_text(extracted_fields.get("OEM Name"), "OEM Name")
        }
        
        # 6. Top-level status deduction
        status = ProcessingStatus.SUCCESS
        if errors or any(v.status == ValidationStatus.NEEDS_REVIEW for v in validated_fields.values()):
            status = ProcessingStatus.PARTIAL_SUCCESS
            
        # 7. Return robust, normalized result map strictly avoiding compliance decisions
        return DocumentResult(
            document_id=document_id,
            document_type=classification.document_type,
            classification_confidence=classification.confidence,
            classification_reason=classification.reason,
            extracted_fields=extracted_fields,
            validated_fields=validated_fields,
            warnings=warnings,
            errors=errors,
            processing_status=status,
            ocr_result=ocr_result,
            raw_text_excerpt=full_text[:200]  # First 200 chars for rapid audit preview
        )
        
    except Exception as e:
        # Global catch-all prevents orchestrator crashes 
        errors.append(f"Unexpected processing error: {str(e)}")
        return DocumentResult(
            document_id=document_id,
            document_type=DocumentType.UNKNOWN,
            classification_confidence=0.0,
            extracted_fields={},
            validated_fields={},
            warnings=warnings,
            errors=errors,
            processing_status=ProcessingStatus.FAILED
        )
