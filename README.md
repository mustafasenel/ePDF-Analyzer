# ePDF - LLM Destekli PDF Analiz Servisi

## 📋 Proje Hakkında

**ePDF**, yapay zeka destekli akıllı bir PDF analiz ve veri çıkarım servisidir. Proje **2 katman** halinde geliştirilmektedir:

### ✅ Katman 1: Temel PDF İşleme (TAMAMLANDI)
Klasik PDF okuma ve işleme kütüphaneleri ile güçlü bir temel oluşturuldu:
- **PyMuPDF** ile hızlı text extraction
- **pdfplumber** ve **camelot** ile tablo çıkarımı
- Excel, JSON, CSV export özellikleri
- RESTful API ile kolay entegrasyon

### 🔜 Katman 2: LLM Entegrasyonu (PLANLANDI)
Multimodal model (Qwen2.5-VL) ile semantik analiz

---

## 🎯 Özellikler (Katman 1)

### PDF Okuma ve Analiz
- ✅ Hızlı metin çıkarımı (PyMuPDF)
- ✅ Layout korumalı text extraction
- ✅ PDF metadata okuma (yazar, tarih, sayfa sayısı, vb.)
- ✅ Otomatik tablo algılama ve çıkarımı
- ✅ Görüntü tespiti

### Tablo İşleme
- ✅ İki farklı tablo extraction motoru:
  - **pdfplumber**: Hızlı ve güvenilir
  - **camelot**: Kompleks tablolar için
- ✅ Otomatik tablo temizleme
- ✅ Sayfa bazında tablo organizasyonu

### Export Formatları
- ✅ **JSON**: Yapılandırılmış veri çıktısı
- ✅ **Excel**: Tablolar + metin içeriği (stil desteği)
- ✅ **CSV**: Her tablo için ayrı dosya

### API Endpoints
- `GET /health` - Sağlık kontrolü
- `POST /api/v1/analyze/full` - Tam analiz (text + tables + metadata)
- `POST /api/v1/extract/text` - Sadece metin çıkarımı
- `POST /api/v1/extract/tables` - Sadece tablo çıkarımı
- `POST /api/v1/export/excel` - Excel dosya indirme
- `POST /api/v1/export/json` - JSON çıktı

---

## 🚀 Kurulum

### Gereksinimler

- Python 3.9+
- pip veya poetry

### Adım Adım Kurulum

1. **Sanal ortam oluşturun**:
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# veya
venv\Scripts\activate  # Windows
```

2. **Bağımlılıkları yükleyin**:
```bash
pip install -r requirements.txt
```

3. **Ortam değişkenlerini ayarlayın** (opsiyonel):
```bash
cp env.example .env
# .env dosyasını düzenleyin
```

4. **Servisi başlatın**:
```bash
python run.py
```

API otomatik olarak şu adreste çalışacak:
- **API**: http://localhost:8000
- **Dökümantasyon**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📚 Kullanım Örnekleri

### 1. Tam Analiz (Text + Tables + Metadata)

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/full" \
  -F "file=@fatura.pdf" \
  -F "extract_text=true" \
  -F "extract_tables=true"
```

**Yanıt**:
```json
{
  "status": "success",
  "metadata": {
    "title": "Fatura",
    "page_count": 3,
    "file_size_formatted": "245.0 KB"
  },
  "text": {
    "page_1": "Fatura içeriği...",
    "page_2": "..."
  },
  "tables": {
    "page_1": [
      {
        "headers": ["Ürün", "Adet", "Fiyat"],
        "rows": [
          ["Kalem", "10", "5.00"],
          ["Defter", "5", "15.00"]
        ],
        "row_count": 2,
        "col_count": 3
      }
    ]
  },
  "statistics": {
    "total_pages": 3,
    "total_tables": 2,
    "total_chars": 1500,
    "pages_with_tables": [1, 3]
  },
  "processing_time": 2.5
}
```

### 2. Sadece Text Çıkarımı

```bash
curl -X POST "http://localhost:8000/api/v1/extract/text" \
  -F "file=@belge.pdf" \
  -F "preserve_layout=false"
```

**Yanıt**:
```json
{
  "status": "success",
  "text": {
    "page_1": "Sayfa 1 metni...",
    "page_2": "Sayfa 2 metni..."
  },
  "all_text": "Tüm sayfalardaki metin...",
  "char_count": 5000,
  "page_count": 2,
  "processing_time": 0.8
}
```

### 3. Sadece Tablo Çıkarımı

```bash
curl -X POST "http://localhost:8000/api/v1/extract/tables" \
  -F "file=@rapor.pdf" \
  -F "method=pdfplumber"
```

**Yanıt**:
```json
{
  "status": "success",
  "tables": {
    "page_1": [
      {
        "headers": ["Ay", "Gelir", "Gider"],
        "rows": [
          ["Ocak", "10000", "8000"],
          ["Şubat", "12000", "9000"]
        ],
        "row_count": 2,
        "col_count": 3
      }
    ]
  },
  "total_tables": 1,
  "processing_time": 1.2
}
```

### 4. Excel Export

```bash
curl -X POST "http://localhost:8000/api/v1/export/excel" \
  -F "file=@fatura.pdf" \
  -F "include_text=true" \
  -F "add_styling=true" \
  -o output.xlsx
```

Direkt olarak Excel dosyası indirilir. Her tablo ayrı sheet'te yer alır.

### 5. JSON Export

```bash
curl -X POST "http://localhost:8000/api/v1/export/json" \
  -F "file=@belge.pdf" \
  -F "include_text=true" \
  -F "include_tables=true" \
  -F "pretty=true"
```

Tüm veri yapılandırılmış JSON formatında döner.

---

## 🏗️ Proje Yapısı

```
ePDF/
├── README.md                    # Bu dosya
├── ARCHITECTURE.md              # Detaylı mimari döküman
├── requirements.txt             # Python bağımlılıkları
├── run.py                       # Ana çalıştırma scripti
├── env.example                  # Örnek ortam değişkenleri
├── .gitignore                   # Git ignore kuralları
├── config/
│   ├── __init__.py
│   └── settings.py              # Merkezi konfigürasyon
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI ana uygulaması
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request_models.py    # API istek modelleri
│   │   └── response_models.py   # API yanıt modelleri
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_reader.py        # PyMuPDF ile PDF okuma
│   │   ├── table_extractor.py   # pdfplumber/camelot ile tablo çıkarımı
│   │   ├── export_manager.py    # Export işlemleri
│   │   └── pdf_analyzer.py      # Ana orchestrator
│   └── utils/
│       ├── __init__.py
│       ├── validators.py        # Validasyon fonksiyonları
│       └── helpers.py           # Yardımcı fonksiyonlar
├── uploads/                     # Geçici yükleme klasörü
└── temp/                        # Geçici işlem klasörü
```

---

## ⚙️ Konfigürasyon

`.env` dosyası ile ayarlanabilir parametreler:

```env
# API Ayarları
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# PDF İşleme
PDF_MAX_SIZE_MB=50              # Maksimum dosya boyutu
PDF_MAX_PAGES=100               # Maksimum sayfa sayısı
PDF_DPI=300                     # Görüntü çözünürlüğü

# Tablo Çıkarımı
TABLE_DETECTION_METHOD=pdfplumber
TABLE_MIN_ROWS=2                # Minimum satır sayısı
TABLE_MIN_COLS=2                # Minimum sütun sayısı

# Export
EXCEL_MAX_SHEETS=50
CSV_ENCODING=utf-8

# Dosya Depolama
UPLOAD_FOLDER=./uploads
TEMP_FOLDER=./temp
```

---

## 🔧 Python'da Kullanım

```python
import requests

# 1. Tam analiz
with open("fatura.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/analyze/full",
        files={"file": f},
        data={
            "extract_text": True,
            "extract_tables": True
        }
    )
    data = response.json()
    print(f"Sayfa sayısı: {data['metadata']['page_count']}")
    print(f"Tablo sayısı: {data['statistics']['total_tables']}")

# 2. Excel indirme
with open("rapor.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/export/excel",
        files={"file": f},
        data={"include_text": True}
    )
    with open("output.xlsx", "wb") as excel_file:
        excel_file.write(response.content)

# 3. Sadece text
with open("belge.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/extract/text",
        files={"file": f}
    )
    text_data = response.json()
    print(text_data["all_text"])
```

---

## 📊 Performans

### Beklenen İşlem Süreleri

| İşlem | 10 Sayfa | 50 Sayfa |
|-------|----------|----------|
| Text extraction | ~0.5 saniye | ~2 saniye |
| Table extraction | ~2 saniye | ~10 saniye |
| Full analysis | ~3 saniye | ~15 saniye |
| Excel export | ~1 saniye | ~3 saniye |

*Performans PDF karmaşıklığına ve tablo sayısına bağlıdır.*

---

## 🐛 Hata Yönetimi

API standart HTTP durum kodları kullanır:

- **200**: Başarılı
- **400**: Geçersiz istek (dosya tipi, boyut vb.)
- **422**: İşlenemeyen varlık (PDF bozuk, tablo bulunamadı vb.)
- **500**: Sunucu hatası

Hata yanıtı formatı:
```json
{
  "detail": "Hata mesajı"
}
```

---

## 🔜 Gelecek Özellikler (Katman 2)

- [ ] Multimodal LLM entegrasyonu (Qwen2.5-VL)
- [ ] OCR desteği (taranmış PDF'ler için)
- [ ] Keyword bazlı semantik arama
- [ ] JSON schema ile veri çıkarımı
- [ ] Custom prompt desteği
- [ ] Batch processing (toplu PDF işleme)
- [ ] Web arayüzü

---

## 📖 Dokümantasyon

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **Mimari Döküman**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

---

## 📝 Notlar

- Geçici dosyalar otomatik olarak 24 saat sonra temizlenir
- Maksimum dosya boyutu varsayılan 50MB (ayarlanabilir)
- Desteklenen format: **sadece PDF**
- Tüm endpoint'ler `multipart/form-data` kabul eder

---

## 📄 Lisans

MIT License

---

## 🎉 Başlangıç

```bash
# Kurulum
pip install -r requirements.txt

# Çalıştır
python run.py

# Test et
curl http://localhost:8000/health
```

**Hazır!** API şimdi kullanıma hazır 🚀
