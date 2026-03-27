/**
 * Legend component - Shows node types and their colors
 */
interface LegendProps {
  nodeTypes: Array<{ type: string; color: string; count: number }>
}

export default function Legend({ nodeTypes }: LegendProps) {
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
    <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg border border-gray-200 p-3 z-10">
      <h3 className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
        Node Types
      </h3>
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
