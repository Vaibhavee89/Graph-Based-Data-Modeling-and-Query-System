# Data Schema Documentation

## Overview

This document describes the data schema for the Graph-Based Data Modeling System. The system uses 7 main entities with relationships that form a complete business flow from customer orders to payments.

## Entities

### 1. Customer
Represents a customer who places orders.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| customer_id | String (PK) | Unique customer identifier | CUST-0001 |
| name | String | Customer full name | John Doe |
| email | String (Unique) | Customer email address | john.doe@example.com |
| segment | String | Customer segment | Enterprise, SMB, Individual |
| created_at | DateTime | Record creation timestamp | 2024-01-01 10:00:00 |
| updated_at | DateTime | Record update timestamp | 2024-01-01 10:00:00 |

**Relationships:**
- One customer can have many orders (1:N)
- One customer can have many addresses (1:N)

---

### 2. Product
Represents a product available for purchase.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| product_id | String (PK) | Unique product identifier | PROD-0001 |
| name | String | Product name | Laptop Pro 15 |
| category | String | Product category | Electronics |
| price | Float | Product unit price | 1299.99 |
| description | String | Product description | High-performance laptop |
| created_at | DateTime | Record creation timestamp | 2024-01-01 10:00:00 |
| updated_at | DateTime | Record update timestamp | 2024-01-01 10:00:00 |

**Relationships:**
- One product can appear in many orders (N:M via order_items)

---

### 3. Address
Represents a physical address for billing or shipping.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| address_id | String (PK) | Unique address identifier | ADDR-0001 |
| customer_id | String (FK, Nullable) | Associated customer | CUST-0001 |
| street | String | Street address | 123 Main St |
| city | String | City name | New York |
| state | String | State/province code | NY |
| postal_code | String | Postal/ZIP code | 10001 |
| country | String | Country name | USA |
| address_type | String | Address type | billing, shipping |
| created_at | DateTime | Record creation timestamp | 2024-01-01 10:00:00 |
| updated_at | DateTime | Record update timestamp | 2024-01-01 10:00:00 |

**Relationships:**
- One address belongs to one customer (N:1)
- One address can have many deliveries (1:N)

---

### 4. Order
Represents a sales order placed by a customer.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| order_id | String (PK) | Unique order identifier | ORD-0001 |
| customer_id | String (FK) | Customer who placed order | CUST-0001 |
| order_date | Date | Date order was placed | 2024-01-15 |
| status | String | Order status | pending, completed, cancelled |
| total_amount | Float | Total order amount | 2599.98 |
| created_at | DateTime | Record creation timestamp | 2024-01-15 10:00:00 |
| updated_at | DateTime | Record update timestamp | 2024-01-15 10:00:00 |

**Relationships:**
- One order belongs to one customer (N:1)
- One order can have many products (N:M via order_items)
- One order can have many invoices (1:N)
- One order can have many deliveries (1:N)

---

### 5. OrderItem
Association table linking orders and products with quantities.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| id | Integer (PK, Auto) | Auto-incrementing ID | 1 |
| order_id | String (FK) | Associated order | ORD-0001 |
| product_id | String (FK) | Associated product | PROD-0001 |
| quantity | Integer | Quantity ordered | 2 |
| unit_price | Float | Price per unit at time of order | 1299.99 |
| subtotal | Float | Line item total (quantity * unit_price) | 2599.98 |

**Relationships:**
- One order item belongs to one order (N:1)
- One order item references one product (N:1)

---

### 6. Invoice
Represents a billing document generated for an order.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| invoice_id | String (PK) | Unique invoice identifier | INV-0001 |
| order_id | String (FK) | Associated order | ORD-0001 |
| invoice_date | Date | Date invoice was generated | 2024-01-15 |
| due_date | Date | Payment due date | 2024-02-14 |
| amount | Float | Invoice amount | 2599.98 |
| status | String | Invoice status | draft, sent, paid, overdue, cancelled |
| created_at | DateTime | Record creation timestamp | 2024-01-15 10:00:00 |
| updated_at | DateTime | Record update timestamp | 2024-01-15 10:00:00 |

**Relationships:**
- One invoice belongs to one order (N:1)
- One invoice can have many payments (1:N)

---

### 7. Payment
Represents a payment made for an invoice.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| payment_id | String (PK) | Unique payment identifier | PAY-0001 |
| invoice_id | String (FK) | Associated invoice | INV-0001 |
| payment_date | Date | Date payment was made | 2024-01-20 |
| amount | Float | Payment amount | 2599.98 |
| method | String | Payment method | credit_card, bank_transfer, check, cash |
| transaction_id | String (Unique) | External transaction ID | TXN-123456 |
| status | String | Payment status | pending, completed, failed, refunded |
| created_at | DateTime | Record creation timestamp | 2024-01-20 10:00:00 |
| updated_at | DateTime | Record update timestamp | 2024-01-20 10:00:00 |

**Relationships:**
- One payment belongs to one invoice (N:1)

---

### 8. Delivery
Represents a delivery/shipment for an order.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| delivery_id | String (PK) | Unique delivery identifier | DEL-0001 |
| order_id | String (FK) | Associated order | ORD-0001 |
| address_id | String (FK, Nullable) | Delivery address | ADDR-0002 |
| delivery_date | Date (Nullable) | Actual delivery date | 2024-01-18 |
| status | String | Delivery status | pending, in_transit, delivered, failed |
| tracking_number | String (Unique) | Shipment tracking number | TRK-987654321 |
| carrier | String | Shipping carrier | FedEx, UPS, USPS, DHL |
| created_at | DateTime | Record creation timestamp | 2024-01-15 12:00:00 |
| updated_at | DateTime | Record update timestamp | 2024-01-18 14:00:00 |

**Relationships:**
- One delivery belongs to one order (N:1)
- One delivery references one address (N:1)

---

## Entity Relationship Diagram

```
Customer ──┐
           ├──► Order ──┬──► Invoice ──► Payment
           │            │
           └──► Address └──► Delivery
                             (to Address)

Order ──┬──► OrderItem ──► Product
        │
        ├──► Invoice
        └──► Delivery
```

## Business Flow

### Complete Order Flow
1. **Customer** places an **Order**
2. **Order** contains one or more **Products** (via OrderItem)
3. **Order** generates an **Invoice**
4. **Invoice** is paid via **Payment**
5. **Order** ships via **Delivery** to **Address**

### Flow Status
- **Complete**: Order → Invoice → Payment → Delivery (all present)
- **Incomplete**: Missing one or more steps
- **Broken**: Relationships don't exist or invalid

## Data Files

### Raw Data (`data/raw/`)
Original CSV files before processing:
- `customers.csv`
- `products.csv`
- `addresses.csv`
- `orders.csv`
- `order_items.csv`
- `invoices.csv`
- `payments.csv`
- `deliveries.csv`

### Processed Data (`data/processed/`)
Cleaned and validated CSV files ready for database loading:
- Same filenames as raw data
- Duplicates removed
- Missing values handled
- Foreign keys validated
- Data types standardized

## Data Quality Rules

### Validation Rules
1. **Referential Integrity**: All foreign keys must reference existing records
2. **No Duplicates**: Primary keys must be unique
3. **Required Fields**: No nulls in non-nullable columns
4. **Data Types**: All numeric fields are valid numbers
5. **Date Formats**: All dates in YYYY-MM-DD format
6. **Status Values**: Only predefined status values allowed

### Cleaning Operations
- Remove duplicate records (by primary key)
- Drop records with missing required fields
- Validate and filter invalid foreign key references
- Standardize text fields (lowercase, trim whitespace)
- Convert and validate numeric fields
- Parse and validate date fields

## Sample Data Generation

If you don't have real data, you can generate sample data:

```bash
python backend/scripts/download_dataset.py
# Select option 1 to create sample data
```

This generates:
- 100 customers
- 50 products
- 200 addresses
- 300 orders (~1000 order items)
- 240 invoices (80% of orders)
- 168 payments (70% of invoices)
- 225 deliveries (75% of orders)

Note: Sample data intentionally has some incomplete flows for testing anomaly detection.

## ETL Pipeline

Run the ETL pipeline to process and load data:

```bash
python backend/scripts/etl.py
```

Pipeline stages:
1. **Extract**: Read CSV files from `data/raw/`
2. **Transform**: Clean, validate, and enrich data
3. **Load**: Insert into PostgreSQL database

## Database Schema

PostgreSQL tables are created by SQLAlchemy ORM models in `backend/app/models/`.

View schema:
```sql
\dt  -- List all tables
\d customers  -- Describe customers table
```

## Graph Representation

In the graph model:
- **Nodes**: Each entity instance (customer, product, order, etc.)
- **Edges**: Relationships between entities
- **Node ID**: Entity's primary key (e.g., CUST-0001)
- **Node Type**: Entity type (Customer, Product, Order, etc.)
- **Node Color**: Color-coded by type
- **Edge Type**: Relationship name (PLACED, CONTAINS, GENERATED, etc.)

See main README.md for graph model details.
