"""Address model."""
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Address(Base):
    """Address entity model."""

    __tablename__ = "addresses"

    address_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=True)
    street = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), nullable=False)
    address_type = Column(String(50))  # e.g., billing, shipping
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", foreign_keys=[customer_id], back_populates="addresses")
    deliveries = relationship("Delivery", back_populates="address", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Address(address_id={self.address_id}, city={self.city})>"
