/**
 * Node details panel - Shows detailed information about selected node
 */
import { X, ExternalLink } from 'lucide-react'
import type { GraphNode } from '@/types'
import { formatDate, formatCurrency } from '@/lib/utils'

interface NodeDetailsPanelProps {
  node: GraphNode | null
  onClose: () => void
  onExpand: (nodeId: string) => void
}

export default function NodeDetailsPanel({
  node,
  onClose,
  onExpand,
}: NodeDetailsPanelProps) {
  if (!node) return null

  return (
    <div className="absolute top-0 right-0 h-full w-96 bg-white shadow-2xl border-l border-gray-200 z-50 flex flex-col animate-slide-in">
      {/* Header */}
      <div
        className="p-4 border-b border-gray-200 flex items-start justify-between"
        style={{ backgroundColor: `${node.color}15` }}
      >
        <div className="flex-1 min-w-0">
          <div
            className="text-xs font-semibold uppercase tracking-wide mb-1"
            style={{ color: node.color }}
          >
            {node.type}
          </div>
          <h3 className="text-lg font-bold text-gray-900 truncate">
            {node.label}
          </h3>
          <p className="text-sm text-gray-500 font-mono">{node.id}</p>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded-full transition-colors"
          aria-label="Close"
        >
          <X className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Actions */}
        <div className="mb-6">
          <button
            onClick={() => onExpand(node.id)}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 font-medium"
          >
            <ExternalLink className="w-4 h-4" />
            Expand Connections
          </button>
        </div>

        {/* Properties */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
            Properties
          </h4>
          <div className="space-y-2">
            {Object.entries(node.properties).map(([key, value]) => (
              <PropertyRow key={key} label={key} value={value} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function PropertyRow({ label, value }: { label: string; value: any }) {
  // Format label (snake_case to Title Case)
  const formattedLabel = label
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')

  // Format value based on type
  let formattedValue: string

  if (value === null || value === undefined) {
    formattedValue = 'N/A'
  } else if (typeof value === 'boolean') {
    formattedValue = value ? 'Yes' : 'No'
  } else if (typeof value === 'number') {
    // Check if it looks like a monetary amount
    if (label.includes('amount') || label.includes('price') || label.includes('total')) {
      formattedValue = formatCurrency(value)
    } else {
      formattedValue = value.toLocaleString()
    }
  } else if (typeof value === 'string') {
    // Check if it's a date string
    if (
      label.includes('date') ||
      label.includes('time') ||
      /^\d{4}-\d{2}-\d{2}/.test(value)
    ) {
      formattedValue = formatDate(value)
    } else {
      formattedValue = value
    }
  } else if (typeof value === 'object') {
    formattedValue = JSON.stringify(value, null, 2)
  } else {
    formattedValue = String(value)
  }

  return (
    <div className="flex items-start py-2 border-b border-gray-100 last:border-b-0">
      <dt className="text-sm font-medium text-gray-600 w-1/3 flex-shrink-0">
        {formattedLabel}
      </dt>
      <dd className="text-sm text-gray-900 w-2/3 break-words">
        {formattedValue}
      </dd>
    </div>
  )
}
