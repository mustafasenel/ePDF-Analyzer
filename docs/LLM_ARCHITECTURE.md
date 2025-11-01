# LLM Architecture - Modular Design

## Overview

The LLM system has been refactored into a modular, maintainable architecture that separates concerns and enables reusability across different use cases (e-invoices, OCR, custom templates).

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LLM Service Layer                     │
│                  (llm_service.py)                        │
│  - Generic text generation                               │
│  - Image processing (OCR ready)                          │
│  - Field extraction                                      │
│  - Regex generation                                      │
│  - Model: Qwen3-VL-2B-Instruct                          │
└─────────────────────────────────────────────────────────┘
                           │
                           │ uses
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Domain-Specific Extractors                  │
├─────────────────────────────────────────────────────────┤
│  invoice_extractor.py                                    │
│  - E-invoice entity extraction                           │
│  - Sender/recipient parsing                              │
│  - Turkish invoice rules                                 │
│                                                          │
│  [Future: ocr_extractor.py]                             │
│  - Image-to-text extraction                              │
│  - Layout understanding                                  │
│                                                          │
│  [Future: custom_template_extractor.py]                 │
│  - User-defined template extraction                      │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. LLMService (`llm_service.py`)

**Purpose**: Generic LLM service for all text generation tasks

**Architecture**: Singleton pattern - only one model instance loaded in memory

**Key Methods**:
- `generate(prompt, max_tokens, temperature)` - Basic text generation
- `generate_with_image(prompt, image_path)` - Vision-language generation (OCR ready)
- `extract_field(text, prompt)` - Custom field extraction for templates
- `generate_regex(description)` - Regex pattern generation from natural language
- `clean_encoding(text)` - Text preprocessing utility

**Usage** (Always use `get_llm_service()` to get singleton instance):
```python
from app.services.llm_service import get_llm_service

# Get singleton instance - model loaded only once
llm = get_llm_service()
if llm.is_available():
    result = llm.generate("Extract the invoice number from: INV-123456")
```

**⚠️ IMPORTANT**: Never create instances with `LLMService()` directly. Always use `get_llm_service()` to ensure singleton pattern.

### 2. InvoiceExtractor (`invoice_extractor.py`)

**Purpose**: E-invoice specific entity extraction

**Key Methods**:
- `extract_sender_and_recipient(header_layout)` - Extract both entities from invoice header
- `extract_single_entity(text, entity_type)` - Fallback single entity extraction
- `generate_regex_pattern(field_name, examples)` - Invoice field regex generation

**Usage**:
```python
from app.services.llm_service import get_llm_service
from app.services.invoice_extractor import InvoiceExtractor

# Get singleton LLM instance
llm = get_llm_service()
extractor = InvoiceExtractor(llm)

result = extractor.extract_sender_and_recipient(header_text)
# Returns: {"sender": {...}, "recipient": {...}}
```

### 3. Integration Points

#### Document Templates (`document_templates.py`)
```python
from app.services.llm_service import get_llm_service
from app.services.invoice_extractor import InvoiceExtractor

# Get singleton instance (loaded once at module import)
llm_service = get_llm_service()
invoice_extractor = InvoiceExtractor(llm_service)

# Use in extraction
if header_layout and invoice_extractor:
    result = invoice_extractor.extract_sender_and_recipient(header_layout)
```

#### Custom Extractor (`custom_extractor.py`)
```python
from app.services.llm_service import get_llm_service

# Get singleton instance (reuses same model)
llm_service = get_llm_service()

# Use for custom field extraction
result = llm_service.extract_field(text, user_prompt)
```

#### API Endpoints (`main.py`)
```python
from app.services.llm_service import get_llm_service

# Get singleton instance (no reload)
llm_service = get_llm_service()

# Regex generation endpoint
result = llm_service.generate_regex(description)
```

## Benefits

### 1. **Separation of Concerns**
- Generic LLM operations in `llm_service.py`
- Domain-specific logic in specialized extractors
- Clear boundaries between layers

### 2. **Singleton Pattern (Memory Efficient)**
- ✅ Model loaded **only once** in memory (~2GB)
- ✅ All services share the **same instance**
- ✅ No duplicate model loading
- ✅ Fast subsequent calls (no initialization overhead)
- ✅ Consistent behavior across application

### 3. **Reusability**
- LLMService can be used for:
  - E-invoices (via InvoiceExtractor)
  - OCR (future OcrExtractor)
  - Custom templates (via extract_field)
  - Regex generation
  - Any text generation task

### 4. **Maintainability**
- Single source of truth for LLM operations
- Easy to upgrade model or add features
- Clear dependency chain
- Testable components

### 5. **Extensibility**
- Easy to add new domain extractors
- Can support multiple models
- Plugin architecture ready

## Migration from Old Structure

### Old (Monolithic)
```python
# Everything in llm_extractor.py
from app.services.llm_extractor import llm_extractor

llm_extractor.extract_sender_and_recipient_from_layout(text)
llm_extractor.extract_field(text, prompt)
llm_extractor.generate_regex(description)
```

### New (Modular + Singleton)
```python
# Generic operations - use singleton getter
from app.services.llm_service import get_llm_service
llm = get_llm_service()  # ✅ Returns same instance every time
llm.generate(prompt)
llm.extract_field(text, prompt)
llm.generate_regex(description)

# Invoice-specific operations
from app.services.invoice_extractor import InvoiceExtractor
extractor = InvoiceExtractor(llm)
extractor.extract_sender_and_recipient(text)
```

**Key Change**: Always use `get_llm_service()` instead of `LLMService()` to ensure singleton pattern.

## Future Enhancements

### OCR Extractor
```python
# Future: app/services/ocr_extractor.py
class OcrExtractor:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
    
    def extract_from_image(self, image_path: str) -> str:
        prompt = "Extract all text from this image..."
        return self.llm.generate_with_image(prompt, image_path)
```

### Custom Template Extractor
```python
# Future: app/services/custom_template_extractor.py
class CustomTemplateExtractor:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
    
    def extract_with_schema(self, text: str, schema: dict) -> dict:
        # Use llm.extract_field for each schema field
        pass
```

## Performance Considerations

- **Singleton Pattern**: Model loaded **only once** across entire application
  - First call: `get_llm_service()` → Loads model (~2GB, takes a few seconds)
  - Subsequent calls: `get_llm_service()` → Returns cached instance (instant)
- **Memory Efficient**: Single ~2GB model in memory, shared by all services
- **No Reload Overhead**: E-invoice, custom templates, regex generation all use same instance
- **GPU Support**: Automatic device mapping (GPU/CPU)
- **Thread-Safe**: Singleton implementation is thread-safe

## Testing

```python
# Test LLM service singleton
def test_llm_service():
    from app.services.llm_service import get_llm_service
    
    llm = get_llm_service()
    assert llm.is_available()
    result = llm.generate("Test prompt")
    assert result is not None

# Test singleton behavior
def test_singleton_pattern():
    from app.services.llm_service import get_llm_service
    
    llm1 = get_llm_service()
    llm2 = get_llm_service()
    assert llm1 is llm2  # Same instance

# Test invoice extractor
def test_invoice_extractor():
    from app.services.llm_service import get_llm_service
    from app.services.invoice_extractor import InvoiceExtractor
    
    llm = get_llm_service()
    extractor = InvoiceExtractor(llm)
    result = extractor.extract_sender_and_recipient(sample_text)
    assert "sender" in result
    assert "recipient" in result
```

## Configuration

Model configuration in `config/settings.py`:
```python
LLM_MODEL_NAME = "Qwen/Qwen3-VL-2B-Instruct"
```

All services automatically use this configuration.
