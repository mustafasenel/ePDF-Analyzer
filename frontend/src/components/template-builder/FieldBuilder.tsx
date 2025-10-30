import { useState } from 'react'
import { Plus, Trash2, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { TemplateField, FieldType, ExtractionMethod } from '@/types/template'

interface FieldBuilderProps {
  fields: TemplateField[]
  onFieldsChange: (fields: TemplateField[]) => void
}

export function FieldBuilder({ fields, onFieldsChange }: FieldBuilderProps) {
  const [editingField, setEditingField] = useState<Partial<TemplateField>>({
    type: 'text',
    method: 'regex',
    required: false,
    patterns: [''],
  })
  
  // Regex generator state
  const [regexPrompt, setRegexPrompt] = useState('')
  const [generatingRegex, setGeneratingRegex] = useState(false)
  const [regexError, setRegexError] = useState<string | null>(null)

  const handleAddField = () => {
    if (!editingField.name) return

    const newField: TemplateField = {
      id: Date.now().toString(),
      name: editingField.name,
      type: editingField.type || 'text',
      method: editingField.method || 'regex',
      required: editingField.required || false,
      patterns: editingField.patterns?.filter(p => p.trim()),
      prompt: editingField.prompt,
      region: editingField.region,
      keywords: editingField.keywords?.filter(k => k.trim()),
      array_separator: editingField.array_separator,
      array_item_type: editingField.array_item_type,
      object_properties: editingField.object_properties?.filter(p => p.trim()),
    }

    onFieldsChange([...fields, newField])
    
    // Reset form
    setEditingField({
      name: '',
      type: 'text',
      method: 'regex',
      required: false,
      patterns: [''],
    })
  }

  const handleRemoveField = (id: string) => {
    onFieldsChange(fields.filter(f => f.id !== id))
  }

  const handlePatternChange = (index: number, value: string) => {
    const newPatterns = [...(editingField.patterns || [])]
    newPatterns[index] = value
    setEditingField({ ...editingField, patterns: newPatterns })
  }

  const handleAddPattern = () => {
    setEditingField({
      ...editingField,
      patterns: [...(editingField.patterns || []), '']
    })
  }
  
  const handleGenerateRegex = async () => {
    if (!regexPrompt.trim()) return
    
    setGeneratingRegex(true)
    setRegexError(null)
    
    try {
      const formData = new FormData()
      formData.append('description', regexPrompt)
      
      const response = await fetch('/api/v1/generate-regex', {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate regex')
      }
      
      const data = await response.json()
      
      // Add generated pattern to patterns list
      const newPatterns = [...(editingField.patterns || []).filter(p => p.trim())]
      newPatterns.push(data.pattern)
      
      setEditingField({
        ...editingField,
        patterns: newPatterns
      })
      
      // Clear prompt
      setRegexPrompt('')
      
    } catch (err) {
      setRegexError(err instanceof Error ? err.message : 'Failed to generate regex')
    } finally {
      setGeneratingRegex(false)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[2fr,1fr] gap-6">
      {/* Left: Add Field Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Yeni Field Ekle</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Field Name</Label>
            <Input
              placeholder="otel_adi"
              value={editingField.name || ''}
              onChange={(e) =>
                setEditingField({ ...editingField, name: e.target.value })
              }
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Type</Label>
              <Select
                value={editingField.type}
                onValueChange={(value: FieldType) =>
                  setEditingField({ ...editingField, type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="text">Text</SelectItem>
                  <SelectItem value="number">Number</SelectItem>
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="array">Array</SelectItem>
                  <SelectItem value="object">Object</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Method</Label>
              <Select
                value={editingField.method}
                onValueChange={(value: ExtractionMethod) =>
                  setEditingField({
                    ...editingField,
                    method: value,
                    patterns: value === 'regex' ? [''] : undefined,
                    prompt: value === 'llm' ? '' : undefined,
                    keywords: value === 'fuzzy' ? [''] : undefined,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="regex">Regex</SelectItem>
                  <SelectItem value="llm">LLM</SelectItem>
                  <SelectItem value="fuzzy">Fuzzy</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={editingField.required}
                  onChange={(e) =>
                    setEditingField({
                      ...editingField,
                      required: e.target.checked,
                    })
                  }
                  className="rounded"
                />
                <span className="text-sm">Required</span>
              </label>
            </div>
          </div>

          {/* Method-specific inputs */}
          {editingField.method === 'regex' && (
            <div className="space-y-3">
              {/* AI Regex Generator */}
              <div className="p-3 rounded-lg border bg-muted/30 space-y-2">
                <Label className="flex items-center gap-2 text-sm">
                  <Sparkles className="h-4 w-4 text-primary" />
                  AI Regex Generator (LLM)
                </Label>
                <p className="text-xs text-muted-foreground">
                  Ne çıkarmak istediğini yaz, LLM regex oluşturur. Örn: "fatura numarası", "tarih formatı", "email adresi"
                </p>
                <div className="flex gap-2">
                  <Input
                    placeholder="Ne çıkarmak istiyorsun?"
                    value={regexPrompt}
                    onChange={(e) => setRegexPrompt(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !generatingRegex) {
                        handleGenerateRegex()
                      }
                    }}
                    className="text-sm"
                  />
                  <Button
                    type="button"
                    size="sm"
                    onClick={handleGenerateRegex}
                    disabled={!regexPrompt.trim() || generatingRegex}
                  >
                    {generatingRegex ? (
                      <>
                        <Sparkles className="h-4 w-4 mr-1 animate-spin" />
                        Oluşturuluyor...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 mr-1" />
                        Oluştur
                      </>
                    )}
                  </Button>
                </div>
                {regexError && (
                  <p className="text-xs text-destructive">{regexError}</p>
                )}
              </div>

              {/* Pattern List */}
              <div className="space-y-2">
                <Label>Regex Patterns</Label>
                {editingField.patterns?.map((pattern, index) => (
                  <Input
                    key={index}
                    placeholder="otel\s+ad[ıi]\s*[:\-]?\s*(.+)"
                    value={pattern}
                    onChange={(e) => handlePatternChange(index, e.target.value)}
                  />
                ))}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleAddPattern}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Manuel Pattern Ekle
                </Button>
              </div>
            </div>
          )}

          {editingField.method === 'llm' && (
            <div className="space-y-2">
              <Label>LLM Prompt</Label>
              <Input
                placeholder="Otel adını ve yıldız sayısını çıkar"
                value={editingField.prompt || ''}
                onChange={(e) =>
                  setEditingField({ ...editingField, prompt: e.target.value })
                }
              />
              <Label className="text-xs text-muted-foreground">
                Region (opsiyonel)
              </Label>
              <Select
                value={editingField.region || 'all'}
                onValueChange={(value) =>
                  setEditingField({
                    ...editingField,
                    region: value === 'all' ? undefined : value,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tüm sayfa</SelectItem>
                  <SelectItem value="top_left">Sol üst</SelectItem>
                  <SelectItem value="top_center">Üst orta</SelectItem>
                  <SelectItem value="top_right">Sağ üst</SelectItem>
                  <SelectItem value="bottom_left">Sol alt</SelectItem>
                  <SelectItem value="bottom_center">Alt orta</SelectItem>
                  <SelectItem value="bottom_right">Sağ alt</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {editingField.method === 'fuzzy' && (
            <div className="space-y-2">
              <Label>Keywords (virgülle ayır)</Label>
              <Input
                placeholder="otel adı, hotel name, otel"
                onChange={(e) =>
                  setEditingField({
                    ...editingField,
                    keywords: e.target.value.split(',').map(k => k.trim()),
                  })
                }
              />
            </div>
          )}

          {/* Array-specific inputs */}
          {editingField.type === 'array' && (
            <div className="space-y-3 p-3 rounded-lg border bg-muted/30">
              <Label className="text-sm font-medium">Array Ayarları</Label>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label className="text-xs">Ayırıcı</Label>
                  <Select
                    value={editingField.array_separator || 'comma'}
                    onValueChange={(value) =>
                      setEditingField({
                        ...editingField,
                        array_separator: value,
                      })
                    }
                  >
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="comma">Virgül (,)</SelectItem>
                      <SelectItem value="newline">Satır (\n)</SelectItem>
                      <SelectItem value="semicolon">Noktalı virgül (;)</SelectItem>
                      <SelectItem value="pipe">Pipe (|)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Eleman Tipi</Label>
                  <Select
                    value={editingField.array_item_type || 'text'}
                    onValueChange={(value: 'text' | 'number') =>
                      setEditingField({
                        ...editingField,
                        array_item_type: value,
                      })
                    }
                  >
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="text">Text</SelectItem>
                      <SelectItem value="number">Number</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Örn: "item1, item2, item3" → ["item1", "item2", "item3"]
              </p>
            </div>
          )}

          {/* Object-specific inputs */}
          {editingField.type === 'object' && (
            <div className="space-y-2 p-3 rounded-lg border bg-muted/30">
              <Label className="text-sm font-medium">Object Ayarları</Label>
              <Label className="text-xs">Property İsimleri (virgülle ayır)</Label>
              <Input
                placeholder="name, age, city"
                className="text-xs"
                onChange={(e) =>
                  setEditingField({
                    ...editingField,
                    object_properties: e.target.value.split(',').map(p => p.trim()),
                  })
                }
              />
              <p className="text-xs text-muted-foreground">
                LLM bu property'leri extract etmeye çalışır
              </p>
            </div>
          )}

          <Button onClick={handleAddField} className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            Field Ekle
          </Button>
        </CardContent>
      </Card>

      {/* Right: Field List */}
      <div className="space-y-3">
        <h3 className="font-semibold text-sm">Fieldler ({fields.length})</h3>
        {fields.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <p className="text-xs text-muted-foreground text-center">
                Henüz field eklenmedi
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
            {fields.map((field) => (
              <div
                key={field.id}
                className="flex items-start justify-between p-2 rounded-md border bg-card hover:bg-muted/50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-xs font-mono truncate">{field.name}</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    <Badge variant="outline" className="text-[10px] px-1 py-0">
                      {field.type}
                    </Badge>
                    <Badge variant="secondary" className="text-[10px] px-1 py-0">
                      {field.method}
                    </Badge>
                    {field.required && (
                      <Badge variant="destructive" className="text-[10px] px-1 py-0">
                        req
                      </Badge>
                    )}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveField(field.id)}
                  className="h-6 w-6 p-0 ml-1"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

