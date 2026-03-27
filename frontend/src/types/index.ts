/**
 * Type definitions for the Graph Data Modeling System
 */

// Node types
export type NodeType =
  | 'Customer'
  | 'Product'
  | 'Order'
  | 'Delivery'
  | 'Invoice'
  | 'Payment'
  | 'Address';

// Graph node
export interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  color: string;
  properties: Record<string, any>;
}

// Graph edge
export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  label: string;
  properties?: Record<string, any>;
}

// Graph data
export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Graph overview statistics
export interface GraphOverview {
  nodes: number;
  edges: number;
  node_types: Record<NodeType, number>;
  edge_types: Record<string, number>;
}

// Chat message types
export type MessageRole = 'user' | 'assistant' | 'system' | 'error';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  data?: any;
  entities?: string[];
  timestamp: Date;
}

// Query response
export interface QueryResponse {
  success: boolean;
  answer?: string;
  data?: any;
  entities?: string[];
  message?: string;
}

// API error
export interface APIError {
  detail: string;
}

// Flow trace response
export interface FlowTraceResponse {
  success: boolean;
  path_nodes: Array<{
    id: string;
    type: string;
    label: string;
    color: string;
    properties: Record<string, any>;
  }>;
  path_edges: Array<{
    source: string;
    target: string;
    type: string;
  }>;
  status: 'complete' | 'partial' | 'incomplete' | 'error';
  message: string;
}
