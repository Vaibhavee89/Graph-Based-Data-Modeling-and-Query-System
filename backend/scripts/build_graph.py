"""Build NetworkX graph from database and save to pickle file."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.utils.graph_builder import GraphBuilder
from app.config import settings


def main():
    """Build and save graph."""
    print("=" * 60)
    print("Graph Builder Script")
    print("=" * 60)

    # Create database session
    db = SessionLocal()

    try:
        # Create graph builder
        builder = GraphBuilder(db)

        # Build graph
        graph = builder.build()

        # Get statistics
        stats = builder.get_statistics()
        print("\n" + "=" * 60)
        print("Graph Statistics")
        print("=" * 60)
        print(f"Total Nodes: {stats['total_nodes']}")
        print(f"Total Edges: {stats['total_edges']}")
        print(f"Graph Density: {stats['density']:.4f}")
        print(f"Directed: {stats['is_directed']}")

        print("\nNode Types:")
        for node_type, count in stats['node_types'].items():
            print(f"  {node_type}: {count}")

        print("\nEdge Types:")
        for edge_type, count in stats['edge_types'].items():
            print(f"  {edge_type}: {count}")

        # Save to pickle
        pickle_path = settings.graph_pickle_path
        builder.save_to_pickle(pickle_path)

        print("\n" + "=" * 60)
        print("✓ Graph build complete!")
        print("=" * 60)
        print(f"Graph saved to: {pickle_path}")
        print("\nNext steps:")
        print("  1. Start backend: uvicorn app.main:app --reload")
        print("  2. Start frontend: cd frontend && npm run dev")
        print("  3. Open http://localhost:5173")

    except Exception as e:
        print(f"\n✗ Graph build failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
