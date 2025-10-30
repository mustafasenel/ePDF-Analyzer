interface JsonHighlightProps {
  json: string
  className?: string
}

export function JsonHighlight({ json, className = '' }: JsonHighlightProps) {
  const tokenize = (jsonStr: string) => {
    const tokens: Array<{ type: string; value: string }> = []
    let i = 0
    
    while (i < jsonStr.length) {
      const char = jsonStr[i]
      
      // String (key or value)
      if (char === '"') {
        let str = '"'
        i++
        while (i < jsonStr.length && jsonStr[i] !== '"') {
          if (jsonStr[i] === '\\') {
            str += jsonStr[i] + (jsonStr[i + 1] || '')
            i += 2
          } else {
            str += jsonStr[i]
            i++
          }
        }
        str += '"'
        i++
        
        // Check if it's a key (followed by :)
        let j = i
        while (j < jsonStr.length && /\s/.test(jsonStr[j])) j++
        const isKey = jsonStr[j] === ':'
        
        tokens.push({ type: isKey ? 'key' : 'string', value: str })
        continue
      }
      
      // Number
      if (/\d|-/.test(char) && (char === '-' || /\d/.test(char))) {
        let num = ''
        while (i < jsonStr.length && /[\d.eE+-]/.test(jsonStr[i])) {
          num += jsonStr[i]
          i++
        }
        tokens.push({ type: 'number', value: num })
        continue
      }
      
      // Boolean or null
      if (char === 't' && jsonStr.substr(i, 4) === 'true') {
        tokens.push({ type: 'boolean', value: 'true' })
        i += 4
        continue
      }
      if (char === 'f' && jsonStr.substr(i, 5) === 'false') {
        tokens.push({ type: 'boolean', value: 'false' })
        i += 5
        continue
      }
      if (char === 'n' && jsonStr.substr(i, 4) === 'null') {
        tokens.push({ type: 'null', value: 'null' })
        i += 4
        continue
      }
      
      // Everything else (whitespace, punctuation)
      tokens.push({ type: 'plain', value: char })
      i++
    }
    
    return tokens
  }

  const tokens = tokenize(json)
  
  const getColor = (type: string) => {
    switch (type) {
      case 'key': return 'text-green-700 dark:text-green-600'
      case 'string': return 'text-blue-700 dark:text-blue-600'
      case 'number': return 'text-amber-700 dark:text-amber-600'
      case 'boolean':
      case 'null': return 'text-orange-700 dark:text-orange-600'
      default: return ''
    }
  }

  return (
    <pre className={className}>
      {tokens.map((token, idx) => (
        <span key={idx} className={getColor(token.type)}>
          {token.value}
        </span>
      ))}
    </pre>
  )
}

