"""Pytest configuration and fixtures."""
import pytest
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.delivery import Delivery
from app.models.address import Address


# Test database URL (in-memory SQLite)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """Create a test database session."""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_graph():
    """Create a sample graph for testing."""
    G = nx.DiGraph()

    # Add customer nodes
    G.add_node("CUST-001", type="Customer", label="Customer A", color="#3B82F6", properties={"name": "Customer A", "email": "a@example.com"})
    G.add_node("CUST-002", type="Customer", label="Customer B", color="#3B82F6", properties={"name": "Customer B", "email": "b@example.com"})

    # Add product nodes
    G.add_node("PROD-001", type="Product", label="Product X", color="#10B981", properties={"name": "Product X", "price": 100.0})
    G.add_node("PROD-002", type="Product", label="Product Y", color="#10B981", properties={"name": "Product Y", "price": 200.0})

    # Add order nodes
    G.add_node("ORD-001", type="Order", label="Order 1", color="#FF9800", properties={"order_id": "ORD-001", "total": 100.0})
    G.add_node("ORD-002", type="Order", label="Order 2", color="#FF9800", properties={"order_id": "ORD-002", "total": 200.0})

    # Add invoice nodes
    G.add_node("INV-001", type="Invoice", label="Invoice 1", color="#F44336", properties={"invoice_id": "INV-001", "amount": 100.0})

    # Add payment nodes
    G.add_node("PAY-001", type="Payment", label="Payment 1", color="#FFEB3B", properties={"payment_id": "PAY-001", "amount": 100.0})

    # Add delivery nodes
    G.add_node("DEL-001", type="Delivery", label="Delivery 1", color="#9C27B0", properties={"delivery_id": "DEL-001"})

    # Add edges
    G.add_edge("CUST-001", "ORD-001", type="PLACED", label="placed")
    G.add_edge("ORD-001", "PROD-001", type="CONTAINS", label="contains", properties={"quantity": 1})
    G.add_edge("ORD-001", "INV-001", type="GENERATED", label="generated")
    G.add_edge("INV-001", "PAY-001", type="PAID_BY", label="paid by")
    G.add_edge("ORD-001", "DEL-001", type="RESULTED_IN", label="resulted in")

    return G


@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing."""
    return {
        "customer_id": "310000108",
        "name": "Test Customer",
        "email": "test@example.com",
        "segment": "RETAIL"
    }


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "product_id": "PROD-TEST-001",
        "name": "Test Product",
        "category": "Electronics",
        "price": 99.99
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return {
        "order_id": "740506",
        "customer_id": "310000108",
        "order_date": "2025-01-15",
        "status": "completed",
        "total_amount": 299.99
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "is_valid": True,
        "reason": "Query is related to business data",
        "intent": "AGGREGATION",
        "confidence": 0.95
    }
