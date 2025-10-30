"""Data models for ePDF Analyzer"""

from .request_models import (
    TextExtractionRequest,
    TableExtractionRequest,
    ExcelExportRequest,
)
from .response_models import (
    PDFMetadata,
    TableData,
    PageText,
    TextExtractionResponse,
    TableExtractionResponse,
    FullAnalysisResponse,
    ErrorResponse,
)

__all__ = [
    # Request models
    "TextExtractionRequest",
    "TableExtractionRequest",
    "ExcelExportRequest",
    # Response models
    "PDFMetadata",
    "TableData",
    "PageText",
    "TextExtractionResponse",
    "TableExtractionResponse",
    "FullAnalysisResponse",
    "ErrorResponse",
]

