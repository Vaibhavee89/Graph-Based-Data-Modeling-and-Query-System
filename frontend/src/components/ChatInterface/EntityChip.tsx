/**
 * Entity chip - Clickable entity reference
 */
import { ExternalLink } from 'lucide-react'
import { cn } from '@/lib/utils'

interface EntityChipProps {
  entityId: string
  onClick: (entityId: string) => void
}

export default function EntityChip({ entityId, onClick }: EntityChipProps) {
  // Determine entity type from ID prefix
  const getEntityType = (id: string) => {
    if (id.startsWith('CUST-')) return { type: 'Customer', color: 'bg-blue-100 text-blue-700 hover:bg-blue-200' }
    if (id.startsWith('PROD-')) return { type: 'Product', color: 'bg-green-100 text-green-700 hover:bg-green-200' }
    if (id.startsWith('ORD-')) return { type: 'Order', color: 'bg-orange-100 text-orange-700 hover:bg-orange-200' }
    if (id.startsWith('INV-')) return { type: 'Invoice', color: 'bg-red-100 text-red-700 hover:bg-red-200' }
    if (id.startsWith('PAY-')) return { type: 'Payment', color: 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200' }
    if (id.startsWith('DEL-')) return { type: 'Delivery', color: 'bg-purple-100 text-purple-700 hover:bg-purple-200' }
    if (id.startsWith('ADDR-')) return { type: 'Address', color: 'bg-gray-100 text-gray-700 hover:bg-gray-200' }
    // Handle numeric IDs (like SAP business partners)
    if (/^\d{9}$/.test(id)) return { type: 'Customer', color: 'bg-blue-100 text-blue-700 hover:bg-blue-200' }
    return { type: 'Entity', color: 'bg-gray-100 text-gray-700 hover:bg-gray-200' }
  }

  const { type, color } = getEntityType(entityId)

  return (
    <button
      onClick={() => onClick(entityId)}
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium transition-colors',
        color
      )}
      title={`View ${type} in graph`}
    >
      <span>{entityId}</span>
      <ExternalLink className="w-3 h-3" />
    </button>
  )
}
