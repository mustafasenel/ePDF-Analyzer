"""Helper utilities for file operations and data processing"""

import os
import time
import shutil
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from config.settings import settings


def format_file_size(bytes_size: int) -> str:
    """
    Format bytes to human-readable string
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string (e.g., "2.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def clean_temp_files(folder: str | Path, max_age_hours: int = 24) -> int:
    """
    Clean old temporary files
    
    Args:
        folder: Folder to clean
        max_age_hours: Maximum age of files in hours
        
    Returns:
        Number of files deleted
    """
    folder_path = Path(folder)
    if not folder_path.exists():
        return 0
    
    deleted_count = 0
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for file_path in folder_path.glob("*"):
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception:
                    pass  # Skip files that can't be deleted
    
    return deleted_count


def ensure_folder_exists(folder: str | Path) -> Path:
    """
    Ensure folder exists, create if it doesn't
    
    Args:
        folder: Folder path
        
    Returns:
        Path object
    """
    folder_path = Path(folder)
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generate unique filename with timestamp
    
    Args:
        original_filename: Original file name
        prefix: Optional prefix
        
    Returns:
        Unique filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    name = Path(original_filename).stem
    ext = Path(original_filename).suffix
    
    if prefix:
        return f"{prefix}_{timestamp}_{name}{ext}"
    return f"{timestamp}_{name}{ext}"


def save_upload_file(upload_file, destination: str | Path) -> Path:
    """
    Save uploaded file to destination
    
    Args:
        upload_file: FastAPI UploadFile
        destination: Destination path
        
    Returns:
        Path to saved file
    """
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    
    with destination_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return destination_path


def dict_to_pretty_string(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Convert dictionary to pretty formatted string
    
    Args:
        data: Dictionary to format
        indent: Indentation level
        
    Returns:
        Formatted string
    """
    import json
    return json.dumps(data, indent=indent, ensure_ascii=False)


def merge_text_blocks(blocks: List[Dict[str, Any]], separator: str = "\n") -> str:
    """
    Merge text blocks into single string
    
    Args:
        blocks: List of text blocks with 'text' key
        separator: Separator between blocks
        
    Returns:
        Merged text
    """
    return separator.join(block.get("text", "") for block in blocks)


def sanitize_sheet_name(name: str, max_length: int = 31) -> str:
    """
    Sanitize sheet name for Excel
    Excel sheet names have restrictions:
    - Max 31 characters
    - Cannot contain: [ ] : * ? / \\
    
    Args:
        name: Original name
        max_length: Maximum length
        
    Returns:
        Sanitized name
    """
    # Remove invalid characters
    invalid_chars = ['[', ']', ':', '*', '?', '/', '\\']
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # Truncate if too long
    if len(name) > max_length:
        name = name[:max_length]
    
    # Remove leading/trailing spaces
    name = name.strip()
    
    # Ensure not empty
    if not name:
        name = "Sheet"
    
    return name

