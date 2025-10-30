"""
LLM Extractor Service

Uses Qwen 0.5B-Instruct model for entity extraction from invoice text.
Small model (~500MB) that runs efficiently on CPU.
"""

import json
import re
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class LLMExtractor:
    """Extract structured entities using Qwen3 0.6B"""
    
    def __init__(self, model_name: str = "Qwen/Qwen3-0.6B"):
        """
        Initialize LLM extractor
        
        Args:
            model_name: Hugging Face model name
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load Qwen3 model from Hugging Face"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            model_size = "~600MB" if "0.6B" in self.model_name else "~3GB" if "1.5B" in self.model_name else "~?GB"
            print(f"📥 Loading LLM model: {self.model_name}")
            print(f"   (İlk çalıştırmada model indirilecek, {model_size})")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Load model (CPU için auto dtype)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype="auto",
                device_map="cpu"  # CPU'da çalıştır
            )
            
            # Set to evaluation mode
            self.model.eval()
            
            print(f"✅ LLM model loaded successfully")
            
        except Exception as e:
            print(f"⚠️  Failed to load LLM model: {e}")
            print("   Entity extraction will use regex-only mode")
            self.model = None
            self.tokenizer = None
    
    def _clean_encoding(self, text: str) -> str:
        """Clean encoding issues in text"""
        if not text:
            return text
        
        # Replace unicode replacement character
        text = text.replace('\ufffd', '-')
        text = text.replace('�', '-')
        
        # Normalize dashes
        text = text.replace('\u2010', '-').replace('\u2011', '-')
        text = text.replace('\u2012', '-').replace('\u2013', '-')
        text = text.replace('\u2014', '-').replace('\u2015', '-')
        
        # Normalize quotes
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        
        return text
    
    def extract_sender_recipient_info(
        self, 
        text: str,
        entity_type: str = "sender"
    ) -> Dict[str, Optional[str]]:
        """
        Extract structured information from sender/recipient text
        
        Args:
            text: Raw text containing entity information
            entity_type: "sender" or "recipient"
            
        Returns:
            Dictionary with extracted fields (name, address, tax_office)
        """
        if not self.model or not self.tokenizer:
            return {
                "name": None,
                "address": None,
                "tax_office": None
            }
        
        # Clean text encoding first
        text = self._clean_encoding(text)
        
        # Create short, directive prompt for small model
        if entity_type == "sender":
            prompt = f"""Extract the COMPLETE company name from this invoice text. Include company type keywords like A.Ş., Ltd., Şti., Ltd. Şti., San. Tic., İnş. Taah., Tur. Ltd. Şti., etc.

IMPORTANT: Skip words like "SAYIN" (greeting), extract only the actual company/person name.

Text:
{text}

Return ONLY this JSON:
{{"name": "FULL company name WITH type (A.Ş./Ltd./Şti./etc)", "address": "full address", "tax_office": "tax office name or null"}}

Example: {{"name": "ABC TEKNOLOJİ A.Ş.", "address": "...", "tax_office": "..."}}"""
        else:
            prompt = f"""Extract the COMPLETE customer name from this invoice text. Include company type keywords like A.Ş., Ltd., Şti., Ltd. Şti., San. Tic., İnş. Taah., etc.

IMPORTANT:
- Skip "SAYIN" word (it's a greeting)
- Extract the actual customer name that comes AFTER "SAYIN"
- Include company type if exists (A.Ş., Ltd., Şti., etc)

Text:
{text}

Return ONLY this JSON:
{{"name": "FULL customer name (without SAYIN)", "address": "customer address", "tax_office": "tax office or null"}}

Example: {{"name": "XYZ TİCARET LTD. ŞTİ.", "address": "...", "tax_office": "..."}}"""

        try:
            import torch
            
            # Prepare messages in chat format
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # Apply chat template
            text_input = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False  # Thinking mode kapalı (daha hızlı)
            )
            
            # Tokenize
            model_inputs = self.tokenizer([text_input], return_tensors="pt").to(self.model.device)
            
            # Generate
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **model_inputs,
                    max_new_tokens=256,
                    temperature=0.1,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode only the generated part (skip input)
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
            response = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip()
            
            # Try to parse JSON
            result = self._parse_json_response(response)
            
            if result:
                # Clean name - remove "SAYIN" greeting and validate it's not an address
                name = result.get("name")
                if name:
                    name = str(name).strip()
                    
                    # Remove "SAYIN" if model included it
                    name = re.sub(r'\b(?:SAYIN|Sayın|sayin)\b', '', name, flags=re.IGNORECASE).strip()
                    # Remove multiple spaces
                    name = re.sub(r'\s+', ' ', name)
                    
                    # Check if it's actually an address (contains location keywords)
                    address_indicators = [
                        'mahalle', 'mah.', 'sokak', 'sok.', 'cadde', 'cad.', 
                        'bulvar', 'no:', 'kat:', 'daire:', '//'
                    ]
                    is_address = any(indicator in name.lower() for indicator in address_indicators)
                    
                    # If name is too short, empty, or looks like address, try to extract from original text
                    if not name or len(name) < 3 or is_address:
                        print(f"⚠️  Invalid name extracted (too short or is address): '{name}'")
                        # Try to find company name with type indicators
                        company_patterns = [
                            r'([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜa-zçğıöşü\s\.&-]+?(?:A\.Ş\.|LTD\.|ŞTİ\.|Ltd\. Şti\.|San\. Tic\.|İnş\. Taah\.|Tur\. Ltd\. Şti\.|Paz\. A\.Ş\.))',
                            r'([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜa-zçğıöşü\s\.&-]+?(?:ANONİM ŞİRKETİ|LİMİTED ŞİRKETİ))',
                        ]
                        for pattern in company_patterns:
                            match = re.search(pattern, text)
                            if match:
                                name = match.group(1).strip()
                                print(f"✅ Found company name via regex: '{name}'")
                                break
                
                # Clean tax_office - if it's a label or empty, set to None
                tax_office = result.get("tax_office")
                if tax_office:
                    tax_office_lower = str(tax_office).lower().strip()
                    # If it's just a label or too short, ignore it
                    if tax_office_lower in ['vergi dairesi', 'tax office', 'null', 'none', ''] or len(tax_office_lower) < 3:
                        tax_office = None
                
                return {
                    "name": name if name else None,
                    "address": result.get("address"),
                    "tax_office": tax_office
                }
            else:
                # Fallback: regex extraction
                return self._regex_fallback(text)
                
        except Exception as e:
            print(f"LLM extraction error: {e}")
            return self._regex_fallback(text)
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse JSON from LLM response"""
        try:
            # Find JSON block (between { and })
            json_match = re.search(r'\{[^{}]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                return {
                    "name": data.get("name"),
                    "address": data.get("address"),
                    "tax_office": data.get("tax_office")
                }
        except:
            pass
        
        return None
    
    def _regex_fallback(self, text: str) -> Dict[str, Optional[str]]:
        """Fallback regex-based extraction"""
        result = {
            "name": None,
            "address": None,
            "tax_office": None
        }
        
        # Try to extract company name with type indicators (A.Ş., Ltd., Şti., etc.)
        company_patterns = [
            r'([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜa-zçğıöşü\s\.&-]+?(?:A\.Ş\.|LTD\.|ŞTİ\.|Ltd\. Şti\.|San\. Tic\.|İnş\. Taah\.|Tur\. Ltd\. Şti\.|Paz\. A\.Ş\.))',
            r'([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜa-zçğıöşü\s\.&-]+?(?:ANONİM ŞİRKETİ|LİMİTED ŞİRKETİ))',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                # Skip if it starts with "SAYIN"
                if not re.match(r'^SAYIN', name, re.IGNORECASE):
                    result["name"] = name
                    break
        
        # Fallback: Name from first non-empty, non-SAYIN, non-address line
        if not result["name"]:
            lines = text.split('\n')
            
            # Address keywords to skip
            address_keywords = [
                'tel:', 'fax:', 'e-posta:', 'email:', 'vergi no', 'vkn', 'tckn', 'ettn',
                'mahalle', 'mah.', 'mah:', 'sokak', 'sok.', 'sok:', 'cadde', 'cad.', 'cad:',
                'bulvar', 'blv.', 'no:', 'no.', 'kat:', 'daire:', 'posta kodu',
                'ilçe', 'il:', 'şehir', '//', 'web:', 'www.', 'http'
            ]
            
            for line in lines[:8]:  # Check first 8 lines
                line = line.strip()
                line_lower = line.lower()
                
                # Skip if:
                # - Too short or too long (addresses are usually longer)
                # - Starts with SAYIN
                # - Contains address keywords
                # - Starts with lowercase (addresses often start with location)
                # - Is mostly numbers (street numbers)
                if (10 < len(line) < 100 and  # Reasonable name length
                    not re.match(r'^SAYIN', line, re.IGNORECASE) and
                    not any(kw in line_lower for kw in address_keywords) and
                    line[0].isupper() and  # Starts with capital (company names)
                    not re.match(r'^\d+', line)):  # Not starting with number
                    result["name"] = line
                    break
        
        # Tax Office: Look for "Vergi Dairesi:" pattern
        vd_pattern = re.compile(r'vergi\s+dairesi\s*[:\-]\s*([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜa-zçğıöşü\s]{2,40})', re.IGNORECASE)
        vd_match = vd_pattern.search(text)
        if vd_match:
            vd_name = vd_match.group(1).strip()
            # Clean up (remove VKN, TCKN, etc.)
            vd_name = re.split(r'(VKN|TCKN|Mersis|Tel|Fax|\d{10})', vd_name)[0].strip()
            result["tax_office"] = vd_name
        
        # Address: Look for address patterns
        address_lines = []
        for line in lines:
            line = line.strip()
            # Address keywords
            if any(kw in line.lower() for kw in ['mah.', 'mahallesi', 'cad.', 'cadde', 'sok.', 'sokak', 'no:', 'blv.', 'bulvar']):
                if not any(kw in line.lower() for kw in ['tel:', 'fax:', 'vergi', 'vkn', 'tckn']):
                    address_lines.append(line)
        
        if address_lines:
            result["address"] = ' '.join(address_lines[:2])  # Max 2 lines
        
        return result
    
    def extract_field(self, text: str, prompt: str) -> Optional[str]:
        """
        Extract a single field using custom prompt
        
        Args:
            text: Text to extract from
            prompt: User-provided extraction prompt
            
        Returns:
            Extracted value as string or None
        """
        if not self.model or not self.tokenizer:
            return None
        
        # Create full prompt
        full_prompt = f"""{prompt}

Text:
{text}

Return only the extracted value, nothing else."""

        try:
            import torch
            
            # Prepare messages
            messages = [
                {"role": "user", "content": full_prompt}
            ]
            
            # Apply chat template
            text_input = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False
            )
            
            # Tokenize
            model_inputs = self.tokenizer([text_input], return_tensors="pt").to(self.model.device)
            
            # Generate
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **model_inputs,
                    max_new_tokens=128,
                    temperature=0.1,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode only generated part
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
            response = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip()
            
            # Clean up response (remove common prefixes/suffixes)
            response = response.strip('"').strip("'").strip()
            
            # Clean encoding issues
            if response:
                response = self._clean_encoding(response)
            
            return response if response else None
                
        except Exception as e:
            print(f"LLM field extraction error: {e}")
            return None
    
    def generate_regex(self, description: str) -> Optional[Dict[str, str]]:
        """
        Generate regex pattern from natural language description using LLM
        
        Args:
            description: What the user wants to extract
            
        Returns:
            Dictionary with 'pattern' and 'explanation'
        """
        if not self.model or not self.tokenizer:
            print("❌ LLM not available for regex generation")
            return None
        
        print(f"🤖 Generating regex with LLM for: {description}")
        
        # Simplified prompt for small LLM
        prompt = f"""Generate regex pattern.

Examples:
"invoice INV + 6 digits" -> INV(\\d{{6}})
"date DD/MM/YYYY" -> (\\d{{2}}/\\d{{2}}/\\d{{4}})
"10 digit phone" -> (\\d{{10}})

Task: {description}
Pattern:"""

        try:
            import torch
            
            # Prepare messages with system instruction
            messages = [
                {"role": "system", "content": "You are a regex pattern generator. Only output valid regex patterns, nothing else."},
                {"role": "user", "content": prompt}
            ]
            
            # Apply chat template
            text_input = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False
            )
            
            # Tokenize
            model_inputs = self.tokenizer([text_input], return_tensors="pt").to(self.model.device)
            
            # Generate (very low temperature for deterministic output)
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **model_inputs,
                    max_new_tokens=128,
                    temperature=0.1,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode only generated part
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
            response = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip()
            
            print(f"🤖 LLM Raw Response: {response}")
            
            # Clean up response - remove common prefixes/labels
            pattern = response
            
            # Remove "Pattern:" prefix if LLM added it
            if pattern.lower().startswith('pattern:'):
                pattern = pattern[8:].strip()
            
            # Remove markdown code blocks
            if '```' in pattern:
                match = re.search(r'```(?:regex|python)?\s*([^`]+)```', pattern)
                if match:
                    pattern = match.group(1).strip()
                else:
                    pattern = pattern.split('```')[1].split('```')[0].strip() if pattern.count('```') >= 2 else pattern
            
            # Remove quotes and backticks
            pattern = pattern.strip('`').strip('"').strip("'").strip()
            
            # Take only the first line (ignore explanations)
            if '\n' in pattern:
                lines = pattern.split('\n')
                # Find the line that looks most like a regex
                for line in lines:
                    line = line.strip()
                    if line and not line.lower().startswith(('this', 'the', 'note', 'explanation', 'example')):
                        pattern = line
                        break
                else:
                    pattern = lines[0].strip()
            
            # Validate it's somewhat regex-like
            if not pattern or len(pattern) < 2:
                print(f"❌ Pattern too short: {pattern}")
                return None
            
            # Check if LLM just repeated the description (must be exact or very similar)
            # But allow patterns that contain common words from description
            if pattern.lower() == description.lower():
                print(f"❌ LLM repeated exact description: {pattern}")
                return None
            
            # Check if pattern looks like natural language (no regex special chars)
            regex_chars = set(r'\.^$*+?{}[]()|\-')
            if not any(c in pattern for c in regex_chars) and len(pattern) > 10:
                print(f"❌ Pattern looks like natural language, not regex: {pattern}")
                return None
            
            # Try to compile it to validate
            try:
                re.compile(pattern)
                print(f"✅ Valid regex generated: {pattern}")
            except re.error as e:
                print(f"❌ Invalid regex: {pattern} - Error: {e}")
                return None
            
            return {
                "pattern": pattern,
                "description": description,
                "explanation": f"Pattern generated for: {description}"
            }
                
        except Exception as e:
            print(f"Regex generation error: {e}")
            return None


# Global instance (uses config settings)
from config.settings import settings

llm_extractor = LLMExtractor(model_name=settings.LLM_MODEL_NAME)

