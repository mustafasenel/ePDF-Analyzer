import base64
import requests
import json
import os # Dosya yolunu kontrol etmek için

# Yerel görsel dosyanızın yolu
# Lütfen bu yolu kendi dosyanızın gerçek yoluna göre güncelleyin.
local_image_path = "/Users/senel/Downloads/WhatsApp Image 2024-11-10 at 14.05.48.jpeg"

# Dosyanın var olup olmadığını kontrol et
if not os.path.exists(local_image_path):
    print(f"Hata: Belirtilen dosya bulunamadı: {local_image_path}")
    exit()

# Görseli Base64 olarak oku
try:
    with open(local_image_path, "rb") as f:
        b64_image = base64.b64encode(f.read()).decode("utf-8")
except Exception as e:
    print(f"Görsel dosyası okunurken hata oluştu: {e}")
    exit()

# Sizin OCR post-processing ve fatura normalizasyonu prompt'unuz
prompt = """
You are an expert in OCR post-processing and invoice normalization.

You will receive the raw OCR text extracted from an invoice.  
Invoices may come from different companies, and the table column order, names, or formats may vary.  
Your task is to extract and normalize all useful data into a structured JSON with three main parts:

1. invoice_meta: General information about the invoice:
   - Firma: the company name (seller/supplier) at the top of the invoice
   - Rechnungsnummer (Invoice number)
   - Rechnungsdatum (Invoice date)

2. invoice_data: Line items of the invoice table.  
   Each row should have:
   - ArtikelNumber: product code (usually numeric/alphanumeric, first or second column)
   - ArtikelBez: product description (free text, product name)
   - Kolli: number of packages (integer)
   - Inhalt: number of items per package (integer)
   - Menge: total quantity (Kolli × Inhalt)
   - Preis: price per unit (float)
   - Netto: total line amount (Menge × Preis)
   - MwSt: VAT rate for this line item (typically 7 or 19, as integer) - ONLY include if explicitly present in the invoice table. Do not add this field if the invoice does not have a VAT column.

3. invoice_summary: Extract financial totals from the invoice footer. This section may not be present on all pages, especially on first pages of multi-page invoices. It will typically be found on the LAST page of the invoice. If NO financial totals are found at all, return null for this entire section.
   
   When financial totals ARE found, you MUST extract and calculate these fields:
   
   REQUIRED FIELDS (must always be present or calculated):
   - total_vat: Total VAT amount (Gesamte MwSt / Gesamt-Steuer) - REQUIRED
   - total_net: Total net amount before VAT (Gesamtbetrag netto / Zwischensumme) - REQUIRED
   - total_gross: Final total gross amount including VAT (Gesamtbetrag brutto / Endbetrag) - REQUIRED
   
   OPTIONAL FIELDS (only include if explicitly present):
   - vat_7: 7% VAT amount (7% MwSt) - OPTIONAL, only if this rate is used
   - vat_19: 19% VAT amount (19% MwSt) - OPTIONAL, only if this rate is used
   
   CRITICAL CALCULATION RULES:
   - If you see total_net and total_gross, calculate: total_vat = total_gross - total_net
   - If you see vat_7 and vat_19, calculate: total_vat = vat_7 + vat_19
   - If you see total_vat and total_net, calculate: total_gross = total_net + total_vat
   - Always verify the equation: total_net + total_vat = total_gross
   - If explicit VAT rate lines are shown (e.g., "7% MwSt: 160,99" or "19% MwSt: 450,00"), include vat_7 and/or vat_19
   - If no separate VAT rates are shown, DO NOT include vat_7 or vat_19 in the output
   
   CALCULATION PRIORITY:
   1. First, look for explicit total amounts in the invoice footer
   2. If total_net and total_gross are found, calculate total_vat
   3. If separate VAT rates (7%, 19%) are explicitly shown, extract them as vat_7 and vat_19
   4. Always perform mathematical verification to ensure accuracy

### Important Rules & Data Validation:
- Your primary task is not just to extract, but to ensure the final JSON is logically correct.
- Common Sense Price & Number Validation: You are processing invoices for retail/grocery goods. A single unit price (Preis) or quantity will be a reasonable number, almost never in the thousands or millions. If you encounter an ambiguous number like 1,234, it is overwhelmingly likely to be 1.234 (one and a bit), NOT one thousand two hundred thirty-four. Use this context to correctly interpret decimal separators (',' or '.') based on the most logical value for the item.
- Handling OCR Zero-Padding Errors: OCR can produce numbers with excessive trailing zeros after a decimal separator, like 2,3900000 or 15,50000. You must correctly interpret these as 2.39 and 15.5 respectively. Do not interpret the trailing zeros as part of a larger number.
- CRITICAL VALIDATION: For every line item, you MUST perform these calculations:
  1. Calculate Menge: Menge must be the result of Kolli * Inhalt. If the OCR text shows a different Menge, ignore it and use your calculated value.
  2. Calculate Netto: Netto must be the result of your calculated Menge * Preis. If the OCR text shows a different Netto, ignore it and use your calculated value.
- Trust your calculations over the raw OCR text for Menge and Netto to correct potential OCR errors.
- Column headers may vary across companies, always map to the target fields above.
- Normalize numeric formats: use a dot . as decimal separator, remove currency signs. All currency values (Preis, Netto, totals) must be numbers with up to 3 decimal places.
- Normalize date formats: The invoice date Rechnungsdatum must always be converted to dd.MM.yyyy format (e.g., 24.10.2025).
- Output must always be valid JSON with exactly this structure:
  {
    "invoice_meta": { ... },
    "invoice_data": [ ... ],
    "invoice_summary": { 
      "vat_7": number (optional),
      "vat_19": number (optional),
      "total_vat": number (required),
      "total_net": number (required),
      "total_gross": number (required)
    } or null
  }
    
###CRITICAL INSTRUCTIONS FOR JSON FORMATTING:
- Your entire response must be ONLY the raw JSON object. Do not include any text, explanations, or markdown like json.
- The JSON must be perfectly valid. Pay close attention to syntax.
- CRITICAL: Do not use trailing commas. The last element in any array or object must NOT be followed by a comma. This is a common mistake you must avoid.
- Ensure all strings are enclosed in double quotes.

Your response must start with { and end with }.
    """

# API endpoint'iniz
api_url = "https://bfsv7d0asfh36k-8000.proxy.runpod.net/describe_image/"

# İstek için payload'ı oluştur
payload = {
    "base64_image": b64_image,     # Base64 kodlu görseli burada gönderiyoruz
    "text_prompt": prompt,         # Sizin prompt'unuz
    "max_new_tokens": 4000         # Max token limiti
}

headers = {
    "Content-Type": "application/json"
}

try:
    res = requests.post(api_url, headers=headers, data=json.dumps(payload))
    res.raise_for_status() # HTTP hatalarını (4xx veya 5xx) kontrol et

    response_data = res.json()
    print("API Yanıtı:")
    # Pretty-print the JSON response for better readability
    print(json.dumps(response_data, indent=2, ensure_ascii=False))

except requests.exceptions.RequestException as e:
    print(f"API isteği sırasında bir HTTP veya bağlantı hatası oluştu: {e}")
    if res is not None:
        print(f"Sunucu durumu: {res.status_code}")
        print(f"Sunucu yanıtı (RAW): {res.text}")
except json.JSONDecodeError:
    print(f"API'den gelen yanıt geçerli bir JSON formatında değil.")
    if res is not None:
        print(f"Sunucu yanıtı (RAW): {res.text}")
except Exception as e:
    print(f"Beklenmeyen bir hata oluştu: {e}")