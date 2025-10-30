import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Upload, FileText, AlertCircle, Loader2 } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { JsonHighlight } from '@/components/JsonHighlight'

interface PageText {
  page_number: number
  text: string
}

interface TextExtractionResult {
  status: string
  text: Record<string, string>
  all_text: string
  char_count: number
  page_count: number
  processing_time: number
}

export default function TextOnly() {
  const [file, setFile] = useState<File | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TextExtractionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedPage, setSelectedPage] = useState(1)
  const [preserveLayout, setPreserveLayout] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile)
      setError(null)
      setResult(null)
      
      const url = URL.createObjectURL(selectedFile)
      setPdfUrl(url)
    } else {
      setError('Lütfen geçerli bir PDF dosyası seçin')
    }
  }

  const handleAnalyze = async () => {
    if (!file) return

    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('preserve_layout', preserveLayout.toString())

    try {
      const response = await fetch('/api/v1/extract/text', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
      setSelectedPage(1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bir hata oluştu')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setPdfUrl(null)
    setResult(null)
    setError(null)
    setSelectedPage(1)
  }

  const pages = result ? Object.keys(result.text).map(key => {
    const pageNum = parseInt(key.replace('page_', ''))
    return {
      page_number: pageNum,
      text: result.text[key]
    }
  }).sort((a, b) => a.page_number - b.page_number) : []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Text Only Extraction</h1>
        <p className="text-muted-foreground mt-1">
          PDF'den sadece text çıkarımı
        </p>
      </div>

      {/* Upload Section */}
      {!result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">PDF Yükle</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border-2 border-dashed rounded-lg p-8 text-center">
              {!file ? (
                <>
                  <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <label className="cursor-pointer">
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handleFileChange}
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
                    <FileText className="h-5 w-5" />
                    <p className="font-medium">{file.name}</p>
                    <Badge variant="secondary">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-center gap-2">
                    <input
                      type="checkbox"
                      id="preserveLayout"
                      checked={preserveLayout}
                      onChange={(e) => setPreserveLayout(e.target.checked)}
                      className="w-4 h-4 rounded cursor-pointer"
                    />
                    <label htmlFor="preserveLayout" className="text-sm cursor-pointer">
                      Layout'u koru (boşluklar ve hizalama)
                    </label>
                  </div>

                  <div className="flex gap-2 justify-center">
                    <Button onClick={handleAnalyze} disabled={loading}>
                      {loading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Çıkarılıyor...
                        </>
                      ) : (
                        'Metni Çıkar'
                      )}
                    </Button>
                    <Button variant="outline" onClick={handleReset}>
                      Sıfırla
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Results Section: PDF Viewer + Text */}
      {result && pdfUrl && (
        <div className="grid gap-4 lg:grid-cols-2 min-h-[700px]">
          {/* Left: PDF Viewer */}
          <Card className="lg:sticky lg:top-4 h-fit max-h-[800px]">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="text-base">PDF Önizleme</CardTitle>
              <Button variant="outline" size="sm" onClick={handleReset}>
                Yeni PDF
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              <iframe
                src={`${pdfUrl}#page=${selectedPage}`}
                className="w-full h-[700px] border-0"
                title="PDF Preview"
              />
            </CardContent>
          </Card>

          {/* Right: Text Results */}
          <div className="space-y-4">
            {/* Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Özet</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Sayfa Sayısı:</span>
                    <Badge>{result.page_count}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Toplam Karakter:</span>
                    <Badge variant="secondary">{result.char_count.toLocaleString('tr-TR')}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">İşlem Süresi:</span>
                    <Badge variant="secondary">{result.processing_time}s</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Layout:</span>
                    <Badge variant={preserveLayout ? "default" : "outline"}>
                      {preserveLayout ? 'Korundu' : 'Normal'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Page Selector */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Sayfa Seç</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {pages && pages.length > 0 && pages.map((page) => (
                    <Button
                      key={page.page_number}
                      variant={selectedPage === page.page_number ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSelectedPage(page.page_number)}
                    >
                      {page.page_number}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Page Text */}
            {pages && pages.length > 0 && pages[selectedPage - 1] && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    Sayfa {selectedPage} - Veri
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="text">
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="text">
                        <FileText className="h-4 w-4 mr-1" />
                        Text
                      </TabsTrigger>
                      <TabsTrigger value="json">JSON</TabsTrigger>
                    </TabsList>

                    <TabsContent value="text" className="mt-4">
                      <ScrollArea className="h-[500px] w-full rounded-md border p-4">
                        <pre className="text-xs whitespace-pre-wrap font-mono">
                          {pages[selectedPage - 1].text || 'Metin bulunamadı'}
                        </pre>
                      </ScrollArea>
                      <p className="text-xs text-muted-foreground mt-2">
                        {pages[selectedPage - 1].text.length.toLocaleString('tr-TR')} karakter
                      </p>
                    </TabsContent>

                    <TabsContent value="json" className="mt-4">
                      <ScrollArea className="h-[500px] w-full">
                        <JsonHighlight
                          json={JSON.stringify(pages[selectedPage - 1], null, 2)}
                          className="p-4 rounded-lg bg-muted text-xs font-mono"
                        />
                      </ScrollArea>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

