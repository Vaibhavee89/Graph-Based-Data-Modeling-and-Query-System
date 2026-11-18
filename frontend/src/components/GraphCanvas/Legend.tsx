/**
 * Legend component - Shows node types and their colors
 */
import { useCallback, useState } from 'react'
import { Layers, Minus } from 'lucide-react'

interface LegendProps {
  nodeTypes: Array<{ type: string; color: string; count: number }>
}

export default function Legend({ nodeTypes }: LegendProps) {
  // Can be minimized; the choice is remembered in this browser
  const [open, setOpen] = useState(() => {
    try {
      return localStorage.getItem('graph-legend-open') !== 'false'
    } catch {
      return true
    }
  })
  const toggle = useCallback((next: boolean) => {
    setOpen(next)
    try {
      localStorage.setItem('graph-legend-open', String(next))
    } catch {
      /* storage unavailable: the choice just lasts for this visit */
    }
  }, [])

  const getIcon = (type: string) => {
    switch (type) {
      case 'Customer':
        return '👤'
      case 'Product':
        return '📦'
      case 'Order':
        return '🛒'
      case 'Invoice':
        return '📄'
      case 'Payment':
        return '💳'
      case 'Delivery':
        return '🚚'
      case 'Address':
        return '📍'
      default:
        return '◆'
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => toggle(true)}
        className="absolute bottom-4 left-4 z-10 p-2 bg-white border border-gray-200 rounded-full shadow-lg text-gray-700 hover:bg-gray-50 transition-colors"
        title="Show node types"
        aria-label="Show node types"
      >
        <Layers className="w-4 h-4" />
      </button>
    )
  }

  return (
    <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg border border-gray-200 p-3 z-10">
      <div className="flex items-center justify-between gap-4 mb-2">
        <h3 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
          Node Types
        </h3>
        <button
          onClick={() => toggle(false)}
          className="p-1 -mr-1 text-gray-500 hover:bg-gray-100 rounded transition-colors"
          title="Minimize node types"
          aria-label="Minimize node types"
        >
          <Minus className="w-4 h-4" />
        </button>
      </div>
      <div className="space-y-1">
        {nodeTypes.map(({ type, color, count }) => (
          <div key={type} className="flex items-center gap-2 text-sm">
            <div
              className="w-3 h-3 rounded-full flex-shrink-0"
              style={{ backgroundColor: color }}
            />
            <span className="text-lg mr-1">{getIcon(type)}</span>
            <span className="text-gray-700 font-medium">{type}</span>
            <span className="text-gray-500 text-xs ml-auto">({count})</span>
          </div>
        ))}
      </div>
    </div>
  )
}
