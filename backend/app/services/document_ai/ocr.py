import abc
import logging
from typing import List, Optional

from .schemas import ExtractionMethod, PageText, OcrResult

logger = logging.getLogger(__name__)

class BaseOcrAdapter(abc.ABC):
    """Clean interface for OCR Adapters. Makes implementations swappable."""
    @abc.abstractmethod
    def extract_text(self, document_id: str, file_content: bytes) -> OcrResult:
        pass


class PyMuPdfAdapter(BaseOcrAdapter):
    """Text-based PDF extraction."""
    def extract_text(self, document_id: str, file_content: bytes) -> OcrResult:
        pages = []
        errors = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_content, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text").strip()
                if not text:
                    errors.append(f"Page {page_num + 1} has no extractable text.")
                
                pages.append(PageText(
                    page_number=page_num + 1,
                    text=text,
                    extraction_method=ExtractionMethod.TEXT_PDF,
                    confidence=1.0 if text else 0.0,
                    warnings=[] if text else ["No text found using text-extraction"]
                ))
            return OcrResult(document_id=document_id, pages=pages, total_pages=len(doc), global_errors=errors)
        except ImportError:
            return OcrResult(document_id=document_id, pages=[], total_pages=0, global_errors=["PyMuPDF (fitz) not installed."])
        except Exception as e:
            return OcrResult(document_id=document_id, pages=[], total_pages=0, global_errors=[f"PyMuPdfAdapter error: {str(e)}"])


class DocTrAdapter(BaseOcrAdapter):
    """docTR OCR extraction for scanned documents."""
    def extract_text(self, document_id: str, file_content: bytes) -> OcrResult:
        try:
            from doctr.io import DocumentFile
            from doctr.models import ocr_predictor
            
            # In a real environment, initialize this once globally to prevent model reloading.
            predictor = ocr_predictor(pretrained=True)
            
            doc = DocumentFile.from_pdf(file_content)
            result = predictor(doc)
            
            pages = []
            for i, page in enumerate(result.pages):
                page_text = []
                for block in page.blocks:
                    for line in block.lines:
                        line_text = " ".join([word.value for word in line.words])
                        page_text.append(line_text)
                
                text = "\n".join(page_text)
                pages.append(PageText(
                    page_number=i + 1,
                    text=text,
                    extraction_method=ExtractionMethod.OCR_DOCTR,
                    confidence=None, # docTR provides word-level confidences, not aggregated page-level trivially
                    warnings=[]
                ))
            return OcrResult(document_id=document_id, pages=pages, total_pages=len(pages), global_errors=[])
        except ImportError:
            return OcrResult(document_id=document_id, pages=[], total_pages=0, global_errors=["docTR not installed. Please install python-doctr."])
        except Exception as e:
            return OcrResult(document_id=document_id, pages=[], total_pages=0, global_errors=[f"DocTrAdapter error: {str(e)}"])


class OcrOrchestrator:
    """Orchestrates extraction, falling back to OCR if text-extraction yields no text."""
    def __init__(self, text_adapter: BaseOcrAdapter = None, ocr_adapter: BaseOcrAdapter = None):
        self.text_adapter = text_adapter or PyMuPdfAdapter()
        self.ocr_adapter = ocr_adapter or DocTrAdapter()

    def perform_extraction(self, document_id: str, file_content: bytes) -> OcrResult:
        # 1. Attempt standard text extraction (fast and highly accurate for digital PDFs)
        text_result = self.text_adapter.extract_text(document_id, file_content)
        
        # 2. Check if fallback is needed (e.g., if it's an image-only/scanned PDF)
        # Fallback heuristic: If successfully opened but average chars per page < 50
        if text_result.total_pages > 0:
            total_chars = sum(len(p.text) for p in text_result.pages)
            if (total_chars / text_result.total_pages) < 50:
                # Fallback to OCR
                ocr_result = self.ocr_adapter.extract_text(document_id, file_content)
                # If OCR worked without global errors, use its result
                if not ocr_result.global_errors and ocr_result.pages:
                    return ocr_result
                else:
                    # If OCR failed, return original text result but attach OCR errors as warnings
                    text_result.global_errors.extend([f"OCR fallback failed: {err}" for err in ocr_result.global_errors])
        elif not text_result.pages and text_result.global_errors:
            # If PyMuPDF couldn't even open it (e.g., an image file rather than PDF)
            ocr_result = self.ocr_adapter.extract_text(document_id, file_content)
            if not ocr_result.global_errors and ocr_result.pages:
                return ocr_result
                
        return text_result
