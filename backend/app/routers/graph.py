"""Graph API router."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, List
import json
import io

from app.core.graph_store import get_graph
from app.services.graph_service import GraphService
from app.schemas.graph import (
    GraphOverview,
    GraphNode,
    GraphData,
    NodeExpandRequest,
    NodeSearchRequest,
    FlowTraceResponse,
)


router = APIRouter()


def get_graph_service() -> GraphService:
    """Get graph service instance."""
    graph = get_graph()
    return GraphService(graph)


@router.get("/overview", response_model=GraphOverview)
async def get_overview():
    """
    Get graph overview statistics.

    Returns graph statistics including:
    - Total number of nodes and edges
    - Count of each node type
    - Count of each edge type
    - Graph density
    """
    service = get_graph_service()
    return service.get_overview()


@router.get("/nodes", response_model=List[GraphNode])
async def get_nodes(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum nodes to return"),
    offset: int = Query(default=0, ge=0, description="Number of nodes to skip"),
    node_type: Optional[str] = Query(default=None, description="Filter by node type")
):
    """
    Get nodes with pagination and optional filtering.

    Query Parameters:
    - limit: Maximum number of nodes (default 100, max 1000)
    - offset: Number of nodes to skip for pagination (default 0)
    - node_type: Filter by entity type (Customer, Product, Order, etc.)

    Returns list of nodes with properties.
    """
    service = get_graph_service()
    return service.get_nodes(limit=limit, offset=offset, node_type=node_type)


@router.get("/nodes/{node_id}", response_model=GraphNode)
async def get_node(node_id: str):
    """
    Get a specific node by ID.

    Path Parameters:
    - node_id: Unique identifier for the node (e.g., CUST-0001, ORD-0123)

    Returns node with all properties and metadata.

    Raises:
    - 404: Node not found
    """
    service = get_graph_service()
    node = service.get_node(node_id)

    if node is None:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    return node


@router.post("/nodes/{node_id}/expand", response_model=GraphData)
async def expand_node(node_id: str, request: NodeExpandRequest):
    """
    Expand a node to get its connected nodes and edges.

    This endpoint returns all nodes connected to the specified node
    within the given depth (number of hops).

    Path Parameters:
    - node_id: Node to expand

    Request Body:
    - depth: Expansion depth (1 or 2 hops)

    Returns GraphData with connected nodes and edges.

    Raises:
    - 404: Node not found
    """
    service = get_graph_service()

    if not get_graph().has_node(node_id):
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    return service.expand_node(node_id, depth=request.depth)


@router.post("/search", response_model=List[GraphNode])
async def search_nodes(request: NodeSearchRequest):
    """
    Search nodes by text query.

    Searches across node IDs, labels, and properties.

    Request Body:
    - query: Search string
    - node_type: Optional filter by node type
    - limit: Maximum results (default 50, max 500)

    Returns list of matching nodes.
    """
    service = get_graph_service()
    return service.search_nodes(
        query=request.query,
        node_type=request.node_type,
        limit=request.limit
    )


@router.get("/nodes/{node_id}/neighbors", response_model=dict)
async def get_node_neighbors(node_id: str):
    """
    Get neighbors of a node grouped by relationship type.

    Path Parameters:
    - node_id: Node identifier

    Returns dictionary mapping edge types to lists of neighbor nodes.

    Raises:
    - 404: Node not found
    """
    service = get_graph_service()

    if not get_graph().has_node(node_id):
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    neighbors = service.get_node_neighbors(node_id)

    # Convert to serializable format
    result = {}
    for edge_type, nodes in neighbors.items():
        result[edge_type] = [node.model_dump() for node in nodes]

    return result


@router.post("/subgraph", response_model=GraphData)
async def get_subgraph(node_ids: List[str]):
    """
    Get a subgraph containing specified nodes.

    Request Body:
    - List of node IDs

    Returns GraphData with the subgraph containing only the specified nodes
    and edges between them.
    """
    service = get_graph_service()
    return service.get_subgraph(node_ids)


@router.get("/trace/{entity_id}", response_model=FlowTraceResponse)
async def trace_flow(entity_id: str):
    """
    Trace flow through the graph for visualization.

    Returns the complete flow path for an entity with nodes and edges
    that can be highlighted in the graph visualization.

    Path Parameters:
    - entity_id: Entity to trace (Order, Invoice, Delivery, etc.)

    Returns:
    - success: Whether the trace was successful
    - path_nodes: List of nodes in the flow path
    - path_edges: List of edges connecting the path
    - status: Flow completeness (complete, partial, incomplete, error)
    - message: Description of the flow

    Example: /api/graph/trace/ORD-0123
    Returns the Order → Invoice → Payment → Delivery flow
    """
    service = get_graph_service()
    result = service.trace_flow_visual(entity_id)
    return FlowTraceResponse(**result)


@router.get("/export")
async def export_graph():
    """
    Export the entire graph as JSON.

    Returns a JSON file containing all nodes and edges in the graph.
    This can be used for backup, sharing, or importing into other tools.

    Response format:
    {
      "nodes": [{id, type, label, color, properties}, ...],
      "edges": [{source, target, type, label, properties}, ...],
      "metadata": {node_count, edge_count, exported_at}
    }
    """
    service = get_graph_service()
    graph = get_graph()

    # Export all nodes
    all_nodes = []
    for node_id in graph.nodes():
        data = graph.nodes[node_id]
        all_nodes.append({
            "id": node_id,
            "type": data.get("type", "Unknown"),
            "label": data.get("label", node_id),
            "color": data.get("color", "#808080"),
            "properties": data.get("properties", {})
        })

    # Export all edges
    all_edges = []
    for source, target in graph.edges():
        edge_data = graph.edges[source, target]
        all_edges.append({
            "source": source,
            "target": target,
            "type": edge_data.get("type", "UNKNOWN"),
            "label": edge_data.get("label", ""),
            "properties": edge_data.get("properties", {})
        })

    # Create export data
    export_data = {
        "nodes": all_nodes,
        "edges": all_edges,
        "metadata": {
            "node_count": len(all_nodes),
            "edge_count": len(all_edges),
            "exported_at": str(__import__("datetime").datetime.now())
        }
    }

    # Convert to JSON
    json_str = json.dumps(export_data, indent=2)
    json_bytes = json_str.encode('utf-8')

    # Return as downloadable file
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=graph_export.json"}
    )
