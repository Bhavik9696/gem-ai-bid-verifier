import re
from typing import Dict, List, Optional
from .schemas import DocumentType, ExtractedFact, PageText

# Strict deterministic regex patterns
REGEX_PAN = re.compile(r'\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b')
REGEX_GSTIN = re.compile(r'\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b')
REGEX_UDYAM = re.compile(r'\b(UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]+)\b')
REGEX_CIN = re.compile(r'\b([LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6})\b')
REGEX_DATE_ISSUE = re.compile(r'(?i)(?:date of issue|issued on|registration date)[\s:-]*(\d{2}[-/]\d{2}[-/]\d{4}|\d{4}[-/]\d{2}[-/]\d{2})')
REGEX_DATE_EXPIRY = re.compile(r'(?i)(?:valid until|expiry date|valid upto)[\s:-]*(\d{2}[-/]\d{2}[-/]\d{4}|\d{4}[-/]\d{2}[-/]\d{2})')
REGEX_PERCENTAGE = re.compile(r'(?i)local content[^0-9]*?([0-9]{1,3}(?:\.[0-9]+)?)\s*%')
REGEX_COMPANY_NAME = re.compile(r'(?i)(?:legal name|enterprise name|name of company)[\s:-]*([A-Za-z0-9\s,&.]{3,60}?)(?=\n|$)')
REGEX_OEM_NAME = re.compile(r'(?i)(?:manufacturer|oem name)[\s:-]*([A-Za-z0-9\s,&.]{3,60}?)(?=\n|$)')


def extract_fields(document_id: str, document_type: DocumentType, pages: List[PageText]) -> Dict[str, ExtractedFact]:
    """
    Schema-first deterministic field extraction.
    NEVER invents a field. Returns None (null) for missing fields.
    """
    target_fields = [
        "PAN", "GSTIN", "Udyam Number", "Legal/Company Name", "CIN", 
        "Issue Date", "Expiry Date", "OEM Name", "Local Content Percentage"
    ]
    
    # Initialize all requested fields as None (not found)
    extracted = {
        f: ExtractedFact(
            field=f, 
            value=None, 
            confidence=0.0, 
            documentId=document_id, 
            page=1, 
            evidence="Not found in document"
        )
        for f in target_fields
    }

    if not pages:
        return extracted
        
    for page in pages:
        text = page.text
        page_num = page.page_number
        
        # 1. PAN
        if extracted["PAN"].value is None:
            matches = REGEX_PAN.findall(text)
            if matches:
                val = matches[0]
                conf = 0.99 if len(matches) == 1 else 0.80
                ev = f"Matched valid PAN format: {val}" if len(matches) == 1 else f"Multiple PANs detected, extracted first: {val}"
                extracted["PAN"] = ExtractedFact(field="PAN", value=val, confidence=conf, documentId=document_id, page=page_num, evidence=ev)

        # 2. GSTIN
        if extracted["GSTIN"].value is None:
            matches = REGEX_GSTIN.findall(text)
            if matches:
                val = matches[0]
                conf = 0.99 if len(matches) == 1 else 0.80
                ev = f"Matched valid GSTIN format: {val}" if len(matches) == 1 else f"Multiple GSTINs detected, extracted first: {val}"
                extracted["GSTIN"] = ExtractedFact(field="GSTIN", value=val, confidence=conf, documentId=document_id, page=page_num, evidence=ev)

        # 3. Udyam Number
        if extracted["Udyam Number"].value is None:
            matches = REGEX_UDYAM.findall(text)
            if matches:
                val = matches[0]
                conf = 0.99 if len(matches) == 1 else 0.80
                ev = f"Matched Udyam format: {val}" if len(matches) == 1 else f"Multiple Udyams detected, extracted first: {val}"
                extracted["Udyam Number"] = ExtractedFact(field="Udyam Number", value=val, confidence=conf, documentId=document_id, page=page_num, evidence=ev)
                
        # 4. CIN
        if extracted["CIN"].value is None:
            matches = REGEX_CIN.findall(text)
            if matches:
                val = matches[0]
                conf = 0.99 if len(matches) == 1 else 0.80
                ev = f"Matched CIN format: {val}" if len(matches) == 1 else f"Multiple CINs detected, extracted first: {val}"
                extracted["CIN"] = ExtractedFact(field="CIN", value=val, confidence=conf, documentId=document_id, page=page_num, evidence=ev)
                
        # 5. Legal/Company Name
        if extracted["Legal/Company Name"].value is None:
            match = REGEX_COMPANY_NAME.search(text)
            if match:
                val = match.group(1).strip()
                extracted["Legal/Company Name"] = ExtractedFact(field="Legal/Company Name", value=val, confidence=0.85, documentId=document_id, page=page_num, evidence=f"Found labelled company name: {val}")
        
        # 6. Issue Date
        if extracted["Issue Date"].value is None:
            match = REGEX_DATE_ISSUE.search(text)
            if match:
                val = match.group(1)
                extracted["Issue Date"] = ExtractedFact(field="Issue Date", value=val, confidence=0.90, documentId=document_id, page=page_num, evidence=f"Matched Issue Date pattern: {val}")
                
        # 7. Expiry Date
        if extracted["Expiry Date"].value is None:
            match = REGEX_DATE_EXPIRY.search(text)
            if match:
                val = match.group(1)
                extracted["Expiry Date"] = ExtractedFact(field="Expiry Date", value=val, confidence=0.90, documentId=document_id, page=page_num, evidence=f"Matched Expiry Date pattern: {val}")
                
        # 8. OEM Name
        if extracted["OEM Name"].value is None:
            match = REGEX_OEM_NAME.search(text)
            if match:
                val = match.group(1).strip()
                extracted["OEM Name"] = ExtractedFact(field="OEM Name", value=val, confidence=0.85, documentId=document_id, page=page_num, evidence=f"Matched OEM Name pattern: {val}")
                    
        # 9. Local Content Percentage
        if extracted["Local Content Percentage"].value is None:
            match = REGEX_PERCENTAGE.search(text)
            if match:
                val_str = match.group(1)
                try:
                    val_float = float(val_str)
                    if 0 <= val_float <= 100:
                        extracted["Local Content Percentage"] = ExtractedFact(field="Local Content Percentage", value=val_str, confidence=0.95, documentId=document_id, page=page_num, evidence=f"Extracted valid percentage: {val_str}%")
                    else:
                        extracted["Local Content Percentage"] = ExtractedFact(field="Local Content Percentage", value=None, confidence=0.0, documentId=document_id, page=page_num, evidence=f"Invalid percentage range (>100): {val_str}%")
                except ValueError:
                    pass
    
    # ---------------------------------------------------------
    # Optional LLM Enhancement Hook (e.g. Ollama / local model)
    # ---------------------------------------------------------
    # If key fields remain missing and an LLM is available, we can safely prompt it 
    # to locate the missing fields, keeping deterministic values intact. 
    # This remains disabled to guarantee reliable offline performance by default.
    # 
    # if any(f.value is None for f in extracted.values()) and LLM_ENABLED:
    #     extracted = enhance_extraction_with_llm(extracted, pages)
    
    return extracted
