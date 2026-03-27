/**
 * Chat interface component - Main chat UI
 */
import { useEffect, useRef, useState } from 'react'
import { Trash2, AlertCircle, Download, MoreVertical } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'

import { queryAPI, graphAPI } from '@/services/api'
import { useChatStore } from '@/stores/chatStore'
import { useGraphStore } from '@/stores/graphStore'
import Message from './Message'
import ChatInput from './ChatInput'
import { exportConversation, exportQueryResults } from '@/lib/export'

export default function ChatInterface() {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [showExportMenu, setShowExportMenu] = useState(false)
  const {
    messages,
    isLoading,
    error,
    addMessage,
    setLoading,
    setError,
    clearMessages,
  } = useChatStore()
  const { focusNode, setFlowPath } = useGraphStore()

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Query mutation
  const queryMutation = useMutation({
    mutationFn: (query: string) => queryAPI.chat(query),
    onSuccess: (response) => {
      setLoading(false)

      if (response.success) {
        addMessage({
          role: 'assistant',
          content: response.answer || 'No response received',
          data: response.data,
          entities: response.entities,
        })
      } else {
        addMessage({
          role: 'error',
          content: response.answer || response.message || 'Query failed',
        })
      }
    },
    onError: (error: any) => {
      setLoading(false)
      setError(error.message || 'Failed to process query')
      addMessage({
        role: 'error',
        content: `Error: ${error.response?.data?.detail || error.message || 'Failed to process query'}`,
      })
    },
  })

  // Handle sending a message
  const handleSend = (message: string) => {
    // Add user message
    addMessage({
      role: 'user',
      content: message,
    })

    // Send to backend
    setLoading(true)
    setError(null)
    queryMutation.mutate(message)
  }

  // Handle entity click (focus in graph and trace flow)
  const handleEntityClick = async (entityId: string) => {
    console.log('Focusing on entity:', entityId)
    focusNode(entityId)

    // Try to trace flow for this entity
    try {
      const flowResult = await graphAPI.traceFlow(entityId)
      if (flowResult.success) {
        setFlowPath(flowResult)
        addMessage({
          role: 'system',
          content: `Focusing on ${entityId} and highlighting ${flowResult.status} flow in the graph`,
        })
      } else {
        addMessage({
          role: 'system',
          content: `Focusing on ${entityId} in the graph`,
        })
      }
    } catch (error) {
      // If flow trace fails, just focus the node
      addMessage({
        role: 'system',
        content: `Focusing on ${entityId} in the graph`,
      })
    }
  }

  // Handle clear chat
  const handleClear = () => {
    if (window.confirm('Clear all messages?')) {
      clearMessages()
    }
  }

  // Handle export conversation
  const handleExportConversation = () => {
    exportConversation(messages)
    setShowExportMenu(false)
  }

  // Handle export last query results
  const handleExportResults = () => {
    // Find the last assistant message with data
    const lastMessageWithData = [...messages]
      .reverse()
      .find((m) => m.role === 'assistant' && m.data)

    if (lastMessageWithData && lastMessageWithData.data) {
      exportQueryResults(lastMessageWithData.data)
    } else {
      alert('No query results to export. Run a query first.')
    }
    setShowExportMenu(false)
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Chat Assistant</h2>
          <p className="text-sm text-gray-500">
            Ask questions about your business data
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Export Menu */}
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              disabled={messages.length === 0}
              className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Export options"
            >
              <Download className="w-5 h-5" />
            </button>

            {/* Export Dropdown */}
            {showExportMenu && (
              <div className="absolute right-0 top-full mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                <button
                  onClick={handleExportConversation}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Export Conversation
                </button>
                <button
                  onClick={handleExportResults}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Export Last Results (CSV)
                </button>
              </div>
            )}
          </div>

          <button
            onClick={handleClear}
            disabled={messages.length === 0}
            className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Clear conversation"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">💬</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Start a Conversation
              </h3>
              <p className="text-sm text-gray-600 mb-6">
                Ask questions about customers, orders, products, invoices, payments, and deliveries.
                I'll help you analyze your business data.
              </p>
              <div className="space-y-2 text-left bg-white rounded-lg p-4 border border-gray-200">
                <p className="text-xs font-semibold text-gray-700 mb-2">Try asking:</p>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• "Which customers have the most orders?"</li>
                  <li>• "Show me top 5 products by revenue"</li>
                  <li>• "Trace the flow of invoice INV-123"</li>
                  <li>• "Find orders with incomplete flows"</li>
                  <li>• "Show me customer 310000108"</li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <Message
                key={message.id}
                message={message}
                onEntityClick={handleEntityClick}
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}

        {/* Connection error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-3 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-red-800">Connection Error</p>
              <p className="text-sm text-red-600 mt-1">{error}</p>
              <p className="text-xs text-red-500 mt-2">
                Make sure the backend is running at http://localhost:8000
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        isLoading={isLoading}
        disabled={!!error}
      />
    </div>
  )
}
