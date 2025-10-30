# ePDF - Teknik Mimari ve Tasarım Dökümanı (v2)

## 🎯 Proje Felsefesi

**Katmanlı Yaklaşım**: Önce sağlam temel, sonra yapay zeka

Bu proje **2 ana katmandan** oluşacak:

### Katman 1: Temel PDF İşleme (LLM'siz) - ÖNCELİK
Klasik araçlarla PDF okuma, analiz, dönüştürme

### Katman 2: LLM Destekli Akıllı Analiz (Sonra)
Multimodal model ile semantik analiz ve OCR

**ŞU AN ODAK: KATMAN 1**

---

## 📚 Katman 1: Temel PDF İşleme (LLM'siz)

### Amaç
PDF'den maksimum bilgiyi çıkarmak - text, tablolar, metadata - klasik kütüphanelerle.

### Kullanılacak Python Kütüphaneleri

#### 1. **PyMuPDF (fitz)** - Ana PDF Okuma Motoru
```python
import fitz  # PyMuPDF
```

**Neden PyMuPDF?**
- En hızlı PDF okuma kütüphanesi
- Text extraction çok iyi
- Metadata okuma
- Sayfa sayfa işlem
- Layout bilgisi (koordinatlar)
- Font, renk bilgileri
- Görüntü extraction

**Kullanım Alanları**:
- Text extraction (her sayfa için)
- Metadata okuma (author, creation date, etc.)
- Sayfa boyutları
- Font bilgileri

#### 2. **pdfplumber** - Tablo Extraction
```python
import pdfplumber
```

**Neden pdfplumber?**
- Tablo algılama ve extraction'da en iyilerden
- Koordinat bazlı layout analizi
- Cell boundaries'i bulur
- Nested table desteği

**Kullanım Alanları**:
- Tablo tespit etme
- Tablo içeriğini extract etme
- Tablonun hangi sayfada olduğunu bulma

#### 3. **camelot-py** - Gelişmiş Tablo Extraction (Opsiyonel)
```python
import camelot
```

**Neden camelot?**
- Kompleks tablolarda çok iyi
- Lattice (çizgili) ve Stream (çizgisiz) mod
- CSV/Excel export built-in

**Kullanım Alanları**:
- Karmaşık tablolar
- Çok sütunlu tablolar
- İç içe tablolar

#### 4. **pandas** - Veri İşleme
```python
import pandas as pd
```

**Kullanım Alanları**:
- Tabloları DataFrame'e çevirme
- Veri temizleme
- Excel export
- JSON export

#### 5. **openpyxl** - Excel Yazma
```python
from openpyxl import Workbook
```

**Kullanım Alanları**:
- Excel dosyası oluşturma
- Stil ve formatlama
- Çoklu sheet
- Formül desteği

### PDF İşleme Pipeline'ı

```
                    ┌──────────────┐
                    │   PDF File   │
                    └──────┬───────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │   1. Basic Info Extraction   │
            │   (PyMuPDF)                  │
            │   - Sayfa sayısı             │
            │   - Metadata                 │
            │   - Dosya boyutu             │
            └──────────┬───────────────────┘
                       │
                       ▼
            ┌──────────────────────────────┐
            │   2. Text Extraction         │
            │   (PyMuPDF)                  │
            │   - Sayfa sayfa text         │
            │   - Layout korunarak         │
            │   - Font bilgileriyle        │
            └──────────┬───────────────────┘
                       │
                       ▼
            ┌──────────────────────────────┐
            │   3. Table Detection         │
            │   (pdfplumber + camelot)     │
            │   - Tablo var mı?            │
            │   - Hangi sayfalarda?        │
            │   - Kaç tane?                │
            └──────────┬───────────────────┘
                       │
                       ▼
            ┌──────────────────────────────┐
            │   4. Table Extraction        │
            │   (pdfplumber/camelot)       │
            │   - Her tablo için:          │
            │     * Başlıklar              │
            │     * Satırlar               │
            │     * DataFrame              │
            └──────────┬───────────────────┘
                       │
                       ├─────────┬──────────┬─────────┐
                       │         │          │         │
                       ▼         ▼          ▼         ▼
              ┌────────────┐ ┌──────┐ ┌──────┐ ┌────────┐
              │ JSON       │ │ Excel│ │ CSV  │ │ Pandas │
              │ Output     │ │ File │ │ File │ │ DataFrame│
              └────────────┘ └──────┘ └──────┘ └────────┘
```

### Detaylı Modül Tasarımı

#### Modül 1: PDF Reader (`services/pdf_reader.py`)

**Sorumluluk**: PDF'i okuma ve temel bilgi çıkarma

```python
class PDFReader:
    """
    PyMuPDF kullanarak PDF okuma ve temel analiz
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = None  # fitz.Document
        
    def open(self):
        """PDF'i aç"""
        
    def get_metadata(self) -> dict:
        """
        Metadata çıkar:
        - title, author, subject, keywords
        - creation_date, modification_date
        - page_count
        - file_size
        - pdf_version
        """
        
    def get_page_count(self) -> int:
        """Toplam sayfa sayısı"""
        
    def extract_text(self, page_num: int = None) -> str | dict:
        """
        Text extraction
        
        Args:
            page_num: Belirli sayfa (None ise tüm sayfa)
            
        Returns:
            Tek sayfa: str
            Tüm sayfa: {1: "text", 2: "text", ...}
        """
        
    def extract_text_with_layout(self, page_num: int) -> dict:
        """
        Layout bilgisiyle text extraction
        
        Returns:
            {
                "text": "...",
                "blocks": [
                    {
                        "bbox": [x0, y0, x1, y1],
                        "text": "...",
                        "font": "Arial",
                        "size": 12
                    }
                ]
            }
        """
        
    def get_page_dimensions(self, page_num: int) -> dict:
        """
        Sayfa boyutları
        
        Returns:
            {
                "width": 595.0,
                "height": 842.0,
                "orientation": "portrait"
            }
        """
        
    def extract_images(self, page_num: int = None) -> list:
        """Sayfadaki görselleri çıkar"""
        
    def close(self):
        """PDF'i kapat"""
```

#### Modül 2: Table Extractor (`services/table_extractor.py`)

**Sorumluluk**: PDF'den tablo bulma ve çıkarma

```python
class TableExtractor:
    """
    pdfplumber ve camelot ile tablo extraction
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        
    def detect_tables(self) -> dict:
        """
        Hangi sayfalarda tablo var tespit et
        
        Returns:
            {
                1: 2,  # Sayfa 1'de 2 tablo
                3: 1,  # Sayfa 3'te 1 tablo
                ...
            }
        """
        
    def extract_tables_from_page(
        self, 
        page_num: int,
        method: str = "pdfplumber"  # veya "camelot"
    ) -> list[pd.DataFrame]:
        """
        Belirli sayfadan tabloları çıkar
        
        Returns:
            [DataFrame1, DataFrame2, ...]
        """
        
    def extract_all_tables(self) -> dict:
        """
        Tüm PDF'den tabloları çıkar
        
        Returns:
            {
                "page_1": {
                    "table_1": pd.DataFrame(...),
                    "table_2": pd.DataFrame(...)
                },
                "page_3": {
                    "table_1": pd.DataFrame(...)
                }
            }
        """
        
    def table_to_dict(self, df: pd.DataFrame) -> dict:
        """
        DataFrame'i JSON-friendly dict'e çevir
        
        Returns:
            {
                "headers": ["Col1", "Col2", "Col3"],
                "rows": [
                    ["val1", "val2", "val3"],
                    ["val4", "val5", "val6"]
                ],
                "row_count": 2,
                "col_count": 3
            }
        """
```

#### Modül 3: Export Manager (`services/export_manager.py`)

**Sorumluluk**: Çıktıları farklı formatlara dönüştürme

```python
class ExportManager:
    """
    Çıkarılan veriyi farklı formatlarda export etme
    """
    
    def export_to_json(self, data: dict, output_path: str = None) -> str | dict:
        """
        JSON formatında export
        
        Args:
            data: Export edilecek veri
            output_path: Dosya yolu (None ise string döner)
            
        Returns:
            JSON string veya dosya yolu
        """
        
    def export_to_excel(
        self, 
        tables: dict[str, pd.DataFrame],
        output_path: str,
        include_text: bool = False,
        text_data: dict = None
    ) -> str:
        """
        Excel formatında export
        
        Args:
            tables: {"Sheet1": df1, "Sheet2": df2}
            output_path: Excel dosya yolu
            include_text: Ayrı sheet'te text ekle
            text_data: Text verileri
            
        Returns:
            Oluşturulan dosya yolu
        """
        
    def export_to_csv(
        self,
        tables: list[pd.DataFrame],
        output_dir: str
    ) -> list[str]:
        """
        Her tablo için ayrı CSV
        
        Returns:
            CSV dosya yolları listesi
        """
        
    def create_combined_output(
        self,
        text_data: dict,
        tables: dict,
        metadata: dict
    ) -> dict:
        """
        Tüm veriyi tek JSON'da birleştir
        
        Returns:
            {
                "metadata": {...},
                "pages": [
                    {
                        "page_number": 1,
                        "text": "...",
                        "tables": [...]
                    }
                ],
                "all_text": "...",
                "table_count": 3
            }
        """
```

#### Modül 4: PDF Analyzer (`services/pdf_analyzer.py`)

**Sorumluluk**: Yukarıdaki modülleri orkestra etme

```python
class PDFAnalyzer:
    """
    Tüm PDF işlemlerini koordine eden ana sınıf
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.reader = PDFReader(pdf_path)
        self.table_extractor = TableExtractor(pdf_path)
        self.export_manager = ExportManager()
        
    def analyze_full(self) -> dict:
        """
        Tam analiz: text + tables + metadata
        
        Returns:
            {
                "metadata": {...},
                "text": {...},
                "tables": {...},
                "statistics": {
                    "total_pages": 10,
                    "total_tables": 5,
                    "total_chars": 15000,
                    "has_images": True
                }
            }
        """
        
    def extract_text_only(self) -> dict:
        """Sadece text extraction"""
        
    def extract_tables_only(self) -> dict:
        """Sadece tablo extraction"""
        
    def export_as_excel(self, output_path: str, include_text: bool = True):
        """Direkt Excel çıktı"""
        
    def export_as_json(self, output_path: str = None):
        """Direkt JSON çıktı"""
```

### API Endpoint Tasarımı (FastAPI)

#### Endpoint 1: Tam Analiz
```
POST /api/v1/analyze/full

Request:
- file: PDF (multipart/form-data)

Response:
{
  "metadata": {
    "title": "Fatura",
    "pages": 3,
    "file_size": "245 KB"
  },
  "text": {
    "page_1": "...",
    "page_2": "...",
    "page_3": "..."
  },
  "tables": {
    "page_1": [
      {
        "headers": ["Ürün", "Adet", "Fiyat"],
        "rows": [...]
      }
    ]
  },
  "statistics": {
    "total_pages": 3,
    "total_tables": 2,
    "total_chars": 5000
  }
}
```

#### Endpoint 2: Sadece Text
```
POST /api/v1/extract/text

Request:
- file: PDF
- pages: [1, 2] (optional - belirli sayfalar)
- preserve_layout: true/false (optional)

Response:
{
  "text": {
    "page_1": "...",
    "page_2": "..."
  },
  "all_text": "...",
  "char_count": 5000
}
```

#### Endpoint 3: Sadece Tablolar
```
POST /api/v1/extract/tables

Request:
- file: PDF
- method: "pdfplumber" | "camelot" (optional)
- pages: [1, 3] (optional)

Response:
{
  "tables": {
    "page_1": {
      "table_1": {
        "headers": [...],
        "rows": [[...], [...]]
      }
    }
  },
  "total_tables": 2
}
```

#### Endpoint 4: Excel Export
```
POST /api/v1/export/excel

Request:
- file: PDF
- include_text: true/false
- sheet_per_table: true/false

Response:
(Binary Excel file download)

Headers:
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="output.xlsx"
```

#### Endpoint 5: CSV Export
```
POST /api/v1/export/csv

Request:
- file: PDF

Response:
(ZIP file containing multiple CSVs)

Headers:
Content-Type: application/zip
Content-Disposition: attachment; filename="tables.zip"
```

#### Endpoint 6: JSON Export
```
POST /api/v1/export/json

Request:
- file: PDF
- format: "structured" | "flat" (optional)

Response:
{
  // Tam JSON çıktı
}
```

### Veri Modelleri (Pydantic)

```python
# models/request_models.py

class TextExtractionRequest(BaseModel):
    pages: Optional[List[int]] = None
    preserve_layout: bool = False
    
class TableExtractionRequest(BaseModel):
    pages: Optional[List[int]] = None
    method: Literal["pdfplumber", "camelot"] = "pdfplumber"
    
class ExcelExportRequest(BaseModel):
    include_text: bool = True
    sheet_per_table: bool = True
    add_styling: bool = True

# models/response_models.py

class PDFMetadata(BaseModel):
    title: Optional[str]
    author: Optional[str]
    subject: Optional[str]
    keywords: Optional[str]
    creator: Optional[str]
    producer: Optional[str]
    creation_date: Optional[str]
    modification_date: Optional[str]
    page_count: int
    file_size_bytes: int
    pdf_version: str

class TableData(BaseModel):
    headers: List[str]
    rows: List[List[Any]]
    row_count: int
    col_count: int

class PageText(BaseModel):
    page_number: int
    text: str
    char_count: int

class FullAnalysisResponse(BaseModel):
    metadata: PDFMetadata
    text: Dict[str, str]  # {page_num: text}
    tables: Dict[str, List[TableData]]  # {page_num: [tables]}
    statistics: Dict[str, Any]
    processing_time: float
```

### Örnek Kullanım Senaryoları

#### Senaryo 1: Fatura PDF'i - Sadece Text
```python
import requests

with open("fatura.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/extract/text",
        files={"file": f}
    )

data = response.json()
print(data["all_text"])
```

#### Senaryo 2: Rapor PDF'i - Tabloları Excel'e
```python
with open("rapor.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/export/excel",
        files={"file": f},
        data={"include_text": True}
    )

with open("output.xlsx", "wb") as f:
    f.write(response.content)
```

#### Senaryo 3: Belge - Tam Analiz JSON
```python
with open("belge.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/analyze/full",
        files={"file": f}
    )

data = response.json()
# data["metadata"] - dosya bilgileri
# data["text"] - tüm text
# data["tables"] - tüm tablolar
```

### Performans Beklentileri

**PyMuPDF Text Extraction**:
- 10 sayfa: ~0.5 saniye
- 50 sayfa: ~2 saniye
- 100 sayfa: ~4 saniye

**pdfplumber Table Extraction**:
- 1 tablo: ~0.2 saniye
- 10 tablo: ~2 saniye
- Kompleks tablo: ~1-3 saniye

**Excel Export**:
- 5 tablo: ~0.5 saniye
- 20 tablo: ~2 saniye

### Hata Yönetimi

```python
class PDFProcessingError(Exception):
    """Base exception"""

class InvalidPDFError(PDFProcessingError):
    """Geçersiz veya bozuk PDF"""

class TableExtractionError(PDFProcessingError):
    """Tablo extraction hatası"""

class ExportError(PDFProcessingError):
    """Export hatası"""
```

### Konfigürasyon

```env
# PDF Processing
PDF_MAX_SIZE_MB=50
PDF_MAX_PAGES=100
PDF_DPI=300  # Görüntü extraction için

# Table Extraction
TABLE_DETECTION_METHOD=pdfplumber  # veya camelot
TABLE_MIN_ROWS=2
TABLE_MIN_COLS=2

# Export
EXCEL_MAX_SHEETS=50
EXCEL_ENGINE=openpyxl
CSV_DELIMITER=,
CSV_ENCODING=utf-8

# API
API_HOST=0.0.0.0
API_PORT=8000
UPLOAD_FOLDER=./uploads
TEMP_FOLDER=./temp
```

### Proje Yapısı

```
ePDF/
├── README.md
├── ARCHITECTURE.md
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── config/
│   ├── __init__.py
│   └── settings.py
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request_models.py
│   │   └── response_models.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_reader.py           # PyMuPDF
│   │   ├── table_extractor.py      # pdfplumber + camelot
│   │   ├── export_manager.py       # Export işlemleri
│   │   └── pdf_analyzer.py         # Ana orchestrator
│   └── utils/
│       ├── __init__.py
│       ├── validators.py           # File validation
│       └── helpers.py              # Helper functions
├── uploads/                         # Temporary uploads
├── temp/                           # Temporary processing
└── tests/
    ├── __init__.py
    ├── test_pdf_reader.py
    ├── test_table_extractor.py
    └── sample_pdfs/
```

### Bağımlılıklar (requirements.txt)

```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# PDF Processing
PyMuPDF==1.23.8
pdfplumber==0.10.3
camelot-py[cv]==0.11.0

# Data Processing
pandas==2.1.3
numpy==1.26.2

# Excel/CSV
openpyxl==3.1.2
xlsxwriter==3.1.9

# Validation
pydantic==2.5.0
pydantic-settings==2.1.0

# Utils
python-dotenv==1.0.0
```

---

## 🔄 Sonraki Adım: Katman 2 (Henüz Değil)

Katman 1 tamamlandıktan sonra:
- Multimodal LLM entegrasyonu (Qwen2.5-VL)
- OCR için görüntü işleme
- Semantik analiz
- Keyword/Schema extraction

Ama şimdilik **SADECE KATMAN 1'e odaklanacağız**.

---

Bu dokümantasyon Katman 1'in detaylı blueprint'idir. Kod yazımına bu dokümana göre başlayacağız.
