"""Validation utilities for file upload and processing"""

import os
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile, HTTPException
from config.settings import settings


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_pdf_file(file: UploadFile) -> None:
    """
    Validate uploaded PDF file
    
    Args:
        file: Uploaded file from FastAPI
        
    Raises:
        HTTPException: If validation fails
    """
    # Check if file exists
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext != ".pdf":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file_ext}. Only PDF files are allowed."
        )
    
    # Check content type
    content_type = file.content_type
    if content_type and content_type not in ["application/pdf"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {content_type}. Expected 'application/pdf'."
        )


def validate_file_size(file_path: str | Path) -> None:
    """
    Validate file size against maximum allowed size
    
    Args:
        file_path: Path to the file
        
    Raises:
        ValidationError: If file size exceeds maximum
    """
    file_size = os.path.getsize(file_path)
    max_size = settings.max_file_size_bytes
    
    if file_size > max_size:
        raise ValidationError(
            f"File size ({format_bytes(file_size)}) exceeds maximum allowed "
            f"size ({format_bytes(max_size)})"
        )


def validate_page_numbers(page_numbers: list[int], total_pages: int) -> None:
    """
    Validate requested page numbers
    
    Args:
        page_numbers: List of requested page numbers (1-indexed)
        total_pages: Total number of pages in document
        
    Raises:
        ValidationError: If page numbers are invalid
    """
    if not page_numbers:
        return
    
    for page_num in page_numbers:
        if page_num < 1:
            raise ValidationError(f"Invalid page number: {page_num}. Page numbers start at 1.")
        if page_num > total_pages:
            raise ValidationError(
                f"Page number {page_num} exceeds total pages ({total_pages})"
            )


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes to human-readable string
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string (e.g., "2.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

