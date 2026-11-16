/**
 * API service for communicating with the backend
 */
import axios, { AxiosInstance } from 'axios';
import { useSessionStore } from '@/stores/sessionStore';
import type {
  GraphData,
  GraphOverview,
  GraphNode,
  QueryResponse,
  FlowTraceResponse,
} from '@/types';

// Get API URL from environment variable or use default
// Node ids come from user data and may contain '/', '?', '#', spaces...
const encodeId = (id: string) => id.split('/').map(encodeURIComponent).join('/');

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Send the connection session (if any) with every request
apiClient.interceptors.request.use((config) => {
  const session = useSessionStore.getState().session;
  if (session) config.headers.set('X-Session-Id', session.sessionId);
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Session expired on the server: drop it so the UI asks the user to reconnect
    if (error?.response?.status === 401 && useSessionStore.getState().session) {
      useSessionStore.getState().setSession(null);
    }
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Graph API endpoints
export const graphAPI = {
  /**
   * Get graph overview statistics
   */
  getOverview: async (): Promise<GraphOverview> => {
    const response = await apiClient.get('/api/graph/overview');
    return response.data;
  },

  /**
   * Get nodes with pagination
   */
  getNodes: async (params?: {
    limit?: number;
    offset?: number;
    node_type?: string;
  }): Promise<GraphNode[]> => {
    const response = await apiClient.get('/api/graph/nodes', { params });
    return response.data;
  },

  /**
   * Get a specific node by ID
   */
  getNode: async (nodeId: string): Promise<GraphNode> => {
    const response = await apiClient.get(`/api/graph/nodes/${encodeId(nodeId)}`);
    return response.data;
  },

  /**
   * Expand node connections
   */
  expandNode: async (
    nodeId: string,
    depth: number = 1
  ): Promise<GraphData> => {
    const response = await apiClient.post(`/api/graph/nodes/${encodeId(nodeId)}/expand`, {
      depth,
    });
    return response.data;
  },

  /**
   * Search nodes
   */
  searchNodes: async (query: string): Promise<GraphNode[]> => {
    const response = await apiClient.post('/api/graph/search', { query });
    return response.data;
  },

  /**
   * Get the nodes with the edges between them
   */
  getSubgraph: async (nodeIds: string[]): Promise<GraphData> => {
    const response = await apiClient.post('/api/graph/subgraph', nodeIds);
    return response.data;
  },

  /**
   * Export the whole graph as a JSON blob
   */
  exportGraph: async (): Promise<Blob> => {
    const response = await apiClient.get('/api/graph/export', {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Trace flow through the graph
   */
  traceFlow: async (entityId: string): Promise<FlowTraceResponse> => {
    const response = await apiClient.get(`/api/graph/trace/${encodeId(entityId)}`);
    return response.data;
  },
};

// Query API endpoints
export const queryAPI = {
  /**
   * Send a natural language query
   */
  chat: async (query: string): Promise<QueryResponse> => {
    const response = await apiClient.post('/api/query/chat', { query });
    return response.data;
  },
};

// Connect to a user-supplied database
export interface ConnectConfig {
  access_code_required: boolean;
  supported: string[];
  session_ttl_minutes: number;
}

export const connectAPI = {
  getConfig: async (): Promise<ConnectConfig> => {
    const response = await apiClient.get('/api/connect/config');
    return response.data;
  },

  connect: async (url: string, accessCode?: string) => {
    const response = await apiClient.post(
      '/api/connect',
      { url },
      { headers: accessCode ? { 'X-Access-Code': accessCode } : {}, timeout: 120000 }
    );
    return response.data as {
      session_id: string;
      dialect: string;
      database: string;
      tables: number;
      nodes: number;
      edges: number;
    };
  },

  disconnect: async (): Promise<void> => {
    await apiClient.delete('/api/connect');
  },
};

// Health check
export const healthCheck = async (): Promise<any> => {
  const response = await apiClient.get('/health');
  return response.data;
};

export default apiClient;
