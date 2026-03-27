/**
 * Graph layout utilities for React Flow
 */
import type { GraphNode as BackendNode } from '@/types'
import type { Node, Edge } from 'reactflow'

/**
 * Convert backend nodes to React Flow nodes with positions
 */
export function layoutNodes(
  backendNodes: BackendNode[],
  options: {
    width?: number
    height?: number
    centerX?: number
    centerY?: number
  } = {}
): Node[] {
  const {
    width = 1200,
    height = 800,
    centerX = width / 2,
    centerY = height / 2,
  } = options

  // Group nodes by type
  const nodesByType: Record<string, BackendNode[]> = {}
  backendNodes.forEach((node) => {
    if (!nodesByType[node.type]) {
      nodesByType[node.type] = []
    }
    nodesByType[node.type].push(node)
  })

  const types = Object.keys(nodesByType)
  const reactFlowNodes: Node[] = []

  // Use circular layout for different entity types
  types.forEach((type, typeIndex) => {
    const nodes = nodesByType[type]
    const radius = 200 + typeIndex * 100 // Different radius for each type
    const angleStep = (2 * Math.PI) / nodes.length

    nodes.forEach((node, nodeIndex) => {
      const angle = angleStep * nodeIndex
      const x = centerX + radius * Math.cos(angle)
      const y = centerY + radius * Math.sin(angle)

      reactFlowNodes.push({
        id: node.id,
        type: 'custom',
        position: { x, y },
        data: {
          label: node.label,
          type: node.type,
          color: node.color,
          properties: node.properties,
        },
      })
    })
  })

  return reactFlowNodes
}

/**
 * Convert backend edges to React Flow edges
 */
export function convertEdges(
  backendEdges: Array<{ source: string; target: string; type: string; label: string }>
): Edge[] {
  return backendEdges.map((edge, index) => ({
    id: `${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    type: 'smoothstep',
    label: edge.label,
    animated: false,
    style: { stroke: '#94a3b8', strokeWidth: 2 },
    labelStyle: { fontSize: 10, fill: '#64748b' },
    labelBgStyle: { fill: '#ffffff', fillOpacity: 0.8 },
  }))
}

/**
 * Force-directed layout simulation (simple version)
 */
export function applyForceLayout(
  nodes: Node[],
  edges: Edge[],
  iterations: number = 50
): Node[] {
  const updatedNodes = [...nodes]
  const nodeMap = new Map(updatedNodes.map((n) => [n.id, n]))

  // Build adjacency list
  const adjacency = new Map<string, string[]>()
  edges.forEach((edge) => {
    if (!adjacency.has(edge.source)) adjacency.set(edge.source, [])
    if (!adjacency.has(edge.target)) adjacency.set(edge.target, [])
    adjacency.get(edge.source)!.push(edge.target)
    adjacency.get(edge.target)!.push(edge.source)
  })

  // Constants
  const k = 100 // Ideal distance
  const c_rep = 50000 // Repulsion constant
  const c_spring = 0.01 // Spring constant

  for (let iter = 0; iter < iterations; iter++) {
    const forces = new Map<string, { x: number; y: number }>()

    // Initialize forces
    updatedNodes.forEach((node) => {
      forces.set(node.id, { x: 0, y: 0 })
    })

    // Repulsive forces (all pairs)
    for (let i = 0; i < updatedNodes.length; i++) {
      for (let j = i + 1; j < updatedNodes.length; j++) {
        const n1 = updatedNodes[i]
        const n2 = updatedNodes[j]

        const dx = n2.position.x - n1.position.x
        const dy = n2.position.y - n1.position.y
        const distance = Math.sqrt(dx * dx + dy * dy) || 1

        const force = c_rep / (distance * distance)
        const fx = (force * dx) / distance
        const fy = (force * dy) / distance

        const f1 = forces.get(n1.id)!
        const f2 = forces.get(n2.id)!

        f1.x -= fx
        f1.y -= fy
        f2.x += fx
        f2.y += fy
      }
    }

    // Attractive forces (connected nodes)
    edges.forEach((edge) => {
      const n1 = nodeMap.get(edge.source)
      const n2 = nodeMap.get(edge.target)

      if (!n1 || !n2) return

      const dx = n2.position.x - n1.position.x
      const dy = n2.position.y - n1.position.y
      const distance = Math.sqrt(dx * dx + dy * dy) || 1

      const force = c_spring * (distance - k)
      const fx = (force * dx) / distance
      const fy = (force * dy) / distance

      const f1 = forces.get(n1.id)!
      const f2 = forces.get(n2.id)!

      f1.x += fx
      f1.y += fy
      f2.x -= fx
      f2.y -= fy
    })

    // Update positions
    updatedNodes.forEach((node) => {
      const force = forces.get(node.id)!
      node.position.x += force.x * 0.1
      node.position.y += force.y * 0.1
    })
  }

  return updatedNodes
}

/**
 * Calculate bounding box of nodes
 */
export function getBoundingBox(nodes: Node[]): {
  minX: number
  minY: number
  maxX: number
  maxY: number
  width: number
  height: number
} {
  if (nodes.length === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0, width: 0, height: 0 }
  }

  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity

  nodes.forEach((node) => {
    minX = Math.min(minX, node.position.x)
    minY = Math.min(minY, node.position.y)
    maxX = Math.max(maxX, node.position.x)
    maxY = Math.max(maxY, node.position.y)
  })

  return {
    minX,
    minY,
    maxX,
    maxY,
    width: maxX - minX,
    height: maxY - minY,
  }
}
