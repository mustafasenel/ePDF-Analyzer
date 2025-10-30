"""Table extraction from PDFs using pdfplumber and camelot"""

import pdfplumber
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal

# Camelot removed - using only pdfplumber

from config.settings import settings


class TableExtractionError(Exception):
    """Table extraction error"""
    pass


class TableExtractor:
    """
    Extract tables from PDF using pdfplumber or camelot
    """
    
    def __init__(self, pdf_path: str | Path):
        """
        Initialize table extractor
        
        Args:
            pdf_path: Path to PDF file
        """
        self.pdf_path = Path(pdf_path)
        
        if not self.pdf_path.exists():
            raise TableExtractionError(f"PDF file not found: {pdf_path}")
    
    def detect_tables(self, method: str = "pdfplumber") -> Dict[int, int]:
        """
        Detect which pages contain tables
        
        Args:
            method: Detection method (only "pdfplumber" supported)
            
        Returns:
            Dictionary mapping page numbers to table counts
            Example: {1: 2, 3: 1} means page 1 has 2 tables, page 3 has 1 table
        """
        if method != "pdfplumber":
            raise TableExtractionError(f"Only pdfplumber is supported, got: {method}")
        
        return self._detect_tables_pdfplumber()
    
    def _detect_tables_pdfplumber(self) -> Dict[int, int]:
        """Detect tables using pdfplumber"""
        page_tables = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.find_tables()
                if tables:
                    page_tables[page_num] = len(tables)
        
        return page_tables
    
    def extract_tables_from_page(
        self,
        page_num: int,
        method: str = "pdfplumber",
        auto_detect_header: bool = True,
        assume_first_row_header: Optional[bool] = None
    ) -> List[pd.DataFrame]:
        """
        Extract tables from a specific page
        
        Args:
            page_num: Page number (1-indexed)
            method: Extraction method (only "pdfplumber" supported)
            auto_detect_header: Auto-detect if first row is header (default True)
            assume_first_row_header: Force header detection (True=has header, False=no header, None=auto)
            
        Returns:
            List of DataFrames, one per table
        """
        if method != "pdfplumber":
            raise TableExtractionError(f"Only pdfplumber is supported, got: {method}")
        
        return self._extract_tables_pdfplumber(page_num, auto_detect_header, assume_first_row_header)
    
    def _extract_tables_pdfplumber(
        self, 
        page_num: int,
        auto_detect_header: bool = True,
        assume_first_row_header: Optional[bool] = None
    ) -> List[pd.DataFrame]:
        """Extract tables using pdfplumber"""
        dataframes = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            if page_num < 1 or page_num > len(pdf.pages):
                raise TableExtractionError(
                    f"Invalid page number: {page_num}. Valid range: 1-{len(pdf.pages)}"
                )
            
            page = pdf.pages[page_num - 1]  # Convert to 0-indexed
            tables = page.extract_tables()
            
            for table in tables:
                if table and len(table) >= settings.TABLE_MIN_ROWS:
                    # Determine header strategy
                    if assume_first_row_header is not None:
                        # User explicitly specified
                        has_header = assume_first_row_header
                    elif auto_detect_header:
                        # Auto-detect
                        has_header = self._detect_header(table)
                    else:
                        # Default: no header
                        has_header = False
                    
                    if has_header:
                        # Use first row as header
                        df = pd.DataFrame(table[1:], columns=table[0])
                    else:
                        # No header, create generic column names
                        df = pd.DataFrame(table)
                        df.columns = [f"Column_{i+1}" for i in range(len(df.columns))]
                    
                    # Clean DataFrame
                    df = self._clean_dataframe(df)
                    
                    # Store metadata about header
                    df.attrs['has_header'] = has_header
                    
                    # Only add if it meets minimum column requirement
                    if len(df.columns) >= settings.TABLE_MIN_COLS:
                        dataframes.append(df)
        
        return dataframes
    
    def extract_all_tables(
        self,
        method: str = "pdfplumber",
        pages: Optional[List[int]] = None,
        auto_detect_header: bool = True,
        assume_first_row_header: Optional[bool] = None
    ) -> Dict[int, List[pd.DataFrame]]:
        """
        Extract all tables from PDF
        
        Args:
            method: Extraction method
            pages: Specific pages to process (None for all pages)
            auto_detect_header: Auto-detect if first row is header
            assume_first_row_header: Force header detection (overrides auto_detect)
            
        Returns:
            Dictionary mapping page numbers to list of DataFrames
        """
        # First detect which pages have tables
        page_tables = self.detect_tables(method=method)
        
        # Filter by requested pages if specified
        if pages:
            page_tables = {p: c for p, c in page_tables.items() if p in pages}
        
        # Extract tables from each page
        all_tables = {}
        for page_num in page_tables.keys():
            try:
                tables = self.extract_tables_from_page(
                    page_num, 
                    method=method,
                    auto_detect_header=auto_detect_header,
                    assume_first_row_header=assume_first_row_header
                )
                if tables:
                    all_tables[page_num] = tables
            except Exception as e:
                # Log error but continue with other pages
                print(f"Warning: Failed to extract tables from page {page_num}: {str(e)}")
                continue
        
        return all_tables
    
    def table_to_dict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Convert DataFrame to JSON-friendly dictionary
        
        Each row is converted to a dictionary with column names as keys.
        This prevents data shifting issues when cells are empty.
        
        Args:
            df: DataFrame to convert
            
        Returns:
            Dictionary with headers, rows (as list of dicts), and metadata
        """
        # Ensure it's actually a DataFrame
        if not isinstance(df, pd.DataFrame):
            raise TableExtractionError(f"Expected DataFrame, got {type(df)}")
        
        # Handle empty DataFrame
        if df.empty or len(df.columns) == 0:
            return {
                "has_header": False,
                "headers": None,
                "rows": [],
                "row_count": 0,
                "col_count": 0,
                "note": "Empty table"
            }
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Get original headers
        original_headers = df.columns.tolist()
        
        # Check for duplicate or invalid column names
        # This happens when headers are "None", empty, or duplicated
        has_duplicates = len(original_headers) != len(set(original_headers))
        has_none_or_empty = any(
            str(h).lower() in ['none', 'nan', ''] or pd.isna(h) 
            for h in original_headers
        )
        
        if has_duplicates or has_none_or_empty:
            # Assign unique generic column names
            df.columns = [f"Column_{i+1}" for i in range(len(df.columns))]
            headers = df.columns.tolist()
            # Force has_header to False since we had to fix the headers
            has_header = False
            note = "Table had duplicate or invalid column names, generic names were assigned"
        else:
            headers = original_headers
            has_header = df.attrs.get('has_header', True)
            note = None
        
        # Convert rows to list of dictionaries (prevents shifting if cell is empty)
        rows = df.to_dict('records')  # Each row becomes {col1: val1, col2: val2, ...}
        
        result = {
            "has_header": has_header,
            "headers": headers,
            "rows": rows,
            "row_count": len(df),
            "col_count": len(df.columns)
        }
        
        # Add note if any
        if note:
            result["note"] = note
        elif not has_header:
            result["note"] = "Table has no header row, generic column names were assigned"
        
        return result
    
    def tables_to_dict(self, tables: Dict[int, List[pd.DataFrame]]) -> Dict[str, List[Dict]]:
        """
        Convert all tables to dictionary format
        
        Args:
            tables: Dictionary of page numbers to DataFrames
            
        Returns:
            Dictionary with string keys (for JSON compatibility)
        """
        result = {}
        
        for page_num, page_tables in tables.items():
            page_key = f"page_{page_num}"
            result[page_key] = []
            
            for table_df in page_tables:
                result[page_key].append(self.table_to_dict(table_df))
        
        return result
    
    @staticmethod
    def _detect_header(table: List[List[Any]]) -> bool:
        """
        Detect if first row is header by comparing data types
        
        Logic: 
        1. Key-value tables (2 columns, all rows same pattern) -> NO HEADER
        2. If all rows have same data types in each column -> NO HEADER
        3. If first row has different data types than other rows -> HAS HEADER
        
        Args:
            table: Raw table data (list of lists)
            
        Returns:
            True if first row appears to be a header, False otherwise
        """
        if not table or len(table) < 2:
            return False
        
        first_row = table[0]
        data_rows = table[1:]
        
        if not first_row:
            return False
        
        # SPECIAL CASE: 2-column key-value tables
        # Pattern: "Label:" | "Value" in every row
        if len(first_row) == 2:
            # Check if first column contains labels (often ending with ":")
            first_col_values = [str(row[0]).strip() for row in table if row and len(row) >= 1]
            
            # If most values in first column end with ":" -> key-value table, NO HEADER
            colon_count = sum(1 for val in first_col_values if val.endswith(':'))
            if colon_count >= len(first_col_values) * 0.7:  # 70% or more have colons
                return False
            
            # Check if all rows have similar pattern (text | text or text | number)
            # This is key-value format, not a table with header
            all_rows_similar = True
            for row in table:
                if len(row) != 2:
                    continue
                # If both columns are non-empty in all rows -> likely key-value
                if not (row[0] and row[1]):
                    all_rows_similar = False
                    break
            
            if all_rows_similar and len(table) > 2:
                # Check if first row looks like a label (not a header)
                first_col_first = str(first_row[0]).strip().lower()
                # Common key-value labels
                kv_indicators = ['tarih', 'fatura', 'no', 'tutar', 'toplam', 'ödeme', 'kdv', 
                                 'matrah', 'vergi', 'iskonto', 'date', 'total', 'amount']
                if any(ind in first_col_first for ind in kv_indicators):
                    return False
        
        # Helper function to determine cell type
        def get_cell_type(cell):
            if not cell or str(cell).strip() == '':
                return 'empty'
            
            cell_str = str(cell).strip().replace(',', '').replace('.', '', 1).replace('-', '', 1).replace('+', '', 1)
            
            # Check if numeric (int or float)
            if cell_str.replace('.', '', 1).isdigit() or (cell_str[0] in ['-', '+'] and cell_str[1:].replace('.', '', 1).isdigit()):
                return 'number'
            
            # Check if it looks like a date
            if '/' in str(cell) or '-' in str(cell):
                parts = str(cell).replace('/', '-').split('-')
                if len(parts) >= 2 and any(p.isdigit() for p in parts):
                    return 'date'
            
            # Everything else is text
            return 'text'
        
        # Get types for each column in first row
        first_row_types = [get_cell_type(cell) for cell in first_row]
        
        # Get types for each column in data rows
        column_types_in_data = [[] for _ in range(len(first_row))]
        
        for row in data_rows[:5]:  # Check first 5 data rows for pattern
            if len(row) != len(first_row):
                continue  # Skip rows with different column count
            
            for col_idx, cell in enumerate(row):
                column_types_in_data[col_idx].append(get_cell_type(cell))
        
        # Compare first row types with data row types
        type_mismatches = 0
        
        for col_idx in range(len(first_row)):
            first_type = first_row_types[col_idx]
            data_types = column_types_in_data[col_idx]
            
            if not data_types:
                continue
            
            # Most common type in this column in data rows
            most_common_data_type = max(set(data_types), key=data_types.count)
            
            # If first row type differs from data rows type
            if first_type != most_common_data_type:
                # Text header with number data is classic header pattern
                if first_type == 'text' and most_common_data_type in ['number', 'date']:
                    type_mismatches += 1
        
        # If more than 50% of columns have type mismatch AND table has 3+ columns -> has header
        if type_mismatches > len(first_row) * 0.5 and len(first_row) >= 3:
            return True
        
        # For tables with 3+ columns, check for real header keywords
        # (exclude words that appear in key-value labels)
        if len(first_row) >= 3:
            real_header_keywords = [
                'sıra', 'sira', 'no', 'ad', 'soyad', 'isim', 'name', 
                'miktar', 'adet', 'quantity', 'birim', 'fiyat', 'price',
                'ürün', 'product', 'hizmet', 'açıklama', 'description', 
                'kategori', 'category', 'kod', 'code', 'durum', 'status'
            ]
            
            first_row_text = ' '.join([str(cell).lower() for cell in first_row if cell])
            keyword_matches = sum(1 for keyword in real_header_keywords if keyword in first_row_text)
            
            # If multiple header keywords found in first row -> likely header
            if keyword_matches >= 2:
                return True
        
        # Default: NO HEADER
        return False
    
    @staticmethod
    def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean DataFrame by removing empty rows/columns and standardizing
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        # Ensure it's actually a DataFrame
        if not isinstance(df, pd.DataFrame):
            raise TableExtractionError(f"Expected DataFrame, got {type(df)}")
        
        # If empty, return as is
        if df.empty or len(df.columns) == 0:
            return df
        
        # Make a copy
        df = df.copy()
        
        # Replace None with empty string
        df = df.fillna('')
        
        # Remove completely empty rows
        if not df.empty:
            df = df[df.astype(str).apply(lambda x: x.str.strip().str.len().sum(), axis=1) > 0]
        
        # Remove completely empty columns
        if not df.empty and len(df.columns) > 0:
            df = df.loc[:, df.astype(str).apply(lambda x: x.str.strip().str.len().sum(), axis=0) > 0]
        
        # Strip whitespace from all string values
        if not df.empty and len(df.columns) > 0:
            for col in df.columns:
                try:
                    if hasattr(df[col], 'dtype') and df[col].dtype == 'object':
                        df[col] = df[col].astype(str).str.strip()
                except Exception:
                    # If any column causes issues, skip it
                    continue
        
        # Reset index
        if not df.empty:
            df = df.reset_index(drop=True)
        
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        return df

