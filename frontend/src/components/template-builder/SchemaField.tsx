import { useState } from 'react'
import { Plus, Trash2, ChevronDown, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { TemplateField, FieldType, ExtractionMethod } from '@/types/template'

interface SchemaFieldProps {
  field: TemplateField
  onUpdate: (field: TemplateField) => void
  onDelete: () => void
  level?: number
}

export function SchemaField({ field, onUpdate, onDelete, level = 0 }: SchemaFieldProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  
  const hasNested = (field.type === 'object' && field.properties) || (field.type === 'array' && field.items)
  const indentClass = level > 0 ? 'ml-8 border-l-2 border-muted pl-4' : ''

  const handleAddNestedField = () => {
    if (field.type === 'object') {
      const newField: TemplateField = {
        id: Date.now().toString(),
        name: '',
        type: 'string',
        description: ''
      }
      onUpdate({
        ...field,
        properties: [...(field.properties || []), newField]
      })
    } else if (field.type === 'array') {
      // For array, set the items type
      if (!field.items) {
        onUpdate({
          ...field,
          items: {
            id: Date.now().toString(),
            name: 'item',
            type: 'string',
            description: ''
          }
        })
      }
    }
  }

  const handleUpdateNested = (index: number, updatedField: TemplateField) => {
    if (field.type === 'object' && field.properties) {
      const newProperties = [...field.properties]
      newProperties[index] = updatedField
      onUpdate({ ...field, properties: newProperties })
    }
  }

  const handleDeleteNested = (index: number) => {
    if (field.type === 'object' && field.properties) {
      onUpdate({
        ...field,
        properties: field.properties.filter((_, i) => i !== index)
      })
    }
  }

  const handleUpdateArrayItems = (updatedItems: TemplateField) => {
    onUpdate({ ...field, items: updatedItems })
  }

  return (
    <div className={`space-y-3 ${indentClass}`}>
      <div className="flex items-start gap-2 p-3 rounded-lg border bg-card">
        {/* Expand/Collapse for nested */}
        {hasNested && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 mt-8"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
        )}

        <div className="flex-1 space-y-2">
          {/* Field Name */}
          <div className="flex gap-2">
            <Input
              placeholder="field_name"
              value={field.name}
              onChange={(e) => onUpdate({ ...field, name: e.target.value })}
              className="flex-1 h-9 text-sm"
            />
            <Select
              value={field.type}
              onValueChange={(value: FieldType) => {
                const updated = { ...field, type: value }
                // Clear nested data when changing type
                if (value !== 'object') delete updated.properties
                if (value !== 'array') delete updated.items
                onUpdate(updated)
              }}
            >
              <SelectTrigger className="w-32 h-9 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="string">String</SelectItem>
                <SelectItem value="number">Number</SelectItem>
                <SelectItem value="boolean">Boolean</SelectItem>
                <SelectItem value="object">Object</SelectItem>
                <SelectItem value="array">Array</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Description */}
          <Input
            placeholder="Description"
            value={field.description || ''}
            onChange={(e) => onUpdate({ ...field, description: e.target.value })}
            className="h-8 text-xs text-muted-foreground"
          />

          {/* Method (Optional) */}
          {field.type !== 'object' && field.type !== 'array' && (
            <div className="flex gap-2 items-center">
              <Select
                value={field.method || 'llm'}
                onValueChange={(value) =>
                  onUpdate({ ...field, method: value as ExtractionMethod })
                }
              >
                <SelectTrigger className="w-28 h-7 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="llm">LLM</SelectItem>
                  <SelectItem value="regex">Regex</SelectItem>
                  <SelectItem value="fuzzy">Fuzzy</SelectItem>
                </SelectContent>
              </Select>
              {(field.method === 'llm' || !field.method) && (
                <>
                  <Input
                    placeholder="Prompt (opsiyonel): Extract company name from header"
                    value={field.prompt || ''}
                    onChange={(e) => onUpdate({ ...field, prompt: e.target.value })}
                    className="flex-1 h-7 text-xs"
                  />
                  <Select
                    value={field.region || 'all'}
                    onValueChange={(value) =>
                      onUpdate({ ...field, region: value === 'all' ? undefined : value })
                    }
                  >
                    <SelectTrigger className="w-32 h-7 text-xs">
                      <SelectValue placeholder="Region" />
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
                </>
              )}
              {field.method === 'regex' && (
                <Input
                  placeholder="Pattern: (\d+)"
                  value={field.patterns?.[0] || ''}
                  onChange={(e) => onUpdate({ ...field, patterns: [e.target.value] })}
                  className="flex-1 h-7 text-xs font-mono"
                />
              )}
              {field.method === 'fuzzy' && (
                <Input
                  placeholder="Keywords: keyword1, keyword2"
                  value={field.keywords?.join(', ') || ''}
                  onChange={(e) => onUpdate({ ...field, keywords: e.target.value.split(',').map(k => k.trim()) })}
                  className="flex-1 h-7 text-xs"
                />
              )}
            </div>
          )}

          {/* Options */}
          <div className="flex items-center gap-4 text-xs">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={field.extract_per_page || false}
                onChange={(e) => onUpdate({ ...field, extract_per_page: e.target.checked })}
                className="rounded"
              />
              <span>Extract per page</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={field.return_as_list || false}
                onChange={(e) => onUpdate({ ...field, return_as_list: e.target.checked })}
                className="rounded"
              />
              <span>Return as list</span>
            </label>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-1 mt-8">
          {(field.type === 'object' || field.type === 'array') && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleAddNestedField}
              className="h-6 w-6 p-0"
              title="Add nested field"
            >
              <Plus className="h-3 w-3" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={onDelete}
            className="h-6 w-6 p-0"
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Nested Fields */}
      {isExpanded && field.type === 'object' && field.properties && field.properties.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground ml-2">Nested fields</div>
          {field.properties.map((nestedField, index) => (
            <SchemaField
              key={nestedField.id}
              field={nestedField}
              onUpdate={(updated) => handleUpdateNested(index, updated)}
              onDelete={() => handleDeleteNested(index)}
              level={level + 1}
            />
          ))}
        </div>
      )}

      {/* Array Items */}
      {isExpanded && field.type === 'array' && field.items && (
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground ml-2">Array item type</div>
          <SchemaField
            field={field.items}
            onUpdate={handleUpdateArrayItems}
            onDelete={() => onUpdate({ ...field, items: undefined })}
            level={level + 1}
          />
        </div>
      )}
    </div>
  )
}

