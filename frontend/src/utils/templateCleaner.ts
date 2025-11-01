import type { Template, TemplateField } from '@/types/template'

/**
 * Clean template by removing frontend-only fields (id, return_as_list)
 * These fields are only used for UI state management and not needed for extraction
 */
export function cleanTemplateForExport(template: Template): Template {
  const cleanField = (field: TemplateField): Partial<TemplateField> => {
    // Remove frontend-only fields
    const { id, return_as_list, ...rest } = field

    // Recursively clean nested properties
    if (rest.properties && Array.isArray(rest.properties)) {
      rest.properties = rest.properties.map(cleanField) as TemplateField[]
    }

    // Recursively clean array items
    if (rest.items && typeof rest.items === 'object') {
      rest.items = cleanField(rest.items as TemplateField) as TemplateField
    }

    return rest
  }

  // Clean all fields in template
  const cleanedTemplate: Template = {
    ...template,
    fields: template.fields.map(cleanField) as TemplateField[]
  }

  return cleanedTemplate
}
