/**
 * Filter panel for graph visualization
 */
import { useState } from 'react'
import { Filter, ChevronDown, ChevronUp } from 'lucide-react'

export interface GraphFilters {
  nodeTypes: Set<string>
  edgeTypes: Set<string>
  dateRange?: {
    start: Date | null
    end: Date | null
  }
  status?: string[]
}

interface FilterPanelProps {
  filters: GraphFilters
  availableNodeTypes: string[]
  availableEdgeTypes: string[]
  onFiltersChange: (filters: GraphFilters) => void
  onReset: () => void
}

export default function FilterPanel({
  filters,
  availableNodeTypes,
  availableEdgeTypes,
  onFiltersChange,
  onReset,
}: FilterPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showNodeTypes, setShowNodeTypes] = useState(true)
  const [showEdgeTypes, setShowEdgeTypes] = useState(false)

  // Toggle node type
  const toggleNodeType = (type: string) => {
    const newTypes = new Set(filters.nodeTypes)
    if (newTypes.has(type)) {
      newTypes.delete(type)
    } else {
      newTypes.add(type)
    }
    onFiltersChange({ ...filters, nodeTypes: newTypes })
  }

  // Toggle edge type
  const toggleEdgeType = (type: string) => {
    const newTypes = new Set(filters.edgeTypes)
    if (newTypes.has(type)) {
      newTypes.delete(type)
    } else {
      newTypes.add(type)
    }
    onFiltersChange({ ...filters, edgeTypes: newTypes })
  }

  // Select all node types
  const selectAllNodeTypes = () => {
    onFiltersChange({ ...filters, nodeTypes: new Set(availableNodeTypes) })
  }

  // Deselect all node types
  const deselectAllNodeTypes = () => {
    onFiltersChange({ ...filters, nodeTypes: new Set() })
  }

  // Select all edge types
  const selectAllEdgeTypes = () => {
    onFiltersChange({ ...filters, edgeTypes: new Set(availableEdgeTypes) })
  }

  // Deselect all edge types
  const deselectAllEdgeTypes = () => {
    onFiltersChange({ ...filters, edgeTypes: new Set() })
  }

  // Active filter count
  const activeFilterCount =
    (filters.nodeTypes.size < availableNodeTypes.length ? 1 : 0) +
    (filters.edgeTypes.size < availableEdgeTypes.length ? 1 : 0)

  return (
    <div className="absolute top-4 right-4 z-10 bg-white rounded-lg shadow-lg border border-gray-200 w-80">
      {/* Header */}
      <div
        className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Filters</h3>
          {activeFilterCount > 0 && (
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
              {activeFilterCount}
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-600" />
        )}
      </div>

      {/* Filter Content */}
      {isExpanded && (
        <div className="border-t border-gray-200">
          {/* Node Types Filter */}
          <div className="p-3 border-b border-gray-200">
            <div
              className="flex items-center justify-between mb-2 cursor-pointer"
              onClick={() => setShowNodeTypes(!showNodeTypes)}
            >
              <span className="text-sm font-medium text-gray-700">Node Types</span>
              {showNodeTypes ? (
                <ChevronUp className="w-3 h-3 text-gray-500" />
              ) : (
                <ChevronDown className="w-3 h-3 text-gray-500" />
              )}
            </div>

            {showNodeTypes && (
              <>
                <div className="flex gap-2 mb-2">
                  <button
                    onClick={selectAllNodeTypes}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Select All
                  </button>
                  <button
                    onClick={deselectAllNodeTypes}
                    className="text-xs text-gray-600 hover:text-gray-800"
                  >
                    Clear All
                  </button>
                </div>

                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {availableNodeTypes.map((type) => (
                    <label
                      key={type}
                      className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded"
                    >
                      <input
                        type="checkbox"
                        checked={filters.nodeTypes.has(type)}
                        onChange={() => toggleNodeType(type)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{type}</span>
                      <span className="ml-auto text-xs text-gray-500">
                        {/* Count would go here if available */}
                      </span>
                    </label>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Edge Types Filter */}
          <div className="p-3 border-b border-gray-200">
            <div
              className="flex items-center justify-between mb-2 cursor-pointer"
              onClick={() => setShowEdgeTypes(!showEdgeTypes)}
            >
              <span className="text-sm font-medium text-gray-700">Edge Types</span>
              {showEdgeTypes ? (
                <ChevronUp className="w-3 h-3 text-gray-500" />
              ) : (
                <ChevronDown className="w-3 h-3 text-gray-500" />
              )}
            </div>

            {showEdgeTypes && (
              <>
                <div className="flex gap-2 mb-2">
                  <button
                    onClick={selectAllEdgeTypes}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Select All
                  </button>
                  <button
                    onClick={deselectAllEdgeTypes}
                    className="text-xs text-gray-600 hover:text-gray-800"
                  >
                    Clear All
                  </button>
                </div>

                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {availableEdgeTypes.map((type) => (
                    <label
                      key={type}
                      className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded"
                    >
                      <input
                        type="checkbox"
                        checked={filters.edgeTypes.has(type)}
                        onChange={() => toggleEdgeType(type)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{type}</span>
                    </label>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Actions */}
          <div className="p-3 flex items-center justify-between">
            <button
              onClick={onReset}
              disabled={activeFilterCount === 0}
              className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Reset All
            </button>
            <span className="text-xs text-gray-500">
              {filters.nodeTypes.size} of {availableNodeTypes.length} node types
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
