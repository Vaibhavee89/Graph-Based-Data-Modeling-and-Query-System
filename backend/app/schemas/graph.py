"""Pydantic schemas for graph API."""
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class GraphNode(BaseModel):
    """Graph node schema."""
    id: str
    type: str
    label: str
    color: str
    properties: Dict[str, Any]


class GraphEdge(BaseModel):
    """Graph edge schema."""
    source: str
    target: str
    type: str
    label: str
    properties: Optional[Dict[str, Any]] = {}


class GraphData(BaseModel):
    """Graph data with nodes and edges."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class GraphOverview(BaseModel):
    """Graph overview statistics."""
    nodes: int = Field(description="Total number of nodes")
    edges: int = Field(description="Total number of edges")
    node_types: Dict[str, int] = Field(description="Count of each node type")
    edge_types: Dict[str, int] = Field(description="Count of each edge type")
    density: float = Field(description="Graph density")
    is_directed: bool = Field(description="Whether graph is directed")


class NodeExpandRequest(BaseModel):
    """Request to expand a node's connections."""
    depth: int = Field(default=1, ge=1, le=2, description="Expansion depth (1-2)")


class NodeSearchRequest(BaseModel):
    """Request to search nodes."""
    query: str = Field(description="Search query")
    node_type: Optional[str] = Field(default=None, description="Filter by node type")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum results")


class NodeListParams(BaseModel):
    """Query parameters for listing nodes."""
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    node_type: Optional[str] = None


class FlowTraceResponse(BaseModel):
    """Response for flow tracing with visualization data."""
    success: bool
    path_nodes: List[Dict[str, Any]]
    path_edges: List[Dict[str, str]]
    status: str = Field(description="Flow status: complete, partial, incomplete, or error")
    message: str
