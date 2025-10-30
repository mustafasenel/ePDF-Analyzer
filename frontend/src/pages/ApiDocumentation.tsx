import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { FileText, Table2, Download, FileJson, Sparkles, Wrench, Activity } from 'lucide-react'

export default function ApiDocumentation() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">API Documentation</h1>
        <p className="text-muted-foreground mt-1">
          ePDF Analyzer REST API - Tüm endpoint'ler ve kullanım örnekleri
        </p>
      </div>

      {/* Base URL */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Base URL</CardTitle>
        </CardHeader>
        <CardContent>
          <code className="px-3 py-1 rounded bg-muted text-sm">
            http://localhost:8000
          </code>
          <p className="text-xs text-muted-foreground mt-2">
            Tüm API istekleri bu base URL ile başlar
          </p>
        </CardContent>
      </Card>

      {/* API Categories */}
      <Tabs defaultValue="extraction" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="extraction">
            <FileText className="h-4 w-4 mr-1" />
            Extraction
          </TabsTrigger>
          <TabsTrigger value="export">
            <Download className="h-4 w-4 mr-1" />
            Export
          </TabsTrigger>
          <TabsTrigger value="template">
            <Sparkles className="h-4 w-4 mr-1" />
            Template
          </TabsTrigger>
          <TabsTrigger value="system">
            <Activity className="h-4 w-4 mr-1" />
            System
          </TabsTrigger>
        </TabsList>

        {/* EXTRACTION ENDPOINTS */}
        <TabsContent value="extraction" className="space-y-4">
          <div className="space-y-6">
              
              {/* Basic Extraction */}
              <EndpointCard
                method="POST"
                path="/api/v1/extract/basic"
                title="Basic Extraction"
                description="Sayfa bazında text ve tablo çıkarımı (yorumlama yok)"
                requestParams={[
                  { name: 'file', type: 'File', required: true, description: 'PDF dosyası' }
                ]}
                responseExample={`{
  "status": "success",
  "filename": "invoice.pdf",
  "page_count": 3,
  "pages": [
    {
      "page_number": 1,
      "text": "...",
      "tables": [...],
      "table_count": 2,
      "text_length": 1543
    }
  ],
  "processing_time": 1.23
}`}
                curlExample={`curl -X POST "http://localhost:8000/api/v1/extract/basic" \\
  -F "file=@invoice.pdf"`}
                pythonExample={`import requests

response = requests.post(
    "http://localhost:8000/api/v1/extract/basic",
    files={"file": open("invoice.pdf", "rb")}
)
print(response.json())`}
              />

              {/* Text Only */}
              <EndpointCard
                method="POST"
                path="/api/v1/extract/text"
                title="Text Only Extraction"
                description="Sadece text çıkarımı (layout opsiyonel)"
                requestParams={[
                  { name: 'file', type: 'File', required: true, description: 'PDF dosyası' },
                  { name: 'preserve_layout', type: 'boolean', required: false, description: 'Layout\'u koru (default: false)' }
                ]}
                responseExample={`{
  "status": "success",
  "text": {
    "page_1": "text...",
    "page_2": "text..."
  },
  "all_text": "combined text...",
  "char_count": 12543,
  "page_count": 5,
  "processing_time": 0.89
}`}
                curlExample={`curl -X POST "http://localhost:8000/api/v1/extract/text" \\
  -F "file=@document.pdf" \\
  -F "preserve_layout=true"`}
                pythonExample={`import requests

response = requests.post(
    "http://localhost:8000/api/v1/extract/text",
    files={"file": open("document.pdf", "rb")},
    data={"preserve_layout": "true"}
)
result = response.json()
print(f"Total characters: {result['char_count']}")
print(result['all_text'])`}
              />

              {/* Tables Only */}
              <EndpointCard
                method="POST"
                path="/api/v1/extract/tables"
                title="Tables Only Extraction"
                description="Sadece tablo çıkarımı (pdfplumber)"
                requestParams={[
                  { name: 'file', type: 'File', required: true, description: 'PDF dosyası' },
                  { name: 'method', type: 'string', required: false, description: 'Extraction method (default: pdfplumber)' }
                ]}
                responseExample={`{
  "status": "success",
  "tables": {
    "page_1": [
      {
        "has_header": true,
        "headers": ["Col1", "Col2"],
        "rows": [
          {"Col1": "val1", "Col2": "val2"}
        ],
        "row_count": 10,
        "col_count": 5
      }
    ]
  },
  "total_tables": 8,
  "page_count": 5,
  "processing_time": 2.45
}`}
                curlExample={`curl -X POST "http://localhost:8000/api/v1/extract/tables" \\
  -F "file=@invoice.pdf"`}
                pythonExample={`import requests

response = requests.post(
    "http://localhost:8000/api/v1/extract/tables",
    files={"file": open("invoice.pdf", "rb")}
)
result = response.json()
print(f"Total tables found: {result['total_tables']}")

# İlk sayfadaki tabloları göster
for i, table in enumerate(result['tables']['page_1'], 1):
    print(f"Table {i}: {table['row_count']}x{table['col_count']}")`}
              />

            </div>
        </TabsContent>

        {/* EXPORT ENDPOINTS */}
        <TabsContent value="export" className="space-y-4">
          <div className="space-y-6">
              
              {/* Tables Excel Export */}
              <EndpointCard
                method="POST"
                path="/api/v1/export/tables-excel"
                title="Export Tables to Excel"
                description="Tabloları Excel dosyası olarak export et"
                requestParams={[
                  { name: 'file', type: 'File', required: true, description: 'PDF dosyası' }
                ]}
                responseType="File"
                responseExample="Binary Excel file (.xlsx)"
                curlExample={`curl -X POST "http://localhost:8000/api/v1/export/tables-excel" \\
  -F "file=@invoice.pdf" \\
  -o output.xlsx`}
                pythonExample={`import requests

response = requests.post(
    "http://localhost:8000/api/v1/export/tables-excel",
    files={"file": open("invoice.pdf", "rb")}
)

with open("output.xlsx", "wb") as f:
    f.write(response.content)`}
              />

              {/* JSON Export */}
              <EndpointCard
                method="POST"
                path="/api/v1/export/json"
                title="Export to JSON"
                description="PDF içeriğini JSON olarak export et"
                requestParams={[
                  { name: 'file', type: 'File', required: true, description: 'PDF dosyası' },
                  { name: 'include_text', type: 'boolean', required: false, description: 'Text içeriğini dahil et' },
                  { name: 'include_tables', type: 'boolean', required: false, description: 'Tabloları dahil et' }
                ]}
                responseType="File"
                responseExample="JSON file"
                curlExample={`curl -X POST "http://localhost:8000/api/v1/export/json" \\
  -F "file=@invoice.pdf" \\
  -o output.json`}
                pythonExample={`import requests
import json

response = requests.post(
    "http://localhost:8000/api/v1/export/json",
    files={"file": open("invoice.pdf", "rb")},
    data={
        "include_text": "true",
        "include_tables": "true"
    }
)

# JSON dosyasını kaydet
with open("output.json", "wb") as f:
    f.write(response.content)

# JSON'u oku ve kullan
data = json.loads(response.content)
print(f"Extracted {len(data)} items")`}
              />

            </div>
        </TabsContent>

        {/* TEMPLATE ENDPOINTS */}
        <TabsContent value="template" className="space-y-4">
          <div className="space-y-6">
              
              {/* Template Extraction */}
              <EndpointCard
                method="POST"
                path="/api/v1/extract/template"
                title="Template Extraction (E-Fatura)"
                description="E-fatura için özel template ile structured data çıkarımı"
                requestParams={[
                  { name: 'file', type: 'File', required: true, description: 'PDF dosyası' },
                  { name: 'template_name', type: 'string', required: false, description: 'Template adı (default: e_fatura)' }
                ]}
                responseExample={`{
  "status": "success",
  "document_type": "e_fatura",
  "sender": {
    "name": "ABC Ltd.",
    "tax_id": "1234567890",
    "tax_id_type": "VKN",
    "address": "...",
    "tax_office": "..."
  },
  "recipient": {...},
  "invoice_metadata": {
    "fatura_no": "ABC2025001",
    "tarih": "01.01.2025",
    "senaryo": "TICARIFATURA"
  },
  "line_items": [...],
  "totals": {
    "mal_hizmet_toplam": {"amount": 1000.00, "currency": "TRY"},
    "hesaplanan_kdv": {"amount": 180.00, "currency": "TRY"},
    "odenecek_tutar": {"amount": 1180.00, "currency": "TRY"}
  },
  "processing_time": 3.45
}`}
                curlExample={`curl -X POST "http://localhost:8000/api/v1/extract/template" \\
  -F "file=@efatura.pdf" \\
  -F "template_name=e_fatura"`}
                pythonExample={`import requests

response = requests.post(
    "http://localhost:8000/api/v1/extract/template",
    files={"file": open("efatura.pdf", "rb")},
    data={"template_name": "e_fatura"}
)

result = response.json()
print(f"Document Type: {result['document_type']}")
print(f"Sender: {result['sender']['name']}")
print(f"Invoice No: {result['invoice_metadata']['fatura_no']}")
print(f"Total Amount: {result['totals']['odenecek_tutar']['amount']} {result['totals']['odenecek_tutar']['currency']}")
print(f"Line Items: {len(result['line_items'])}")`}
              />

              {/* List Templates */}
              <EndpointCard
                method="GET"
                path="/api/v1/templates"
                title="List Available Templates"
                description="Mevcut template'leri listele"
                requestParams={[]}
                responseExample={`{
  "templates": [
    {
      "name": "e_fatura",
      "description": "Turkish e-invoice template",
      "fields": [...]
    }
  ]
}`}
                curlExample={`curl -X GET "http://localhost:8000/api/v1/templates"`}
                pythonExample={`import requests

response = requests.get("http://localhost:8000/api/v1/templates")
templates = response.json()["templates"]

print(f"Available templates: {len(templates)}")
for template in templates:
    print(f"- {template['name']}: {template['description']}")`}
              />

              {/* Custom Template */}
              <EndpointCard
                method="POST"
                path="/api/v1/extract/custom"
                title="Custom Template Extraction"
                description="Kullanıcı tanımlı template ile extraction"
                requestParams={[
                  { name: 'file', type: 'File', required: true, description: 'PDF dosyası' },
                  { name: 'template_schema', type: 'JSON', required: true, description: 'Template şema JSON' }
                ]}
                responseExample={`{
  "status": "success",
  "extracted_data": {...},
  "processing_time": 2.15
}`}
                curlExample={`curl -X POST "http://localhost:8000/api/v1/extract/custom" \\
  -F "file=@document.pdf" \\
  -F 'template_schema={"template_name":"custom",...}'`}
                pythonExample={`import requests
import json

# Özel template şeması
schema = {
    "template_name": "invoice",
    "fields": [
        {
            "name": "invoice_number",
            "type": "string",
            "method": "regex",
            "pattern": "INV-\\d{6}",
            "description": "Invoice number"
        },
        {
            "name": "total_amount",
            "type": "number",
            "method": "fuzzy",
            "keywords": ["total", "amount", "toplam"],
            "description": "Total invoice amount"
        }
    ]
}

response = requests.post(
    "http://localhost:8000/api/v1/extract/custom",
    files={"file": open("document.pdf", "rb")},
    data={"template_schema": json.dumps(schema)}
)

result = response.json()
print(result["extracted_data"])`}
              />

            </div>
        </TabsContent>

        {/* SYSTEM ENDPOINTS */}
        <TabsContent value="system" className="space-y-4">
          <div className="space-y-6">
              
              {/* Health Check */}
              <EndpointCard
                method="GET"
                path="/health"
                title="Health Check"
                description="API durumunu kontrol et"
                requestParams={[]}
                responseExample={`{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-01T12:00:00Z"
}`}
                curlExample={`curl -X GET "http://localhost:8000/health"`}
                pythonExample={`import requests

response = requests.get("http://localhost:8000/health")
health = response.json()

if health["status"] == "healthy":
    print(f"✓ API is healthy (v{health['version']})")
else:
    print("✗ API is not healthy")`}
              />

              {/* Generate Regex */}
              <EndpointCard
                method="POST"
                path="/api/v1/generate-regex"
                title="Generate Regex Pattern"
                description="LLM ile doğal dilden regex pattern oluştur"
                requestParams={[
                  { name: 'description', type: 'string', required: true, description: 'Regex açıklaması (TR veya EN)' }
                ]}
                responseExample={`{
  "pattern": "\\d{2}\\.\\d{2}\\.\\d{4}",
  "description": "DD.MM.YYYY formatında tarih",
  "examples": ["01.01.2025", "31.12.2024"]
}`}
                curlExample={`curl -X POST "http://localhost:8000/api/v1/generate-regex" \\
  -F "description=10 haneli vergi kimlik numarası"`}
                pythonExample={`import requests

response = requests.post(
    "http://localhost:8000/api/v1/generate-regex",
    data={"description": "Email adresi"}
)
print(response.json()["pattern"])`}
              />

            </div>
        </TabsContent>
      </Tabs>

      {/* Common Headers */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Common Headers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between items-center">
              <code className="text-xs">Content-Type</code>
              <Badge variant="outline">multipart/form-data</Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              File upload içeren endpoint'ler için gerekli
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Error Codes */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">HTTP Status Codes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 text-sm">
            <div className="flex items-center gap-3">
              <Badge className="bg-green-500">200</Badge>
              <span>Success - İstek başarılı</span>
            </div>
            <div className="flex items-center gap-3">
              <Badge className="bg-yellow-500">400</Badge>
              <span>Bad Request - Geçersiz parametre</span>
            </div>
            <div className="flex items-center gap-3">
              <Badge className="bg-orange-500">422</Badge>
              <span>Unprocessable Entity - Validation hatası</span>
            </div>
            <div className="flex items-center gap-3">
              <Badge className="bg-red-500">500</Badge>
              <span>Internal Server Error - Sunucu hatası</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Endpoint Card Component
interface EndpointCardProps {
  method: 'GET' | 'POST'
  path: string
  title: string
  description: string
  requestParams: Array<{
    name: string
    type: string
    required: boolean
    description: string
  }>
  responseType?: string
  responseExample: string
  curlExample: string
  pythonExample?: string
}

function EndpointCard({
  method,
  path,
  title,
  description,
  requestParams,
  responseType,
  responseExample,
  curlExample,
  pythonExample
}: EndpointCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <Badge variant={method === 'GET' ? 'default' : 'secondary'} className="font-mono">
            {method}
          </Badge>
          <code className="text-sm font-mono">{path}</code>
        </div>
        <CardTitle className="text-lg mt-2">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        
        {/* Request Parameters */}
        {requestParams.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold mb-2">Request Parameters</h4>
            <div className="space-y-2">
              {requestParams.map((param, idx) => (
                <div key={idx} className="flex items-start gap-2 text-sm border-l-2 border-muted pl-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <code className="text-xs font-mono">{param.name}</code>
                      <Badge variant="outline" className="text-xs">{param.type}</Badge>
                      {param.required && <Badge variant="destructive" className="text-xs">required</Badge>}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{param.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <Separator />

        {/* Response */}
        <div>
          <h4 className="text-sm font-semibold mb-2">
            Response {responseType && <Badge variant="outline" className="ml-2 text-xs">{responseType}</Badge>}
          </h4>
          <pre className="text-xs bg-muted p-3 rounded font-mono whitespace-pre overflow-auto max-h-[250px]">
            {responseExample}
          </pre>
        </div>

        <Separator />

        {/* Examples */}
        <Tabs defaultValue="curl" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="curl">cURL</TabsTrigger>
            <TabsTrigger value="python">Python</TabsTrigger>
          </TabsList>
          
          <TabsContent value="curl">
            <pre className="text-xs bg-muted p-3 rounded font-mono whitespace-pre overflow-auto max-h-[200px]">
              {curlExample}
            </pre>
          </TabsContent>
          
          <TabsContent value="python">
            <pre className="text-xs bg-muted p-3 rounded font-mono whitespace-pre overflow-auto max-h-[200px]">
              {pythonExample || "Python örneği mevcut değil"}
            </pre>
          </TabsContent>
        </Tabs>

      </CardContent>
    </Card>
  )
}

