/**
 * Custom node component for React Flow
 */
import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'
import { cn } from '@/lib/utils'

interface CustomNodeData {
  label: string
  type: string
  color: string
  properties: Record<string, any>
}

const CustomNode = memo(({ data, selected }: NodeProps<CustomNodeData>) => {
  // Icon mapping by entity type
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

  return (
    <div
      className={cn(
        'px-4 py-2 rounded-lg border-2 bg-white shadow-md transition-all duration-200 min-w-[120px]',
        'hover:shadow-lg hover:scale-105 cursor-pointer',
        selected && 'ring-2 ring-blue-500 ring-offset-2 shadow-xl scale-105'
      )}
      style={{
        borderColor: data.color,
      }}
    >
      {/* Handles for connections */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-gray-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-gray-400"
      />

      {/* Node content */}
      <div className="flex items-center gap-2">
        <span className="text-xl">{getIcon(data.type)}</span>
        <div className="flex-1 min-w-0">
          <div
            className="text-xs font-semibold uppercase tracking-wide"
            style={{ color: data.color }}
          >
            {data.type}
          </div>
          <div className="text-sm font-medium text-gray-900 truncate">
            {data.label}
          </div>
        </div>
      </div>
    </div>
  )
})

CustomNode.displayName = 'CustomNode'

export default CustomNode
