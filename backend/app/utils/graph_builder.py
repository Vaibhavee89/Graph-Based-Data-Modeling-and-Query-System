"""Graph builder utility - Builds NetworkX graph from database."""
import networkx as nx
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple
import pickle
from datetime import datetime

from app.models import (
    Customer, Product, Order, OrderItem,
    Invoice, Payment, Delivery, Address
)


class GraphBuilder:
    """Builds and manages the NetworkX graph from database entities."""

    # Node colors by entity type
    NODE_COLORS = {
        'Customer': '#3B82F6',    # Blue
        'Product': '#10B981',     # Green
        'Order': '#F59E0B',       # Orange
        'Delivery': '#8B5CF6',    # Purple
        'Invoice': '#EF4444',     # Red
        'Payment': '#FBBF24',     # Yellow
        'Address': '#6B7280',     # Gray
    }

    def __init__(self, db: Session):
        """
        Initialize GraphBuilder.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.graph = nx.DiGraph()  # Directed graph

    def add_customer_nodes(self) -> int:
        """Add customer nodes to graph."""
        customers = self.db.query(Customer).all()
        count = 0

        for customer in customers:
            self.graph.add_node(
                customer.customer_id,
                type='Customer',
                label=customer.name,
                color=self.NODE_COLORS['Customer'],
                properties={
                    'customer_id': customer.customer_id,
                    'name': customer.name,
                    'email': customer.email,
                    'segment': customer.segment,
                    'created_at': customer.created_at.isoformat() if customer.created_at else None,
                }
            )
            count += 1

        return count

    def add_product_nodes(self) -> int:
        """Add product nodes to graph."""
        products = self.db.query(Product).all()
        count = 0

        for product in products:
            self.graph.add_node(
                product.product_id,
                type='Product',
                label=product.name,
                color=self.NODE_COLORS['Product'],
                properties={
                    'product_id': product.product_id,
                    'name': product.name,
                    'category': product.category,
                    'price': float(product.price),
                    'description': product.description,
                }
            )
            count += 1

        return count

    def add_address_nodes(self) -> int:
        """Add address nodes to graph."""
        addresses = self.db.query(Address).all()
        count = 0

        for address in addresses:
            label = f"{address.city}, {address.state}"
            self.graph.add_node(
                address.address_id,
                type='Address',
                label=label,
                color=self.NODE_COLORS['Address'],
                properties={
                    'address_id': address.address_id,
                    'street': address.street,
                    'city': address.city,
                    'state': address.state,
                    'postal_code': address.postal_code,
                    'country': address.country,
                    'address_type': address.address_type,
                }
            )
            count += 1

        return count

    def add_order_nodes(self) -> int:
        """Add order nodes to graph."""
        orders = self.db.query(Order).all()
        count = 0

        for order in orders:
            self.graph.add_node(
                order.order_id,
                type='Order',
                label=f"Order {order.order_id}",
                color=self.NODE_COLORS['Order'],
                properties={
                    'order_id': order.order_id,
                    'customer_id': order.customer_id,
                    'order_date': order.order_date.isoformat() if order.order_date else None,
                    'status': order.status,
                    'total_amount': float(order.total_amount),
                }
            )
            count += 1

        return count

    def add_invoice_nodes(self) -> int:
        """Add invoice nodes to graph."""
        invoices = self.db.query(Invoice).all()
        count = 0

        for invoice in invoices:
            self.graph.add_node(
                invoice.invoice_id,
                type='Invoice',
                label=f"Invoice {invoice.invoice_id}",
                color=self.NODE_COLORS['Invoice'],
                properties={
                    'invoice_id': invoice.invoice_id,
                    'order_id': invoice.order_id,
                    'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                    'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                    'amount': float(invoice.amount),
                    'status': invoice.status,
                }
            )
            count += 1

        return count

    def add_payment_nodes(self) -> int:
        """Add payment nodes to graph."""
        payments = self.db.query(Payment).all()
        count = 0

        for payment in payments:
            self.graph.add_node(
                payment.payment_id,
                type='Payment',
                label=f"Payment {payment.payment_id}",
                color=self.NODE_COLORS['Payment'],
                properties={
                    'payment_id': payment.payment_id,
                    'invoice_id': payment.invoice_id,
                    'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                    'amount': float(payment.amount),
                    'method': payment.method,
                    'transaction_id': payment.transaction_id,
                    'status': payment.status,
                }
            )
            count += 1

        return count

    def add_delivery_nodes(self) -> int:
        """Add delivery nodes to graph."""
        deliveries = self.db.query(Delivery).all()
        count = 0

        for delivery in deliveries:
            self.graph.add_node(
                delivery.delivery_id,
                type='Delivery',
                label=f"Delivery {delivery.delivery_id}",
                color=self.NODE_COLORS['Delivery'],
                properties={
                    'delivery_id': delivery.delivery_id,
                    'order_id': delivery.order_id,
                    'address_id': delivery.address_id,
                    'delivery_date': delivery.delivery_date.isoformat() if delivery.delivery_date else None,
                    'status': delivery.status,
                    'tracking_number': delivery.tracking_number,
                    'carrier': delivery.carrier,
                }
            )
            count += 1

        return count

    def add_edges(self) -> Tuple[int, Dict[str, int]]:
        """Add all edges (relationships) to graph."""
        edge_counts = {}

        # Customer → Order (PLACED)
        orders = self.db.query(Order).all()
        count = 0
        for order in orders:
            if self.graph.has_node(order.customer_id) and self.graph.has_node(order.order_id):
                self.graph.add_edge(
                    order.customer_id,
                    order.order_id,
                    type='PLACED',
                    label='placed',
                    properties={'date': order.order_date.isoformat() if order.order_date else None}
                )
                count += 1
        edge_counts['PLACED'] = count

        # Order → Product (CONTAINS) via OrderItem
        order_items = self.db.query(OrderItem).all()
        count = 0
        for item in order_items:
            if self.graph.has_node(item.order_id) and self.graph.has_node(item.product_id):
                self.graph.add_edge(
                    item.order_id,
                    item.product_id,
                    type='CONTAINS',
                    label=f'contains ({item.quantity})',
                    properties={
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'subtotal': float(item.subtotal),
                    }
                )
                count += 1
        edge_counts['CONTAINS'] = count

        # Order → Invoice (GENERATED)
        invoices = self.db.query(Invoice).all()
        count = 0
        for invoice in invoices:
            if self.graph.has_node(invoice.order_id) and self.graph.has_node(invoice.invoice_id):
                self.graph.add_edge(
                    invoice.order_id,
                    invoice.invoice_id,
                    type='GENERATED',
                    label='generated',
                    properties={'date': invoice.invoice_date.isoformat() if invoice.invoice_date else None}
                )
                count += 1
        edge_counts['GENERATED'] = count

        # Invoice → Payment (PAID_BY)
        payments = self.db.query(Payment).all()
        count = 0
        for payment in payments:
            if self.graph.has_node(payment.invoice_id) and self.graph.has_node(payment.payment_id):
                self.graph.add_edge(
                    payment.invoice_id,
                    payment.payment_id,
                    type='PAID_BY',
                    label='paid by',
                    properties={
                        'date': payment.payment_date.isoformat() if payment.payment_date else None,
                        'method': payment.method,
                    }
                )
                count += 1
        edge_counts['PAID_BY'] = count

        # Order → Delivery (RESULTED_IN)
        deliveries = self.db.query(Delivery).all()
        count = 0
        for delivery in deliveries:
            if self.graph.has_node(delivery.order_id) and self.graph.has_node(delivery.delivery_id):
                self.graph.add_edge(
                    delivery.order_id,
                    delivery.delivery_id,
                    type='RESULTED_IN',
                    label='resulted in',
                    properties={'status': delivery.status}
                )
                count += 1
        edge_counts['RESULTED_IN'] = count

        # Delivery → Address (TO_ADDRESS)
        count = 0
        for delivery in deliveries:
            if delivery.address_id and self.graph.has_node(delivery.delivery_id) and self.graph.has_node(delivery.address_id):
                self.graph.add_edge(
                    delivery.delivery_id,
                    delivery.address_id,
                    type='TO_ADDRESS',
                    label='to address',
                    properties={}
                )
                count += 1
        edge_counts['TO_ADDRESS'] = count

        # Customer → Address (HAS_ADDRESS)
        addresses = self.db.query(Address).filter(Address.customer_id.isnot(None)).all()
        count = 0
        for address in addresses:
            if self.graph.has_node(address.customer_id) and self.graph.has_node(address.address_id):
                self.graph.add_edge(
                    address.customer_id,
                    address.address_id,
                    type='HAS_ADDRESS',
                    label='has address',
                    properties={'type': address.address_type}
                )
                count += 1
        edge_counts['HAS_ADDRESS'] = count

        total_edges = sum(edge_counts.values())
        return total_edges, edge_counts

    def build(self) -> nx.DiGraph:
        """
        Build the complete graph from database.

        Returns:
            NetworkX directed graph
        """
        print("Building graph from database...")
        print("=" * 60)

        # Add all nodes
        print("\nAdding nodes...")
        customer_count = self.add_customer_nodes()
        print(f"  ✓ Added {customer_count} Customer nodes")

        product_count = self.add_product_nodes()
        print(f"  ✓ Added {product_count} Product nodes")

        address_count = self.add_address_nodes()
        print(f"  ✓ Added {address_count} Address nodes")

        order_count = self.add_order_nodes()
        print(f"  ✓ Added {order_count} Order nodes")

        invoice_count = self.add_invoice_nodes()
        print(f"  ✓ Added {invoice_count} Invoice nodes")

        payment_count = self.add_payment_nodes()
        print(f"  ✓ Added {payment_count} Payment nodes")

        delivery_count = self.add_delivery_nodes()
        print(f"  ✓ Added {delivery_count} Delivery nodes")

        total_nodes = self.graph.number_of_nodes()
        print(f"\nTotal nodes: {total_nodes}")

        # Add all edges
        print("\nAdding edges...")
        total_edges, edge_counts = self.add_edges()

        for edge_type, count in edge_counts.items():
            print(f"  ✓ Added {count} {edge_type} edges")

        print(f"\nTotal edges: {total_edges}")

        print("\n" + "=" * 60)
        print("Graph construction complete!")
        print("=" * 60)
        print(f"Nodes: {total_nodes}")
        print(f"Edges: {total_edges}")
        print(f"Density: {nx.density(self.graph):.4f}")

        return self.graph

    def save_to_pickle(self, filepath: str):
        """
        Save graph to pickle file.

        Args:
            filepath: Path to save pickle file
        """
        print(f"\nSaving graph to {filepath}...")
        with open(filepath, 'wb') as f:
            pickle.dump(self.graph, f)
        print(f"✓ Graph saved successfully")

    @staticmethod
    def load_from_pickle(filepath: str) -> nx.DiGraph:
        """
        Load graph from pickle file.

        Args:
            filepath: Path to pickle file

        Returns:
            NetworkX directed graph
        """
        print(f"Loading graph from {filepath}...")
        with open(filepath, 'rb') as f:
            graph = pickle.load(f)
        print(f"✓ Loaded graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
        return graph

    def get_statistics(self) -> Dict:
        """
        Get graph statistics.

        Returns:
            Dictionary with statistics
        """
        node_types = {}
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get('type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1

        edge_types = {}
        for _, _, data in self.graph.edges(data=True):
            edge_type = data.get('type', 'Unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': node_types,
            'edge_types': edge_types,
            'density': nx.density(self.graph),
            'is_directed': self.graph.is_directed(),
        }
