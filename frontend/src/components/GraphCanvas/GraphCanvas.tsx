/**
 * Main graph canvas component with React Flow
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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
import { Search, Loader2, Download, Info, Minus } from 'lucide-react'

import { graphAPI } from '@/services/api'
import { getTimestampedFilename } from '@/lib/export'
import { useGraphStore } from '@/stores/graphStore'
import { useSessionStore } from '@/stores/sessionStore'
import CustomNode from './CustomNode'
import Legend from './Legend'
import NodeDetailsPanel from '../NodeDetails/NodeDetailsPanel'
import FilterPanel, { GraphFilters } from './FilterPanel'
import { layoutNodes, convertEdges, applyForceLayout } from '@/lib/graphLayout'
import { debounce } from '@/lib/utils'
import { FLOW_COLORS, getFlowStatusLabel, getFlowStatusIcon } from '@/lib/flowHighlight'

const nodeTypes = {
  custom: CustomNode,
}

function GraphCanvasInner() {
  const { setCenter, fitView, getViewport, setViewport } = useReactFlow()
  const {
    nodes: storeNodes,
    selectedNode,
    setSelectedNode,
    addNodes,
    addEdges,
    markNodeExpanded,
    flowPath,
    highlightedNodes,
    highlightedEdges,
    focusRequest,
    clearFocusRequest,
    requestFocus,
    setFlowPath,
  } = useGraphStore()

  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isExpanding, setIsExpanding] = useState(false)

  // The "click / double-click" tips can be minimized; the choice is remembered in this browser
  const [hintOpen, setHintOpen] = useState(() => {
    try {
      return localStorage.getItem('graph-hint-open') !== 'false'
    } catch {
      return true
    }
  })
  const toggleHint = useCallback((open: boolean) => {
    setHintOpen(open)
    try {
      localStorage.setItem('graph-hint-open', String(open))
    } catch {
      /* storage unavailable: the choice just lasts for this visit */
    }
  }, [])

  const sessionId = useSessionStore((st) => st.session?.sessionId ?? 'demo')

  // Entity and relationship types come from the connected database
  const { data: overview } = useQuery({
    queryKey: ['graph-overview', sessionId],
    queryFn: () => graphAPI.getOverview(),
  })
  const availableNodeTypes = useMemo(() => Object.keys(overview?.node_types ?? {}).sort(), [overview])
  const availableEdgeTypes = useMemo(() => Object.keys(overview?.edge_types ?? {}).sort(), [overview])

  // Filter state: start with everything visible, and re-seed when the available types change
  const [filters, setFilters] = useState<GraphFilters>({
    nodeTypes: new Set(),
    edgeTypes: new Set(),
  })
  useEffect(() => {
    setFilters({ nodeTypes: new Set(availableNodeTypes), edgeTypes: new Set(availableEdgeTypes) })
  }, [availableNodeTypes, availableEdgeTypes])

  // Fetch a connected starting view (nodes and their edges together)
  const { data: starter, isLoading } = useQuery({
    queryKey: ['graph-starter', sessionId],
    queryFn: () => graphAPI.getStarter(40),
    staleTime: 5 * 60 * 1000,
  })

  // Initialize graph when data loads
  useEffect(() => {
    if (starter && starter.nodes.length > 0) {
      const flowEdges = convertEdges(starter.edges)
      const seeded = layoutNodes(starter.nodes, { width: 1600, height: 1000, centerX: 800, centerY: 500 })
      // Spread connected nodes apart so labels stay readable
      const laidOut = applyForceLayout(seeded, flowEdges, 300, {
        idealDistance: 170,
        repulsion: 160000,
        spring: 0.02,
      })
      setNodes(laidOut)
      setEdges(flowEdges)
      addNodes(starter.nodes)
      addEdges(starter.edges)
    }
  }, [starter])

  // Apply flow highlighting when flowPath changes
  useEffect(() => {
    if (nodes.length === 0) return

    // Highlight cleared: remove any highlight styling left on nodes/edges
    if (!flowPath) {
      setNodes((nds) =>
        nds.map((node) => {
          if (!node.data?.isHighlighted) return node
          const { border, boxShadow, ...restStyle } = (node.style || {}) as Record<string, unknown>
          return {
            ...node,
            data: { ...node.data, isHighlighted: false },
            style: restStyle,
          }
        })
      )
      setEdges((eds) =>
        eds.map((edge) => {
          if (!edge.animated) return edge
          const { stroke, strokeWidth, ...restStyle } = (edge.style || {}) as Record<string, unknown>
          return { ...edge, animated: false, style: restStyle }
        })
      )
      return
    }

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
      // Not part of the current highlight: drop any styling left from an earlier one
      if (node.data?.isHighlighted) {
        const { border, boxShadow, ...restStyle } = (node.style || {}) as Record<string, unknown>
        return { ...node, data: { ...node.data, isHighlighted: false }, style: restStyle }
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
      if (edge.animated) {
        const { stroke, strokeWidth, ...restStyle } = (edge.style || {}) as Record<string, unknown>
        return { ...edge, animated: false, style: restStyle }
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
      // Fetch via the shared API client so VITE_API_URL is respected
      const blob = await graphAPI.exportGraph()

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
    (_event, node) => {
      const backendNode = storeNodes.find((n) => n.id === node.id)
      if (backendNode) {
        setSelectedNode(backendNode)
      }
    },
    [storeNodes, setSelectedNode]
  )

  // Expand a node: fetch its direct connections, add any that are missing, highlight them all,
  // and bring them into view. Says what happened even when everything was already on the canvas.
  const expandAndShow = useCallback(
    async (nodeId: string) => {
      if (isExpanding) return
      setIsExpanding(true)
      try {
        const graphData = await graphAPI.expandNode(nodeId, 1)
        const known = new Set(useGraphStore.getState().nodes.map((n) => n.id))
        const fresh = graphData.nodes.filter((n) => !known.has(n.id)).length
        const others = graphData.nodes.length - 1
        const label = graphData.nodes.find((n) => n.id === nodeId)?.label ?? nodeId

        setFlowPath({
          success: true,
          path_nodes: graphData.nodes,
          path_edges: graphData.edges,
          status: 'complete',
          message:
            others === 0
              ? `${label} has no connections`
              : fresh === 0
                ? `${label}: all ${others} connection${others === 1 ? '' : 's'} are already shown (highlighted)`
                : `${label}: ${others} connection${others === 1 ? '' : 's'}, ${fresh} newly added`,
        })
        requestFocus(nodeId, graphData.nodes, graphData.edges)
        markNodeExpanded(nodeId)
      } catch (error) {
        console.error('Failed to expand node:', error)
        setFlowPath({
          success: false,
          path_nodes: [],
          path_edges: [],
          status: 'error',
          message: 'Could not load connections for this node. Please try again.',
        })
      } finally {
        setIsExpanding(false)
      }
    },
    [isExpanding, requestFocus, setFlowPath, markNodeExpanded]
  )

  // Handle node double click (expand)
  const onNodeDoubleClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      void expandAndShow(node.id)
    },
    [expandAndShow]
  )

  // Handle expand button click from details panel
  const handleExpand = useCallback(
    async (nodeId: string) => {
      await expandAndShow(nodeId)
    },
    [expandAndShow]
  )

  // Keep the latest values in refs so the debounced handler can stay stable
  const nodesRef = useRef<Node[]>([])
  const storeNodesRef = useRef(storeNodes)
  const setCenterRef = useRef(setCenter)
  const searchSeq = useRef(0)
  nodesRef.current = nodes
  storeNodesRef.current = storeNodes
  setCenterRef.current = setCenter

  const resetSearchHighlight = useCallback(() => {
    setNodes((nds) =>
      nds.some((n) => n.style?.opacity !== undefined && n.style.opacity !== 1)
        ? nds.map((node) => ({ ...node, style: { ...node.style, opacity: 1 } }))
        : nds
    )
  }, [])

  // Handle search (created once; reads current state through refs)
  const handleSearch = useMemo(
    () =>
      debounce(async (query: string) => {
        const seq = ++searchSeq.current
        try {
          const results = await graphAPI.searchNodes(query)
          if (seq !== searchSeq.current) return // a newer search or a clear won

          if (results.length === 0) {
            resetSearchHighlight()
            return
          }

          // Results that aren't on the canvas yet: add them, with their edges
          const known = new Set(storeNodesRef.current.map((n) => n.id))
          const missing = results.filter((n) => !known.has(n.id)).slice(0, 20)
          if (missing.length > 0) {
            const baseY = Math.max(0, ...nodesRef.current.map((n) => n.position.y)) + 200
            const added: Node[] = missing.map((n, idx) => ({
              id: n.id,
              type: 'custom',
              position: { x: 200 * idx, y: baseY },
              data: { label: n.label, type: n.type, color: n.color, properties: n.properties },
            }))
            setNodes((nds) => [...nds, ...added])
            addNodes(missing)

            try {
              const allIds = [...nodesRef.current.map((n) => n.id), ...missing.map((n) => n.id)]
              const sub = await graphAPI.getSubgraph(allIds)
              if (seq !== searchSeq.current) return
              const newEdges = convertEdges(sub.edges)
              setEdges((eds) => {
                const have = new Set(eds.map((e) => e.id))
                return [...eds, ...newEdges.filter((e) => !have.has(e.id))]
              })
              addEdges(sub.edges)
            } catch (error) {
              console.error('Failed to load edges for search results:', error)
            }
          }

          const matchingNodeIds = new Set(results.map((n) => n.id))
          setNodes((nds) =>
            nds.map((node) => ({
              ...node,
              style: { ...node.style, opacity: matchingNodeIds.has(node.id) ? 1 : 0.3 },
            }))
          )

          // Focus on the first result if it was already on the canvas
          const target = nodesRef.current.find((n) => n.id === results[0].id)
          if (target) {
            setCenterRef.current(target.position.x, target.position.y, { zoom: 1.5, duration: 800 })
          }
        } catch (error) {
          console.error('Search failed:', error)
        }
      }, 500),
    [addNodes, addEdges, resetSearchHighlight]
  )

  useEffect(() => {
    if (searchQuery.trim()) {
      handleSearch(searchQuery)
    } else {
      // Cleared: drop any pending/in-flight search and restore opacity
      handleSearch.cancel()
      searchSeq.current++
      resetSearchHighlight()
    }
    return () => handleSearch.cancel()
  }, [searchQuery, handleSearch, resetSearchHighlight])

  // The chat asked us to show an entity: add it (and its neighbours) to the canvas, select it, centre on it
  useEffect(() => {
    if (!focusRequest) return
    const { nodeId, nodes: incoming, edges: incomingEdges } = focusRequest
    const current = nodesRef.current
    const have = new Set(current.map((n) => n.id))

    // Anchor: where the entity already is, or a free spot below the existing graph
    const existing = current.find((n) => n.id === nodeId)
    const maxY = current.length ? Math.max(...current.map((n) => n.position.y)) : 0
    const avgX = current.length ? current.reduce((a, n) => a + n.position.x, 0) / current.length : 400
    const anchor = existing ? existing.position : { x: avgX, y: maxY + 300 }

    const toAdd = incoming.filter((n) => !have.has(n.id))
    const ring = toAdd.filter((n) => n.id !== nodeId)
    const added: Node[] = toAdd.map((n) => {
      let position = anchor
      if (n.id !== nodeId) {
        const i = ring.findIndex((r) => r.id === n.id)
        const angle = (2 * Math.PI * i) / Math.max(ring.length, 1)
        position = { x: anchor.x + 300 * Math.cos(angle), y: anchor.y + 300 * Math.sin(angle) }
      }
      return {
        id: n.id,
        type: 'custom',
        position,
        data: { label: n.label, type: n.type, color: n.color, properties: n.properties },
      }
    })

    const highlight = useGraphStore.getState().highlightedNodes
    const mark = (node: Node): Node =>
      highlight.has(node.id)
        ? {
            ...node,
            data: { ...node.data, isHighlighted: true },
            style: {
              ...node.style,
              border: `3px solid ${FLOW_COLORS.complete}`,
              boxShadow: `0 0 20px ${FLOW_COLORS.complete}80`,
            },
          }
        : node
    setNodes((nds) => [...nds, ...added].map(mark))

    const newEdges = convertEdges(incomingEdges)
    setEdges((eds) => {
      const ids = new Set(eds.map((e) => e.id))
      const keys = useGraphStore.getState().highlightedEdges
      return [...eds, ...newEdges.filter((e) => !ids.has(e.id))].map((e) =>
        keys.has(`${e.source}-${e.target}`)
          ? { ...e, animated: true, style: { ...e.style, stroke: FLOW_COLORS.edge, strokeWidth: 3 } }
          : e
      )
    })

    addNodes(incoming)
    addEdges(incomingEdges)
    const target = incoming.find((n) => n.id === nodeId)
    if (target) setSelectedNode(target)

    // After the nodes are on the canvas, frame the entity together with its connections
    setTimeout(() => {
      fitView({ nodes: incoming.map((n) => ({ id: n.id })), padding: 0.3, maxZoom: 1.1, duration: 500 })
      // The details panel (w-96) covers the right side of the canvas: slide the view left so the result isn't hidden
      setTimeout(() => {
        const v = getViewport()
        setViewport({ ...v, x: v.x - 190 }, { duration: 250 })
      }, 560)
    }, 120)
    clearFocusRequest()
  }, [focusRequest])

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

        {/* Instructions Panel (can be minimized) */}
        {nodes.length > 0 && !flowPath && (
          <Panel position="top-left" className="mt-14 max-w-sm">
            {hintOpen ? (
              <div className="flex items-start gap-2 bg-blue-50 border border-blue-200 rounded-lg pl-4 pr-2 py-2">
                <p className="text-sm text-blue-900">
                  <strong>Click</strong> to view details • <strong>Double-click</strong> to expand connections
                </p>
                <button
                  onClick={() => toggleHint(false)}
                  className="shrink-0 p-1 text-blue-700 hover:bg-blue-100 rounded transition-colors"
                  title="Minimize tips"
                  aria-label="Minimize tips"
                >
                  <Minus className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => toggleHint(true)}
                className="p-2 bg-blue-50 border border-blue-200 rounded-full text-blue-700 hover:bg-blue-100 shadow-sm transition-colors"
                title="Show tips"
                aria-label="Show tips"
              >
                <Info className="w-4 h-4" />
              </button>
            )}
          </Panel>
        )}

        {/* Flow Status Panel */}
        {flowPath && (
          <Panel position="top-left" className={`mt-14 max-w-sm border rounded-lg px-4 py-2 ${
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
                {flowPath.message
                  ? flowPath.path_nodes.length > 0
                    ? `${flowPath.message} · ${flowPath.path_nodes.length} nodes highlighted`
                    : flowPath.message
                  : `${getFlowStatusLabel(flowPath.status)} - ${flowPath.path_nodes.length} nodes highlighted`}
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
