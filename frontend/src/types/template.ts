export type FieldType = 'string' | 'number' | 'boolean' | 'array' | 'object'
export type ExtractionMethod = 'llm' | 'regex' | 'fuzzy'

export interface TemplateField {
  id: string
  name: string
  type: FieldType
  description?: string
  method?: ExtractionMethod
  required?: boolean
  extract_per_page?: boolean
  return_as_list?: boolean
  
  // For nested fields (object/array)
  properties?: TemplateField[]  // nested fields for object
  items?: TemplateField  // item type for array
  
  // Method-specific (optional)
  patterns?: string[]  // for regex
  prompt?: string      // for llm
  region?: string      // for llm
  keywords?: string[]  // for fuzzy
  enum?: string[]      // for enum type (predefined list)
}

export interface TemplateTable {
  id: string
  name: string
  label: string
  required: boolean
  min_columns?: number
  keywords?: string[]
}

export interface Template {
  template_name: string
  description: string
  fields: TemplateField[]
  tables?: TemplateTable[]
}

