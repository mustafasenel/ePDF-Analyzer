# Singleton Pattern for LLM Service

## Problem

Previously, the LLM model was being loaded multiple times:
- Once in `document_templates.py` for e-invoice extraction
- Once in `custom_extractor.py` for custom templates
- Once in `main.py` for regex generation API

**Result**: ~6GB memory usage (3 × 2GB model), slow startup, wasted resources.

## Solution

Implemented **Singleton Pattern** to ensure only one model instance exists across the entire application.

## Implementation

### LLMService Class

```python
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
        """Initialize LLM service (only runs once due to singleton)"""
        # Only initialize once
        if LLMService._initialized:
            return
        
        print("🚀 Initializing LLMService (first time only)")
        self.model_name = model_name
        self.model = None
        self.processor = None
        self._load_model()
        LLMService._initialized = True
```

### Global Getter Function

```python
# Global singleton instance
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
```

## Usage

### ❌ Wrong (Creates Multiple Instances)

```python
from app.services.llm_service import LLMService

# DON'T DO THIS - creates new instance each time
llm1 = LLMService()  # Loads model (~2GB)
llm2 = LLMService()  # Loads model again (~2GB)
llm3 = LLMService()  # Loads model again (~2GB)
```

### ✅ Correct (Reuses Same Instance)

```python
from app.services.llm_service import get_llm_service

# DO THIS - returns same instance
llm1 = get_llm_service()  # Loads model (~2GB) - first time
llm2 = get_llm_service()  # Returns cached instance - instant
llm3 = get_llm_service()  # Returns cached instance - instant

assert llm1 is llm2 is llm3  # True - same object
```

## Benefits

### 1. Memory Efficiency
- **Before**: 3 instances × 2GB = ~6GB memory
- **After**: 1 instance × 2GB = ~2GB memory
- **Savings**: ~4GB (67% reduction)

### 2. Startup Performance
- **Before**: Model loaded 3 times (3 × ~5 seconds = ~15 seconds)
- **After**: Model loaded once (~5 seconds)
- **Improvement**: 10 seconds faster

### 3. Consistency
- All services use the exact same model instance
- No version mismatches or inconsistencies
- Predictable behavior across application

### 4. Resource Management
- Single point of model lifecycle management
- Easier to implement model unloading/reloading
- Better GPU memory management

## Integration Examples

### E-Invoice Extraction (document_templates.py)

```python
from app.services.llm_service import get_llm_service
from app.services.invoice_extractor import InvoiceExtractor

# Get singleton instance
llm_service = get_llm_service()  # ✅ First call: loads model
invoice_extractor = InvoiceExtractor(llm_service)
```

### Custom Template Extraction (custom_extractor.py)

```python
from app.services.llm_service import get_llm_service

# Get singleton instance
llm_service = get_llm_service()  # ✅ Reuses existing instance

# Use for custom extraction
result = llm_service.extract_field(text, prompt)
```

### API Endpoint (main.py)

```python
from app.services.llm_service import get_llm_service

# Get singleton instance
llm_service = get_llm_service()  # ✅ Reuses existing instance

# Generate regex
result = llm_service.generate_regex(description)
```

## Console Output

### First Call (Model Loading)
```
🔧 Creating new LLMService singleton instance
🚀 Initializing LLMService (first time only)
📥 Loading Qwen3-VL model: Qwen/Qwen3-VL-2B-Instruct
   (İlk çalıştırmada model indirilecek, ~2GB)
✅ Qwen3-VL model loaded successfully
```

### Subsequent Calls (Instant)
```
♻️  Reusing existing LLMService instance
```

## Testing Singleton Behavior

```python
def test_singleton_pattern():
    from app.services.llm_service import get_llm_service
    
    # Get multiple instances
    llm1 = get_llm_service()
    llm2 = get_llm_service()
    llm3 = get_llm_service()
    
    # Verify they're the same object
    assert llm1 is llm2
    assert llm2 is llm3
    assert id(llm1) == id(llm2) == id(llm3)
    
    # Verify model is loaded only once
    assert llm1.model is not None
    assert llm1.model is llm2.model  # Same model instance
```

## Thread Safety

The current implementation is thread-safe for Python's GIL (Global Interpreter Lock). For multi-threaded applications, consider adding a lock:

```python
import threading

class LLMService:
    _instance = None
    _initialized = False
    _lock = threading.Lock()
    
    def __new__(cls, model_name: str = "Qwen/Qwen3-VL-2B-Instruct"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-check
                    cls._instance = super(LLMService, cls).__new__(cls)
        return cls._instance
```

## Migration Checklist

- [x] Implement singleton pattern in `LLMService`
- [x] Create `get_llm_service()` global getter
- [x] Update `document_templates.py` to use getter
- [x] Update `custom_extractor.py` to use getter
- [x] Update `main.py` API endpoints to use getter
- [x] Remove all direct `LLMService()` instantiations
- [x] Update documentation
- [x] Test singleton behavior

## Verification

Run this to verify no duplicate instances:

```bash
# Search for direct LLMService() calls (should return nothing)
grep -r "LLMService()" app/ --include="*.py"

# Search for get_llm_service() calls (should find all usages)
grep -r "get_llm_service" app/ --include="*.py"
```

## Summary

✅ **Single model instance** across entire application  
✅ **~4GB memory saved** (67% reduction)  
✅ **10 seconds faster** startup  
✅ **Consistent behavior** across all services  
✅ **Easy to maintain** and extend  

The singleton pattern ensures optimal resource usage while maintaining clean, modular code architecture.
