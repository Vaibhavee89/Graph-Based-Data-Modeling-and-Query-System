/**
 * Message component - Displays a single chat message
 */
import { User, Bot, AlertCircle, Info } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { ChatMessage } from '@/types'
import EntityChip from './EntityChip'
import { extractEntityIds, formatDate } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface MessageProps {
  message: ChatMessage
  onEntityClick: (entityId: string) => void
}

export default function Message({ message, onEntityClick }: MessageProps) {
  const { role, content, timestamp } = message

  // Extract entity IDs from content
  const entityIds = extractEntityIds(content)

  // Render based on role
  const renderIcon = () => {
    switch (role) {
      case 'user':
        return <User className="w-5 h-5" />
      case 'assistant':
        return <Bot className="w-5 h-5" />
      case 'error':
        return <AlertCircle className="w-5 h-5" />
      case 'system':
        return <Info className="w-5 h-5" />
    }
  }

  const getMessageStyles = () => {
    switch (role) {
      case 'user':
        return 'bg-blue-50 border-blue-200'
      case 'assistant':
        return 'bg-white border-gray-200'
      case 'error':
        return 'bg-red-50 border-red-200'
      case 'system':
        return 'bg-gray-50 border-gray-200'
    }
  }

  const getIconStyles = () => {
    switch (role) {
      case 'user':
        return 'bg-blue-600 text-white'
      case 'assistant':
        return 'bg-gray-600 text-white'
      case 'error':
        return 'bg-red-600 text-white'
      case 'system':
        return 'bg-gray-400 text-white'
    }
  }

  // Process content to replace entity IDs with chips
  const renderContent = () => {
    if (entityIds.length === 0) {
      return (
        <ReactMarkdown
          className="prose prose-sm max-w-none"
          components={{
            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
            strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
            ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
            li: ({ children }) => <li className="mb-1">{children}</li>,
          }}
        >
          {content}
        </ReactMarkdown>
      )
    }

    // Split content by entity IDs and render with chips
    let parts: React.ReactNode[] = []
    let lastIndex = 0
    let key = 0

    // Sort entity IDs by their position in content
    const sortedEntities = entityIds
      .map(id => ({ id, index: content.indexOf(id) }))
      .sort((a, b) => a.index - b.index)

    sortedEntities.forEach(({ id, index }) => {
      if (index > lastIndex) {
        // Add text before entity
        parts.push(
          <ReactMarkdown
            key={`text-${key++}`}
            className="inline"
          >
            {content.slice(lastIndex, index)}
          </ReactMarkdown>
        )
      }
      // Add entity chip
      parts.push(
        <EntityChip
          key={`entity-${key++}`}
          entityId={id}
          onClick={onEntityClick}
        />
      )
      lastIndex = index + id.length
    })

    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(
        <ReactMarkdown
          key={`text-${key++}`}
          className="inline"
        >
          {content.slice(lastIndex)}
        </ReactMarkdown>
      )
    }

    return <div className="prose prose-sm max-w-none">{parts}</div>
  }

  return (
    <div className={cn('rounded-lg border p-4 mb-3 animate-fade-in', getMessageStyles())}>
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className={cn('rounded-full p-2 flex-shrink-0', getIconStyles())}>
          {renderIcon()}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">
              {role === 'user' ? 'You' : role === 'assistant' ? 'Assistant' : role === 'error' ? 'Error' : 'System'}
            </span>
            <span className="text-xs text-gray-500">
              {formatDate(timestamp.toISOString())}
            </span>
          </div>

          {/* Message content */}
          <div className="text-sm text-gray-800">
            {renderContent()}
          </div>

          {/* Data preview if available */}
          {message.data && Array.isArray(message.data) && message.data.length > 0 && (
            <div className="mt-3 overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-xs">
                <thead className="bg-gray-50">
                  <tr>
                    {Object.keys(message.data[0]).map((key) => (
                      <th
                        key={key}
                        className="px-3 py-2 text-left font-medium text-gray-700 uppercase tracking-wider"
                      >
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {message.data.slice(0, 5).map((row, idx) => (
                    <tr key={idx}>
                      {Object.values(row).map((value, vidx) => (
                        <td key={vidx} className="px-3 py-2 whitespace-nowrap">
                          {String(value)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {message.data.length > 5 && (
                <p className="text-xs text-gray-500 mt-2">
                  ... and {message.data.length - 5} more rows
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
