import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Upload, FileText, AlertCircle, Loader2, Table2, Download } from 'lucide-react'
import { JsonHighlight } from '@/components/JsonHighlight'

interface TableData {
  has_header: boolean
  headers: string[]
  rows: Array<Record<string, any>>
  row_count: number
  col_count: number
  note?: string
}

interface TablesExtractionResult {
  status: string
  tables: Record<string, TableData[]>
  total_tables: number
  page_count: number
  processing_time: number
}

export default function TablesOnly() {
  const [file, setFile] = useState<File | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TablesExtractionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedPage, setSelectedPage] = useState(1)
  const method = 'pdfplumber'  // Sadece pdfplumber kullanılıyor

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
    formData.append('method', method)

    try {
      const response = await fetch('/api/v1/extract/tables', {
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

  const handleExportExcel = async () => {
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/v1/export/tables-excel', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const error = await response.text()
        throw new Error(`Export failed: ${error}`)
      }

      // Download the file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${file.name.replace('.pdf', '')}_tables.xlsx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Export error:', err)
      alert(`Excel export başarısız: ${err instanceof Error ? err.message : 'Bilinmeyen hata'}`)
    }
  }

  const pageNumbers = result ? Object.keys(result.tables).map(key => 
    parseInt(key.replace('page_', ''))
  ).sort((a, b) => a - b) : []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Tables Only Extraction</h1>
        <p className="text-muted-foreground mt-1">
          PDF'den sadece tablo çıkarımı
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

                  <div className="flex gap-2 justify-center">
                    <Button onClick={handleAnalyze} disabled={loading}>
                      {loading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Çıkarılıyor...
                        </>
                      ) : (
                        'Tabloları Çıkar'
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

      {/* Results Section: PDF Viewer + Tables */}
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

          {/* Right: Tables Results */}
          <div className="space-y-4">
            {/* Summary */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <CardTitle className="text-base">Özet</CardTitle>
                <Button 
                  size="sm" 
                  onClick={handleExportExcel}
                  className="gap-2"
                >
                  <Download className="h-4 w-4" />
                  Excel İndir
                </Button>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Sayfa Sayısı:</span>
                    <Badge>{result.page_count}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Toplam Tablo:</span>
                    <Badge variant="secondary">{result.total_tables}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">İşlem Süresi:</span>
                    <Badge variant="secondary">{result.processing_time}s</Badge>
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
                  {pageNumbers && pageNumbers.length > 0 && pageNumbers.map((pageNum) => {
                    const pageKey = `page_${pageNum}`
                    const tableCount = result.tables[pageKey]?.length || 0
                    return (
                      <Button
                        key={pageNum}
                        variant={selectedPage === pageNum ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setSelectedPage(pageNum)}
                      >
                        {pageNum}
                        {tableCount > 0 && (
                          <Badge variant="secondary" className="ml-1 h-4 px-1 text-[10px]">
                            {tableCount}
                          </Badge>
                        )}
                      </Button>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Page Tables */}
            {result.tables && result.tables[`page_${selectedPage}`] && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    Sayfa {selectedPage} - Tablolar
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="tables">
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="tables">
                        <Table2 className="h-4 w-4 mr-1" />
                        Tables ({result.tables[`page_${selectedPage}`].length})
                      </TabsTrigger>
                      <TabsTrigger value="json">JSON</TabsTrigger>
                    </TabsList>

                    <TabsContent value="tables" className="mt-4">
                      <ScrollArea className="h-[500px] w-full">
                        {result.tables[`page_${selectedPage}`].length > 0 ? (
                          <div className="space-y-4">
                            {result.tables[`page_${selectedPage}`].map((table: TableData, idx: number) => (
                              <div key={idx} className="border rounded-lg p-3">
                                <div className="flex items-center justify-between mb-2">
                                  <h4 className="text-sm font-semibold">
                                    Tablo {idx + 1}
                                    {table.has_header && (
                                      <Badge variant="outline" className="ml-2 text-xs">
                                        Header
                                      </Badge>
                                    )}
                                  </h4>
                                  {table.note && (
                                    <span className="text-xs text-muted-foreground italic">
                                      {table.note}
                                    </span>
                                  )}
                                </div>
                                <div className="overflow-x-auto">
                                  <table className="w-full text-xs border-collapse">
                                    {table.headers && table.headers.length > 0 && (
                                      <thead>
                                        <tr className="bg-muted">
                                          {table.headers.map((header: string, i: number) => (
                                            <th key={i} className="border p-2 text-left font-medium">
                                              {header}
                                            </th>
                                          ))}
                                        </tr>
                                      </thead>
                                    )}
                                    <tbody>
                                      {table.rows && table.rows.length > 0 ? (
                                        table.rows.map((row: Record<string, any>, rIdx: number) => (
                                          <tr key={rIdx} className="border-b">
                                            {table.headers && table.headers.map((header: string, cIdx: number) => (
                                              <td key={cIdx} className="border p-2">
                                                {String(row[header] !== undefined && row[header] !== null ? row[header] : '')}
                                              </td>
                                            ))}
                                          </tr>
                                        ))
                                      ) : (
                                        <tr>
                                          <td colSpan={table.col_count} className="border p-2 text-center text-muted-foreground">
                                            Veri yok
                                          </td>
                                        </tr>
                                      )}
                                    </tbody>
                                  </table>
                                </div>
                                <p className="text-xs text-muted-foreground mt-2">
                                  {table.row_count} satır × {table.col_count} sütun
                                </p>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground text-center py-8">
                            Bu sayfada tablo bulunamadı
                          </p>
                        )}
                      </ScrollArea>
                    </TabsContent>

                    <TabsContent value="json" className="mt-4">
                      <ScrollArea className="h-[500px] w-full">
                        <JsonHighlight
                          json={JSON.stringify(result.tables[`page_${selectedPage}`], null, 2)}
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

