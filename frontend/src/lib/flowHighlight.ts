/**
 * Flow highlighting utilities for graph visualization
 */

import { Node, Edge } from 'reactflow'

export interface FlowPath {
  success: boolean
  path_nodes: Array<{
    id: string
    type: string
    label: string
    color: string
    properties: Record<string, any>
  }>
  path_edges: Array<{
    source: string
    target: string
    type: string
  }>
  status: 'complete' | 'partial' | 'incomplete' | 'error'
  message: string
}

export interface FlowHighlightColors {
  complete: string
  partial: string
  incomplete: string
  edge: string
}

export const FLOW_COLORS: FlowHighlightColors = {
  complete: '#10b981', // green
  partial: '#f59e0b', // yellow/amber
  incomplete: '#ef4444', // red
  edge: '#3b82f6', // blue
}

/**
 * Apply flow highlighting to nodes
 */
export function highlightFlowNodes(
  nodes: Node[],
  flowPath: FlowPath
): Node[] {
  if (!flowPath.success || flowPath.path_nodes.length === 0) {
    return nodes
  }

  const pathNodeIds = new Set(flowPath.path_nodes.map((n) => n.id))

  // Determine node colors based on flow status
  const getFlowColor = (status: string) => {
    switch (status) {
      case 'complete':
        return FLOW_COLORS.complete
      case 'partial':
        return FLOW_COLORS.partial
      case 'incomplete':
        return FLOW_COLORS.incomplete
      default:
        return FLOW_COLORS.incomplete
    }
  }

  const flowColor = getFlowColor(flowPath.status)

  return nodes.map((node) => {
    if (pathNodeIds.has(node.id)) {
      return {
        ...node,
        data: {
          ...node.data,
          isHighlighted: true,
          highlightColor: flowColor,
        },
        style: {
          ...node.style,
          border: `3px solid ${flowColor}`,
          boxShadow: `0 0 20px ${flowColor}80`,
        },
      }
    }
    return node
  })
}

/**
 * Apply flow highlighting to edges
 */
export function highlightFlowEdges(
  edges: Edge[],
  flowPath: FlowPath
): Edge[] {
  if (!flowPath.success || flowPath.path_edges.length === 0) {
    return edges
  }

  // Create a set of path edge identifiers
  const pathEdgeKeys = new Set(
    flowPath.path_edges.map((e) => `${e.source}-${e.target}`)
  )

  return edges.map((edge) => {
    const edgeKey = `${edge.source}-${edge.target}`
    if (pathEdgeKeys.has(edgeKey)) {
      return {
        ...edge,
        animated: true,
        style: {
          ...edge.style,
          stroke: FLOW_COLORS.edge,
          strokeWidth: 3,
        },
        data: {
          ...edge.data,
          isHighlighted: true,
        },
      }
    }
    return edge
  })
}

/**
 * Clear all flow highlighting from nodes and edges
 */
export function clearFlowHighlight(
  nodes: Node[],
  edges: Edge[]
): { nodes: Node[]; edges: Edge[] } {
  const clearedNodes = nodes.map((node) => {
    if (node.data?.isHighlighted) {
      const { isHighlighted, highlightColor, ...restData } = node.data
      return {
        ...node,
        data: restData,
        style: {
          ...node.style,
          border: undefined,
          boxShadow: undefined,
        },
      }
    }
    return node
  })

  const clearedEdges = edges.map((edge) => {
    if (edge.data?.isHighlighted) {
      const { isHighlighted, ...restData } = edge.data
      return {
        ...edge,
        animated: false,
        data: restData,
        style: {
          ...edge.style,
          stroke: '#94a3b8',
          strokeWidth: 1,
        },
      }
    }
    return edge
  })

  return { nodes: clearedNodes, edges: clearedEdges }
}

/**
 * Get flow status icon
 */
export function getFlowStatusIcon(status: string): string {
  switch (status) {
    case 'complete':
      return '✅'
    case 'partial':
      return '⚠️'
    case 'incomplete':
      return '❌'
    default:
      return '❓'
  }
}

/**
 * Get flow status label
 */
export function getFlowStatusLabel(status: string): string {
  switch (status) {
    case 'complete':
      return 'Complete Flow'
    case 'partial':
      return 'Partial Flow'
    case 'incomplete':
      return 'Incomplete Flow'
    default:
      return 'Unknown Status'
  }
}
