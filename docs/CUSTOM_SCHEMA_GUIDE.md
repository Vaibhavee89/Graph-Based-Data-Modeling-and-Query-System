# Custom Schema Guide

This guide shows how to adapt the system for your specific data model.

## Scenario 1: E-commerce Platform

If you have an e-commerce platform with different entities:

### Add Custom Models

Create `backend/app/models/ecommerce.py`:

```python
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Store(Base):
    """Store/Shop entity."""
    __tablename__ = "stores"

    store_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    category = Column(String(100))
    rating = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    products = relationship("Product", back_populates="store")


class Review(Base):
    """Product review entity."""
    __tablename__ = "reviews"

    review_id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey("products.product_id"))
    customer_id = Column(String(50), ForeignKey("customers.customer_id"))
    rating = Column(Integer)
    comment = Column(String(1000))
    review_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product")
    customer = relationship("Customer")


class Cart(Base):
    """Shopping cart entity."""
    __tablename__ = "carts"

    cart_id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"))
    status = Column(String(50))  # active, abandoned, converted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer")
    items = relationship("CartItem", back_populates="cart")


class CartItem(Base):
    """Items in shopping cart."""
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(String(50), ForeignKey("carts.cart_id"))
    product_id = Column(String(50), ForeignKey("products.product_id"))
    quantity = Column(Integer)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
```

### Update Graph Builder

Modify `backend/app/utils/graph_builder.py` to include your entities:

```python
def build(self) -> nx.DiGraph:
    """Build graph with custom entities."""

    # ... existing code ...

    # Add Store nodes
    stores = self.db.query(Store).all()
    for store in stores:
        self.add_node(
            node_id=store.store_id,
            node_type="Store",
            label=store.name,
            color="#8B5CF6",  # Purple
            properties={
                "store_id": store.store_id,
                "name": store.name,
                "location": store.location,
                "rating": store.rating,
            }
        )

    # Add Review nodes
    reviews = self.db.query(Review).all()
    for review in reviews:
        self.add_node(
            node_id=review.review_id,
            node_type="Review",
            label=f"Review {review.rating}★",
            color="#EC4899",  # Pink
            properties={
                "review_id": review.review_id,
                "rating": review.rating,
                "comment": review.comment[:100],
            }
        )

    # Add Store-Product edges
    for store in stores:
        for product in store.products:
            self.add_edge(
                source=store.store_id,
                target=product.product_id,
                edge_type="SELLS",
                label="sells"
            )

    # Add Customer-Review-Product edges
    for review in reviews:
        self.add_edge(
            source=review.customer_id,
            target=review.review_id,
            edge_type="WROTE",
            label="wrote"
        )
        self.add_edge(
            source=review.review_id,
            target=review.product_id,
            edge_type="REVIEWS",
            label="reviews"
        )

    return self.graph
```

## Scenario 2: Healthcare System

### Custom Models for Healthcare

```python
class Patient(Base):
    """Patient entity."""
    __tablename__ = "patients"

    patient_id = Column(String(50), primary_key=True)
    name = Column(String(255))
    date_of_birth = Column(Date)
    blood_type = Column(String(10))
    medical_record_number = Column(String(50))


class Doctor(Base):
    """Doctor entity."""
    __tablename__ = "doctors"

    doctor_id = Column(String(50), primary_key=True)
    name = Column(String(255))
    specialization = Column(String(100))
    license_number = Column(String(50))


class Appointment(Base):
    """Medical appointment."""
    __tablename__ = "appointments"

    appointment_id = Column(String(50), primary_key=True)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"))
    doctor_id = Column(String(50), ForeignKey("doctors.doctor_id"))
    appointment_date = Column(DateTime)
    status = Column(String(50))
    diagnosis = Column(String(500))


class Prescription(Base):
    """Medical prescription."""
    __tablename__ = "prescriptions"

    prescription_id = Column(String(50), primary_key=True)
    appointment_id = Column(String(50), ForeignKey("appointments.appointment_id"))
    medication = Column(String(255))
    dosage = Column(String(100))
    duration_days = Column(Integer)
```

## Scenario 3: Supply Chain

### Custom Models for Supply Chain

```python
class Supplier(Base):
    """Supplier entity."""
    __tablename__ = "suppliers"

    supplier_id = Column(String(50), primary_key=True)
    name = Column(String(255))
    country = Column(String(100))
    rating = Column(Float)


class Warehouse(Base):
    """Warehouse entity."""
    __tablename__ = "warehouses"

    warehouse_id = Column(String(50), primary_key=True)
    name = Column(String(255))
    location = Column(String(255))
    capacity = Column(Integer)
    current_stock = Column(Integer)


class Shipment(Base):
    """Shipment tracking."""
    __tablename__ = "shipments"

    shipment_id = Column(String(50), primary_key=True)
    supplier_id = Column(String(50), ForeignKey("suppliers.supplier_id"))
    warehouse_id = Column(String(50), ForeignKey("warehouses.warehouse_id"))
    product_id = Column(String(50), ForeignKey("products.product_id"))
    quantity = Column(Integer)
    shipped_date = Column(DateTime)
    received_date = Column(DateTime)
    status = Column(String(50))
```

## General Steps to Customize

1. **Define your entities** in `backend/app/models/`
2. **Update graph builder** in `backend/app/utils/graph_builder.py`
3. **Create data loader** in `backend/scripts/`
4. **Add colors** for new node types in frontend
5. **Update LLM prompts** to understand new entities
6. **Rebuild graph** after loading data

## Testing Your Custom Schema

```bash
# 1. Initialize database with new schema
docker-compose exec backend python scripts/init_db.py

# 2. Load your custom data
docker-compose exec backend python scripts/load_custom_data.py

# 3. Build graph
docker-compose exec backend python scripts/build_graph.py

# 4. Restart backend
docker-compose restart backend

# 5. Test in frontend
open http://localhost:3000
```

## Color Scheme for Node Types

Choose distinct colors for your entities:

```python
NODE_COLORS = {
    "Customer": "#3B82F6",    # Blue
    "Product": "#10B981",      # Green
    "Order": "#F59E0B",        # Orange
    "Invoice": "#EF4444",      # Red
    "Payment": "#FBBF24",      # Yellow
    "Delivery": "#8B5CF6",     # Purple
    "Address": "#6B7280",      # Gray

    # Add your custom types
    "Store": "#8B5CF6",        # Purple
    "Review": "#EC4899",       # Pink
    "Supplier": "#06B6D4",     # Cyan
    "Warehouse": "#84CC16",    # Lime
    "Shipment": "#F97316",     # Orange-red
}
```

## Example: Complete Custom Implementation

See `backend/scripts/load_from_existing_db.py` for a complete example of loading custom data.
