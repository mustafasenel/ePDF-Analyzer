import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SchemaField } from './SchemaField'
import type { TemplateField } from '@/types/template'

interface SchemaBuilderProps {
  fields: TemplateField[]
  onFieldsChange: (fields: TemplateField[]) => void
}

export function SchemaBuilder({ fields, onFieldsChange }: SchemaBuilderProps) {
  const handleAddField = () => {
    const newField: TemplateField = {
      id: Date.now().toString(),
      name: '',
      type: 'string',
      description: ''
    }
    onFieldsChange([...fields, newField])
  }

  const handleUpdateField = (index: number, updatedField: TemplateField) => {
    const newFields = [...fields]
    newFields[index] = updatedField
    onFieldsChange(newFields)
  }

  const handleDeleteField = (index: number) => {
    onFieldsChange(fields.filter((_, i) => i !== index))
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Schema Fields</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {fields.length === 0 ? (
          <div className="text-center py-8 text-sm text-muted-foreground">
            Henüz field eklenmedi. Başlamak için field ekleyin.
          </div>
        ) : (
          <div className="space-y-3">
            {fields.map((field, index) => (
              <SchemaField
                key={field.id}
                field={field}
                onUpdate={(updated) => handleUpdateField(index, updated)}
                onDelete={() => handleDeleteField(index)}
              />
            ))}
          </div>
        )}

        <Button onClick={handleAddField} variant="outline" className="w-full">
          <Plus className="h-4 w-4 mr-2" />
          Add Field
        </Button>
      </CardContent>
    </Card>
  )
}

