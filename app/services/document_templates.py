"""
Document Templates Service

Manages document templates and structured data extraction.
Uses modular LLM service for entity extraction (sender/recipient).
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from difflib import SequenceMatcher

# Import LLM services (lazy load to avoid startup delay)
try:
    from .llm_service import get_llm_service
    from .invoice_extractor import InvoiceExtractor
    
    # Get singleton instance
    llm_service = get_llm_service()
    invoice_extractor = InvoiceExtractor(llm_service)
    LLM_AVAILABLE = llm_service.is_available()
except Exception as e:
    print(f"⚠️  LLM services not available: {e}")
    llm_service = None
    invoice_extractor = None
    LLM_AVAILABLE = False


@dataclass
class ExtractionField:
    """Field to extract from document"""
    name: str
    patterns: List[str]
    data_type: str = "string"  # string, number, date


@dataclass
class DocumentTemplate:
    """Template for structured document extraction"""
    name: str
    detection_patterns: List[str]  # Patterns to detect this document type
    fields: List[ExtractionField]


class DocumentTemplateManager:
    """Manages document templates and extraction"""
    
    def __init__(self):
        self.templates: Dict[str, DocumentTemplate] = {}
        self._register_default_templates()
    
    def _register_default_templates(self):
        """Register default templates (e.g., Turkish e-invoice)"""
        
        # Turkish E-Invoice Template
        # Metadata fields (fatura bilgileri)
        metadata_fields = [
            ExtractionField("fatura_no", [
                r'(?i)fatura\s+no\.?\s*[:\-]?\s*([A-Z0-9]+)',
                r'(?i)fatura\s+numaras[ıi]\.?\s*[:\-]?\s*([A-Z0-9]+)',
                r'(?i)invoice\s+no\.?\s*[:\-]?\s*([A-Z0-9]+)',
                r'(?i)invoice\s+number\.?\s*[:\-]?\s*([A-Z0-9]+)',
                r'(?i)belge\s+no\.?\s*[:\-]?\s*([A-Z0-9]+)',
                r'(?i)document\s+no\.?\s*[:\-]?\s*([A-Z0-9]+)',
                r'(?i)fatura\s*#\s*([A-Z0-9]+)'
            ]),
            ExtractionField("tarih", [
                r'fatura\s+tarihi?\s*[:\-]?\s*(\d{1,2}[\s\-\./]\d{1,2}[\s\-\./]\d{2,4})',
                r'tarih\s*[:\-]\s*(\d{1,2}[\s\-\./]\d{1,2}[\s\-\./]\d{2,4})',
                r'invoice\s+date\s*[:\-]?\s*(\d{1,2}[\s\-\./]\d{1,2}[\s\-\./]\d{2,4})',
                r'date\s*[:\-]\s*(\d{1,2}[\s\-\./]\d{1,2}[\s\-\./]\d{2,4})',
                r'd[üu]zenleme\s+tarihi\s*[:\-]?\s*(\d{1,2}[\s\-\./]\d{1,2}[\s\-\./]\d{2,4})',
                r'belge\s+tarihi\s*[:\-]?\s*(\d{1,2}[\s\-\./]\d{1,2}[\s\-\./]\d{2,4})',
                r'(\d{1,2}[\s\-\./]\d{1,2}[\s\-\./]\d{4})'  # Fallback: sadece tarih formatı
            ]),
            ExtractionField("ettn", [
                r'ettn\s*[:\-]\s*([a-f0-9\-]{36})',
                r'e-fatura\s+uuid\s*[:\-]\s*([a-f0-9\-]{36})'
            ]),
            ExtractionField("ozellestirme_no", [
                r'[öo]zelle[şs]tirme\s+no\s*[:\-]\s*([A-Z0-9\.]+)',
                r'customization\s+no\s*[:\-]\s*([A-Z0-9\.]+)'
            ]),
            ExtractionField("senaryo", [
                r'senaryo\s*[:\-]\s*([A-Z]+)',
                r'scenario\s*[:\-]\s*([A-Z]+)'
            ]),
            ExtractionField("fatura_tipi", [
                r'fatura\s+tipi\s*[:\-]\s*([A-ZÇĞİÖŞÜ]+)',
                r'invoice\s+type\s*[:\-]\s*([A-Z]+)'
            ]),
            ExtractionField("siparis_no", [
                r'sipari[şs]\s+no\s*[:\-]\s*([A-Z0-9]+)',
                r'order\s+no\s*[:\-]\s*([A-Z0-9]+)',
                r'order\s+number\s*[:\-]\s*([A-Z0-9]+)'
            ]),
            ExtractionField("siparis_tarihi", [
                r'sipari[şs]\s+tarihi\s*[:\-]\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})',
                r'order\s+date\s*[:\-]\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})'
            ]),
            ExtractionField("son_odeme_tarihi", [
                r'son\s+[öo]deme\s+tarihi\s*[:\-]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})',
                r'due\s+date\s*[:\-]\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})'
            ]),
            ExtractionField("olusma_zamani", [
                r'olu[şs]ma\s+zaman[ıi]\s*[:\-]\s*(\d{2}:\d{2}:\d{2})',
                r'creation\s+time\s*[:\-]\s*(\d{2}:\d{2}:\d{2})'
            ]),
        ]
        
        # Totals fields (genel toplamlar)
        totals_fields = [
            ExtractionField("mal_hizmet_toplam", [
                r'mal\s+hizmet\s+toplam\s+tutar[ıi]?\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)',
                r'ara\s+toplam\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)',
                r'subtotal\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)'
            ], "amount"),
            ExtractionField("toplam_iskonto", [
                r'toplam\s+[iİ]skonto\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)',
                r'total\s+discount\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)'
            ], "amount"),
            ExtractionField("kdv_matrahi", [
                r'kdv\s+matrah[ıi]?\s*(?:\([^)]+\))?\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)',
                r'vat\s+base\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)'
            ], "amount"),
            ExtractionField("vergi_haric_tutar", [
                r'vergi\s+hari[çc]\s+tutar\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)',
                r'tax\s+exclusive\s+amount\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)'
            ], "amount"),
            ExtractionField("hesaplanan_kdv", [
                r'hesaplanan\s+kdv\s*(?:\([^)]+\))?\s*[:\-]?\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)',
                r'calculated\s+vat\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)',
                r'toplam\s+kdv\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)'
            ], "amount"),
            ExtractionField("vergiler_dahil_toplam", [
                r'vergiler\s+dahil\s+toplam\s+tutar\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)',
                r'vergi\s+dahil\s+toplam\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)',
                r'tax\s+inclusive\s+total\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)'
            ], "amount"),
            ExtractionField("odenecek_tutar", [
                r'[öo]denecek\s+tutar\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)',
                r'genel\s+toplam\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)',
                r'payable\s+amount\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)',
                r'grand\s+total\s*[:\-]\s*([\d\.,]+\s*(?:TL|TRY|USD|EUR|GBP)?)'
            ], "amount"),
        ]
        
        tr_efatura = DocumentTemplate(
            name="Türkiye E-Fatura",
            detection_patterns=[
                r'e-ar[şs]iv\s+fatura',
                r'fatura\s+no\s*:',
                r'ettn\s*:',
                r'mal\s+hizmet.*tutar',
                r'vergi\s+dairesi',
            ],
            fields=metadata_fields + totals_fields
        )
        
        self.register_template("tr_efatura", tr_efatura)
    
    def register_template(self, template_id: str, template: DocumentTemplate):
        """Register a new template"""
        self.templates[template_id] = template
    
    def get_available_templates(self) -> List[Dict[str, str]]:
        """Get list of available templates"""
        return [
            {"id": template_id, "name": template.name}
            for template_id, template in self.templates.items()
        ]
    
    def detect_document_type(self, text: str) -> Optional[str]:
        """
        Auto-detect document type from text
        
        Returns:
            Template ID if detected, None otherwise
        """
        text_lower = text.lower()
        
        for template_id, template in self.templates.items():
            match_count = 0
            for pattern in template.detection_patterns:
                if re.search(pattern, text_lower):
                    match_count += 1
            
            # Need at least 60% of patterns to match
            if match_count >= len(template.detection_patterns) * 0.6:
                return template_id
        
        return None
    
    def extract_data(
        self, 
        template_id: str, 
        text: str, 
        tables: Optional[List] = None, 
        header_layout: Optional[str] = None,
        invoice_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data using template
        
        Args:
            template_id: Template to use
            text: Document text
            tables: Extracted tables
            header_layout: Layout-preserved text from invoice header (for LLM processing)
            invoice_metadata: Invoice metadata (tarih, fatura_no, etc.)
            
        Returns:
            Extracted structured data
        """
        print(f"📋 Starting template extraction with template_id: {template_id}")
        print(f"📊 Text length: {len(text) if text else 0}")
        print(f"📊 Tables count: {len(tables) if tables else 0}")
        print(f"📊 Header layout: {header_layout is not None}")
        print(f"📊 Invoice metadata: {invoice_metadata is not None}")
        
        if template_id not in self.templates:
            raise ValueError(f"Unknown template: {template_id}")
        
        template = self.templates[template_id]
        result = {
            "document_type": template.name,
            "template_id": template_id,
            "extraction_date": datetime.now().isoformat(),
            "sender": {
                "raw_text": None,  # LLM için ham text
                "name": None,
                "address": None,
                "tax_id": None,
                "tax_id_type": None,
                "tax_office": None
            },
            "recipient": {
                "raw_text": None,  # LLM için ham text
                "name": None,
                "address": None,
                "tax_id": None,
                "tax_id_type": None,
                "tax_office": None
            },
            "invoice_metadata": {},  # Fatura no, tarih, senaryo vs.
            "totals": {},  # Genel toplamlar
            "line_items": None,  # Ürün tablosu
        }
        
        # Extract sender/recipient using LLM from header layout
        if header_layout and LLM_AVAILABLE and invoice_extractor:
            try:
                print(f"🤖 Extracting sender and recipient with LLM from header layout...")
                llm_result = invoice_extractor.extract_sender_and_recipient(header_layout)
                print(f"✅ LLM extraction result: {llm_result}")
                
                # Store raw layout text
                result["sender"]["raw_text"] = header_layout
                result["recipient"]["raw_text"] = header_layout
                
                # Extract name, address, tax_office from LLM result
                result["sender"]["name"] = llm_result["sender"].get("name")
                result["sender"]["address"] = llm_result["sender"].get("address")
                result["sender"]["tax_office"] = llm_result["sender"].get("tax_office")
                
                result["recipient"]["name"] = llm_result["recipient"].get("name")
                result["recipient"]["address"] = llm_result["recipient"].get("address")
                result["recipient"]["tax_office"] = llm_result["recipient"].get("tax_office")
                
                # VKN/TCKN extraction from header layout
                import re
                
                vkn_patterns = [
                    r'(?i)vergi\s*no\.?\s*[:\-]?\s*(\d{10})',
                    r'(?i)vergi\s*numaras[ıiİI]\.?\s*[:\-]?\s*(\d{10})',
                    r'(?i)vkn\.?\s*[:\-]?\s*(\d{10})',
                    r'(?i)vergi\s*kimlik\s*no\.?\s*[:\-]?\s*(\d{10})',
                    r'(?i)vergi\s*kimlik\s*numaras[ıiİI]\.?\s*[:\-]?\s*(\d{10})',
                    r'(?i)tax\s*no\.?\s*[:\-]?\s*(\d{10})',
                    r'(?i)tax\s*id\.?\s*[:\-]?\s*(\d{10})'
                ]
                
                tckn_patterns = [
                    r'(?i)tckn\.?\s*[:\-]?\s*(\d{11})',
                    r'(?i)tc\s+kimlik\s+no\.?\s*[:\-]?\s*(\d{11})',
                    r'(?i)tc\s+no\.?\s*[:\-]?\s*(\d{11})',
                    r'(?i)t\.?\s*c\.?\s*kimlik\s+no\.?\s*[:\-]?\s*(\d{11})',
                    r'(?i)t\.?\s*c\.?\s*no\.?\s*[:\-]?\s*(\d{11})',
                    r'(?i)kimlik\s+no\.?\s*[:\-]?\s*(\d{11})'
                ]
                
                # Find all VKN/TCKN in header (we'll have 2: sender and recipient)
                all_vkn = []
                all_tckn = []
                
                for pattern in vkn_patterns:
                    all_vkn.extend(re.findall(pattern, header_layout))
                
                for pattern in tckn_patterns:
                    all_tckn.extend(re.findall(pattern, header_layout))
                
                # Assign first to sender, second to recipient
                if all_vkn:
                    if len(all_vkn) >= 1 and not result["sender"]["tax_id"]:
                        result["sender"]["tax_id"] = all_vkn[0]
                        result["sender"]["tax_id_type"] = "VKN"
                        print(f"🔍 VKN found for sender: {all_vkn[0]}")
                    
                    if len(all_vkn) >= 2 and not result["recipient"]["tax_id"]:
                        result["recipient"]["tax_id"] = all_vkn[1]
                        result["recipient"]["tax_id_type"] = "VKN"
                        print(f"🔍 VKN found for recipient: {all_vkn[1]}")
                
                if all_tckn:
                    if len(all_tckn) >= 1 and not result["sender"]["tax_id"]:
                        result["sender"]["tax_id"] = all_tckn[0]
                        result["sender"]["tax_id_type"] = "TCKN"
                        print(f"🔍 TCKN found for sender: {all_tckn[0]}")
                    
                    if len(all_tckn) >= 2 and not result["recipient"]["tax_id"]:
                        result["recipient"]["tax_id"] = all_tckn[1]
                        result["recipient"]["tax_id_type"] = "TCKN"
                        print(f"🔍 TCKN found for recipient: {all_tckn[1]}")
                
            except Exception as e:
                print(f"❌ LLM extraction failed: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
        
        # Extract key-value pairs for fuzzy matching
        kv_pairs = self._extract_key_value_pairs(text)
        
        # Define metadata field names (fatura bilgileri)
        metadata_field_names = [
            'fatura_no', 'tarih', 'ettn', 'ozellestirme_no', 'senaryo',
            'fatura_tipi', 'siparis_no', 'siparis_tarihi', 'son_odeme_tarihi', 'olusma_zamani'
        ]
        
        # Define totals field names (genel toplamlar)
        totals_field_names = [
            'mal_hizmet_toplam', 'toplam_iskonto', 'kdv_matrahi',
            'vergi_haric_tutar', 'hesaplanan_kdv', 'vergiler_dahil_toplam', 'odenecek_tutar'
        ]
        
        # Extract metadata fields
        for field in template.fields:
            if field.name in metadata_field_names:
                value = self._extract_field(text, field, kv_pairs)
                result["invoice_metadata"][field.name] = value
        
        # Extract totals from totals table (more reliable than regex on full text)
        print(f"🔍 Searching for totals table in {len(tables) if tables else 0} tables...")
        totals_table = self._find_totals_table(tables) if tables else None
        if totals_table:
            print(f"✅ Totals table found: {totals_table.get('row_count')}x{totals_table.get('col_count')}")
            # Extract from totals table
            for field in template.fields:
                if field.name in totals_field_names:
                    value = self._extract_from_table(totals_table, field)
                    print(f"   📊 {field.name}: {value}")
                    result["totals"][field.name] = value
        else:
            print(f"⚠️  Totals table NOT found, using fallback text extraction")
            # Fallback: extract from text
            for field in template.fields:
                if field.name in totals_field_names:
                    value = self._extract_field(text, field, kv_pairs)
                    print(f"   📊 {field.name}: {value}")
                    result["totals"][field.name] = value
        
        # Extract line items (biggest table with headers) - dict format
        if tables:
            line_items_table = self._find_line_items_table(tables)
            if line_items_table:
                rows = line_items_table.get("rows", [])
                
                # Rows are already in dict format from table_extractor.table_to_dict()
                # Each row is like: {header1: value1, header2: value2, ...}
                result["line_items"] = rows if rows else []
        
        return result
    
    # =============================================================================
    # Helper Methods
    # =============================================================================
    
    def _extract_key_value_pairs(self, text: str) -> Dict[str, str]:
        """
        Extract key-value pairs from text (key: value or key value)
        
        Args:
            text: Text to extract from
            
        Returns:
            Dictionary of key-value pairs
        """
        pairs = {}
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try key: value format
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    if key and value:
                        pairs[key] = value
        
        return pairs
    
    def _extract_field(self, text: str, field: ExtractionField, kv_pairs: Dict[str, str]) -> Any:
        """
        Extract a field value using patterns or fuzzy matching
        
        Args:
            text: Document text
            field: Field to extract
            kv_pairs: Extracted key-value pairs
            
        Returns:
            Extracted value (parsed according to data_type)
        """
        # Try regex patterns first
        for pattern in field.patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                return self._parse_value(value, field.data_type)
        
        # Try fuzzy matching in key-value pairs
        for key, value in kv_pairs.items():
            if self._fuzzy_match(field.name, key):
                return self._parse_value(value, field.data_type)
        
        return None
    
    def _fuzzy_match(self, target: str, candidate: str, threshold: float = 0.6) -> bool:
        """
        Fuzzy string matching using SequenceMatcher
        
        Args:
            target: Target string to match
            candidate: Candidate string
            threshold: Similarity threshold (0-1)
            
        Returns:
            True if similarity >= threshold
        """
        # Normalize strings
        target = target.lower().replace('_', ' ')
        candidate = candidate.lower()
        
        # Calculate similarity
        ratio = SequenceMatcher(None, target, candidate).ratio()
        return ratio >= threshold
    
    def _parse_value(self, value: str, data_type: str) -> Any:
        """
        Parse value according to data type
        
        Args:
            value: String value to parse
            data_type: Target data type ("number", "date", "amount")
            
        Returns:
            Parsed value
            - For "amount": {"amount": float, "currency": str}
            - For "number": float
            - For "date": str
        """
        if value is None:
            return None
        
        try:
            if data_type == "amount":
                # Parse amount with currency
                # Examples: "1.245,09 TL", "22562.10 TRY TL", "1000 USD"
                import re
                
                # Extract currency (TL, TRY, USD, EUR, GBP, etc.)
                currency_match = re.search(r'\b(TL|TRY|USD|EUR|GBP|CHF|JPY|CNY)\b', value.upper())
                currency = currency_match.group(1) if currency_match else "TRY"  # Default: TRY
                
                # Remove currency codes and clean number
                clean_value = value.upper()
                for curr in ['TL', 'TRY', 'USD', 'EUR', 'GBP', 'CHF', 'JPY', 'CNY']:
                    clean_value = clean_value.replace(curr, '')
                
                # Handle Turkish number format (1.234,56 -> 1234.56)
                clean_value = clean_value.strip()
                clean_value = clean_value.replace('.', '').replace(',', '.')
                
                amount = float(clean_value)
                
                return {
                    "amount": amount,
                    "currency": currency
                }
            elif data_type == "number":
                # Handle Turkish number format (1.234,56 -> 1234.56)
                clean_value = value.replace('.', '').replace(',', '.').strip()
                # Remove currency if present
                for curr in ['TL', 'TRY', 'USD', 'EUR', 'GBP']:
                    clean_value = clean_value.replace(curr, '')
                clean_value = clean_value.strip()
                return float(clean_value)
            elif data_type == "date":
                # Basic date parsing - could be enhanced
                return value
            else:
                return value
        except Exception as e:
            # Fallback: return as string if parsing fails
            return value
    
    def _find_totals_table(self, tables: List[Dict]) -> Optional[Dict]:
        """
        Find the totals/summary table (2-column table with total keywords)
        
        Args:
            tables: List of extracted tables
            
        Returns:
            Totals table or None
        """
        if not tables:
            return None
        
        print(f"   🔎 Analyzing {len(tables)} tables for totals...")
        
        # Score each table
        candidates = []
        for idx, table in enumerate(tables):
            score = 0
            
            # Must be 2-column format (key-value pairs)
            col_count = table.get("col_count", 0)
            row_count = table.get("row_count", 0)
            print(f"      Table {idx+1}: {row_count}x{col_count} columns")
            
            if col_count != 2:
                print(f"         ❌ Skipped (not 2-column)")
                continue
            
            # Get all table text
            rows = table.get("rows", [])
            headers = table.get("headers", [])
            
            # Handle dict format rows
            all_cells = []
            if headers:
                all_cells.extend(headers)
            for row in rows:
                if isinstance(row, dict):
                    all_cells.extend(row.values())
                elif isinstance(row, list):
                    all_cells.extend(row)
            
            table_text = ' '.join(str(cell).lower() for cell in all_cells if cell)
            
            # Check for totals keywords
            totals_keywords = [
                'toplam', 'tutar', 'total', 'kdv', 'matrah', 
                'vergi', 'ödenecek', 'iskonto', 'mal hizmet',
                'ara toplam', 'genel toplam', 'subtotal', 'grand total'
            ]
            
            keyword_count = sum(1 for kw in totals_keywords if kw in table_text)
            score += keyword_count * 10
            
            # Prefer smaller tables (totals tables are usually compact)
            if 3 <= row_count <= 15:
                score += (15 - abs(row_count - 8)) * 2  # Ideal: ~8 rows
            
            print(f"         Score: {score} (keywords: {keyword_count}, rows: {row_count})")
            
            if score > 0:
                candidates.append((score, table))
        
        # Return table with highest score
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            print(f"   ✅ Best totals table: score={candidates[0][0]}")
            return candidates[0][1]
        
        print(f"   ❌ No suitable totals table found")
        return None
    
    def _extract_from_table(self, table: Dict, field: ExtractionField) -> Any:
        """
        Extract field value from a specific table (key-value format)
        
        Args:
            table: Table dict with headers and rows
            field: Field to extract
            
        Returns:
            Extracted value or None
        """
        try:
            rows = table.get("rows", [])
            headers = table.get("headers", [])
            
            # Combine headers and rows into key-value pairs
            all_rows = []
            if headers:
                all_rows.append(headers)
            if rows:
                all_rows.extend(rows)
            
            # Define field-specific keywords for matching
            field_keywords = {
                'mal_hizmet_toplam': ['mal hizmet toplam', 'mal/hizmet toplam', 'ara toplam', 'subtotal'],
                'toplam_iskonto': ['toplam iskonto', 'toplam i̇skonto', 'toplam indirim', 'total discount'],
                'kdv_matrahi': ['kdv matrah', 'kdv matrahı', 'vat base'],
                'vergi_haric_tutar': ['vergi hariç', 'vergi haric', 'tax exclusive'],
                'hesaplanan_kdv': ['hesaplanan kdv', 'toplam kdv', 'calculated vat', 'total vat'],
                'vergiler_dahil_toplam': ['vergiler dahil toplam', 'vergi dahil toplam', 'tax inclusive'],
                'odenecek_tutar': ['ödenecek tutar', 'odenecek tutar', 'genel toplam', 'grand total', 'payable']
            }
            
            keywords = field_keywords.get(field.name, [])
            
            if not keywords:
                print(f"         ⚠️  No keywords defined for field: {field.name}")
            
            for row in all_rows:
                if isinstance(row, dict):
                    # Row is dict format {col1: val1, col2: val2}
                    row_values = list(row.values())
                    if len(row_values) >= 2:
                        key = str(row_values[0]).lower().strip()
                        value = str(row_values[1]).strip()
                        
                        # Check if any keyword matches the key
                        for keyword in keywords:
                            if keyword in key:
                                parsed = self._parse_value(value, field.data_type)
                                print(f"         ✅ Match! key='{key}' keyword='{keyword}' value='{value}'")
                                return parsed
                elif isinstance(row, list) and len(row) >= 2:
                    # Row is list format [val1, val2, ...]
                    key = str(row[0]).lower().strip()
                    value = str(row[1]).strip()
                    
                    # Check if any keyword matches the key
                    for keyword in keywords:
                        if keyword in key:
                            parsed = self._parse_value(value, field.data_type)
                            print(f"         ✅ Match! key='{key}' keyword='{keyword}' value='{value}'")
                            return parsed
            
            print(f"         ❌ No match found for {field.name} with keywords: {keywords}")
            return None
        except Exception as e:
            print(f"❌ Error in _extract_from_table for field {field.name}: {type(e).__name__}: {e}")
            return None
    
    def _find_line_items_table(self, tables: List[Dict]) -> Optional[Dict]:
        """
        Find the main line items table (usually the largest table with specific headers)
        
        Args:
            tables: List of extracted tables
            
        Returns:
            Line items table or None
        """
        if not tables:
            return None
        
        # Score each table
        candidates = []
        for table in tables:
            score = 0
            
            # Check if it has headers
            if table.get("has_header"):
                score += 10
            
            # Check for line item keywords in headers
            table_headers = table.get("headers")
            if table_headers:
                header_text = ' '.join(str(h).lower() for h in table_headers if h)
                line_item_keywords = ['sıra', 'mal', 'hizmet', 'miktar', 'fiyat', 'tutar', 'kdv']
                for keyword in line_item_keywords:
                    if keyword in header_text:
                        score += 5
            
            # Prefer larger tables (but not too large)
            row_count = table.get("row_count", 0)
            col_count = table.get("col_count", 0)
            
            if 3 <= row_count <= 100:
                score += min(row_count, 20)  # Cap at 20 points
            
            if 5 <= col_count <= 15:
                score += col_count * 2
            
            candidates.append((score, table))
        
        # Return table with highest score
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        
        return None


# Global instance
template_manager = DocumentTemplateManager()
