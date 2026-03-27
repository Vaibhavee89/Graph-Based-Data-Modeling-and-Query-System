"""Graph service - Business logic for graph operations."""
import networkx as nx
from typing import List, Dict, Optional, Set
from app.schemas.graph import GraphNode, GraphEdge, GraphData, GraphOverview


class GraphService:
    """Service for graph operations."""

    def __init__(self, graph: nx.DiGraph):
        """
        Initialize GraphService.

        Args:
            graph: NetworkX directed graph
        """
        self.graph = graph

    def get_overview(self) -> GraphOverview:
        """
        Get graph overview statistics.

        Returns:
            GraphOverview with statistics
        """
        if self.graph.number_of_nodes() == 0:
            return GraphOverview(
                nodes=0,
                edges=0,
                node_types={},
                edge_types={},
                density=0.0,
                is_directed=True
            )

        # Count node types
        node_types = {}
        for _, data in self.graph.nodes(data=True):
            node_type = data.get('type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1

        # Count edge types
        edge_types = {}
        for _, _, data in self.graph.edges(data=True):
            edge_type = data.get('type', 'Unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

        return GraphOverview(
            nodes=self.graph.number_of_nodes(),
            edges=self.graph.number_of_edges(),
            node_types=node_types,
            edge_types=edge_types,
            density=nx.density(self.graph),
            is_directed=self.graph.is_directed()
        )

    def get_nodes(
        self,
        limit: int = 100,
        offset: int = 0,
        node_type: Optional[str] = None
    ) -> List[GraphNode]:
        """
        Get nodes with pagination and optional filtering.

        Args:
            limit: Maximum number of nodes to return
            offset: Number of nodes to skip
            node_type: Filter by node type (e.g., 'Customer', 'Order')

        Returns:
            List of GraphNode objects
        """
        nodes = []

        # Get all nodes or filter by type
        all_nodes = list(self.graph.nodes(data=True))

        if node_type:
            all_nodes = [
                (node_id, data) for node_id, data in all_nodes
                if data.get('type') == node_type
            ]

        # Apply pagination
        paginated_nodes = all_nodes[offset:offset + limit]

        # Convert to GraphNode schema
        for node_id, data in paginated_nodes:
            nodes.append(GraphNode(
                id=node_id,
                type=data.get('type', 'Unknown'),
                label=data.get('label', node_id),
                color=data.get('color', '#808080'),
                properties=data.get('properties', {})
            ))

        return nodes

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """
        Get a specific node by ID.

        Args:
            node_id: Node identifier

        Returns:
            GraphNode or None if not found
        """
        if not self.graph.has_node(node_id):
            return None

        data = self.graph.nodes[node_id]

        return GraphNode(
            id=node_id,
            type=data.get('type', 'Unknown'),
            label=data.get('label', node_id),
            color=data.get('color', '#808080'),
            properties=data.get('properties', {})
        )

    def expand_node(self, node_id: str, depth: int = 1) -> GraphData:
        """
        Expand a node to get its connected nodes and edges.

        Args:
            node_id: Node identifier to expand
            depth: Depth of expansion (1 or 2 hops)

        Returns:
            GraphData with connected nodes and edges
        """
        if not self.graph.has_node(node_id):
            return GraphData(nodes=[], edges=[])

        # Get connected nodes using BFS
        connected_nodes = self._get_connected_nodes(node_id, depth)

        # Get edges between these nodes
        edges = self._get_edges_between_nodes(connected_nodes)

        # Convert to schema objects
        nodes = []
        for nid in connected_nodes:
            data = self.graph.nodes[nid]
            nodes.append(GraphNode(
                id=nid,
                type=data.get('type', 'Unknown'),
                label=data.get('label', nid),
                color=data.get('color', '#808080'),
                properties=data.get('properties', {})
            ))

        edge_objects = []
        for source, target, data in edges:
            edge_objects.append(GraphEdge(
                source=source,
                target=target,
                type=data.get('type', 'UNKNOWN'),
                label=data.get('label', ''),
                properties=data.get('properties', {})
            ))

        return GraphData(nodes=nodes, edges=edge_objects)

    def _get_connected_nodes(self, node_id: str, depth: int) -> Set[str]:
        """
        Get all nodes connected to a node within specified depth.

        Args:
            node_id: Starting node
            depth: Maximum distance

        Returns:
            Set of connected node IDs
        """
        connected = {node_id}
        current_level = {node_id}

        for _ in range(depth):
            next_level = set()
            for node in current_level:
                # Get successors (outgoing edges)
                next_level.update(self.graph.successors(node))
                # Get predecessors (incoming edges)
                next_level.update(self.graph.predecessors(node))

            connected.update(next_level)
            current_level = next_level

        return connected

    def _get_edges_between_nodes(self, node_ids: Set[str]) -> List[tuple]:
        """
        Get all edges between a set of nodes.

        Args:
            node_ids: Set of node IDs

        Returns:
            List of (source, target, data) tuples
        """
        edges = []

        for source in node_ids:
            for target in self.graph.successors(source):
                if target in node_ids:
                    edge_data = self.graph.edges[source, target]
                    edges.append((source, target, edge_data))

        return edges

    def search_nodes(
        self,
        query: str,
        node_type: Optional[str] = None,
        limit: int = 50
    ) -> List[GraphNode]:
        """
        Search nodes by text query.

        Args:
            query: Search query string
            node_type: Optional filter by node type
            limit: Maximum results

        Returns:
            List of matching GraphNode objects
        """
        query_lower = query.lower()
        matching_nodes = []

        for node_id, data in self.graph.nodes(data=True):
            # Filter by type if specified
            if node_type and data.get('type') != node_type:
                continue

            # Search in node ID, label, and properties
            if self._node_matches_query(node_id, data, query_lower):
                matching_nodes.append(GraphNode(
                    id=node_id,
                    type=data.get('type', 'Unknown'),
                    label=data.get('label', node_id),
                    color=data.get('color', '#808080'),
                    properties=data.get('properties', {})
                ))

                # Stop if we've reached the limit
                if len(matching_nodes) >= limit:
                    break

        return matching_nodes

    def _node_matches_query(self, node_id: str, data: Dict, query: str) -> bool:
        """
        Check if a node matches the search query.

        Args:
            node_id: Node identifier
            data: Node data dictionary
            query: Search query (lowercase)

        Returns:
            True if node matches query
        """
        # Check node ID
        if query in node_id.lower():
            return True

        # Check label
        label = data.get('label', '')
        if query in label.lower():
            return True

        # Check properties
        properties = data.get('properties', {})
        for key, value in properties.items():
            if isinstance(value, str) and query in value.lower():
                return True

        return False

    def get_subgraph(self, node_ids: List[str]) -> GraphData:
        """
        Get a subgraph containing specified nodes.

        Args:
            node_ids: List of node IDs to include

        Returns:
            GraphData with nodes and edges
        """
        # Filter to existing nodes
        existing_nodes = [nid for nid in node_ids if self.graph.has_node(nid)]

        if not existing_nodes:
            return GraphData(nodes=[], edges=[])

        # Create subgraph
        subgraph = self.graph.subgraph(existing_nodes)

        # Convert nodes
        nodes = []
        for node_id in subgraph.nodes():
            data = self.graph.nodes[node_id]
            nodes.append(GraphNode(
                id=node_id,
                type=data.get('type', 'Unknown'),
                label=data.get('label', node_id),
                color=data.get('color', '#808080'),
                properties=data.get('properties', {})
            ))

        # Convert edges
        edges = []
        for source, target in subgraph.edges():
            edge_data = self.graph.edges[source, target]
            edges.append(GraphEdge(
                source=source,
                target=target,
                type=edge_data.get('type', 'UNKNOWN'),
                label=edge_data.get('label', ''),
                properties=edge_data.get('properties', {})
            ))

        return GraphData(nodes=nodes, edges=edges)

    def get_node_neighbors(self, node_id: str) -> Dict[str, List[GraphNode]]:
        """
        Get neighbors of a node grouped by relationship type.

        Args:
            node_id: Node identifier

        Returns:
            Dictionary mapping edge types to lists of neighbor nodes
        """
        if not self.graph.has_node(node_id):
            return {}

        neighbors_by_type = {}

        # Get outgoing edges
        for target in self.graph.successors(node_id):
            edge_data = self.graph.edges[node_id, target]
            edge_type = edge_data.get('type', 'UNKNOWN')

            if edge_type not in neighbors_by_type:
                neighbors_by_type[edge_type] = []

            target_data = self.graph.nodes[target]
            neighbors_by_type[edge_type].append(GraphNode(
                id=target,
                type=target_data.get('type', 'Unknown'),
                label=target_data.get('label', target),
                color=target_data.get('color', '#808080'),
                properties=target_data.get('properties', {})
            ))

        # Get incoming edges
        for source in self.graph.predecessors(node_id):
            edge_data = self.graph.edges[source, node_id]
            edge_type = f"REVERSE_{edge_data.get('type', 'UNKNOWN')}"

            if edge_type not in neighbors_by_type:
                neighbors_by_type[edge_type] = []

            source_data = self.graph.nodes[source]
            neighbors_by_type[edge_type].append(GraphNode(
                id=source,
                type=source_data.get('type', 'Unknown'),
                label=source_data.get('label', source),
                color=source_data.get('color', '#808080'),
                properties=source_data.get('properties', {})
            ))

        return neighbors_by_type

    def trace_flow_visual(self, entity_id: str) -> Dict[str, any]:
        """
        Trace flow through the graph and return path data for visualization.

        Args:
            entity_id: Starting entity ID

        Returns:
            Dictionary with path nodes, edges, and status
        """
        if not self.graph.has_node(entity_id):
            return {
                "success": False,
                "message": f"Entity {entity_id} not found",
                "path_nodes": [],
                "path_edges": [],
                "status": "error"
            }

        entity_type = self.graph.nodes[entity_id].get('type')
        path_nodes = [entity_id]
        path_edges = []
        flow_status = "complete"

        if entity_type == 'Order':
            # Trace Order → Invoice → Payment → Delivery

            # Find invoice
            invoice_id = None
            for successor in self.graph.successors(entity_id):
                if self.graph.nodes[successor].get('type') == 'Invoice':
                    invoice_id = successor
                    path_nodes.append(invoice_id)
                    path_edges.append({
                        "source": entity_id,
                        "target": invoice_id,
                        "type": "GENERATED"
                    })
                    break

            if not invoice_id:
                flow_status = "incomplete"
            else:
                # Find payment
                payment_id = None
                for successor in self.graph.successors(invoice_id):
                    if self.graph.nodes[successor].get('type') == 'Payment':
                        payment_id = successor
                        path_nodes.append(payment_id)
                        path_edges.append({
                            "source": invoice_id,
                            "target": payment_id,
                            "type": "PAID_BY"
                        })
                        break

                if not payment_id:
                    flow_status = "partial"

            # Find delivery
            delivery_id = None
            for successor in self.graph.successors(entity_id):
                if self.graph.nodes[successor].get('type') == 'Delivery':
                    delivery_id = successor
                    path_nodes.append(delivery_id)
                    path_edges.append({
                        "source": entity_id,
                        "target": delivery_id,
                        "type": "RESULTED_IN"
                    })
                    break

            if not delivery_id and flow_status == "complete":
                flow_status = "partial"

        elif entity_type == 'Invoice':
            # Trace Invoice → Payment
            payment_id = None
            for successor in self.graph.successors(entity_id):
                if self.graph.nodes[successor].get('type') == 'Payment':
                    payment_id = successor
                    path_nodes.append(payment_id)
                    path_edges.append({
                        "source": entity_id,
                        "target": payment_id,
                        "type": "PAID_BY"
                    })
                    break

            if not payment_id:
                flow_status = "incomplete"

            # Trace back to Order
            for predecessor in self.graph.predecessors(entity_id):
                if self.graph.nodes[predecessor].get('type') == 'Order':
                    path_nodes.insert(0, predecessor)
                    path_edges.insert(0, {
                        "source": predecessor,
                        "target": entity_id,
                        "type": "GENERATED"
                    })
                    break

        elif entity_type == 'Delivery':
            # Trace back to Order
            for predecessor in self.graph.predecessors(entity_id):
                if self.graph.nodes[predecessor].get('type') == 'Order':
                    order_id = predecessor
                    path_nodes.insert(0, order_id)
                    path_edges.insert(0, {
                        "source": order_id,
                        "target": entity_id,
                        "type": "RESULTED_IN"
                    })

                    # Find invoice for this order
                    for successor in self.graph.successors(order_id):
                        if self.graph.nodes[successor].get('type') == 'Invoice':
                            invoice_id = successor
                            path_nodes.insert(1, invoice_id)
                            path_edges.insert(0, {
                                "source": order_id,
                                "target": invoice_id,
                                "type": "GENERATED"
                            })
                            break
                    break

        # Get full node data for path nodes
        nodes_data = []
        for node_id in path_nodes:
            data = self.graph.nodes[node_id]
            nodes_data.append(GraphNode(
                id=node_id,
                type=data.get('type', 'Unknown'),
                label=data.get('label', node_id),
                color=data.get('color', '#808080'),
                properties=data.get('properties', {})
            ))

        return {
            "success": True,
            "path_nodes": [node.dict() for node in nodes_data],
            "path_edges": path_edges,
            "status": flow_status,
            "message": f"Flow trace for {entity_id}: {flow_status}"
        }
