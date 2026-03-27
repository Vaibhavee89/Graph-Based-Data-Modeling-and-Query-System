"""Unit tests for GraphService."""
import pytest
from app.services.graph_service import GraphService


@pytest.mark.unit
class TestGraphService:
    """Test cases for GraphService."""

    def test_get_overview(self, sample_graph):
        """Test graph overview statistics."""
        service = GraphService(sample_graph)
        overview = service.get_overview()

        assert overview.nodes == 9
        assert overview.edges == 5
        assert overview.node_types["Customer"] == 2
        assert overview.node_types["Product"] == 2
        assert overview.node_types["Order"] == 2
        assert overview.is_directed is True

    def test_get_overview_empty_graph(self):
        """Test overview with empty graph."""
        import networkx as nx
        empty_graph = nx.DiGraph()
        service = GraphService(empty_graph)
        overview = service.get_overview()

        assert overview.nodes == 0
        assert overview.edges == 0
        assert overview.node_types == {}

    def test_get_nodes(self, sample_graph):
        """Test getting nodes with pagination."""
        service = GraphService(sample_graph)

        # Get first 5 nodes
        nodes = service.get_nodes(limit=5, offset=0)
        assert len(nodes) == 5

        # Get next 4 nodes
        nodes = service.get_nodes(limit=5, offset=5)
        assert len(nodes) == 4

    def test_get_nodes_filtered_by_type(self, sample_graph):
        """Test filtering nodes by type."""
        service = GraphService(sample_graph)

        # Get only Customer nodes
        nodes = service.get_nodes(node_type="Customer")
        assert len(nodes) == 2
        assert all(node.type == "Customer" for node in nodes)

        # Get only Product nodes
        nodes = service.get_nodes(node_type="Product")
        assert len(nodes) == 2
        assert all(node.type == "Product" for node in nodes)

    def test_get_node(self, sample_graph):
        """Test getting a specific node."""
        service = GraphService(sample_graph)

        # Get existing node
        node = service.get_node("CUST-001")
        assert node is not None
        assert node.id == "CUST-001"
        assert node.type == "Customer"
        assert node.label == "Customer A"

        # Get non-existing node
        node = service.get_node("NONEXISTENT")
        assert node is None

    def test_expand_node(self, sample_graph):
        """Test expanding a node's connections."""
        service = GraphService(sample_graph)

        # Expand customer node (depth=1)
        graph_data = service.expand_node("CUST-001", depth=1)
        node_ids = {node.id for node in graph_data.nodes}

        # Should include customer and connected order
        assert "CUST-001" in node_ids
        assert "ORD-001" in node_ids

        # Should have edge between them
        assert len(graph_data.edges) >= 1

    def test_expand_node_depth_2(self, sample_graph):
        """Test expanding a node with depth 2."""
        service = GraphService(sample_graph)

        # Expand customer node (depth=2)
        graph_data = service.expand_node("CUST-001", depth=2)
        node_ids = {node.id for node in graph_data.nodes}

        # Should include customer, order, and order's connections
        assert "CUST-001" in node_ids
        assert "ORD-001" in node_ids
        assert "PROD-001" in node_ids or "INV-001" in node_ids

    def test_expand_nonexistent_node(self, sample_graph):
        """Test expanding a node that doesn't exist."""
        service = GraphService(sample_graph)

        graph_data = service.expand_node("NONEXISTENT", depth=1)
        assert len(graph_data.nodes) == 0
        assert len(graph_data.edges) == 0

    def test_search_nodes(self, sample_graph):
        """Test searching nodes."""
        service = GraphService(sample_graph)

        # Search by ID
        nodes = service.search_nodes("CUST-001")
        assert len(nodes) == 1
        assert nodes[0].id == "CUST-001"

        # Search by label
        nodes = service.search_nodes("Customer A")
        assert len(nodes) == 1
        assert nodes[0].label == "Customer A"

        # Search by partial match
        nodes = service.search_nodes("Customer")
        assert len(nodes) == 2

    def test_search_nodes_filtered(self, sample_graph):
        """Test searching nodes with type filter."""
        service = GraphService(sample_graph)

        # Search only in Product nodes
        nodes = service.search_nodes("Product", node_type="Product")
        assert len(nodes) == 2
        assert all(node.type == "Product" for node in nodes)

    def test_search_nodes_limit(self, sample_graph):
        """Test search with limit."""
        service = GraphService(sample_graph)

        # Search with limit
        nodes = service.search_nodes("", limit=3)
        assert len(nodes) <= 3

    def test_get_subgraph(self, sample_graph):
        """Test extracting a subgraph."""
        service = GraphService(sample_graph)

        # Get subgraph with specific nodes
        node_ids = ["CUST-001", "ORD-001", "PROD-001"]
        graph_data = service.get_subgraph(node_ids)

        assert len(graph_data.nodes) == 3
        returned_ids = {node.id for node in graph_data.nodes}
        assert returned_ids == set(node_ids)

        # Should have edges between these nodes
        assert len(graph_data.edges) >= 1

    def test_get_subgraph_nonexistent_nodes(self, sample_graph):
        """Test subgraph with nonexistent nodes."""
        service = GraphService(sample_graph)

        # Mix of existing and nonexistent nodes
        node_ids = ["CUST-001", "NONEXISTENT", "ORD-001"]
        graph_data = service.get_subgraph(node_ids)

        # Should only return existing nodes
        assert len(graph_data.nodes) == 2

    def test_get_node_neighbors(self, sample_graph):
        """Test getting node neighbors grouped by type."""
        service = GraphService(sample_graph)

        # Get neighbors of order node
        neighbors = service.get_node_neighbors("ORD-001")

        # Should have both outgoing and incoming edges
        assert len(neighbors) > 0

        # Check edge types exist
        edge_types = set(neighbors.keys())
        assert any("CONTAINS" in et or "GENERATED" in et for et in edge_types)

    def test_trace_flow_visual_order(self, sample_graph):
        """Test visual flow tracing for an order."""
        service = GraphService(sample_graph)

        result = service.trace_flow_visual("ORD-001")

        assert result["success"] is True
        assert result["status"] == "complete"  # Has invoice, payment, and delivery
        assert len(result["path_nodes"]) >= 3
        assert len(result["path_edges"]) >= 2

        # Check node IDs in path
        node_ids = [node["id"] for node in result["path_nodes"]]
        assert "ORD-001" in node_ids
        assert "INV-001" in node_ids
        assert "PAY-001" in node_ids

    def test_trace_flow_visual_invoice(self, sample_graph):
        """Test visual flow tracing for an invoice."""
        service = GraphService(sample_graph)

        result = service.trace_flow_visual("INV-001")

        assert result["success"] is True
        assert len(result["path_nodes"]) >= 2
        node_ids = [node["id"] for node in result["path_nodes"]]
        assert "INV-001" in node_ids
        assert "PAY-001" in node_ids

    def test_trace_flow_visual_nonexistent(self, sample_graph):
        """Test flow tracing for nonexistent entity."""
        service = GraphService(sample_graph)

        result = service.trace_flow_visual("NONEXISTENT")

        assert result["success"] is False
        assert result["status"] == "error"
        assert len(result["path_nodes"]) == 0

    def test_trace_flow_visual_incomplete(self, sample_graph):
        """Test flow tracing for incomplete flow."""
        # Create order without invoice
        sample_graph.add_node("ORD-003", type="Order", label="Order 3", color="#FF9800", properties={})

        service = GraphService(sample_graph)
        result = service.trace_flow_visual("ORD-003")

        assert result["success"] is True
        assert result["status"] == "incomplete"
        assert len(result["path_nodes"]) == 1  # Only the order itself
