"""Test script for query service."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import json


BASE_URL = "http://localhost:8000"


def test_query(query: str, description: str = ""):
    """Test a single query."""
    print("\n" + "="*60)
    print(f"Test: {description or query}")
    print("="*60)
    print(f"Query: {query}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/query/chat",
            json={"query": query},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Success: {result.get('success')}")
            print(f"Intent: {result.get('intent')}")
            print(f"\nAnswer:\n{result.get('answer')}")

            if result.get('data'):
                print(f"\nData preview:")
                data_str = json.dumps(result['data'], indent=2)
                # Show first 500 chars
                print(data_str[:500])
                if len(data_str) > 500:
                    print("...")

            if result.get('entities'):
                print(f"\nReferenced entities: {result['entities']}")

        else:
            print(f"\n✗ Error {response.status_code}: {response.text}")

    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Backend not running!")
        print("Start backend with: uvicorn app.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")


def main():
    """Run test suite."""
    print("="*60)
    print("Query Service Test Suite")
    print("="*60)

    # Test 1: Greeting (guardrail)
    test_query("Hello!", "Greeting test")

    # Test 2: Off-topic (guardrail rejection)
    test_query("What is the capital of France?", "Off-topic rejection test")

    # Test 3: Aggregation
    test_query("Which customers have the most orders?", "Aggregation test")

    # Test 4: Entity lookup
    test_query("Show me customer 310000108", "Entity lookup test")

    # Test 5: Traversal
    test_query("Trace the flow of order 740506", "Flow tracing test")

    # Test 6: Anomaly detection
    test_query("Find orders with incomplete flows", "Anomaly detection test")

    print("\n" + "="*60)
    print("Test suite completed!")
    print("="*60)


if __name__ == "__main__":
    main()
