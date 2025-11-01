"""Custom template-based extraction service"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from difflib import SequenceMatcher

from app.services.pdf_reader import PDFReader
from app.services.table_extractor import TableExtractor
from app.services.llm_service import get_llm_service

# Get singleton LLM service instance
llm_service = get_llm_service()


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
    
    def _clean_template_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove unnecessary fields from template schema (id, return_as_list, etc.)
        These are only used by frontend, not needed for extraction
        """
        def clean_field(field: Dict[str, Any]) -> Dict[str, Any]:
            # Remove frontend-only fields
            cleaned = {k: v for k, v in field.items() if k not in ['id', 'return_as_list']}
            
            # Recursively clean nested properties
            if 'properties' in cleaned and isinstance(cleaned['properties'], list):
                cleaned['properties'] = [clean_field(prop) for prop in cleaned['properties']]
            
            # Recursively clean array items
            if 'items' in cleaned and isinstance(cleaned['items'], dict):
                cleaned['items'] = clean_field(cleaned['items'])
            
            return cleaned
        
        # Clean all fields in template
        cleaned_schema = schema.copy()
        if 'fields' in cleaned_schema:
            cleaned_schema['fields'] = [clean_field(field) for field in cleaned_schema['fields']]
        
        return cleaned_schema
    
    def extract_with_schema(self, template_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data based on custom template schema"""
        
        # Clean template schema (remove frontend-only fields)
        template_schema = self._clean_template_schema(template_schema)
        
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
            # Limit text for LLM - use more for arrays to capture all items
            if field_type == "array":
                text_to_analyze = text[:5000]  # More context for arrays
            else:
                text_to_analyze = text[:3000]  # Standard limit for other fields
        
        # Use custom prompt if provided, otherwise generate automatic prompt
        if custom_prompt:
            prompt = custom_prompt
        else:
            # Build prompt based on field schema - fully dynamic, NO EXAMPLES
            if field_type == "object" and field.get("properties"):
                # For nested objects, use description for context
                if description:
                    prompt = f"Extract {description}"
                else:
                    prompt = f"Extract '{field_name}'"
                
                # List field names and types with their descriptions
                props = field.get("properties", [])
                field_details = []
                has_numbers = False
                for p in props:
                    pname = p.get("name")
                    ptype = p.get("type", "string")
                    pdesc = p.get("prompt", "") or p.get("description", "")
                    if ptype == "number":
                        has_numbers = True
                    if pdesc:
                        field_details.append(f"{pname} ({ptype}): {pdesc}")
                    else:
                        field_details.append(f"{pname} ({ptype})")
                
                prompt += " as a JSON object with these fields:\n"
                prompt += "\n".join([f"- {detail}" for detail in field_details])
                prompt += "\n\nReturn actual extracted values, not placeholders."
                if has_numbers:
                    prompt += " For number type fields, return them as actual JSON numbers (e.g., 1962.5, not \"1962.5\"). Remove currency symbols and convert to numeric format."
                if description:
                    prompt += f" Only extract {description}, ignore other content."
                
            elif field_type == "array":
                # For arrays, be very explicit about what to extract
                if description:
                    # Use description as main context
                    prompt = f"Extract {description}"
                else:
                    prompt = f"Extract all '{field_name}' items"
                
                # Add detailed field descriptions if properties are defined
                if field.get("items") and field["items"].get("properties"):
                    props = field["items"].get("properties", [])
                    field_details = []
                    has_numbers = False
                    for p in props:
                        pname = p.get("name")
                        ptype = p.get("type", "string")
                        pdesc = p.get("prompt", "") or p.get("description", "")
                        if ptype == "number":
                            has_numbers = True
                        if pdesc:
                            field_details.append(f"{pname} ({ptype}): {pdesc}")
                        else:
                            field_details.append(f"{pname} ({ptype})")
                    
                    prompt += " as a JSON array. Each item must be a complete object with these fields:\n"
                    prompt += "\n".join([f"- {detail}" for detail in field_details])
                    prompt += "\n\nIMPORTANT: "
                    if description:
                        prompt += f"Only extract {description}, ignore other content. "
                    if has_numbers:
                        prompt += "For number type fields, return them as actual JSON numbers (e.g., 1962.5, not \"1962.5\" or \"1.962,50\"). Remove currency symbols and convert to numeric format. "
                    prompt += "Return a valid JSON array of objects, not individual strings."
                else:
                    prompt += " as a JSON array."
                    if description:
                        prompt += f" Only extract {description}, ignore other content."
                    
            elif field_type == "number":
                # For numbers, tell LLM to return as JSON number
                prompt = f"Extract '{field_name}'"
                if description:
                    prompt += f" ({description})"
                prompt += " as a NUMBER. Return only the numeric value in standard format (e.g., 1962.5, not \"1.962,50\" or \"1962.5\"). Remove currency symbols, units, and convert to numeric format."
                    
            else:
                # Simple field extraction
                prompt = f"Extract '{field_name}'"
                if description:
                    prompt += f" ({description})"
                prompt += ". Return the actual extracted value from the document."
        
        try:
            result = llm_service.extract_field(text_to_analyze, prompt)
            
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
                # LLM should return numbers directly, but fallback to conversion if needed
                if not value or value.strip() == '':
                    return None
                
                # If already a number, return it
                if isinstance(value, (int, float)):
                    return float(value)
                
                # Fallback: Try to parse string (LLM might return string sometimes)
                cleaned = str(value).strip()
                
                # Remove currency symbols and units
                cleaned = re.sub(r'\s*(TL|₺|EUR|USD|\$|€|Adet|adet|ADET)\s*', '', cleaned)
                
                # Remove all non-numeric except comma, dot, minus
                cleaned = re.sub(r'[^\d,.-]', '', cleaned)
                
                if not cleaned:
                    print(f"⚠️  Empty value after cleaning: '{value}'")
                    return None
                
                # Auto-detect format and convert
                try:
                    # If has both comma and dot, detect which is decimal separator
                    if ',' in cleaned and '.' in cleaned:
                        last_comma = cleaned.rfind(',')
                        last_dot = cleaned.rfind('.')
                        if last_comma > last_dot:
                            # Turkish: 1.234,56
                            cleaned = cleaned.replace('.', '').replace(',', '.')
                        else:
                            # English: 1,234.56
                            cleaned = cleaned.replace(',', '')
                    elif ',' in cleaned:
                        # Only comma - Turkish decimal
                        cleaned = cleaned.replace(',', '.')
                    
                    return float(cleaned)
                except ValueError:
                    print(f"⚠️  Could not convert '{value}' to number (cleaned: '{cleaned}')")
                    return None
            elif field_type == "boolean":
                # Convert to boolean
                value_lower = str(value).lower().strip()
                return value_lower in ['true', 'yes', '1', 'evet', 'var']
            elif field_type == "array":
                # Clean markdown code blocks from LLM response
                cleaned_value = self._clean_markdown_json(value)
                
                # Try to parse as JSON array
                try:
                    import json
                    parsed = json.loads(cleaned_value)
                    if isinstance(parsed, list):
                        # Apply type conversion to array items if schema is defined
                        if field and field.get("items") and field["items"].get("properties"):
                            item_properties = field["items"].get("properties", [])
                            parsed = [self._convert_nested_types(item, item_properties) for item in parsed if isinstance(item, dict)]
                        return parsed
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON array parsing failed: {e}")
                    print(f"   Cleaned value length: {len(cleaned_value)} chars")
                    print(f"   First 300 chars: {cleaned_value[:300]}")
                    print(f"   Last 100 chars: {cleaned_value[-100:]}")
                    print(f"   💡 Hint: LLM response may be truncated. Increase max_tokens if needed.")
                    
                    # Check if it looks like truncated JSON
                    if cleaned_value.strip().startswith('[') or cleaned_value.strip().startswith('{'):
                        print(f"   ⚠️  Response looks like incomplete JSON - returning empty array")
                        return []
                except Exception as e:
                    print(f"⚠️  Unexpected error: {e}")
                
                # Fallback: only split if it doesn't look like JSON
                if not (value.strip().startswith('[') or value.strip().startswith('{')):
                    if ',' in value:
                        print(f"   📋 Fallback: Splitting by comma")
                        return [item.strip() for item in value.split(',') if item.strip()]
                    elif '\n' in value:
                        print(f"   📋 Fallback: Splitting by newline")
                        return [item.strip() for item in value.split('\n') if item.strip()]
                
                # Last resort
                print(f"   ⚠️  Could not parse array - returning empty")
                return []
            elif field_type == "object":
                # Clean markdown code blocks from LLM response
                cleaned_value = self._clean_markdown_json(value)
                
                # Try to parse as JSON object
                try:
                    import json
                    parsed = json.loads(cleaned_value)
                    if isinstance(parsed, dict):
                        # Apply type conversion to nested properties
                        if field and field.get("properties"):
                            parsed = self._convert_nested_types(parsed, field.get("properties", []))
                        return parsed
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON object parsing failed: {e}")
                    print(f"   Cleaned value length: {len(cleaned_value)} chars")
                    print(f"   First 300 chars: {cleaned_value[:300]}")
                    print(f"   💡 Hint: LLM response may be truncated. Increase max_tokens if needed.")
                except Exception as e:
                    print(f"⚠️  Unexpected error: {e}")
                
                # Fallback: return as raw value
                return {"value": value}
            else:  # string
                return value
        except:
            return value
    
    def _convert_nested_types(self, data: dict, properties: List[Dict[str, Any]]) -> dict:
        """
        Recursively convert types for nested object properties
        
        Args:
            data: Parsed JSON object
            properties: Schema properties with type information
            
        Returns:
            Object with properly typed values
        """
        if not isinstance(data, dict) or not properties:
            return data
        
        result = {}
        # Create property lookup by name
        prop_map = {prop.get("name"): prop for prop in properties}
        
        for key, value in data.items():
            if key in prop_map:
                prop = prop_map[key]
                prop_type = prop.get("type", "string")
                
                # Convert based on type
                if prop_type == "number":
                    result[key] = self._convert_type(str(value), "number", prop)
                elif prop_type == "boolean":
                    result[key] = self._convert_type(str(value), "boolean", prop)
                elif prop_type == "array" and isinstance(value, list):
                    # Recursively convert array items
                    if prop.get("items") and prop["items"].get("properties"):
                        item_props = prop["items"].get("properties", [])
                        result[key] = [self._convert_nested_types(item, item_props) if isinstance(item, dict) else item for item in value]
                    else:
                        result[key] = value
                elif prop_type == "object" and isinstance(value, dict):
                    # Recursively convert nested object
                    if prop.get("properties"):
                        result[key] = self._convert_nested_types(value, prop.get("properties", []))
                    else:
                        result[key] = value
                else:
                    # String or unknown type - keep as is
                    result[key] = value
            else:
                # Property not in schema - keep as is
                result[key] = value
        
        return result
    
    def _clean_markdown_json(self, text: str) -> str:
        """
        Clean markdown code blocks from LLM JSON responses
        
        LLM often returns: ```json\n{...}\n```
        We need to extract just the JSON part
        """
        if not text:
            return text
        
        text = text.strip()
        
        # Remove markdown code blocks
        if '```' in text:
            # Pattern: ```json\n{...}\n``` or ```\n{...}\n```
            match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
            if match:
                text = match.group(1).strip()
                print(f"🧹 Cleaned markdown code block")
        
        return text

