"""Graph store - Singleton for managing the in-memory NetworkX graph."""
import networkx as nx
from pathlib import Path
from typing import Optional
import os

from app.config import settings
from app.utils.graph_builder import GraphBuilder


class GraphStore:
    """Singleton class for managing the global graph instance."""

    _instance: Optional['GraphStore'] = None
    _graph: Optional[nx.DiGraph] = None

    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(GraphStore, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the graph store."""
        # Only initialize once
        if self._graph is None:
            self._load_graph()

    def _load_graph(self):
        """Load graph from pickle file or create empty graph."""
        pickle_path = settings.graph_pickle_path

        if os.path.exists(pickle_path):
            try:
                print(f"Loading graph from {pickle_path}...")
                self._graph = GraphBuilder.load_from_pickle(pickle_path)
                print(f"✓ Graph loaded: {self._graph.number_of_nodes()} nodes, {self._graph.number_of_edges()} edges")
            except Exception as e:
                print(f"✗ Failed to load graph: {e}")
                print("Creating empty graph...")
                self._graph = nx.DiGraph()
        else:
            print(f"Graph pickle not found at {pickle_path}")
            print("Creating empty graph. Run 'python scripts/build_graph.py' to build the graph.")
            self._graph = nx.DiGraph()

    def get_graph(self) -> nx.DiGraph:
        """
        Get the graph instance.

        Returns:
            NetworkX directed graph
        """
        return self._graph

    def reload_graph(self):
        """Reload graph from pickle file."""
        self._load_graph()

    def set_graph(self, graph: nx.DiGraph):
        """
        Set a new graph instance.

        Args:
            graph: NetworkX directed graph
        """
        self._graph = graph
        print(f"✓ Graph updated: {self._graph.number_of_nodes()} nodes, {self._graph.number_of_edges()} edges")

    def is_loaded(self) -> bool:
        """
        Check if graph is loaded and has data.

        Returns:
            True if graph has nodes, False otherwise
        """
        return self._graph is not None and self._graph.number_of_nodes() > 0

    def get_statistics(self) -> dict:
        """
        Get graph statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.is_loaded():
            return {
                'total_nodes': 0,
                'total_edges': 0,
                'node_types': {},
                'edge_types': {},
                'density': 0.0,
                'is_directed': True,
            }

        node_types = {}
        for node_id, data in self._graph.nodes(data=True):
            node_type = data.get('type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1

        edge_types = {}
        for _, _, data in self._graph.edges(data=True):
            edge_type = data.get('type', 'Unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

        return {
            'total_nodes': self._graph.number_of_nodes(),
            'total_edges': self._graph.number_of_edges(),
            'node_types': node_types,
            'edge_types': edge_types,
            'density': nx.density(self._graph),
            'is_directed': self._graph.is_directed(),
        }


# Global graph store instance
graph_store = GraphStore()


def get_graph() -> nx.DiGraph:
    """
    Dependency function to get graph instance.

    Returns:
        NetworkX directed graph

    Usage:
        from app.core.graph_store import get_graph
        graph = get_graph()
    """
    return graph_store.get_graph()
