import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { UploadSection } from '@/components/efatura/UploadSection'
import { ResultsDisplay } from '@/components/efatura/ResultsDisplay'
import { DocumentationSection } from '@/components/efatura/DocumentationSection'

interface InvoiceData {
  document_type: string
  template_id: string
  sender: {
    tax_id: string | null
    tax_id_type: string | null
    name: string | null
    address: string | null
    tax_office: string | null
  }
  recipient: {
    tax_id: string | null
    tax_id_type: string | null
    name: string | null
    address: string | null
    tax_office: string | null
  }
  invoice_metadata: Record<string, any>
  totals: Record<string, any>
  line_items: Array<Record<string, any>>
  processing_time: number
  status: string
}

export default function TemplateFatura() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<InvoiceData | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileUpload = (uploadedFile: File) => {
    setFile(uploadedFile)
    setResult(null)
    setError(null)
  }

  const handleAnalyze = async () => {
    if (!file) return

    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('template_id', 'tr_efatura')

    try {
      const response = await fetch('/api/v1/extract/template', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bir hata oluştu')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">E-Fatura Analyzer</h1>
        <p className="text-muted-foreground mt-1">
          LLM destekli otomatik e-fatura analizi
        </p>
      </div>

      <Tabs defaultValue="test" className="w-full">
        <TabsList>
          <TabsTrigger value="test">Test & Sonuçlar</TabsTrigger>
          <TabsTrigger value="docs">API Dokümantasyonu</TabsTrigger>
        </TabsList>

        <TabsContent value="test" className="space-y-6 mt-6">
          <div className="max-w-2xl">
            <UploadSection
              onUpload={handleFileUpload}
              onAnalyze={handleAnalyze}
              loading={loading}
              error={error}
              file={file}
            />
          </div>

          {result && <ResultsDisplay data={result} />}
        </TabsContent>

        <TabsContent value="docs" className="mt-6">
          <DocumentationSection />
        </TabsContent>
      </Tabs>
    </div>
  )
}
