def perform_ocr(file_content: bytes, file_name: str) -> str:
    """
    Extracts text from the document bytes.
    
    In a real production system, this module would:
    1. Check if the file is a PDF or an Image.
    2. Use PyMuPDF (fitz) or pdfplumber to extract text directly if it's a text-based PDF.
    3. Use Tesseract (pytesseract) or a cloud OCR service (AWS Textract, Google Document AI)
       if it's a scanned PDF or an image.
       
    For the hackathon prototype/demo scope, this simulates OCR by reading 
    fallback patterns to avoid heavy ML dependencies on startup, whilst
    maintaining the exact interface the Core API expects.
    """
    lower_name = file_name.lower()
    text = ""
    
    # Simulated OCR extraction based on context
    if "pan" in lower_name:
        text = "INCOME TAX DEPARTMENT GOVT OF INDIA PAN ABCDE1234F Name: Aster Tech"
    elif "gst" in lower_name:
        text = "Form GST REG-06 Registration Certificate GSTIN 33ABCDE1234F1Z5 Legal Name Aster Tech Private Limited"
    elif "udyam" in lower_name:
        text = "UDYAM REGISTRATION CERTIFICATE UDYAM-TN-01-0001234 Enterprise Name: Aster Tech"
    elif "oem" in lower_name:
        text = "OEM AUTHORISATION LETTER Auth No: OEM-2026-991 Valid Until: 2026-12-31 Manufacturer: Cisco"
    elif "mii" in lower_name or "make_in_india" in lower_name:
        text = "MAKE IN INDIA DECLARATION Local Content: 60% Class I Local Supplier"
    else:
        text = "Standard corporate declaration document without specific identifiers."
        
    return text
