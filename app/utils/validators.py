import os
from fastapi import HTTPException, UploadFile

# Allowed extensions and mime-types
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg', '.zip'}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "image/png",
    "image/jpeg",
    "application/zip",
    "application/x-zip-compressed"
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def validate_attachment(file: UploadFile):
    """
    Validates file extension, mime-type, and file size.
    Raises HTTPException 400 Bad Request if validation fails.
    """
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty")
    
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' is not allowed. Supported extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    
    # Check mime type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Content-type '{file.content_type}' is not allowed."
        )
        
    # Check file size
    try:
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Failed to read file size during validation."
        )
        
    if size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File size ({size / (1024 * 1024):.2f} MB) exceeds maximum limit of {max_mb:.0f} MB."
        )
