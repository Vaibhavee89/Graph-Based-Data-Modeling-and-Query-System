"""Delivery model."""
from sqlalchemy import Column, String, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Delivery(Base):
    """Delivery entity model."""

    __tablename__ = "deliveries"

    delivery_id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    address_id = Column(String(50), ForeignKey("addresses.address_id", ondelete="SET NULL"), nullable=True)
    delivery_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=False)  # e.g., pending, in_transit, delivered, failed
    tracking_number = Column(String(100), unique=True, index=True)
    carrier = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="deliveries")
    address = relationship("Address", back_populates="deliveries")

    def __repr__(self):
        return f"<Delivery(delivery_id={self.delivery_id}, status={self.status})>"
