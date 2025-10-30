"""FastAPI main application"""

import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from app.models.response_models import (
    HealthCheckResponse,
    ErrorResponse,
    TextExtractionResponse,
    TableExtractionResponse,
    FullAnalysisResponse,
)
from app.services.pdf_analyzer import PDFAnalyzer, PDFAnalyzerError
from app.utils.validators import validate_pdf_file, validate_file_size, ValidationError
from app.utils.helpers import (
    save_upload_file,
    generate_unique_filename,
    clean_temp_files,
    ensure_folder_exists
)

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="LLM destekli PDF analiz servisi - Katman 1: Temel PDF İşleme",
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure folders exist
ensure_folder_exists(settings.UPLOAD_FOLDER)
ensure_folder_exists(settings.TEMP_FOLDER)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    # Clean old temp files
    deleted = clean_temp_files(settings.TEMP_FOLDER, max_age_hours=24)
    deleted += clean_temp_files(settings.UPLOAD_FOLDER, max_age_hours=24)
    if deleted > 0:
        print(f"Cleaned {deleted} old temporary files")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "ePDF Analyzer API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        version=settings.API_VERSION,
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/analyze/full", response_model=FullAnalysisResponse, tags=["Analysis"])
async def analyze_full(
    file: UploadFile = File(..., description="PDF file to analyze"),
    extract_text: bool = Form(True, description="Extract text content"),
    extract_tables: bool = Form(True, description="Extract tables"),
    preserve_layout: bool = Form(False, description="Preserve text layout"),
    table_method: str = Form("pdfplumber", description="Table extraction method")
):
    """
    Perform full PDF analysis: metadata + text + tables
    """
    temp_file_path = None
    
    try:
        # Validate file
        validate_pdf_file(file)
        
        # Save uploaded file
        unique_filename = generate_unique_filename(file.filename, prefix="analyze")
        temp_file_path = Path(settings.UPLOAD_FOLDER) / unique_filename
        save_upload_file(file, temp_file_path)
        
        # Validate file size
        validate_file_size(temp_file_path)
        
        # Analyze PDF
        analyzer = PDFAnalyzer(temp_file_path)
        result = analyzer.analyze_full(
            extract_text=extract_text,
            extract_tables=extract_tables,
            preserve_layout=preserve_layout,
            table_method=table_method
        )
        
        return JSONResponse(content=result)
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PDFAnalyzerError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Cleanup
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except:
                pass


@app.post("/api/v1/extract/basic", tags=["Extraction"])
async def extract_basic(
    file: UploadFile = File(..., description="PDF file")
):
    """
    Basic PDF extraction: text + tables per page, no interpretation
    
    Returns page-by-page analysis without any inference or template matching.
    """
    temp_file_path = None
    
    try:
        # Validate file
        validate_pdf_file(file)
        
        # Save uploaded file
        unique_filename = generate_unique_filename(file.filename, prefix="basic")
        temp_file_path = Path(settings.UPLOAD_FOLDER) / unique_filename
        save_upload_file(file, temp_file_path)
        
        # Validate file size
        validate_file_size(temp_file_path)
        
        # Extract basic data
        analyzer = PDFAnalyzer(temp_file_path)
        result = analyzer.extract_basic_analysis()
        
        return JSONResponse(content=result)
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PDFAnalyzerError as e:
        raise HTTPException(status_code=500, detail=f"PDF analysis error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    finally:
        # Cleanup
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except:
                pass


@app.post("/api/v1/extract/text", response_model=TextExtractionResponse, tags=["Extraction"])
async def extract_text(
    file: UploadFile = File(..., description="PDF file"),
    preserve_layout: bool = Form(False, description="Preserve text layout")
):
    """
    Extract text content from PDF
    """
    temp_file_path = None
    
    try:
        # Validate file
        validate_pdf_file(file)
        
        # Save uploaded file
        unique_filename = generate_unique_filename(file.filename, prefix="text")
        temp_file_path = Path(settings.UPLOAD_FOLDER) / unique_filename
        save_upload_file(file, temp_file_path)
        
        # Validate file size
        validate_file_size(temp_file_path)
        
        # Extract text
        analyzer = PDFAnalyzer(temp_file_path)
        result = analyzer.extract_text_only(preserve_layout=preserve_layout)
        
        return JSONResponse(content=result)
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PDFAnalyzerError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Cleanup
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except:
                pass


@app.post("/api/v1/extract/tables", response_model=TableExtractionResponse, tags=["Extraction"])
async def extract_tables(
    file: UploadFile = File(..., description="PDF file"),
    method: str = Form("pdfplumber", description="Extraction method (only pdfplumber supported)"),
    assume_first_row_header: Optional[bool] = Form(None, description="Force header detection (None=auto, True=has header, False=no header)")
):
    """
    Extract tables from PDF
    """
    temp_file_path = None
    
    try:
        # Validate file
        validate_pdf_file(file)
        
        # Save uploaded file
        unique_filename = generate_unique_filename(file.filename, prefix="tables")
        temp_file_path = Path(settings.UPLOAD_FOLDER) / unique_filename
        save_upload_file(file, temp_file_path)
        
        # Validate file size
        validate_file_size(temp_file_path)
        
        # Extract tables
        analyzer = PDFAnalyzer(temp_file_path)
        result = analyzer.extract_tables_only(method=method, assume_first_row_header=assume_first_row_header)
        
        return JSONResponse(content=result)
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PDFAnalyzerError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Cleanup
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except:
                pass


@app.post("/api/v1/export/tables-excel", tags=["Export"])
async def export_tables_excel(
    file: UploadFile = File(..., description="PDF file")
):
    """
    Export PDF tables as Excel file (tables only, no text)
    """
    temp_file_path = None
    excel_file_path = None
    
    try:
        # Validate file
        validate_pdf_file(file)
        
        # Save uploaded file
        unique_filename = generate_unique_filename(file.filename, prefix="excel")
        temp_file_path = Path(settings.UPLOAD_FOLDER) / unique_filename
        save_upload_file(file, temp_file_path)
        
        # Validate file size
        validate_file_size(temp_file_path)
        
        # Create Excel file
        analyzer = PDFAnalyzer(temp_file_path)
        
        # Generate output filename
        excel_filename = f"{Path(file.filename).stem}_tables.xlsx"
        excel_file_path = Path(settings.TEMP_FOLDER) / excel_filename
        
        # Export with styling, tables only
        analyzer.export_as_excel(
            output_path=excel_file_path,
            include_text=False,
            add_styling=True
        )
        
        # Return file
        return FileResponse(
            path=excel_file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=excel_filename
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PDFAnalyzerError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")
    finally:
        # Cleanup uploaded PDF
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except:
                pass
        # Excel file will be cleaned by periodic cleanup


@app.post("/api/v1/export/excel", tags=["Export"])
async def export_excel(
    file: UploadFile = File(..., description="PDF file"),
    include_text: Optional[bool] = Form(None, description="Include text in separate sheet"),
    add_styling: Optional[bool] = Form(None, description="Add styling to Excel")
):
    """
    Export PDF content as Excel file
    """
    temp_file_path = None
    excel_file_path = None
    
    try:
        # Validate file
        validate_pdf_file(file)
        
        # Save uploaded file
        unique_filename = generate_unique_filename(file.filename, prefix="excel")
        temp_file_path = Path(settings.UPLOAD_FOLDER) / unique_filename
        save_upload_file(file, temp_file_path)
        
        # Validate file size
        validate_file_size(temp_file_path)
        
        # Create Excel file
        analyzer = PDFAnalyzer(temp_file_path)
        
        # Generate output filename
        excel_filename = f"export_{Path(file.filename).stem}.xlsx"
        excel_file_path = Path(settings.TEMP_FOLDER) / excel_filename
        
        analyzer.export_as_excel(
            output_path=excel_file_path,
            include_text=include_text if include_text is not None else True,
            add_styling=add_styling if add_styling is not None else True
        )
        
        # Return file
        return FileResponse(
            path=excel_file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=excel_filename
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PDFAnalyzerError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Cleanup uploaded PDF
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except:
                pass
        # Excel file will be cleaned by periodic cleanup


@app.post("/api/v1/export/json", tags=["Export"])
async def export_json(
    file: UploadFile = File(..., description="PDF file"),
    include_text: bool = Form(True, description="Include text content"),
    include_tables: bool = Form(True, description="Include tables"),
    pretty: bool = Form(True, description="Pretty print JSON")
):
    """
    Export PDF content as JSON
    """
    temp_file_path = None
    
    try:
        # Validate file
        validate_pdf_file(file)
        
        # Save uploaded file
        unique_filename = generate_unique_filename(file.filename, prefix="json")
        temp_file_path = Path(settings.UPLOAD_FOLDER) / unique_filename
        save_upload_file(file, temp_file_path)
        
        # Validate file size
        validate_file_size(temp_file_path)
        
        # Export as JSON
        analyzer = PDFAnalyzer(temp_file_path)
        json_data = analyzer.export_as_json(
            output_path=None,  # Return as string
            include_text=include_text,
            include_tables=include_tables,
            pretty=pretty
        )
        
        # Return JSON response
        return JSONResponse(content=json_data if not pretty else eval(json_data))
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PDFAnalyzerError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Cleanup
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except:
                pass


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "error": "Not Found",
            "message": "The requested endpoint does not exist",
            "path": str(request.url.path)
        }
    )


@app.post("/api/v1/extract/template", tags=["Template Extraction"])
async def extract_with_template(
    file: UploadFile = File(..., description="PDF file"),
    template_id: Optional[str] = Form(None, description="Template ID (None for auto-detection)")
):
    """
    Extract structured data using document template (e.g., e-fatura)
    
    Auto-detects document type if template_id is not provided.
    """
    temp_file_path = None
    
    try:
        # Validate file
        validate_pdf_file(file)
        
        # Save uploaded file
        unique_filename = generate_unique_filename(file.filename, prefix="template")
        temp_file_path = Path(settings.UPLOAD_FOLDER) / unique_filename
        save_upload_file(file, temp_file_path)
        
        # Validate file size
        validate_file_size(temp_file_path)
        
        # Extract using template
        analyzer = PDFAnalyzer(temp_file_path)
        result = analyzer.extract_with_template(template_id=template_id)
        
        return JSONResponse(content=result)
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PDFAnalyzerError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Cleanup
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except:
                pass


@app.get("/api/v1/templates", tags=["Template Extraction"])
async def get_available_templates():
    """
    Get list of available document templates
    
    Returns available templates like e-fatura, invoice, etc.
    """
    try:
        from app.services.document_templates import template_manager
        templates = template_manager.get_available_templates()
        
        return JSONResponse(content={
            "status": "success",
            "templates": templates,
            "count": len(templates)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting templates: {str(e)}")


@app.post("/api/v1/extract/custom", tags=["Custom Extraction"])
async def extract_custom(
    file: UploadFile = File(..., description="PDF file"),
    template: str = Form(..., description="Custom template JSON schema")
):
    """
    Extract data using custom template
    
    Custom template allows users to define their own extraction fields with regex, LLM, or fuzzy methods.
    """
    temp_file_path = None
    
    try:
        import json
        
        # Validate file
        validate_pdf_file(file)
        
        # Parse template
        try:
            template_schema = json.loads(template)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON template: {str(e)}")
        
        # Validate template schema
        if not template_schema.get("template_name"):
            raise HTTPException(status_code=400, detail="Template must have 'template_name'")
        if not template_schema.get("fields"):
            raise HTTPException(status_code=400, detail="Template must have at least one field")
        
        # Save uploaded file
        unique_filename = generate_unique_filename(file.filename, prefix="custom")
        temp_file_path = Path(settings.UPLOAD_FOLDER) / unique_filename
        save_upload_file(file, temp_file_path)
        
        # Validate file size
        validate_file_size(temp_file_path)
        
        # Extract using custom template
        from app.services.custom_extractor import CustomExtractor
        extractor = CustomExtractor(temp_file_path)
        result = extractor.extract_with_schema(template_schema)
        
        return JSONResponse(content=result)
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PDFAnalyzerError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Custom extraction error: {str(e)}")
    finally:
        # Cleanup
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except:
                pass


@app.post("/api/v1/generate-regex", tags=["Tools"])
async def generate_regex(
    description: str = Form(..., description="What you want to extract")
):
    """
    Generate regex pattern from natural language description using LLM (Qwen3 0.6B)
    
    Note: Small LLM may not always generate perfect patterns. Consider upgrading to larger model for better results.
    
    Example: "invoice number that starts with INV followed by 6 digits"
    Returns: {"pattern": "INV\\d{6}", "explanation": "..."}
    """
    try:
        from app.services.llm_extractor import llm_extractor
        
        if not llm_extractor.model or not llm_extractor.tokenizer:
            raise HTTPException(
                status_code=503,
                detail="LLM service not available. Regex generation requires LLM model."
            )
        
        # Generate regex using LLM
        result = llm_extractor.generate_regex(description)
        
        if not result:
            raise HTTPException(
                status_code=422,
                detail="Could not generate regex pattern. Try a more specific description."
            )
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regex generation error: {str(e)}")


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

