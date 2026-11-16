"""Payment model."""

from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Payment(Base):
    """Payment entity model."""

    __tablename__ = "payments"

    payment_id = Column(String(50), primary_key=True, index=True)
    invoice_id = Column(
        String(50),
        ForeignKey("invoices.invoice_id", ondelete="CASCADE"),
        nullable=False,
    )
    payment_date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    method = Column(
        String(50), nullable=False
    )  # e.g., credit_card, bank_transfer, check, cash
    transaction_id = Column(String(100), unique=True, index=True)
    status = Column(
        String(50), nullable=False
    )  # e.g., pending, completed, failed, refunded
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")

    def __repr__(self):
        return f"<Payment(payment_id={self.payment_id}, amount={self.amount}, method={self.method})>"
