# SAP O2C Dataset Setup Guide

This guide explains how to use the actual SAP Order-to-Cash (O2C) dataset with the Graph-Based Data Modeling System.

## Dataset Location

Dataset path: `/Users/vaibhavee/Downloads/sap-o2c-data`

## Dataset Structure

The SAP O2C dataset contains JSONL files organized in directories:

### Core Entities
- `business_partners/` - Customer/partner master data
- `business_partner_addresses/` - Address information
- `products/` - Product master data
- `product_descriptions/` - Product text descriptions
- `sales_order_headers/` - Sales orders (our Orders)
- `sales_order_items/` - Order line items
- `billing_document_headers/` - Invoices
- `billing_document_items/` - Invoice line items
- `outbound_delivery_headers/` - Deliveries/shipments
- `outbound_delivery_items/` - Delivery line items
- `payments_accounts_receivable/` - Payment transactions
- `journal_entry_items_accounts_receivable/` - Accounting entries

### Supporting Data
- `plants/` - Manufacturing/distribution plants
- `product_plants/` - Product-plant assignments
- `product_storage_locations/` - Warehouse locations
- `customer_company_assignments/` - Customer company codes
- `customer_sales_area_assignments/` - Sales area assignments

## Data Mappings

### SAP → Our Model

| SAP Entity | Field | Our Model | Field |
|------------|-------|-----------|-------|
| business_partners | businessPartner | Customer | customer_id |
| business_partners | businessPartnerFullName | Customer | name |
| business_partners | businessPartnerGrouping | Customer | segment |
| products | product | Product | product_id |
| product_descriptions | productDescription | Product | name |
| products | productGroup | Product | category |
| sales_order_headers | salesOrder | Order | order_id |
| sales_order_headers | soldToParty | Order | customer_id |
| sales_order_headers | totalNetAmount | Order | total_amount |
| billing_document_headers | billingDocument | Invoice | invoice_id |
| billing_document_headers | totalNetAmount | Invoice | amount |
| outbound_delivery_headers | deliveryDocument | Delivery | delivery_id |
| payments_accounts_receivable | (derived) | Payment | payment_id |

## Setup Steps

### 1. Ensure PostgreSQL is Running

```bash
cd "Graph Based Data Modelling and Query System"
docker-compose up -d postgres
```

### 2. Activate Python Environment

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Ensure dependencies are installed
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
python scripts/init_db.py
```

### 4. Run SAP O2C ETL Pipeline

```bash
python scripts/etl_sap_o2c.py "/Users/vaibhavee/Downloads/sap-o2c-data"
```

**Expected Output:**
```
[HH:MM:SS] SAP O2C ETL Pipeline Starting
[HH:MM:SS] Extract & Transform Phase
[HH:MM:SS] Extracting business partners...
[HH:MM:SS]   ✓ Extracted X customers
[HH:MM:SS] Extracting products...
[HH:MM:SS]   ✓ Extracted X products
...
[HH:MM:SS] Loading data into PostgreSQL...
[HH:MM:SS]   ✓ Loaded X customers
...
[HH:MM:SS] ETL Pipeline Complete!
```

### 5. Build the Graph

```bash
python scripts/build_graph.py
```

**Expected Output:**
```
Building graph from database...
Adding nodes...
  ✓ Added X Customer nodes
  ✓ Added X Product nodes
  ✓ Added X Order nodes
  ...
Adding edges...
  ✓ Added X PLACED edges
  ✓ Added X CONTAINS edges
  ...
Graph saved to: backend/graph.pickle
```

### 6. Start the Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Start the Frontend (New Terminal)

```bash
cd ../frontend
npm install  # First time only
npm run dev
```

### 8. Access the Application

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Verify the Data

### Check Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d graphdb

# Check record counts
SELECT 'customers' as table, COUNT(*) as count FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'deliveries', COUNT(*) FROM deliveries;
```

### Test Graph API

```bash
# Get graph overview
curl http://localhost:8000/api/graph/overview | python3 -m json.tool

# Get first 5 customers
curl "http://localhost:8000/api/graph/nodes?limit=5&node_type=Customer" | python3 -m json.tool

# Get specific node (replace with actual ID from your data)
curl http://localhost:8000/api/graph/nodes/310000108 | python3 -m json.tool

# Expand a node
curl -X POST http://localhost:8000/api/graph/nodes/310000108/expand \
  -H "Content-Type: application/json" \
  -d '{"depth": 1}' | python3 -m json.tool
```

## Data Characteristics

### Expected Volumes (Based on SAP O2C Dataset)

- **Customers:** ~100-200 business partners
- **Products:** ~69 products
- **Orders:** ~100+ sales orders
- **Order Items:** ~167 line items
- **Invoices:** ~163 billing documents
- **Payments:** Variable (based on cleared payments)
- **Deliveries:** ~86 outbound deliveries
- **Addresses:** ~50+ addresses

### Relationships

The ETL script creates these relationships:
1. Customer → Order (via soldToParty)
2. Order → Product (via sales order items)
3. Order → Invoice (via billing document items)
4. Invoice → Payment (via accounting documents)
5. Order → Delivery (via delivery items)
6. Delivery → Address (assigned)
7. Customer → Address (via business partner addresses)

### Known Limitations

1. **Email Addresses:** SAP data doesn't include email, so we generate placeholder emails
2. **Product Prices:** Calculated from weight data (dummy values)
3. **Payment Linking:** Uses accounting documents to link payments to invoices
4. **Address Assignment:** Some deliveries get randomly assigned addresses from the pool
5. **Incomplete Flows:** Some orders may not have invoices/deliveries (realistic for anomaly detection)

## Troubleshooting

### Issue: No records extracted

**Cause:** Wrong directory path or missing JSONL files

**Solution:**
```bash
# Verify directory exists
ls -la "/Users/vaibhavee/Downloads/sap-o2c-data"

# Check for JSONL files
find "/Users/vaibhavee/Downloads/sap-o2c-data" -name "*.jsonl" | head -10
```

### Issue: Foreign key violations

**Cause:** Referential integrity issues in source data

**Solution:** The ETL script filters out records with missing references automatically. Check the log for "Warning" messages to see what was skipped.

### Issue: Graph pickle not found

**Cause:** Graph hasn't been built yet

**Solution:**
```bash
python backend/scripts/build_graph.py
```

### Issue: Empty graph in frontend

**Cause:** Graph pickle exists but is empty or corrupt

**Solution:**
```bash
# Rebuild graph
python backend/scripts/build_graph.py

# Restart backend to reload graph
# Stop (Ctrl+C) and restart:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Next Steps

After loading the SAP O2C data:

1. **Explore the Graph:** Use the frontend to visualize relationships
2. **Test Queries:** Try the example queries from the main README
3. **Trace Flows:** Use the chat interface to trace order-to-cash flows
4. **Find Anomalies:** Query for incomplete flows

## Additional Resources

- Main README: `../README.md`
- Data Schema Documentation: `../data/README.md`
- API Documentation: http://localhost:8000/docs (when backend is running)
