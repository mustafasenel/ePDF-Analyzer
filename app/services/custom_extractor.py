"""Custom template-based extraction service"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from difflib import SequenceMatcher

from app.services.pdf_reader import PDFReader
from app.services.table_extractor import TableExtractor
from app.services.llm_extractor import llm_extractor


class CustomExtractor:
    """
    Custom extraction based on user-defined template schema.
    
    Supports three extraction methods:
    - regex: Pattern-based extraction
    - llm: LLM-based extraction
    - fuzzy: Fuzzy matching based extraction
    """
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.pdf_reader = PDFReader(pdf_path)
        self.table_extractor = TableExtractor(pdf_path)
    
    def extract_with_schema(self, template_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data based on custom template schema"""
        
        # Open PDF
        self.pdf_reader.open()
        
        try:
            # Extract full text (returns dict of page_num: text)
            text_dict = self.pdf_reader.extract_text()
            
            # Combine all pages into single text
            if isinstance(text_dict, dict):
                full_text = '\n\n'.join(text_dict.values())
            else:
                full_text = text_dict
            
            # Clean text encoding issues
            full_text = self._clean_text_encoding(full_text)
            
            # Extract text regions if needed for LLM
            text_regions_raw = self.pdf_reader.extract_text_regions()
            
            # Convert regions to text strings and clean encoding
            text_regions = {}
            for region_name, blocks in text_regions_raw.items():
                region_text = '\n'.join(block.get('text', '') for block in blocks)
                text_regions[region_name] = self._clean_text_encoding(region_text)
            
            # Extract tables if needed
            tables_raw = self.table_extractor.extract_all_tables()
            
            # Convert tables to dict format
            tables_dict = {}
            if tables_raw:
                for page_num, page_tables in tables_raw.items():
                    page_key = f"page_{page_num}"
                    tables_dict[page_key] = [
                        self.table_extractor.table_to_dict(df) for df in page_tables
                    ]
            
            # Initialize result
            result = {
                "template_name": template_schema.get("template_name"),
                "description": template_schema.get("description"),
                "extraction_date": datetime.now().isoformat(),
                "data": {}
            }
            
            # Process each field
            for field in template_schema.get("fields", []):
                field_name = field.get("name")
                method = field.get("method", "llm")  # Default to LLM
                
                if method == "regex":
                    value = self._extract_with_regex(field, full_text)
                elif method == "fuzzy":
                    value = self._extract_with_fuzzy(field, full_text)
                else:  # llm (default)
                    value = self._extract_field_llm(field, full_text, text_regions)
                
                result["data"][field_name] = value
            
            # Process tables if defined
            if template_schema.get("tables"):
                result["tables"] = self._extract_tables(template_schema.get("tables", []), tables_dict)
            
            return result
            
        finally:
            # Always close PDF
            self.pdf_reader.close()
    
    def _clean_text_encoding(self, text: str) -> str:
        """
        Clean text encoding issues from PDF extraction
        
        Common issues:
        - Unicode replacement character (�)
        - Various dash/hyphen encodings
        - Ligatures (fi, fl, etc.)
        - Smart quotes
        """
        if not text:
            return text
        
        # Replace unicode replacement character and similar
        text = text.replace('\ufffd', '-')  # Unicode replacement char
        text = text.replace('�', '-')
        
        # Normalize dashes and hyphens
        text = text.replace('\u2010', '-')  # Hyphen
        text = text.replace('\u2011', '-')  # Non-breaking hyphen
        text = text.replace('\u2012', '-')  # Figure dash
        text = text.replace('\u2013', '-')  # En dash
        text = text.replace('\u2014', '-')  # Em dash
        text = text.replace('\u2015', '-')  # Horizontal bar
        
        # Normalize quotes
        text = text.replace('\u2018', "'")  # Left single quote
        text = text.replace('\u2019', "'")  # Right single quote
        text = text.replace('\u201a', "'")  # Single low quote
        text = text.replace('\u201c', '"')  # Left double quote
        text = text.replace('\u201d', '"')  # Right double quote
        text = text.replace('\u201e', '"')  # Double low quote
        
        # Common ligatures
        text = text.replace('\ufb01', 'fi')
        text = text.replace('\ufb02', 'fl')
        
        # Remove any remaining control characters except newlines and tabs
        import unicodedata
        text = ''.join(
            char if char in '\n\r\t' or not unicodedata.category(char).startswith('C')
            else '-' if unicodedata.category(char) == 'Cc' else ''
            for char in text
        )
        
        return text
    
    def _extract_with_regex(self, field: Dict[str, Any], text: str) -> Optional[str]:
        """Extract field value using regex patterns"""
        patterns = field.get("patterns", [])
        
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    if match.groups():
                        value = match.group(1).strip()
                    else:
                        value = match.group(0).strip()
                    
                    return self._convert_type(value, field.get("type", "string"), field)
            except re.error:
                continue
        
        return None
    
    def _extract_with_fuzzy(self, field: Dict[str, Any], text: str) -> Optional[str]:
        """Extract field value using fuzzy matching"""
        keywords = field.get("keywords", [])
        
        lines = text.split('\n')
        best_match = None
        best_score = 0.0
        
        for line in lines:
            for keyword in keywords:
                similarity = SequenceMatcher(None, keyword.lower(), line.lower()).ratio()
                
                if similarity > best_score and similarity > 0.6:
                    best_score = similarity
                    pattern = rf"{re.escape(keyword)}\s*[:=\-]?\s*(.+?)(?:\n|$)"
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        best_match = match.group(1).strip()
                    else:
                        best_match = line.strip()
        
        if best_match:
            return self._convert_type(best_match, field.get("type", "string"), field)
        
        return None
    
    def _extract_field_llm(self, field: Dict[str, Any], text: str, text_regions: Optional[Dict[str, str]] = None) -> Any:
        """
        Extract field value using LLM based on field schema
        
        Args:
            field: Field schema with name, type, description, properties, etc.
            text: Full document text
            text_regions: Optional dict of text by region
            
        Returns:
            Extracted value in correct type
        """
        field_name = field.get("name")
        field_type = field.get("type", "string")
        description = field.get("description", "")
        custom_prompt = field.get("prompt", "")
        region = field.get("region")
        
        # Select text based on region
        if region and text_regions and region in text_regions:
            text_to_analyze = text_regions[region]
        else:
            # Limit text for LLM (first 3000 chars for performance)
            text_to_analyze = text[:3000]
        
        # Use custom prompt if provided, otherwise generate automatic prompt
        if custom_prompt:
            prompt = custom_prompt
        else:
            # Build prompt based on field schema
            if field_type == "object" and field.get("properties"):
                # For nested objects, extract all properties
                prompt = f"Extract '{field_name}' data"
                if description:
                    prompt += f" ({description})"
                prompt += " as JSON with these fields: "
                prop_names = [p.get("name") for p in field.get("properties", [])]
                prompt += ", ".join(prop_names)
            elif field_type == "array":
                # For arrays, explain what to extract
                prompt = f"Extract all '{field_name}' items"
                if description:
                    prompt += f" ({description})"
                prompt += " as a list"
            else:
                # Simple field extraction
                prompt = f"Extract '{field_name}'"
                if description:
                    prompt += f" ({description})"
        
        try:
            result = llm_extractor.extract_field(text_to_analyze, prompt)
            
            # Type conversion
            if result:
                return self._convert_type(result, field_type, field)
            
            return None
        except Exception as e:
            print(f"LLM extraction error for field {field_name}: {e}")
            return None
    
    def _extract_tables(
        self, 
        table_schemas: List[Dict[str, Any]], 
        extracted_tables: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Extract and match tables based on schema"""
        result = {}
        
        for table_schema in table_schemas:
            table_name = table_schema.get("name")
            keywords = table_schema.get("keywords", [])
            min_columns = table_schema.get("min_columns", 2)
            
            # Find matching table
            matched_table = None
            
            for page_tables in extracted_tables.values():
                for table in page_tables:
                    # Check column count
                    if table.get("col_count", 0) < min_columns:
                        continue
                    
                    # Check keywords in headers or rows
                    headers = table.get("headers", []) or []
                    rows = table.get("rows", []) or []
                    
                    table_text = ' '.join(str(h) for h in headers).lower()
                    if rows and len(rows) > 0:
                        table_text += ' ' + ' '.join(str(cell) for row in rows[:3] for cell in row).lower()
                    
                    # Count keyword matches
                    keyword_matches = sum(1 for kw in keywords if kw.lower() in table_text)
                    
                    if keyword_matches >= len(keywords) * 0.5:  # At least 50% of keywords
                        matched_table = table
                        break
                
                if matched_table:
                    break
            
            if matched_table:
                result[table_name] = {
                    "headers": matched_table.get("headers", []),
                    "rows": matched_table.get("rows", []),
                    "row_count": matched_table.get("row_count", 0),
                    "col_count": matched_table.get("col_count", 0)
                }
            else:
                result[table_name] = None
        
        return result
    
    def _convert_type(self, value: str, field_type: str, field: Optional[Dict[str, Any]] = None) -> Any:
        """Convert extracted value to specified type"""
        if value is None:
            return None
        
        try:
            if field_type == "number":
                # Remove common formatting
                cleaned = re.sub(r'[^\d,.-]', '', value)
                cleaned = cleaned.replace(',', '.')
                return float(cleaned)
            elif field_type == "boolean":
                # Convert to boolean
                value_lower = str(value).lower().strip()
                return value_lower in ['true', 'yes', '1', 'evet', 'var']
            elif field_type == "array":
                # Try to parse as JSON array
                try:
                    import json
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                except:
                    pass
                # Fallback: split by common delimiters
                if ',' in value:
                    return [item.strip() for item in value.split(',') if item.strip()]
                elif '\n' in value:
                    return [item.strip() for item in value.split('\n') if item.strip()]
                else:
                    return [value]
            elif field_type == "object":
                # Try to parse as JSON object
                try:
                    import json
                    parsed = json.loads(value)
                    if isinstance(parsed, dict):
                        return parsed
                except:
                    pass
                # Fallback: return as raw value
                return {"value": value}
            else:  # string
                return value
        except:
            return value

