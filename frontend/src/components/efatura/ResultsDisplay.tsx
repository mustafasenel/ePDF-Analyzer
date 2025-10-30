import { CheckCircle2, User, Users, Package, Calculator } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'

interface AmountValue {
  amount: number
  currency: string
}

interface InvoiceData {
  document_type: string
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
  totals: Record<string, string | number | AmountValue | null>
  line_items: Array<Record<string, any>>
  processing_time: number
  status: string
}

interface ResultsDisplayProps {
  data: InvoiceData
}

export function ResultsDisplay({ data }: ResultsDisplayProps) {
  return (
    <div className="space-y-4">
      {/* Success Header */}
      <div className="flex items-center gap-2">
        <CheckCircle2 className="h-5 w-5 text-green-500" />
        <span className="font-semibold">Analiz Tamamlandı</span>
        <Badge variant="secondary" className="ml-2">{data.processing_time}s</Badge>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground font-normal">
              Fatura No
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">
              {data.invoice_metadata.fatura_no || '-'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground font-normal">
              Tarih
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">
              {data.invoice_metadata.tarih || '-'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground font-normal">
              Ödenecek
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-primary">
              {data.totals.odenecek_tutar 
                ? (typeof data.totals.odenecek_tutar === 'object' 
                    ? `${data.totals.odenecek_tutar.amount?.toLocaleString('tr-TR', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ${data.totals.odenecek_tutar.currency}` 
                    : data.totals.odenecek_tutar)
                : '-'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground font-normal">
              Ürün
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">
              {data.line_items?.length || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Parties */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <User className="h-4 w-4" />
              Gönderici
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <p className="text-muted-foreground">Şirket</p>
              <p className="font-medium">{data.sender.name || '-'}</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-muted-foreground">{data.sender.tax_id_type}</p>
                <p className="font-mono text-xs">{data.sender.tax_id || '-'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Vergi Dairesi</p>
                <p>{data.sender.tax_office || '-'}</p>
              </div>
            </div>
            <div>
              <p className="text-muted-foreground">Adres</p>
              <p className="text-xs">{data.sender.address || '-'}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Users className="h-4 w-4" />
              Alıcı
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <p className="text-muted-foreground">İsim</p>
              <p className="font-medium">{data.recipient.name || '-'}</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-muted-foreground">{data.recipient.tax_id_type}</p>
                <p className="font-mono text-xs">{data.recipient.tax_id || '-'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Vergi Dairesi</p>
                <p>{data.recipient.tax_office || '-'}</p>
              </div>
            </div>
            <div>
              <p className="text-muted-foreground">Adres</p>
              <p className="text-xs">{data.recipient.address || '-'}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Line Items */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Package className="h-4 w-4" />
            Ürün Kalemleri ({data.line_items?.length || 0})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px]">
            <div className="rounded-md border">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b bg-muted/50">
                    {data.line_items &&
                      data.line_items.length > 0 &&
                      Object.keys(data.line_items[0]).map((key) => (
                        <th
                          key={key}
                          className="px-3 py-2 text-left font-medium"
                        >
                          {key}
                        </th>
                      ))}
                  </tr>
                </thead>
                <tbody>
                  {data.line_items?.map((item, idx) => (
                    <tr key={idx} className="border-b">
                      {Object.values(item).map((value, vIdx) => (
                        <td key={vIdx} className="px-3 py-2">
                          {String(value)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Totals */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Calculator className="h-4 w-4" />
            Mali Toplamlar
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-2">
            {Object.entries(data.totals).map(([key, value]) => {
              // Handle both old format (string/number) and new format (object with amount + currency)
              let displayValue = '-'
              if (value) {
                if (typeof value === 'object' && value.amount !== undefined) {
                  // New format: {amount: number, currency: string}
                  displayValue = `${value.amount.toLocaleString('tr-TR', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ${value.currency}`
                } else {
                  // Old format: string or number
                  displayValue = `${value} TL`
                }
              }
              
              return (
                <div
                  key={key}
                  className="flex justify-between items-center p-3 rounded-md bg-muted/30"
                >
                  <span className="text-sm capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="font-semibold">
                    {displayValue}
                  </span>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Raw JSON */}
      <details className="group">
        <summary className="cursor-pointer text-sm font-medium hover:underline">
          Ham JSON Çıktısı
        </summary>
        <pre className="mt-2 p-4 rounded-lg bg-muted text-xs overflow-auto max-h-96">
          {JSON.stringify(data, null, 2)}
        </pre>
      </details>
    </div>
  )
}
