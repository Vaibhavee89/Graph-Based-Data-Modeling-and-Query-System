"""Add performance indexes

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 12:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Add indexes for better query performance."""
    # Customer indexes
    op.create_index('idx_customer_email', 'customers', ['email'])
    op.create_index('idx_customer_segment', 'customers', ['segment'])

    # Product indexes
    op.create_index('idx_product_category', 'products', ['category'])
    op.create_index('idx_product_name', 'products', ['name'])

    # Order indexes
    op.create_index('idx_order_customer_id', 'orders', ['customer_id'])
    op.create_index('idx_order_date', 'orders', ['order_date'])
    op.create_index('idx_order_status', 'orders', ['status'])
    op.create_index('idx_order_customer_date', 'orders', ['customer_id', 'order_date'])

    # Order Items indexes
    op.create_index('idx_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('idx_order_items_product_id', 'order_items', ['product_id'])

    # Invoice indexes
    op.create_index('idx_invoice_order_id', 'invoices', ['order_id'])
    op.create_index('idx_invoice_date', 'invoices', ['invoice_date'])
    op.create_index('idx_invoice_status', 'invoices', ['status'])

    # Payment indexes
    op.create_index('idx_payment_invoice_id', 'payments', ['invoice_id'])
    op.create_index('idx_payment_date', 'payments', ['payment_date'])
    op.create_index('idx_payment_method', 'payments', ['payment_method'])

    # Delivery indexes
    op.create_index('idx_delivery_order_id', 'deliveries', ['order_id'])
    op.create_index('idx_delivery_date', 'deliveries', ['delivery_date'])
    op.create_index('idx_delivery_status', 'deliveries', ['delivery_status'])
    op.create_index('idx_delivery_address_id', 'deliveries', ['address_id'])

    # Address indexes
    op.create_index('idx_address_customer_id', 'addresses', ['customer_id'])
    op.create_index('idx_address_city', 'addresses', ['city'])
    op.create_index('idx_address_state', 'addresses', ['state'])


def downgrade():
    """Remove performance indexes."""
    # Customer indexes
    op.drop_index('idx_customer_email', table_name='customers')
    op.drop_index('idx_customer_segment', table_name='customers')

    # Product indexes
    op.drop_index('idx_product_category', table_name='products')
    op.drop_index('idx_product_name', table_name='products')

    # Order indexes
    op.drop_index('idx_order_customer_id', table_name='orders')
    op.drop_index('idx_order_date', table_name='orders')
    op.drop_index('idx_order_status', table_name='orders')
    op.drop_index('idx_order_customer_date', table_name='orders')

    # Order Items indexes
    op.drop_index('idx_order_items_order_id', table_name='order_items')
    op.drop_index('idx_order_items_product_id', table_name='order_items')

    # Invoice indexes
    op.drop_index('idx_invoice_order_id', table_name='invoices')
    op.drop_index('idx_invoice_date', table_name='invoices')
    op.drop_index('idx_invoice_status', table_name='invoices')

    # Payment indexes
    op.drop_index('idx_payment_invoice_id', table_name='payments')
    op.drop_index('idx_payment_date', table_name='payments')
    op.drop_index('idx_payment_method', table_name='payments')

    # Delivery indexes
    op.drop_index('idx_delivery_order_id', table_name='deliveries')
    op.drop_index('idx_delivery_date', table_name='deliveries')
    op.drop_index('idx_delivery_status', table_name='deliveries')
    op.drop_index('idx_delivery_address_id', table_name='deliveries')

    # Address indexes
    op.drop_index('idx_address_customer_id', table_name='addresses')
    op.drop_index('idx_address_city', table_name='addresses')
    op.drop_index('idx_address_state', table_name='addresses')
