/**
 * Main graph canvas component with React Flow
 */
import { useCallback, useEffect, useMemo, useState } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useReactFlow,
  ReactFlowProvider,
  NodeMouseHandler,
  OnNodesChange,
  OnEdgesChange,
  applyNodeChanges,
  applyEdgeChanges,
  Panel,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useQuery } from '@tanstack/react-query'
import { Search, Loader2, Download } from 'lucide-react'

import { graphAPI } from '@/services/api'
import { downloadJSON, getTimestampedFilename } from '@/lib/export'
import { useGraphStore } from '@/stores/graphStore'
import CustomNode from './CustomNode'
import Legend from './Legend'
import NodeDetailsPanel from '../NodeDetails/NodeDetailsPanel'
import FilterPanel, { GraphFilters } from './FilterPanel'
import { layoutNodes, convertEdges } from '@/lib/graphLayout'
import { debounce } from '@/lib/utils'
import { highlightFlowNodes, highlightFlowEdges, FLOW_COLORS, getFlowStatusLabel, getFlowStatusIcon } from '@/lib/flowHighlight'

const nodeTypes = {
  custom: CustomNode,
}

function GraphCanvasInner() {
  const { fitView, setCenter, setViewport } = useReactFlow()
  const {
    nodes: storeNodes,
    edges: storeEdges,
    selectedNode,
    setSelectedNode,
    addNodes,
    addEdges,
    markNodeExpanded,
    flowPath,
    highlightedNodes,
    highlightedEdges,
  } = useGraphStore()

  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isExpanding, setIsExpanding] = useState(false)

  // Filter state
  const [filters, setFilters] = useState<GraphFilters>({
    nodeTypes: new Set(['Customer', 'Product', 'Order', 'Invoice', 'Payment', 'Delivery', 'Address']),
    edgeTypes: new Set(['PLACED', 'CONTAINS', 'GENERATED', 'PAID_BY', 'RESULTED_IN', 'TO_ADDRESS', 'HAS_ADDRESS']),
  })

  const availableNodeTypes = ['Customer', 'Product', 'Order', 'Invoice', 'Payment', 'Delivery', 'Address']
  const availableEdgeTypes = ['PLACED', 'CONTAINS', 'GENERATED', 'PAID_BY', 'RESULTED_IN', 'TO_ADDRESS', 'HAS_ADDRESS']

  // Fetch initial nodes
  const { data: initialNodes, isLoading } = useQuery({
    queryKey: ['graph-nodes'],
    queryFn: () => graphAPI.getNodes({ limit: 100 }),
    staleTime: 5 * 60 * 1000,
  })

  // Initialize graph when data loads
  useEffect(() => {
    if (initialNodes && initialNodes.length > 0) {
      // Layout nodes
      const layoutedNodes = layoutNodes(initialNodes, {
        width: 1600,
        height: 1000,
        centerX: 800,
        centerY: 500,
      })

      setNodes(layoutedNodes)
      addNodes(initialNodes)

      // Fetch edges for initial nodes
      const nodeIds = initialNodes.map((n) => n.id)
      // For now, we'll add edges as we expand nodes
    }
  }, [initialNodes])

  // Apply flow highlighting when flowPath changes
  useEffect(() => {
    if (!flowPath || nodes.length === 0) return

    // Apply node highlighting
    const highlightedNodesData = nodes.map((node) => {
      const isHighlighted = highlightedNodes.has(node.id)

      if (isHighlighted) {
        // Determine color based on flow status
        let highlightColor = FLOW_COLORS.complete
        if (flowPath.status === 'partial') highlightColor = FLOW_COLORS.partial
        if (flowPath.status === 'incomplete') highlightColor = FLOW_COLORS.incomplete

        return {
          ...node,
          data: {
            ...node.data,
            isHighlighted: true,
          },
          style: {
            ...node.style,
            border: `3px solid ${highlightColor}`,
            boxShadow: `0 0 20px ${highlightColor}80`,
          },
        }
      }
      return node
    })

    // Apply edge highlighting
    const highlightedEdgesData = edges.map((edge) => {
      const edgeKey = `${edge.source}-${edge.target}`
      const isHighlighted = highlightedEdges.has(edgeKey)

      if (isHighlighted) {
        return {
          ...edge,
          animated: true,
          style: {
            ...edge.style,
            stroke: FLOW_COLORS.edge,
            strokeWidth: 3,
          },
        }
      }
      return edge
    })

    setNodes(highlightedNodesData)
    setEdges(highlightedEdgesData)
  }, [flowPath, highlightedNodes, highlightedEdges])

  // Apply filters to visible nodes and edges
  const { filteredNodes, filteredEdges } = useMemo(() => {
    // Filter nodes by type
    const visibleNodes = nodes.filter((node) =>
      filters.nodeTypes.has(node.data.type)
    )

    // Get IDs of visible nodes
    const visibleNodeIds = new Set(visibleNodes.map((n) => n.id))

    // Filter edges: keep only if both source and target are visible AND edge type is selected
    const visibleEdges = edges.filter((edge) => {
      const edgeType = edge.data?.type || 'UNKNOWN'
      return (
        visibleNodeIds.has(edge.source) &&
        visibleNodeIds.has(edge.target) &&
        filters.edgeTypes.has(edgeType)
      )
    })

    return { filteredNodes: visibleNodes, filteredEdges: visibleEdges }
  }, [nodes, edges, filters])

  // Reset filters
  const handleResetFilters = () => {
    setFilters({
      nodeTypes: new Set(availableNodeTypes),
      edgeTypes: new Set(availableEdgeTypes),
    })
  }

  // Handle export graph
  const handleExportGraph = async () => {
    try {
      // Fetch from backend export endpoint
      const response = await fetch('http://localhost:8000/api/graph/export')
      const blob = await response.blob()

      // Create download link
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = getTimestampedFilename('graph_export', 'json')
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export graph:', error)
      alert('Failed to export graph. Please try again.')
    }
  }

  // Handle node changes
  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  )

  // Handle edge changes
  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  )

  // Handle node click
  const onNodeClick: NodeMouseHandler = useCallback(
    (event, node) => {
      const backendNode = storeNodes.find((n) => n.id === node.id)
      if (backendNode) {
        setSelectedNode(backendNode)
      }
    },
    [storeNodes, setSelectedNode]
  )

  // Handle node double click (expand)
  const onNodeDoubleClick: NodeMouseHandler = useCallback(
    async (event, node) => {
      if (isExpanding) return

      setIsExpanding(true)
      try {
        const graphData = await graphAPI.expandNode(node.id, 1)

        // Add new nodes
        const newBackendNodes = graphData.nodes.filter(
          (n) => !storeNodes.some((sn) => sn.id === n.id)
        )

        if (newBackendNodes.length > 0) {
          // Layout new nodes around the clicked node
          const clickedNodePosition = node.position
          const newLayoutedNodes = newBackendNodes.map((n, idx) => {
            const angle = (2 * Math.PI * idx) / newBackendNodes.length
            const radius = 150
            return {
              id: n.id,
              type: 'custom',
              position: {
                x: clickedNodePosition.x + radius * Math.cos(angle),
                y: clickedNodePosition.y + radius * Math.sin(angle),
              },
              data: {
                label: n.label,
                type: n.type,
                color: n.color,
                properties: n.properties,
              },
            }
          })

          setNodes((nds) => [...nds, ...newLayoutedNodes])
          addNodes(newBackendNodes)
        }

        // Add new edges
        const newEdges = convertEdges(graphData.edges).filter(
          (e) => !edges.some((se) => se.id === e.id)
        )

        if (newEdges.length > 0) {
          setEdges((eds) => [...eds, ...newEdges])
          addEdges(graphData.edges)
        }

        markNodeExpanded(node.id)
      } catch (error) {
        console.error('Failed to expand node:', error)
      } finally {
        setIsExpanding(false)
      }
    },
    [storeNodes, edges, isExpanding, addNodes, addEdges, markNodeExpanded]
  )

  // Handle expand button click from details panel
  const handleExpand = useCallback(
    async (nodeId: string) => {
      const node = nodes.find((n) => n.id === nodeId)
      if (node) {
        await onNodeDoubleClick({} as any, node)
      }
    },
    [nodes, onNodeDoubleClick]
  )

  // Handle search
  const handleSearch = useMemo(
    () =>
      debounce(async (query: string) => {
        if (!query.trim()) {
          // Reset to initial view
          return
        }

        try {
          const results = await graphAPI.searchNodes(query)

          if (results.length > 0) {
            // Highlight matching nodes
            const matchingNodeIds = new Set(results.map((n) => n.id))

            setNodes((nds) =>
              nds.map((node) => ({
                ...node,
                style: {
                  ...node.style,
                  opacity: matchingNodeIds.has(node.id) ? 1 : 0.3,
                },
              }))
            )

            // Focus on first result
            const firstResult = nodes.find((n) => n.id === results[0].id)
            if (firstResult) {
              setCenter(
                firstResult.position.x,
                firstResult.position.y,
                { zoom: 1.5, duration: 800 }
              )
            }
          }
        } catch (error) {
          console.error('Search failed:', error)
        }
      }, 500),
    [nodes, setCenter]
  )

  useEffect(() => {
    if (searchQuery) {
      handleSearch(searchQuery)
    } else {
      // Reset opacity
      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          style: { ...node.style, opacity: 1 },
        }))
      )
    }
  }, [searchQuery, handleSearch])

  // Calculate legend data
  const legendData = useMemo(() => {
    const typeCounts: Record<string, { color: string; count: number }> = {}

    storeNodes.forEach((node) => {
      if (!typeCounts[node.type]) {
        typeCounts[node.type] = { color: node.color, count: 0 }
      }
      typeCounts[node.type].count++
    })

    return Object.entries(typeCounts)
      .map(([type, data]) => ({
        type,
        color: data.color,
        count: data.count,
      }))
      .sort((a, b) => b.count - a.count)
  }, [storeNodes])

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600 font-medium">Loading graph...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full h-full">
      <ReactFlow
        nodes={filteredNodes}
        edges={filteredEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onNodeDoubleClick={onNodeDoubleClick}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: false,
        }}
      >
        <Background />
        <Controls />
        <MiniMap
          nodeColor={(node) => node.data.color}
          pannable
          zoomable
        />

        {/* Search Panel */}
        <Panel position="top-left" className="bg-white rounded-lg shadow-lg p-2">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm w-64"
            />
            <button
              onClick={handleExportGraph}
              className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
              title="Export graph as JSON"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </Panel>

        {/* Instructions Panel */}
        {nodes.length > 0 && !flowPath && (
          <Panel position="top-center" className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2">
            <p className="text-sm text-blue-900">
              <strong>Click</strong> to view details • <strong>Double-click</strong> to expand connections
            </p>
          </Panel>
        )}

        {/* Flow Status Panel */}
        {flowPath && (
          <Panel position="top-center" className={`border rounded-lg px-4 py-2 ${
            flowPath.status === 'complete' ? 'bg-green-50 border-green-200' :
            flowPath.status === 'partial' ? 'bg-yellow-50 border-yellow-200' :
            'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-center gap-2">
              <span className="text-xl">{getFlowStatusIcon(flowPath.status)}</span>
              <p className={`text-sm font-medium ${
                flowPath.status === 'complete' ? 'text-green-900' :
                flowPath.status === 'partial' ? 'text-yellow-900' :
                'text-red-900'
              }`}>
                {getFlowStatusLabel(flowPath.status)} - {flowPath.path_nodes.length} nodes highlighted
              </p>
              <button
                onClick={() => useGraphStore.getState().clearFlowHighlight()}
                className="ml-2 px-2 py-1 text-xs bg-white rounded hover:bg-gray-100 transition-colors"
              >
                Clear
              </button>
            </div>
          </Panel>
        )}
      </ReactFlow>

      {/* Legend */}
      {legendData.length > 0 && <Legend nodeTypes={legendData} />}

      {/* Node Details Panel */}
      <NodeDetailsPanel
        node={selectedNode}
        onClose={() => setSelectedNode(null)}
        onExpand={handleExpand}
      />

      {/* Filter Panel */}
      <FilterPanel
        filters={filters}
        availableNodeTypes={availableNodeTypes}
        availableEdgeTypes={availableEdgeTypes}
        onFiltersChange={setFilters}
        onReset={handleResetFilters}
      />

      {/* Loading overlay during expansion */}
      {isExpanding && (
        <div className="absolute inset-0 bg-black bg-opacity-10 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl px-6 py-4 flex items-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
            <span className="text-gray-700 font-medium">Expanding node...</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default function GraphCanvas() {
  return (
    <ReactFlowProvider>
      <GraphCanvasInner />
    </ReactFlowProvider>
  )
}
