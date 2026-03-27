/**
 * Chat input component - Input field with send button
 */
import { useState, KeyboardEvent } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSend: (message: string) => void
  isLoading: boolean
  disabled?: boolean
}

export default function ChatInput({ onSend, isLoading, disabled }: ChatInputProps) {
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim() || isLoading || disabled) return

    onSend(input.trim())
    setInput('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="flex items-end gap-2">
        <div className="flex-1">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your business data..."
            disabled={isLoading || disabled}
            rows={3}
            className={cn(
              'w-full px-4 py-3 border border-gray-300 rounded-lg resize-none',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              'placeholder:text-gray-400 text-sm',
              'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed'
            )}
          />
          <div className="flex items-center justify-between mt-2">
            <p className="text-xs text-gray-500">
              Press <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs">Shift+Enter</kbd> for new line
            </p>
            <p className="text-xs text-gray-500">
              {input.length} / 500
            </p>
          </div>
        </div>

        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading || disabled}
          className={cn(
            'px-4 py-3 rounded-lg font-medium transition-colors flex items-center gap-2',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            !input.trim() || isLoading || disabled
              ? 'bg-gray-300 text-gray-500'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          )}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Thinking...</span>
            </>
          ) : (
            <>
              <Send className="w-5 h-5" />
              <span>Send</span>
            </>
          )}
        </button>
      </div>

      {/* Example queries */}
      <div className="mt-3">
        <p className="text-xs font-medium text-gray-600 mb-2">Example queries:</p>
        <div className="flex flex-wrap gap-2">
          {[
            "Which customers have the most orders?",
            "Find orders with incomplete flows",
            "Show me top 5 products",
          ].map((example, idx) => (
            <button
              key={idx}
              onClick={() => !isLoading && !disabled && setInput(example)}
              disabled={isLoading || disabled}
              className="text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
