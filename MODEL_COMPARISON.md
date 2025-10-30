# LLM Model Karşılaştırması

## Mevcut Modeller

### 1. Qwen3-0.6B (Varsayılan) ⚡
- **Boyut:** ~600MB
- **RAM:** 1-2GB
- **CPU Hızı:** ~2-3 saniye/çıkarım
- **GPU Hızı:** ~0.5 saniye/çıkarım
- **Kalite:** Orta (basit şirket adları için yeterli)
- **Önerilen:** CPU ortamları için

### 2. Qwen2.5-1.5B (Daha İyi) 🎯
- **Boyut:** ~3GB
- **RAM:** 4-5GB
- **CPU Hızı:** ~5-8 saniye/çıkarım
- **GPU Hızı:** ~1-2 saniye/çıkarım
- **Kalite:** İyi (karmaşık şirket adları ve yapılandırılmış veri için)
- **Önerilen:** GPU ortamları için veya yüksek doğruluk gerektiğinde

## Model Değiştirme

### Yöntem 1: Config Dosyası

`config/settings.py` dosyasını düzenle:

```python
# LLM Settings
LLM_MODEL_NAME: str = "Qwen/Qwen2.5-1.5B"  # 0.6B yerine 1.5B
LLM_MAX_TOKENS: int = 256
LLM_TEMPERATURE: float = 0.1
```

### Yöntem 2: Environment Variable

`.env` dosyası oluştur (veya düzenle):

```bash
LLM_MODEL_NAME=Qwen/Qwen2.5-1.5B
```

### Yöntem 3: Sistem Environment

```bash
export LLM_MODEL_NAME="Qwen/Qwen2.5-1.5B"
python3 run.py
```

## Performans Karşılaştırması

| Özellik | 0.6B | 1.5B |
|---------|------|------|
| Model indirme süresi | ~2 dk | ~5 dk |
| İlk başlatma | ~5 sn | ~10 sn |
| Çıkarım/sayfa (CPU) | 2-3 sn | 5-8 sn |
| Çıkarım/sayfa (GPU) | 0.5 sn | 1-2 sn |
| Şirket adı doğruluğu | %75-80 | %90-95 |
| Adres doğruluğu | %70-75 | %85-90 |
| RAM kullanımı | 1-2GB | 4-5GB |

## Tavsiyeler

### 0.6B Kullan Eğer:
- ✅ CPU'da çalışıyorsan
- ✅ Hız önemliyse
- ✅ RAM sınırlıysa (< 4GB)
- ✅ Basit e-faturalar işliyorsan

### 1.5B Kullan Eğer:
- ✅ GPU varsa
- ✅ Doğruluk kritikse
- ✅ RAM yeterliyse (> 4GB)
- ✅ Karmaşık şirket adları var (çok uzun, kısaltmalar, vs.)

## Test Etme

Model değişikliğinden sonra test et:

```bash
# Servisi yeniden başlat
python3 run.py

# Log'da göreceksin:
# 📥 Loading LLM model: Qwen/Qwen2.5-1.5B
# (İlk çalıştırmada model indirilecek, ~3GB)
```

## Diğer Modeller

Gelecekte eklenebilir:
- `Qwen2.5-3B` - Daha yüksek doğruluk (ama çok yavaş)
- `Qwen2.5-7B` - Maksimum doğruluk (GPU gerekli, çok yavaş)

Not: 3B+ modeller CPU'da pratik değil, sadece GPU ile kullanılabilir.

