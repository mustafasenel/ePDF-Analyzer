import { useState, useEffect } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { Loader2, Upload, AlertCircle, Download, RotateCcw, FileJson, FileUp } from 'lucide-react'
import { SchemaBuilder } from '@/components/template-builder/SchemaBuilder'
import { TemplatePreview } from '@/components/template-builder/TemplatePreview'
import { JsonHighlight } from '@/components/JsonHighlight'
import { cleanTemplateForExport } from '@/utils/templateCleaner'
import type { Template, TemplateField } from '@/types/template'

const STORAGE_KEY = 'epdf_custom_template'

export default function CustomTemplate() {
  const [templateName, setTemplateName] = useState('')
  const [description, setDescription] = useState('')
  const [fields, setFields] = useState<TemplateField[]>([])
  const [importJson, setImportJson] = useState('')
  const [importError, setImportError] = useState<string | null>(null)
  const [importSheetOpen, setImportSheetOpen] = useState(false)
  
  // Test state
  const [testFile, setTestFile] = useState<File | null>(null)
  const [testLoading, setTestLoading] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [testError, setTestError] = useState<string | null>(null)
  const [testTemplateJson, setTestTemplateJson] = useState('')

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setTemplateName(parsed.template_name || '')
        setDescription(parsed.description || '')
        setFields(parsed.fields || [])
      } catch (e) {
        console.error('Failed to load saved template:', e)
      }
    }
  }, [])

  // Save to localStorage when template changes
  useEffect(() => {
    if (templateName || description || fields.length > 0) {
      const template = {
        template_name: templateName,
        description: description,
        fields: fields,
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(template))
    }
  }, [templateName, description, fields])

  const template: Template = {
    template_name: templateName,
    description: description,
    fields: fields,
  }

  const handleImportJson = () => {
    setImportError(null)
    try {
      const parsed = JSON.parse(importJson)
      
      // Validate basic structure
      if (!parsed.template_name || !parsed.fields || !Array.isArray(parsed.fields)) {
        throw new Error('Geçersiz template yapısı. template_name ve fields array gerekli.')
      }

      // Load into state (which will also save to localStorage)
      setTemplateName(parsed.template_name)
      setDescription(parsed.description || '')
      setFields(parsed.fields)
      
      // Clear import area and close sheet
      setImportJson('')
      setImportError(null)
      setImportSheetOpen(false)
      
      // Show success
      setTimeout(() => {
        alert(`✅ Template başarıyla yüklendi!\n\n📋 ${parsed.fields.length} field inputlara yüklendi.\n🔧 Şimdi düzenleyebilirsin.`)
      }, 100)
    } catch (e) {
      setImportError(e instanceof Error ? e.message : 'Geçersiz JSON formatı')
    }
  }

  const handleReset = () => {
    if (confirm('Tüm template verilerini silmek istediğinize emin misiniz?')) {
      setTemplateName('')
      setDescription('')
      setFields([])
      setImportJson('')
      setImportError(null)
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  const handleExportJson = () => {
    // Clean template before export (remove id, return_as_list)
    const cleanedTemplate = cleanTemplateForExport(template)
    const json = JSON.stringify(cleanedTemplate, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${templateName || 'template'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleTestAnalyze = async () => {
    if (!testFile) return

    // Determine which template to use
    let templateToUse
    
    if (testTemplateJson.trim()) {
      // Use manually entered JSON
      try {
        templateToUse = JSON.parse(testTemplateJson)
      } catch (e) {
        setTestError('Invalid JSON format')
        return
      }
    } else if (templateName && fields.length > 0) {
      // Use builder template
      templateToUse = template
    } else {
      setTestError('Lütfen JSON şeması yapıştırın veya builder ile template oluşturun')
      return
    }

    setTestLoading(true)
    setTestError(null)
    setTestResult(null)

    const formData = new FormData()
    formData.append('file', testFile)
    formData.append('template', JSON.stringify(templateToUse))

    try {
      const response = await fetch('/api/v1/extract/custom', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setTestResult(data)
    } catch (err) {
      setTestError(err instanceof Error ? err.message : 'Bir hata oluştu')
    } finally {
      setTestLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Custom Template Builder</h1>
        <p className="text-muted-foreground mt-1">
          Kendi extraction template'inizi oluşturun
        </p>
      </div>

      <Tabs defaultValue="builder" className="w-full">
        <TabsList>
          <TabsTrigger value="builder">Template Builder</TabsTrigger>
          <TabsTrigger value="test">Test</TabsTrigger>
        </TabsList>

        <TabsContent value="builder" className="space-y-6 mt-6">
          {/* Quick Actions Bar */}
          <div className="flex gap-2 flex-wrap">
            <Sheet open={importSheetOpen} onOpenChange={setImportSheetOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="sm">
                  <FileUp className="mr-2 h-4 w-4" />
                  JSON'dan Yükle
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[600px] sm:max-w-[600px]">
                <SheetHeader>
                  <SheetTitle>JSON Şemasından İçe Aktar</SheetTitle>
                  <SheetDescription>
                    Hazır JSON şemasını yapıştır, otomatik olarak inputlara dönüşsün
                  </SheetDescription>
                </SheetHeader>
                <div className="mt-6 space-y-4">
                  <div className="space-y-2">
                    <Label>JSON Şeması</Label>
                    <textarea
                      className="w-full h-[400px] p-3 rounded-lg border bg-muted font-mono text-xs resize-none"
                      style={{
                        colorScheme: 'dark'
                      }}
                      placeholder={`{
  "template_name": "otel_faturasi",
  "description": "Otel konaklama faturaları için",
  "fields": [
    {
      "name": "otel_adi",
      "type": "string",
      "method": "llm",
      "prompt": "Extract hotel name",
      "region": "top_left"
    },
    {
      "name": "tarih",
      "type": "string",
      "method": "regex",
      "patterns": ["(\\\\d{2}[.-/]\\\\d{2}[.-/]\\\\d{4})"]
    }
  ]
}`}
                      value={importJson}
                      onChange={(e) => setImportJson(e.target.value)}
                    />
                  </div>
                  
                  {importError && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-xs">{importError}</AlertDescription>
                    </Alert>
                  )}
                  
                  <Button
                    onClick={handleImportJson}
                    disabled={!importJson.trim()}
                    className="w-full"
                  >
                    <FileJson className="mr-2 h-4 w-4" />
                    Yükle ve Inputlara Dönüştür
                  </Button>
                  
                  <Alert>
                    <AlertDescription className="text-xs">
                      JSON yüklendikten sonra aşağıdaki builder'da tüm field'lar düzenlenebilir hale gelir.
                    </AlertDescription>
                  </Alert>
                </div>
              </SheetContent>
            </Sheet>

            <Button
              onClick={handleExportJson}
              disabled={!templateName || fields.length === 0}
              variant="outline"
              size="sm"
            >
              <Download className="mr-2 h-4 w-4" />
              JSON İndir
            </Button>
            
            <Button
              onClick={handleReset}
              variant="outline"
              size="sm"
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Sıfırla
            </Button>

            <div className="ml-auto text-xs text-muted-foreground flex items-center gap-1">
              💾 Otomatik kaydediliyor
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1fr,480px]">
            {/* Left: Builder */}
            <div className="space-y-6">
              {/* Template Info */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    <span>Template Bilgileri</span>
                    {fields.length > 0 && (
                      <span className="text-xs font-normal text-muted-foreground">
                        {fields.length} field yüklü
                      </span>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Template Name</Label>
                    <Input
                      placeholder="otel_faturasi"
                      value={templateName}
                      onChange={(e) => setTemplateName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Açıklama</Label>
                    <Input
                      placeholder="Otel konaklama faturaları için"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                    />
                  </div>
                  {templateName && (
                    <Alert>
                      <AlertDescription className="text-xs">
                        ✅ Template hazır! Aşağıdan field'ları düzenleyebilir veya yeni ekleyebilirsin.
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              {/* Schema Builder */}
              <SchemaBuilder fields={fields} onFieldsChange={setFields} />
            </div>

            {/* Right: Preview (Sidebar) */}
            <div className="lg:sticky lg:top-4 h-fit">
              <TemplatePreview template={template} />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="test" className="space-y-6 mt-6">
          <div className="max-w-2xl space-y-6">
            {/* Template JSON Input */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Template JSON Şeması</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>JSON Template (opsiyonel - builder'dan otomatik alır)</Label>
                  <textarea
                    className="w-full h-48 p-3 rounded-lg border bg-muted font-mono text-xs resize-y"
                    placeholder={`{
  "template_name": "otel_faturasi",
  "description": "Otel konaklama faturaları için",
  "fields": [
    {
      "name": "otel_adi",
      "type": "string",
      "method": "regex",
      "patterns": ["otel\\\\s+ad[ıi]\\\\s*[:\\\\-]?\\\\s*(.+)"]
    }
  ]
}`}
                    value={testTemplateJson}
                    onChange={(e) => setTestTemplateJson(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Builder ile template oluşturduysan boş bırakabilirsin. Kendi JSON'ını test etmek istersen buraya yapıştır.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Upload */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">PDF Yükle ve Test Et</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="border-2 border-dashed rounded-lg p-8 text-center">
                  {!testFile ? (
                    <>
                      <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                      <label className="cursor-pointer">
                        <input
                          type="file"
                          accept=".pdf"
                          onChange={(e) => {
                            if (e.target.files?.[0]) {
                              setTestFile(e.target.files[0])
                              setTestResult(null)
                              setTestError(null)
                            }
                          }}
                          className="hidden"
                        />
                        <Button variant="outline" asChild>
                          <span>PDF Seç</span>
                        </Button>
                      </label>
                    </>
                  ) : (
                    <div className="space-y-4">
                      <div className="flex items-center justify-center gap-2">
                        <p className="font-medium">{testFile.name}</p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setTestFile(null)
                          setTestResult(null)
                        }}
                      >
                        Değiştir
                      </Button>
                    </div>
                  )}
                </div>

                {testError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{testError}</AlertDescription>
                  </Alert>
                )}

                <Button
                  onClick={handleTestAnalyze}
                  disabled={!testFile || testLoading}
                  className="w-full"
                >
                  {testLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analiz Ediliyor...
                    </>
                  ) : (
                    'Analiz Et'
                  )}
                </Button>

                {!testFile && (
                  <p className="text-sm text-muted-foreground text-center">
                    PDF yükleyin ve JSON şeması yapıştırın
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Results */}
            {testResult && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Sonuçlar</CardTitle>
                </CardHeader>
                <CardContent>
                  <JsonHighlight 
                    json={JSON.stringify(testResult, null, 2)}
                    className="p-4 rounded-lg bg-muted text-xs overflow-auto max-h-96 font-mono"
                  />
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

