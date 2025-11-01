"""
Base LLM Service

Generic LLM service for text generation using Qwen3-VL-2B-Instruct model.
Can be used for OCR, entity extraction, custom templates, and more.

Uses singleton pattern to ensure only one model instance is loaded in memory.
"""

import warnings
warnings.filterwarnings('ignore')


class LLMService:
    """Singleton LLM service - only one model instance across entire application"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, model_name: str = "Qwen/Qwen3-VL-2B-Instruct"):
        """Singleton pattern: return same instance if already created"""
        if cls._instance is None:
            print("🔧 Creating new LLMService singleton instance")
            cls._instance = super(LLMService, cls).__new__(cls)
        else:
            print("♻️  Reusing existing LLMService instance")
        return cls._instance
    
    def __init__(self, model_name: str = "Qwen/Qwen3-VL-2B-Instruct"):
        """
        Initialize LLM service (only runs once due to singleton)
        
        Args:
            model_name: Hugging Face model name
        """
        # Only initialize once
        if LLMService._initialized:
            return
        
        print("🚀 Initializing LLMService (first time only)")
        self.model_name = model_name
        self.model = None
        self.processor = None
        self._load_model()
        LLMService._initialized = True
    
    def _load_model(self):
        """Load Qwen3-VL vision-language model from Hugging Face"""
        try:
            from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
            import torch
            
            model_size = "~2GB" if "2B" in self.model_name else "~?GB"
            print(f"📥 Loading Qwen3-VL model: {self.model_name}")
            print(f"   (İlk çalıştırmada model indirilecek, {model_size})")
            
            # Load processor (replaces tokenizer for vision models)
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            
            # Load model with auto dtype and device mapping
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype="auto",
                device_map="auto"  # Automatically use available device (GPU/CPU)
            )
            
            # Set to evaluation mode
            self.model.eval()
            
            print(f"✅ Qwen3-VL model loaded successfully")
            
        except Exception as e:
            print(f"⚠️  Failed to load Qwen3-VL model: {e}")
            print("   LLM features will be disabled")
            self.model = None
            self.processor = None
    
    def is_available(self) -> bool:
        """Check if LLM is loaded and available"""
        return self.model is not None and self.processor is not None
    
    def generate(
        self, 
        prompt: str, 
        max_tokens: int = 256,
        temperature: float = 0.1
    ) -> str:
        """
        Generate text from prompt
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more deterministic)
            
        Returns:
            Generated text
        """
        if not self.is_available():
            raise RuntimeError("LLM model not available")
        
        try:
            import torch
            
            # Prepare messages in Qwen3VL format
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Apply chat template and prepare inputs
            inputs = self.processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt"
            )
            inputs = inputs.to(self.model.device)
            
            # Generate
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0
                )
            
            # Decode only the generated part
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            response = self.processor.batch_decode(
                generated_ids_trimmed, 
                skip_special_tokens=True, 
                clean_up_tokenization_spaces=False
            )[0].strip()
            
            return response
            
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {e}")
    
    def generate_with_image(
        self,
        prompt: str,
        image_path: str,
        max_tokens: int = 256,
        temperature: float = 0.1
    ) -> str:
        """
        Generate text from prompt and image (for OCR, visual understanding)
        
        Args:
            prompt: Input prompt
            image_path: Path to image file
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        if not self.is_available():
            raise RuntimeError("LLM model not available")
        
        try:
            import torch
            from PIL import Image
            
            # Load image
            image = Image.open(image_path)
            
            # Prepare messages with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Apply chat template and prepare inputs
            inputs = self.processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt"
            )
            inputs = inputs.to(self.model.device)
            
            # Generate
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0
                )
            
            # Decode only the generated part
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            response = self.processor.batch_decode(
                generated_ids_trimmed, 
                skip_special_tokens=True, 
                clean_up_tokenization_spaces=False
            )[0].strip()
            
            return response
            
        except Exception as e:
            raise RuntimeError(f"LLM generation with image failed: {e}")
    
    def extract_field(self, text: str, prompt: str) -> str:
        """
        Extract a single field using custom prompt (for custom templates)
        
        Args:
            text: Text to extract from
            prompt: User-provided extraction prompt
            
        Returns:
            Extracted value as string or None
        """
        if not self.is_available():
            return None
        
        # Detect if JSON output is expected
        is_json_expected = any(keyword in prompt.lower() for keyword in ['json', 'array', 'list', 'object'])
        
        # Create full prompt with specific instructions
        if is_json_expected:
            full_prompt = f"""{prompt}

Text:
{text}

IMPORTANT: Return ONLY raw JSON without markdown code blocks (no ```json or ```).
Just the pure JSON array or object."""
        else:
            full_prompt = f"""{prompt}

Text:
{text}

Return only the extracted value, nothing else."""

        try:
            # Use more tokens for JSON responses, especially for arrays
            if 'array' in prompt.lower() and 'all' in prompt.lower():
                max_tokens = 1024  # Large arrays need more tokens
            elif is_json_expected:
                max_tokens = 512   # Standard JSON
            else:
                max_tokens = 128   # Simple extraction
            
            response = self.generate(full_prompt, max_tokens=max_tokens, temperature=0.1)
            
            # Clean up response (remove common prefixes/suffixes)
            response = response.strip('"').strip("'").strip()
            
            # Clean encoding issues
            if response:
                response = self.clean_encoding(response)
            
            return response if response else None
                
        except Exception as e:
            print(f"LLM field extraction error: {e}")
            return None
    
    def generate_regex(self, description: str) -> dict:
        """
        Generate regex pattern from natural language description
        
        Args:
            description: What the user wants to extract
            
        Returns:
            Dictionary with 'pattern', 'description', and 'explanation'
        """
        if not self.is_available():
            print("❌ LLM not available for regex generation")
            return None
        
        print(f"🤖 Generating regex with LLM for: {description}")
        
        # Dynamic prompt - no hardcoded examples
        prompt = f"""Generate a regex pattern for: {description}

Return ONLY the regex pattern, nothing else.
Do not use markdown code blocks.
Pattern:"""

        try:
            import re as regex_module
            
            response = self.generate(prompt, max_tokens=128, temperature=0.2)
            print(f"🤖 LLM Raw Response: {response}")
            
            # Clean up response - remove common prefixes/labels
            pattern = response
            
            # Remove "Pattern:" prefix if LLM added it
            if pattern.lower().startswith('pattern:'):
                pattern = pattern[8:].strip()
            
            # Remove markdown code blocks
            if '```' in pattern:
                match = regex_module.search(r'```(?:regex|python)?\s*([^`]+)```', pattern)
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
            
            # Check if LLM just repeated the description
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
                regex_module.compile(pattern)
                print(f"✅ Valid regex generated: {pattern}")
            except regex_module.error as e:
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
    
    @staticmethod
    def clean_encoding(text: str) -> str:
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


# Global singleton instance - import this instead of creating new instances
_llm_service_instance = None

def get_llm_service() -> LLMService:
    """
    Get the global LLM service singleton instance
    
    Returns:
        LLMService: The singleton instance
    """
    global _llm_service_instance
    if _llm_service_instance is None:
        from config.settings import settings
        _llm_service_instance = LLMService(model_name=settings.LLM_MODEL_NAME)
    return _llm_service_instance
