"""Main PDF analyzer orchestrating all services"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from .pdf_reader import PDFReader, PDFReaderError
from .table_extractor import TableExtractor, TableExtractionError
from .export_manager import ExportManager, ExportError
from .document_templates import template_manager
from config.settings import settings


class PDFAnalyzerError(Exception):
    """PDF analyzer error"""
    pass


class PDFAnalyzer:
    """
    Main orchestrator for PDF analysis
    Coordinates PDFReader, TableExtractor, and ExportManager
    """
    
    def __init__(self, pdf_path: str | Path):
        """
        Initialize PDF analyzer
        
        Args:
            pdf_path: Path to PDF file
        """
        self.pdf_path = Path(pdf_path)
        
        if not self.pdf_path.exists():
            raise PDFAnalyzerError(f"PDF file not found: {pdf_path}")
        
        # Initialize services
        self.reader = PDFReader(pdf_path)
        self.table_extractor = TableExtractor(pdf_path)
        self.export_manager = ExportManager()
    
    def analyze_full(
        self,
        extract_text: bool = True,
        extract_tables: bool = True,
        preserve_layout: bool = False,
        table_method: str = "pdfplumber"
    ) -> Dict[str, Any]:
        """
        Perform full analysis: metadata + text + tables
        
        Args:
            extract_text: Whether to extract text
            extract_tables: Whether to extract tables
            preserve_layout: Preserve text layout
            table_method: Table extraction method
            
        Returns:
            Dictionary with complete analysis results
        """
        start_time = time.time()
        
        try:
            with self.reader:
                # Get metadata
                metadata = self.reader.get_metadata()
                
                # Extract text if requested
                text_data = None
                if extract_text:
                    if preserve_layout:
                        # Extract with layout (slower)
                        text_data = {}
                        for page_num in range(1, metadata['page_count'] + 1):
                            layout_data = self.reader.extract_text_with_layout(page_num)
                            text_data[page_num] = layout_data['text']
                    else:
                        # Simple text extraction (faster)
                        text_data = self.reader.extract_text()
                
                # Extract tables if requested
                tables = None
                if extract_tables:
                    tables = self.table_extractor.extract_all_tables(method=table_method)
                
                # Check for images
                has_images = self.reader.has_images()
            
            # Calculate statistics
            total_chars = sum(len(text) for text in (text_data or {}).values())
            total_tables = sum(len(page_tables) for page_tables in (tables or {}).values())
            pages_with_tables = sorted(tables.keys()) if tables else []
            
            statistics = {
                "total_pages": metadata['page_count'],
                "total_tables": total_tables,
                "total_chars": total_chars,
                "has_images": has_images,
                "pages_with_tables": pages_with_tables
            }
            
            # Convert tables to dict format
            tables_dict = None
            if tables:
                tables_dict = {}
                for page_num, page_tables in tables.items():
                    page_key = f"page_{page_num}"
                    tables_dict[page_key] = [
                        self.table_extractor.table_to_dict(df) for df in page_tables
                    ]
            
            # Convert text to dict format with string keys
            text_dict = None
            if text_data:
                text_dict = {f"page_{k}": v for k, v in text_data.items()}
            
            processing_time = time.time() - start_time
            
            return {
                "status": "success",
                "metadata": metadata,
                "text": text_dict,
                "tables": tables_dict,
                "statistics": statistics,
                "processing_time": round(processing_time, 2)
            }
            
        except PDFReaderError as e:
            raise PDFAnalyzerError(f"PDF reading error: {str(e)}")
        except TableExtractionError as e:
            raise PDFAnalyzerError(f"Table extraction error: {str(e)}")
        except Exception as e:
            raise PDFAnalyzerError(f"Analysis error: {str(e)}")
    
    def extract_basic_analysis(self) -> Dict[str, Any]:
        """
        Extract basic data from PDF: text + tables per page, no interpretation
        
        Returns:
            Dictionary with page-by-page data (no inference or template matching)
        """
        start_time = time.time()
        
        try:
            with self.reader:
                page_count = self.reader.get_page_count()
                metadata = self.reader.get_metadata()
                
                pages_data = []
                
                for page_num in range(1, page_count + 1):
                    # Extract text
                    text = self.reader.extract_text(page_num)
                    
                    # Extract tables (no need to open/close for each page)
                    tables_df = self.table_extractor.extract_tables_from_page(page_num)
                    
                    # Convert DataFrames to dicts
                    tables = [
                        self.table_extractor.table_to_dict(df) 
                        for df in tables_df
                    ] if tables_df else []
                    
                    page_data = {
                        "page_number": page_num,
                        "text": text,
                        "tables": tables,
                        "table_count": len(tables),
                        "text_length": len(text) if text else 0
                    }
                    
                    pages_data.append(page_data)
                
                processing_time = time.time() - start_time
                
                return {
                    "status": "success",
                    "filename": self.pdf_path.name,
                    "page_count": page_count,
                    "metadata": metadata,
                    "pages": pages_data,
                    "processing_time": round(processing_time, 2)
                }
                
        except Exception as e:
            raise PDFAnalyzerError(f"Basic analysis error: {e}")
    
    def extract_text_only(
        self,
        pages: Optional[List[int]] = None,
        preserve_layout: bool = False
    ) -> Dict[str, Any]:
        """
        Extract only text from PDF
        
        Args:
            pages: Specific pages to extract (None for all)
            preserve_layout: Preserve text layout
            
        Returns:
            Dictionary with text data
        """
        start_time = time.time()
        
        try:
            with self.reader:
                page_count = self.reader.get_page_count()
                
                # Determine which pages to process
                if pages:
                    pages_to_process = pages
                else:
                    pages_to_process = list(range(1, page_count + 1))
                
                text_data = {}
                
                for page_num in pages_to_process:
                    # Always use extract_text - it maintains proper order
                    # For layout, we'll use a different approach in the reader
                    text_data[page_num] = self.reader.extract_text(page_num, preserve_layout=preserve_layout)
            
            # Calculate total character count
            total_chars = sum(len(text) for text in text_data.values())
            
            # Create all_text
            all_text = "\n\n".join(text_data[page] for page in sorted(text_data.keys()))
            
            # Convert to string keys for JSON
            text_dict = {f"page_{k}": v for k, v in text_data.items()}
            
            processing_time = time.time() - start_time
            
            return {
                "status": "success",
                "text": text_dict,
                "all_text": all_text,
                "char_count": total_chars,
                "page_count": len(text_data),
                "processing_time": round(processing_time, 2)
            }
            
        except PDFReaderError as e:
            raise PDFAnalyzerError(f"Text extraction error: {str(e)}")
        except Exception as e:
            raise PDFAnalyzerError(f"Extraction error: {str(e)}")
    
    def extract_tables_only(
        self,
        pages: Optional[List[int]] = None,
        method: str = "pdfplumber",
        assume_first_row_header: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Extract only tables from PDF
        
        Args:
            pages: Specific pages to extract (None for all)
            method: Table extraction method
            assume_first_row_header: Force header detection
            
        Returns:
            Dictionary with table data
        """
        start_time = time.time()
        
        try:
            # Extract tables
            tables = self.table_extractor.extract_all_tables(
                method=method, 
                pages=pages,
                assume_first_row_header=assume_first_row_header
            )
            
            # Convert to dict format
            tables_dict = {}
            for page_num, page_tables in tables.items():
                page_key = f"page_{page_num}"
                tables_dict[page_key] = [
                    self.table_extractor.table_to_dict(df) for df in page_tables
                ]
            
            # Calculate total
            total_tables = sum(len(page_tables) for page_tables in tables.values())
            
            # Get page count for context
            with self.reader:
                total_pages = self.reader.get_page_count()
            
            processing_time = time.time() - start_time
            
            return {
                "status": "success",
                "tables": tables_dict,
                "total_tables": total_tables,
                "page_count": total_pages,
                "processing_time": round(processing_time, 2)
            }
            
        except TableExtractionError as e:
            raise PDFAnalyzerError(f"Table extraction error: {str(e)}")
        except Exception as e:
            raise PDFAnalyzerError(f"Extraction error: {str(e)}")
    
    def export_as_excel(
        self,
        output_path: str | Path,
        include_text: bool = True,
        add_styling: bool = True
    ) -> str:
        """
        Export PDF content as Excel file
        
        Args:
            output_path: Output file path
            include_text: Include text in separate sheet
            add_styling: Add styling to Excel
            
        Returns:
            Path to created Excel file
        """
        try:
            # Extract data
            with self.reader:
                text_data = self.reader.extract_text() if include_text else None
            
            tables = self.table_extractor.extract_all_tables()
            
            if not tables:
                raise PDFAnalyzerError("No tables found in PDF")
            
            # Export to Excel
            excel_path = self.export_manager.export_to_excel(
                tables=tables,
                output_path=output_path,
                include_text=include_text,
                text_data=text_data,
                add_styling=add_styling
            )
            
            return excel_path
            
        except ExportError as e:
            raise PDFAnalyzerError(f"Excel export error: {str(e)}")
        except Exception as e:
            raise PDFAnalyzerError(f"Export error: {str(e)}")
    
    def export_as_json(
        self,
        output_path: Optional[str | Path] = None,
        include_text: bool = True,
        include_tables: bool = True,
        pretty: bool = True
    ) -> str | Dict:
        """
        Export PDF content as JSON
        
        Args:
            output_path: Output file path (None to return as string)
            include_text: Include text extraction
            include_tables: Include table extraction
            pretty: Pretty print JSON
            
        Returns:
            JSON string or file path
        """
        try:
            # Extract data
            with self.reader:
                metadata = self.reader.get_metadata()
                text_data = self.reader.extract_text() if include_text else None
            
            tables = self.table_extractor.extract_all_tables() if include_tables else None
            
            # Create combined output
            combined_data = self.export_manager.create_combined_output(
                metadata=metadata,
                text_data=text_data,
                tables=tables
            )
            
            # Export to JSON
            return self.export_manager.export_to_json(
                data=combined_data,
                output_path=output_path,
                pretty=pretty
            )
            
        except ExportError as e:
            raise PDFAnalyzerError(f"JSON export error: {str(e)}")
        except Exception as e:
            raise PDFAnalyzerError(f"Export error: {str(e)}")
    
    def export_tables_as_csv(
        self,
        output_dir: str | Path,
        prefix: str = "table"
    ) -> List[str]:
        """
        Export tables as individual CSV files
        
        Args:
            output_dir: Output directory
            prefix: Filename prefix
            
        Returns:
            List of created CSV file paths
        """
        try:
            # Extract tables
            tables = self.table_extractor.extract_all_tables()
            
            if not tables:
                raise PDFAnalyzerError("No tables found in PDF")
            
            # Export to CSV
            csv_files = self.export_manager.export_tables_to_csv(
                tables=tables,
                output_dir=output_dir,
                prefix=prefix
            )
            
            return csv_files
            
        except ExportError as e:
            raise PDFAnalyzerError(f"CSV export error: {str(e)}")
        except Exception as e:
            raise PDFAnalyzerError(f"Export error: {str(e)}")
    
    def extract_with_template(
        self,
        template_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data using document template
        
        Args:
            template_id: Specific template ID to use, or None for auto-detection
            
        Returns:
            Structured data according to template
        """
        start_time = time.time()
        
        try:
            # Extract text
            with self.reader:
                text_data = self.reader.extract_text()
            
            # Combine all text
            full_text = "\n\n".join(str(text_data[page]) for page in sorted(text_data.keys()))
            
            # Auto-detect document type if not specified
            if not template_id:
                template_id = template_manager.detect_document_type(full_text)
                if not template_id:
                    raise PDFAnalyzerError(
                        "Could not auto-detect document type. Please specify template_id."
                    )
            
            # Extract sender/recipient blocks (from first page)
            sender_recipient_blocks = None
            try:
                with self.reader:
                    sender_recipient_blocks = self.reader.extract_sender_recipient_blocks(page_num=0)
            except Exception as e:
                print(f"Sender/recipient extraction failed: {e}")
            
            # Extract invoice metadata (from first page)
            invoice_metadata = None
            try:
                with self.reader:
                    invoice_metadata = self.reader.extract_invoice_metadata(page_num=0)
            except Exception as e:
                print(f"Invoice metadata extraction failed: {e}")
            
            # Extract tables for template
            try:
                tables_raw = self.table_extractor.extract_all_tables()
                # Convert to dict format for template
                tables_for_template = []
                for page_num, page_tables in tables_raw.items():
                    for df in page_tables:
                        tables_for_template.append(
                            self.table_extractor.table_to_dict(df)
                        )
            except:
                tables_for_template = []
            
            # Extract using template
            result = template_manager.extract_data(
                template_id=template_id,
                text=full_text,
                tables=tables_for_template,
                sender_recipient_blocks=sender_recipient_blocks,
                invoice_metadata=invoice_metadata
            )
            
            processing_time = time.time() - start_time
            result["processing_time"] = round(processing_time, 2)
            result["status"] = "success"
            
            return result
            
        except PDFReaderError as e:
            print(f"❌ PDFReaderError in template extraction: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise PDFAnalyzerError(f"Text extraction error: {str(e)}")
        except Exception as e:
            print(f"❌ Exception in template extraction: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise PDFAnalyzerError(f"Template extraction error: {str(e)}")
    
    def get_available_templates(self) -> List[Dict[str, str]]:
        """
        Get list of available document templates
        
        Returns:
            List of template info
        """
        return template_manager.get_available_templates()

