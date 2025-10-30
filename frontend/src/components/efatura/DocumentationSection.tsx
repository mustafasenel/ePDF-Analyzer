import { BookOpen, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'

export function DocumentationSection() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <BookOpen className="h-4 w-4" />
          API Dokümantasyonu
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Endpoint */}
        <div className="space-y-3">
          <h3 className="font-semibold">Endpoint</h3>
          <div className="flex items-center gap-2">
            <Badge>POST</Badge>
            <code className="text-sm bg-muted px-2 py-1 rounded">
              /api/v1/extract/template
            </code>
          </div>
        </div>

        <Separator />

        {/* Parameters */}
        <div className="space-y-3">
          <h3 className="font-semibold">Parametreler</h3>
          <div className="rounded-md border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-3 py-2 text-left font-medium">Parametre</th>
                  <th className="px-3 py-2 text-left font-medium">Tip</th>
                  <th className="px-3 py-2 text-left font-medium">Zorunlu</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="px-3 py-2 font-mono text-xs">file</td>
                  <td className="px-3 py-2">
                    <Badge variant="outline" className="text-xs">File</Badge>
                  </td>
                  <td className="px-3 py-2">✅</td>
                </tr>
                <tr>
                  <td className="px-3 py-2 font-mono text-xs">template_id</td>
                  <td className="px-3 py-2">
                    <Badge variant="outline" className="text-xs">String</Badge>
                  </td>
                  <td className="px-3 py-2">✅</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <Separator />

        {/* Features */}
        <div className="space-y-3">
          <h3 className="font-semibold">Özellikler</h3>
          <ul className="space-y-1 text-sm">
            <li className="flex items-start gap-2">
              <ArrowRight className="h-4 w-4 mt-0.5 text-primary flex-shrink-0" />
              <span>Otomatik belge tanıma</span>
            </li>
            <li className="flex items-start gap-2">
              <ArrowRight className="h-4 w-4 mt-0.5 text-primary flex-shrink-0" />
              <span>LLM entity extraction (Qwen3 0.6B)</span>
            </li>
            <li className="flex items-start gap-2">
              <ArrowRight className="h-4 w-4 mt-0.5 text-primary flex-shrink-0" />
              <span>Akıllı tablo tespiti</span>
            </li>
            <li className="flex items-start gap-2">
              <ArrowRight className="h-4 w-4 mt-0.5 text-primary flex-shrink-0" />
              <span>Context-aware VKN/TCKN</span>
            </li>
          </ul>
        </div>

        <Separator />

        {/* Request Examples */}
        <div className="space-y-3">
          <h3 className="font-semibold">Request Örnekleri</h3>
          
          <div className="space-y-3">
            <div>
              <p className="text-sm font-medium mb-2">cURL</p>
              <pre className="p-3 rounded-lg bg-muted text-xs overflow-x-auto">
{`curl -X POST http://localhost:8000/api/v1/extract/template \\
  -H "Content-Type: multipart/form-data" \\
  -F "file=@fatura.pdf" \\
  -F "template_id=tr_efatura"`}
              </pre>
            </div>

            <div>
              <p className="text-sm font-medium mb-2">Python</p>
              <pre className="p-3 rounded-lg bg-muted text-xs overflow-x-auto">
{`import requests

files = {'file': ('fatura.pdf', open('fatura.pdf', 'rb'))}
data = {'template_id': 'tr_efatura'}

response = requests.post(
    'http://localhost:8000/api/v1/extract/template',
    files=files,
    data=data
)
result = response.json()`}
              </pre>
            </div>

            <div>
              <p className="text-sm font-medium mb-2">JavaScript</p>
              <pre className="p-3 rounded-lg bg-muted text-xs overflow-x-auto">
{`const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('template_id', 'tr_efatura');

const response = await fetch('/api/v1/extract/template', {
  method: 'POST',
  body: formData
});
const data = await response.json();`}
              </pre>
            </div>
          </div>
        </div>

        <Separator />

        {/* Response */}
        <div className="space-y-3">
          <h3 className="font-semibold">Response</h3>
          
          <div className="space-y-3">
            <div>
              <p className="text-sm font-medium mb-2">Success (200)</p>
              <pre className="p-3 rounded-lg bg-muted text-xs overflow-x-auto max-h-80">
{`{
  "status": "success",
  "processing_time": 8.05,
  "sender": {
    "tax_id": "3302632220",
    "tax_id_type": "VKN",
    "name": "EKREM ÖZANDIÇLAR OTO YEDEK PARÇA...",
    "address": "ÇINARLI MAH. 1572 SK. No:31...",
    "tax_office": "KARŞIYAKA"
  },
  "recipient": {
    "tax_id": "11111111111",
    "tax_id_type": "TCKN",
    "name": "Mustafa Şenel",
    "address": "Yukarı Mh. Yukarı Mah...",
    "tax_office": null
  },
  "invoice_metadata": {
    "fatura_no": "T012025000141713",
    "tarih": "31-08-2025",
    "ettn": "d1f5579c-47fd-4357-a65b-...",
    "senaryo": "EARSIVFATURA"
  },
  "totals": {
    "mal_hizmet_toplam": 1058.75,
    "hesaplanan_kdv": 207.51,
    "odenecek_tutar": 1245.09
  },
  "line_items": [
    {
      "Sıra No": "1",
      "Mal Hizmet": "Honda Civic Filtre...",
      "Miktar": "1 Adet",
      "Birim Fiyat": "1.058,75 TL"
    }
  ]
}`}
              </pre>
            </div>

            <div>
              <p className="text-sm font-medium mb-2">Error (422)</p>
              <pre className="p-3 rounded-lg bg-muted text-xs overflow-x-auto">
{`{
  "detail": "Template extraction error: ..."
}`}
              </pre>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
