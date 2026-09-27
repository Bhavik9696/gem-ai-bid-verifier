import pytest
from app.services.document_ai.ocr import OcrOrchestrator, BaseOcrAdapter
from app.services.document_ai.schemas import OcrResult, PageText, ExtractionMethod

class MockTextAdapter(BaseOcrAdapter):
    def extract_text(self, document_id: str, file_content: bytes) -> OcrResult:
        if file_content == b"text_pdf":
            return OcrResult(
                document_id=document_id,
                pages=[PageText(page_number=1, text="This is a text PDF with lots of content to exceed the fallback limit. It contains plenty of text.", extraction_method=ExtractionMethod.TEXT_PDF)],
                total_pages=1
            )
        elif file_content == b"scanned_pdf":
            return OcrResult(
                document_id=document_id,
                pages=[PageText(page_number=1, text="short", extraction_method=ExtractionMethod.TEXT_PDF)],
                total_pages=1
            )
        elif file_content == b"empty_pdf":
            return OcrResult(
                document_id=document_id,
                pages=[],
                total_pages=1,
                global_errors=["Page 1 has no extractable text."]
            )
        elif file_content == b"multipage_pdf":
            return OcrResult(
                document_id=document_id,
                pages=[
                    PageText(page_number=1, text="Page 1 full text with plenty of words to avoid fallback to OCR.", extraction_method=ExtractionMethod.TEXT_PDF),
                    PageText(page_number=2, text="Page 2 full text with plenty of words to avoid fallback to OCR.", extraction_method=ExtractionMethod.TEXT_PDF)
                ],
                total_pages=2
            )
        else:
            return OcrResult(document_id=document_id, pages=[], total_pages=0, global_errors=["Cannot open file"])


class MockOcrAdapter(BaseOcrAdapter):
    def extract_text(self, document_id: str, file_content: bytes) -> OcrResult:
        if file_content == b"scanned_pdf":
            return OcrResult(
                document_id=document_id,
                pages=[PageText(page_number=1, text="This is OCR extracted text from a scanned PDF.", extraction_method=ExtractionMethod.OCR_DOCTR)],
                total_pages=1
            )
        elif file_content == b"empty_pdf":
            return OcrResult(
                document_id=document_id,
                pages=[],
                total_pages=1,
                global_errors=["OCR failed on empty image"]
            )
        else:
            return OcrResult(document_id=document_id, pages=[], total_pages=0, global_errors=["OCR failed"])


def test_ocr_normal_text_pdf():
    orchestrator = OcrOrchestrator(text_adapter=MockTextAdapter(), ocr_adapter=MockOcrAdapter())
    result = orchestrator.perform_extraction("doc-1", b"text_pdf")
    
    assert result.total_pages == 1
    assert result.pages[0].extraction_method == ExtractionMethod.TEXT_PDF
    assert "lots of content" in result.pages[0].text


def test_ocr_fallback_behavior():
    # If the text adapter returns < 50 chars per page, it should fallback to OCR adapter
    orchestrator = OcrOrchestrator(text_adapter=MockTextAdapter(), ocr_adapter=MockOcrAdapter())
    result = orchestrator.perform_extraction("doc-2", b"scanned_pdf")
    
    assert result.total_pages == 1
    assert result.pages[0].extraction_method == ExtractionMethod.OCR_DOCTR
    assert "OCR extracted text" in result.pages[0].text


def test_ocr_empty_unreadable():
    orchestrator = OcrOrchestrator(text_adapter=MockTextAdapter(), ocr_adapter=MockOcrAdapter())
    result = orchestrator.perform_extraction("doc-3", b"empty_pdf")
    
    assert result.total_pages == 1
    assert len(result.pages) == 0
    assert len(result.global_errors) > 0
    assert "Page 1 has no extractable text." in result.global_errors


def test_ocr_multiple_pages():
    orchestrator = OcrOrchestrator(text_adapter=MockTextAdapter(), ocr_adapter=MockOcrAdapter())
    result = orchestrator.perform_extraction("doc-4", b"multipage_pdf")
    
    assert result.total_pages == 2
    assert len(result.pages) == 2
    assert result.pages[0].page_number == 1
    assert result.pages[1].page_number == 2
    assert result.pages[1].extraction_method == ExtractionMethod.TEXT_PDF
