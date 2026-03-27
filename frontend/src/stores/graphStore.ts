/**
 * Graph state management using Zustand
 */
import { create } from 'zustand';
import type { GraphNode, GraphEdge, FlowTraceResponse } from '@/types';

interface GraphStore {
  // State
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNode: GraphNode | null;
  expandedNodes: Set<string>;
  flowPath: FlowTraceResponse | null;
  highlightedNodes: Set<string>;
  highlightedEdges: Set<string>;

  // Actions
  setNodes: (nodes: GraphNode[]) => void;
  setEdges: (edges: GraphEdge[]) => void;
  addNodes: (nodes: GraphNode[]) => void;
  addEdges: (edges: GraphEdge[]) => void;
  setSelectedNode: (node: GraphNode | null) => void;
  markNodeExpanded: (nodeId: string) => void;
  clearGraph: () => void;
  focusNode: (nodeId: string) => void;
  setFlowPath: (flowPath: FlowTraceResponse | null) => void;
  clearFlowHighlight: () => void;
}

export const useGraphStore = create<GraphStore>((set, get) => ({
  // Initial state
  nodes: [],
  edges: [],
  selectedNode: null,
  expandedNodes: new Set(),
  flowPath: null,
  highlightedNodes: new Set(),
  highlightedEdges: new Set(),

  // Set all nodes (replace existing)
  setNodes: (nodes) => set({ nodes }),

  // Set all edges (replace existing)
  setEdges: (edges) => set({ edges }),

  // Add nodes (merge with existing, avoid duplicates)
  addNodes: (newNodes) =>
    set((state) => {
      const existingIds = new Set(state.nodes.map((n) => n.id));
      const uniqueNewNodes = newNodes.filter((n) => !existingIds.has(n.id));
      return { nodes: [...state.nodes, ...uniqueNewNodes] };
    }),

  // Add edges (merge with existing, avoid duplicates)
  addEdges: (newEdges) =>
    set((state) => {
      const existingEdges = new Set(
        state.edges.map((e) => `${e.source}-${e.target}-${e.type}`)
      );
      const uniqueNewEdges = newEdges.filter(
        (e) => !existingEdges.has(`${e.source}-${e.target}-${e.type}`)
      );
      return { edges: [...state.edges, ...uniqueNewEdges] };
    }),

  // Select a node
  setSelectedNode: (node) => set({ selectedNode: node }),

  // Mark node as expanded
  markNodeExpanded: (nodeId) =>
    set((state) => {
      const newExpanded = new Set(state.expandedNodes);
      newExpanded.add(nodeId);
      return { expandedNodes: newExpanded };
    }),

  // Clear all graph data
  clearGraph: () =>
    set({
      nodes: [],
      edges: [],
      selectedNode: null,
      expandedNodes: new Set(),
    }),

  // Focus on a specific node (used for entity linking)
  focusNode: (nodeId) => {
    const node = get().nodes.find((n) => n.id === nodeId);
    if (node) {
      set({ selectedNode: node });
    }
  },

  // Set flow path for highlighting
  setFlowPath: (flowPath) => {
    if (!flowPath) {
      set({ flowPath: null, highlightedNodes: new Set(), highlightedEdges: new Set() });
      return;
    }

    const highlightedNodes = new Set(flowPath.path_nodes.map((n) => n.id));
    const highlightedEdges = new Set(
      flowPath.path_edges.map((e) => `${e.source}-${e.target}`)
    );

    set({ flowPath, highlightedNodes, highlightedEdges });
  },

  // Clear flow highlighting
  clearFlowHighlight: () => {
    set({ flowPath: null, highlightedNodes: new Set(), highlightedEdges: new Set() });
  },
}));
