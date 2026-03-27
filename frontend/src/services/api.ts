/**
 * API service for communicating with the backend
 */
import axios, { AxiosInstance } from 'axios';
import type {
  GraphData,
  GraphOverview,
  GraphNode,
  QueryResponse,
} from '@/types';

// Get API URL from environment variable or use default
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
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
    const response = await apiClient.get(`/api/graph/nodes/${nodeId}`);
    return response.data;
  },

  /**
   * Expand node connections
   */
  expandNode: async (
    nodeId: string,
    depth: number = 1
  ): Promise<GraphData> => {
    const response = await apiClient.post(`/api/graph/nodes/${nodeId}/expand`, {
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

// Health check
export const healthCheck = async (): Promise<any> => {
  const response = await apiClient.get('/health');
  return response.data;
};

export default apiClient;
