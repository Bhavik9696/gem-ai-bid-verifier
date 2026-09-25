import mimetypes

ALLOWED_MIME_TYPES = ["application/pdf", "image/jpeg", "image/png"]
MAX_FILE_SIZE_MB = 10


def validate_document(file_name: str, file_size_bytes: int, file_content: bytes) -> bool:
    """
    Validates the uploaded document prior to processing.
    Checks file extension/mime type and size limit.
    """
    mime_type, _ = mimetypes.guess_type(file_name)
    
    # Fallback for some environments where mimetypes might not guess correctly
    if mime_type is None:
        if file_name.lower().endswith(".pdf"):
            mime_type = "application/pdf"
        elif file_name.lower().endswith(".jpg") or file_name.lower().endswith(".jpeg"):
            mime_type = "image/jpeg"
        elif file_name.lower().endswith(".png"):
            mime_type = "image/png"

    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"Unsupported file type: {mime_type}. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    if file_size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File size exceeds {MAX_FILE_SIZE_MB}MB limit.")
    
    # In a production environment, you might also add malware scanning (e.g., ClamAV)
    # and magic bytes validation to ensure it's not a disguised malicious file.
    return True
