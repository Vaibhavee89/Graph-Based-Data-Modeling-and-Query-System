/**
 * Export utilities for downloading data
 */

import type { ChatMessage } from '@/types'

/**
 * Download data as JSON file
 */
export function downloadJSON(data: any, filename: string) {
  const jsonStr = JSON.stringify(data, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Download data as CSV file
 */
export function downloadCSV(data: Array<Record<string, any>>, filename: string) {
  if (!data || data.length === 0) {
    console.error('No data to export')
    return
  }

  // Get headers from first row
  const headers = Object.keys(data[0])

  // Create CSV content
  const csvRows = [
    headers.join(','), // Header row
    ...data.map((row) =>
      headers.map((header) => {
        const value = row[header]
        // Escape values containing commas or quotes
        if (value === null || value === undefined) return ''
        const stringValue = String(value)
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
          return `"${stringValue.replace(/"/g, '""')}"`
        }
        return stringValue
      }).join(',')
    )
  ]

  const csvStr = csvRows.join('\n')
  const blob = new Blob([csvStr], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Download text content as file
 */
export function downloadText(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Export chat conversation as text file
 */
export function exportConversation(messages: ChatMessage[], filename: string = 'conversation.txt') {
  const lines: string[] = [
    'Graph Data Modeling System - Chat Conversation',
    '='.repeat(50),
    '',
  ]

  messages.forEach((message) => {
    const timestamp = new Date(message.timestamp).toLocaleString()
    const role = message.role.toUpperCase()

    lines.push(`[${timestamp}] ${role}:`)
    lines.push(message.content)
    lines.push('')

    // Include data if present
    if (message.data && typeof message.data === 'object') {
      if (Array.isArray(message.data) && message.data.length > 0) {
        lines.push('Data:')
        lines.push(JSON.stringify(message.data, null, 2))
        lines.push('')
      }
    }
  })

  lines.push('='.repeat(50))
  lines.push(`Exported at: ${new Date().toLocaleString()}`)

  downloadText(lines.join('\n'), filename)
}

/**
 * Export query results as CSV
 */
export function exportQueryResults(data: any, filename: string = 'query_results.csv') {
  if (!data) {
    console.error('No data to export')
    return
  }

  // Handle array of objects
  if (Array.isArray(data)) {
    if (data.length === 0) {
      console.error('Empty data array')
      return
    }
    downloadCSV(data, filename)
  }
  // Handle object with rows property
  else if (data.rows && Array.isArray(data.rows)) {
    downloadCSV(data.rows, filename)
  }
  // Fallback to JSON export
  else {
    console.warn('Data format not suitable for CSV, exporting as JSON')
    downloadJSON(data, filename.replace('.csv', '.json'))
  }
}

/**
 * Get timestamp for filename
 */
export function getTimestampedFilename(basename: string, extension: string): string {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  return `${basename}_${timestamp}.${extension}`
}
