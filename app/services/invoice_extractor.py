"""
Invoice Entity Extractor

Specialized extractor for Turkish e-invoice entities using LLM.
Built on top of the generic LLM service.
"""

import json
import re
from typing import Dict, Optional
from .llm_service import LLMService


class InvoiceExtractor:
    """Extract structured entities from Turkish e-invoices"""
    
    def __init__(self, llm_service: LLMService):
        """
        Initialize invoice extractor
        
        Args:
            llm_service: Base LLM service instance
        """
        self.llm = llm_service
    
    def extract_sender_and_recipient(self, header_layout: str) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Extract both sender and recipient information from invoice header layout
        
        Args:
            header_layout: Layout-preserved text from invoice header (top portion)
            
        Returns:
            Dictionary with 'sender' and 'recipient' keys, each containing name, address, tax_office
        """
        if not self.llm.is_available():
            return {
                "sender": {"name": None, "address": None, "tax_office": None},
                "recipient": {"name": None, "address": None, "tax_office": None}
            }
        
        # Clean text encoding first
        header_layout = LLMService.clean_encoding(header_layout)
        
        # Create comprehensive prompt for the model
        prompt = f"""Analyze this Turkish e-invoice header and extract BOTH sender (gönderici) and recipient (alıcı) information.

IMPORTANT RULES:
1. Sender is usually at the TOP or LEFT side
2. Recipient comes AFTER "SAYIN" keyword or in a separate section
3. Extract COMPLETE company names including type (A.Ş., Ltd., Şti., Ltd. Şti., San. Tic., İnş. Taah., etc.)
4. DO NOT include "SAYIN" in the recipient name (it's just a greeting)
5. Tax office (Vergi Dairesi) should be the office name only, not the label

Invoice Header Text:
{header_layout}

Return ONLY this JSON structure (no markdown, no code blocks):
{{
  "sender": {{
    "name": "FULL sender company name WITH type",
    "address": "sender full address",
    "tax_office": "sender tax office name or null"
  }},
  "recipient": {{
    "name": "FULL recipient company/person name (without SAYIN)",
    "address": "recipient full address",
    "tax_office": "recipient tax office name or null"
  }}
}}"""

        try:
            # Generate with LLM
            response = self.llm.generate(prompt, max_tokens=512, temperature=0.1)
            print(f"🤖 LLM Response for sender+recipient:\n{response}")
            
            # Parse JSON response
            result = self._parse_sender_recipient_json(response)
            
            if result:
                # Clean sender name
                if result["sender"]["name"]:
                    result["sender"]["name"] = self._clean_entity_name(result["sender"]["name"])
                
                # Clean recipient name (remove SAYIN)
                if result["recipient"]["name"]:
                    result["recipient"]["name"] = self._clean_entity_name(result["recipient"]["name"])
                    result["recipient"]["name"] = re.sub(
                        r'\b(?:SAYIN|Sayın|sayin)\b', 
                        '', 
                        result["recipient"]["name"], 
                        flags=re.IGNORECASE
                    ).strip()
                    result["recipient"]["name"] = re.sub(r'\s+', ' ', result["recipient"]["name"])
                
                # Clean tax offices
                for entity in ["sender", "recipient"]:
                    tax_office = result[entity].get("tax_office")
                    if tax_office:
                        tax_office_lower = str(tax_office).lower().strip()
                        if tax_office_lower in ['vergi dairesi', 'tax office', 'null', 'none', ''] or len(tax_office_lower) < 3:
                            result[entity]["tax_office"] = None
                
                return result
            else:
                # Fallback: try to extract separately
                print("⚠️  JSON parsing failed, using fallback extraction")
                return self._fallback_separate_extraction(header_layout)
                
        except Exception as e:
            print(f"❌ LLM extraction error: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_separate_extraction(header_layout)
    
    def extract_single_entity(
        self, 
        text: str,
        entity_type: str = "sender"
    ) -> Dict[str, Optional[str]]:
        """
        Extract structured information from single entity text (fallback method)
        
        Args:
            text: Raw text containing entity information
            entity_type: "sender" or "recipient"
            
        Returns:
            Dictionary with extracted fields (name, address, tax_office)
        """
        if not self.llm.is_available():
            return {
                "name": None,
                "address": None,
                "tax_office": None
            }
        
        # Clean text encoding
        text = LLMService.clean_encoding(text)
        
        entity_label = "gönderici (sender)" if entity_type == "sender" else "alıcı (recipient)"
        
        prompt = f"""Extract {entity_label} information from this Turkish e-invoice text.

Text:
{text}

Return ONLY this JSON (no markdown, no code blocks):
{{
  "name": "company or person name",
  "address": "address",
  "tax_office": "tax office name or null"
}}

Rules:
- Extract COMPLETE company name including type (A.Ş., Ltd., Şti., etc.)
- DO NOT include "SAYIN" in name
- Tax office should be office name only, not label"""

        try:
            response = self.llm.generate(prompt, max_tokens=256, temperature=0.1)
            
            # Parse JSON
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                data = json.loads(json_match.group(0))
                result = {
                    "name": self._clean_entity_name(data.get("name")),
                    "address": data.get("address"),
                    "tax_office": data.get("tax_office")
                }
                
                # Clean tax office
                if result["tax_office"]:
                    tax_office_lower = str(result["tax_office"]).lower().strip()
                    if tax_office_lower in ['vergi dairesi', 'tax office', 'null', 'none', ''] or len(tax_office_lower) < 3:
                        result["tax_office"] = None
                
                return result
        except Exception as e:
            print(f"⚠️  Single entity extraction failed: {e}")
        
        return {"name": None, "address": None, "tax_office": None}
    
    def generate_regex_pattern(self, field_name: str, examples: list) -> Optional[str]:
        """
        Generate regex pattern for field extraction using LLM
        
        Args:
            field_name: Name of the field
            examples: List of example values
            
        Returns:
            Regex pattern string or None
        """
        if not self.llm.is_available():
            return None
        
        prompt = f"""Generate a Python regex pattern to extract "{field_name}" from Turkish invoice text.

Examples of values to match:
{chr(10).join(f'- {ex}' for ex in examples[:5])}

Return ONLY the regex pattern as a raw string (no explanation).
Pattern should be flexible to match variations.
Use named groups if helpful: (?P<name>...)"""

        try:
            response = self.llm.generate(prompt, max_tokens=128, temperature=0.2)
            # Extract pattern (remove quotes if present)
            pattern = response.strip().strip('"').strip("'")
            
            # Validate it's a valid regex
            re.compile(pattern)
            return pattern
        except Exception as e:
            print(f"⚠️  Regex generation failed: {e}")
            return None
    
    def _parse_sender_recipient_json(self, response: str) -> Optional[Dict]:
        """Parse JSON response containing both sender and recipient"""
        try:
            # Find JSON block
            json_match = re.search(r'\{[\s\S]*"sender"[\s\S]*"recipient"[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                return {
                    "sender": {
                        "name": data.get("sender", {}).get("name"),
                        "address": data.get("sender", {}).get("address"),
                        "tax_office": data.get("sender", {}).get("tax_office")
                    },
                    "recipient": {
                        "name": data.get("recipient", {}).get("name"),
                        "address": data.get("recipient", {}).get("address"),
                        "tax_office": data.get("recipient", {}).get("tax_office")
                    }
                }
        except Exception as e:
            print(f"⚠️  JSON parsing error: {e}")
        
        return None
    
    def _clean_entity_name(self, name: str) -> Optional[str]:
        """Clean entity name from common issues"""
        if not name:
            return None
        
        name = str(name).strip()
        
        # Remove multiple spaces
        name = re.sub(r'\s+', ' ', name)
        
        # Check if it's actually an address
        address_indicators = [
            'mahalle', 'mah.', 'sokak', 'sok.', 'cadde', 'cad.', 
            'bulvar', 'no:', 'kat:', 'daire:', '//'
        ]
        is_address = any(indicator in name.lower() for indicator in address_indicators)
        
        if is_address or len(name) < 3:
            return None
        
        return name
    
    def _fallback_separate_extraction(self, text: str) -> Dict[str, Dict[str, Optional[str]]]:
        """Fallback: try to split text and extract separately"""
        # Try to split by SAYIN
        sayin_pattern = re.compile(r'sa\s*y[iıİ]n', re.IGNORECASE)
        match = sayin_pattern.search(text)
        
        if match:
            sender_text = text[:match.start()].strip()
            recipient_text = text[match.start():].strip()
        else:
            # Split by largest gap or middle
            lines = text.split('\n')
            mid = len(lines) // 2
            sender_text = '\n'.join(lines[:mid])
            recipient_text = '\n'.join(lines[mid:])
        
        # Extract separately using old method
        sender_info = self.extract_single_entity(sender_text, "sender")
        recipient_info = self.extract_single_entity(recipient_text, "recipient")
        
        return {
            "sender": sender_info,
            "recipient": recipient_info
        }
