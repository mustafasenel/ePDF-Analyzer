"""Response models for API endpoints"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PDFMetadata(BaseModel):
    """PDF metadata information"""
    
    title: Optional[str] = Field(default=None, description="Document title")
    author: Optional[str] = Field(default=None, description="Document author")
    subject: Optional[str] = Field(default=None, description="Document subject")
    keywords: Optional[str] = Field(default=None, description="Document keywords")
    creator: Optional[str] = Field(default=None, description="Creator application")
    producer: Optional[str] = Field(default=None, description="Producer application")
    creation_date: Optional[str] = Field(default=None, description="Creation date")
    modification_date: Optional[str] = Field(default=None, description="Last modification date")
    page_count: int = Field(..., description="Total number of pages")
    file_size_bytes: int = Field(..., description="File size in bytes")
    file_size_formatted: str = Field(..., description="Formatted file size (e.g., '2.5 MB')")
    pdf_version: Optional[str] = Field(default=None, description="PDF version")


class TableData(BaseModel):
    """Extracted table data"""
    
    has_header: bool = Field(..., description="Whether table has a header row")
    headers: Optional[List[str]] = Field(default=None, description="Table column headers (if detected)")
    rows: List[List[Any]] = Field(..., description="Table rows")
    row_count: int = Field(..., description="Number of rows")
    col_count: int = Field(..., description="Number of columns")
    note: Optional[str] = Field(default=None, description="Additional information about the table")


class PageText(BaseModel):
    """Text content from a single page"""
    
    page_number: int = Field(..., description="Page number (1-indexed)")
    text: str = Field(..., description="Extracted text content")
    char_count: int = Field(..., description="Character count")


class TextExtractionResponse(BaseModel):
    """Response for text extraction endpoint"""
    
    status: str = Field(default="success", description="Request status")
    text: Dict[str, str] = Field(..., description="Text content by page number")
    all_text: str = Field(..., description="All text concatenated")
    char_count: int = Field(..., description="Total character count")
    page_count: int = Field(..., description="Number of pages processed")
    processing_time: float = Field(..., description="Processing time in seconds")


class TableExtractionResponse(BaseModel):
    """Response for table extraction endpoint"""
    
    status: str = Field(default="success", description="Request status")
    tables: Dict[str, List[TableData]] = Field(
        ..., 
        description="Tables organized by page number"
    )
    total_tables: int = Field(..., description="Total number of tables found")
    page_count: int = Field(..., description="Number of pages processed")
    processing_time: float = Field(..., description="Processing time in seconds")


class Statistics(BaseModel):
    """Statistics about the PDF analysis"""
    
    total_pages: int = Field(..., description="Total pages in PDF")
    total_tables: int = Field(..., description="Total tables found")
    total_chars: int = Field(..., description="Total characters extracted")
    has_images: bool = Field(..., description="Whether PDF contains images")
    pages_with_tables: List[int] = Field(
        default_factory=list,
        description="Page numbers containing tables"
    )


class FullAnalysisResponse(BaseModel):
    """Response for full PDF analysis"""
    
    status: str = Field(default="success", description="Request status")
    metadata: PDFMetadata = Field(..., description="PDF metadata")
    text: Optional[Dict[str, str]] = Field(
        default=None,
        description="Text content by page number"
    )
    tables: Optional[Dict[str, List[TableData]]] = Field(
        default=None,
        description="Tables organized by page number"
    )
    statistics: Statistics = Field(..., description="Analysis statistics")
    processing_time: float = Field(..., description="Processing time in seconds")


class ErrorResponse(BaseModel):
    """Error response model"""
    
    status: str = Field(default="error", description="Request status")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )


class HealthCheckResponse(BaseModel):
    """Health check response"""
    
    status: str = Field(default="healthy", description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")

