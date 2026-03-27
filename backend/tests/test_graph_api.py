"""Integration tests for Graph API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import networkx as nx

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_graph(sample_graph):
    """Mock the get_graph function."""
    with patch('app.core.graph_store.get_graph') as mock:
        mock.return_value = sample_graph
        yield mock


@pytest.mark.integration
class TestGraphAPI:
    """Integration tests for graph API endpoints."""

    def test_get_overview(self, client, mock_graph):
        """Test GET /api/graph/overview."""
        response = client.get("/api/graph/overview")

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "node_types" in data
        assert data["nodes"] == 9
        assert data["edges"] == 5

    def test_get_nodes(self, client, mock_graph):
        """Test GET /api/graph/nodes."""
        response = client.get("/api/graph/nodes?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_get_nodes_filtered(self, client, mock_graph):
        """Test GET /api/graph/nodes with type filter."""
        response = client.get("/api/graph/nodes?node_type=Customer")

        assert response.status_code == 200
        data = response.json()
        assert all(node["type"] == "Customer" for node in data)

    def test_get_node_by_id(self, client, mock_graph):
        """Test GET /api/graph/nodes/{id}."""
        response = client.get("/api/graph/nodes/CUST-001")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "CUST-001"
        assert data["type"] == "Customer"
        assert "label" in data
        assert "properties" in data

    def test_get_node_not_found(self, client, mock_graph):
        """Test GET /api/graph/nodes/{id} with nonexistent ID."""
        response = client.get("/api/graph/nodes/NONEXISTENT")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_expand_node(self, client, mock_graph):
        """Test POST /api/graph/nodes/{id}/expand."""
        response = client.post(
            "/api/graph/nodes/CUST-001/expand",
            json={"depth": 1}
        )

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_expand_node_invalid_depth(self, client, mock_graph):
        """Test expand with invalid depth."""
        response = client.post(
            "/api/graph/nodes/CUST-001/expand",
            json={"depth": 5}  # Max is 2
        )

        assert response.status_code == 422  # Validation error

    def test_search_nodes(self, client, mock_graph):
        """Test POST /api/graph/search."""
        response = client.post(
            "/api/graph/search",
            json={"query": "Customer"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_search_nodes_with_filter(self, client, mock_graph):
        """Test search with type filter."""
        response = client.post(
            "/api/graph/search",
            json={"query": "Product", "node_type": "Product"}
        )

        assert response.status_code == 200
        data = response.json()
        assert all(node["type"] == "Product" for node in data)

    def test_get_node_neighbors(self, client, mock_graph):
        """Test GET /api/graph/nodes/{id}/neighbors."""
        response = client.get("/api/graph/nodes/ORD-001/neighbors")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_subgraph(self, client, mock_graph):
        """Test POST /api/graph/subgraph."""
        response = client.post(
            "/api/graph/subgraph",
            json=["CUST-001", "ORD-001"]
        )

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2

    def test_trace_flow(self, client, mock_graph):
        """Test GET /api/graph/trace/{id}."""
        response = client.get("/api/graph/trace/ORD-001")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "path_nodes" in data
        assert "path_edges" in data
        assert "status" in data
        assert data["status"] in ["complete", "partial", "incomplete", "error"]

    def test_export_graph(self, client, mock_graph):
        """Test GET /api/graph/export."""
        response = client.get("/api/graph/export")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers["content-disposition"]

        # Verify JSON structure
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "metadata" in data
        assert "node_count" in data["metadata"]
        assert "edge_count" in data["metadata"]

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
