"""Request models for API endpoints"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class TextExtractionRequest(BaseModel):
    """Request model for text extraction endpoint"""
    
    pages: Optional[List[int]] = Field(
        default=None,
        description="Specific pages to extract (None means all pages)",
        example=[1, 2, 3]
    )
    preserve_layout: bool = Field(
        default=False,
        description="Whether to preserve text layout and formatting"
    )


class TableExtractionRequest(BaseModel):
    """Request model for table extraction endpoint"""
    
    pages: Optional[List[int]] = Field(
        default=None,
        description="Specific pages to extract tables from (None means all pages)",
        example=[1, 3]
    )
    method: Literal["pdfplumber", "camelot"] = Field(
        default="pdfplumber",
        description="Table extraction method"
    )


class ExcelExportRequest(BaseModel):
    """Request model for Excel export endpoint"""
    
    include_text: bool = Field(
        default=True,
        description="Include text in separate sheet"
    )
    sheet_per_table: bool = Field(
        default=True,
        description="Create separate sheet for each table"
    )
    add_styling: bool = Field(
        default=True,
        description="Add basic styling to Excel file"
    )


class AnalysisRequest(BaseModel):
    """Request model for full analysis endpoint"""
    
    extract_tables: bool = Field(
        default=True,
        description="Whether to extract tables"
    )
    extract_text: bool = Field(
        default=True,
        description="Whether to extract text"
    )
    preserve_layout: bool = Field(
        default=False,
        description="Preserve text layout"
    )

