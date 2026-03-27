"""Invoice model."""
from sqlalchemy import Column, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Invoice(Base):
    """Invoice entity model."""

    __tablename__ = "invoices"

    invoice_id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)  # e.g., draft, sent, paid, overdue, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice(invoice_id={self.invoice_id}, amount={self.amount}, status={self.status})>"
