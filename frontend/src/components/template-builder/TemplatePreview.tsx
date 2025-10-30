import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { JsonHighlight } from '@/components/JsonHighlight'
import type { Template } from '@/types/template'

interface TemplatePreviewProps {
  template: Template
}

export function TemplatePreview({ template }: TemplatePreviewProps) {
  const [copied, setCopied] = useState(false)

  const jsonString = JSON.stringify(template, null, 2)

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">Template JSON</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopy}
            disabled={!template.template_name}
            className="h-7 text-xs"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 mr-1" />
                Kopyalandı
              </>
            ) : (
              <>
                <Copy className="h-3 w-3 mr-1" />
                Kopyala
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <ScrollArea className="h-[500px]">
          <JsonHighlight 
            json={jsonString}
            className="p-3 rounded-lg bg-muted text-[11px] leading-relaxed font-mono"
          />
        </ScrollArea>
      </CardContent>
    </Card>
  )
}

