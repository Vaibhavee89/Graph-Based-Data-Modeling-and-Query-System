# Graph-Based Data Modeling and Query System

A complete system that unifies fragmented business data into an interactive graph with an LLM-powered natural language query interface.

## Screenshot

![Application Screenshot](docs/images/app-screenshot.png)

*Graph visualization with interactive node exploration, entity details panel, and AI-powered chat interface*

## 🚀 Quick Start

### Local Development (Docker)

```bash
# 1. Clone and configure
git clone <repo-url>
cd "Graph Based Data Modelling and Query System"

# 2. Configure environment
cd backend && cp .env.example .env
# Add your ANTHROPIC_API_KEY or GROQ_API_KEY in .env

cd ../frontend && echo "VITE_API_URL=http://localhost:8000" > .env

# 3. Start everything
cd .. && docker-compose up -d

# 4. Load sample data
docker-compose exec backend python scripts/load_sample_data.py

# 5. Access app at http://localhost:3000
```

⏱️ **Time:** 7 minutes | **See:** [Complete Setup Guide](docs/USER_FLOW.md#setup-flow-first-time)

### Production Deployment (Vercel + Railway)

```bash
# Option 1: Interactive script
./scripts/deploy.sh

# Option 2: Manual deployment
# See detailed guide: docs/PRODUCTION_DEPLOYMENT.md
# Or use checklist: DEPLOYMENT_CHECKLIST.md
```

⏱️ **Time:** 30 minutes | **Cost:** $0-20/month | **See:** [Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md)

---

## Overview

This project converts business data (orders, deliveries, invoices, payments, customers, products, addresses) into an interconnected graph with:

- **Interactive Graph Visualization** - Explore entity relationships with node expansion and metadata inspection
- **Natural Language Queries** - Ask questions using plain English, powered by Claude AI
- **Flow Tracing** - Trace complete order → invoice → payment flows
- **Anomaly Detection** - Identify broken or incomplete business flows
- **Data-backed Answers** - All responses grounded in actual data with guardrails

## Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **PostgreSQL** - Relational database for data persistence
- **NetworkX** - In-memory graph operations
- **SQLAlchemy** - ORM for database access
- **Claude API (Haiku)** - LLM for natural language understanding
- **LangChain** - LLM framework with guardrails

### Frontend
- **React + TypeScript** - Type-safe UI framework
- **React Flow** - Graph visualization
- **Tailwind CSS** - Utility-first styling
- **Zustand** - State management
- **TanStack Query** - Server state & caching

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration settings
│   │   ├── models/              # SQLAlchemy ORM models (7 entities)
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic (graph, query, guardrail)
│   │   ├── routers/             # API endpoints
│   │   ├── core/                # Database & graph store
│   │   └── utils/               # Graph builder utilities
│   ├── scripts/                 # ETL, database init, dataset download
│   ├── tests/                   # Backend tests
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/          # React components (Graph, Chat, Details)
│   │   ├── services/            # API client
│   │   ├── stores/              # Zustand state stores
│   │   ├── types/               # TypeScript types
│   │   ├── App.tsx              # Main application
│   │   └── main.tsx             # Entry point
│   ├── package.json             # Node dependencies
│   └── vite.config.ts           # Vite configuration
├── data/
│   ├── raw/                     # Original CSV files
│   └── processed/               # Cleaned data
├── docker-compose.yml           # PostgreSQL service
└── README.md
```

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose** (for PostgreSQL)
- **Anthropic API Key** (get from https://console.anthropic.com)

### 1. Clone Repository

```bash
git clone <repository-url>
cd "Graph Based Data Modelling and Query System"
```

### 2. Set Up Backend

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Create Python virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Initialize database
python scripts/init_db.py
```

### 3. Set Up Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
```

### 4. Load Data (Optional - requires dataset)

```bash
cd ../backend

# Download dataset (requires Google Drive link)
python scripts/download_dataset.py

# Run ETL pipeline
python scripts/etl.py

# Build graph
python scripts/build_graph.py
```

### 5. Run Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

### Example Queries

1. **Aggregation**: "Which products are associated with the highest number of billing documents?"
2. **Flow Tracing**: "Trace the full flow of billing document INV-12345"
3. **Anomaly Detection**: "Identify sales orders that have broken or incomplete flows"
4. **Entity Lookup**: "Show me details for customer CUST-123"

### Graph Interaction

- **Single Click** - View node details in side panel
- **Double Click** - Expand node connections
- **Hover** - Show quick info tooltip
- **Search** - Filter and highlight nodes
- **Pan & Zoom** - Navigate large graphs

## Documentation

### 📚 Complete Guides

- **[USER_FLOW.md](docs/USER_FLOW.md)** - Complete user flow guide covering all interactions
  - Setup flow (first-time installation)
  - Daily usage patterns
  - Data integration workflows
  - Graph exploration features
  - Query processing pipeline
  - Advanced features
  - Troubleshooting guide

- **[USER_FLOW_DIAGRAM.md](docs/USER_FLOW_DIAGRAM.md)** - Visual flowcharts and diagrams
  - Main application flow
  - Query processing pipeline (step-by-step)
  - Data integration flow
  - Graph interaction flow
  - Troubleshooting decision tree
  - Performance benchmarks

### 🔌 Integration Guides

- **[QUICK_START_CUSTOM_DATA.md](docs/QUICK_START_CUSTOM_DATA.md)** - Get started with your data in 10 minutes
  - 4 common scenarios with step-by-step instructions
  - CSV files, existing databases, APIs, real-time sync

- **[DATA_INTEGRATION_GUIDE.md](docs/DATA_INTEGRATION_GUIDE.md)** - Comprehensive integration guide
  - All supported databases (MySQL, SQLite, SQL Server, Oracle, etc.)
  - REST API integration (Salesforce, SAP, custom APIs)
  - Real-time sync patterns (polling, webhooks, database triggers)
  - Field mapping examples
  - Troubleshooting section

- **[CUSTOM_SCHEMA_GUIDE.md](docs/CUSTOM_SCHEMA_GUIDE.md)** - Extend system for your domain
  - E-commerce example (Store, Review, Cart entities)
  - Healthcare example (Patient, Doctor, Appointment entities)
  - Supply Chain example (Supplier, Warehouse, Shipment entities)
  - Step-by-step customization instructions

### 🚀 Deployment & Testing

- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide
  - Docker deployment (complete)
  - Railway backend deployment
  - Vercel frontend deployment
  - Environment configuration
  - CI/CD setup

- **[TESTING.md](docs/TESTING.md)** - Testing documentation
  - 48 backend tests (90% coverage)
  - 13 frontend tests (75% coverage)
  - Performance optimizations
  - Database indexes

## Development

### Backend Development

```bash
cd backend

# Run tests
pytest tests/ --cov=app

# Format code
black app/ scripts/
isort app/ scripts/

# Lint
flake8 app/ scripts/
```

### Frontend Development

```bash
cd frontend

# Run tests
npm test

# Lint
npm run lint

# Build for production
npm run build
```

## Graph Model

### Node Types (7 Entities)
- **Customer** (Blue) - customer_id, name, email, segment
- **Product** (Green) - product_id, name, category, price
- **Order** (Orange) - order_id, date, status, amount
- **Delivery** (Purple) - delivery_id, date, status, tracking
- **Invoice** (Red) - invoice_id, date, amount, status
- **Payment** (Yellow) - payment_id, date, amount, method
- **Address** (Gray) - address_id, street, city, state

### Relationships
- Customer → Order (PLACED)
- Order → Product (CONTAINS, with quantity)
- Order → Invoice (GENERATED)
- Order → Delivery (RESULTED_IN)
- Invoice → Payment (PAID_BY)
- Customer → Address (HAS_ADDRESS)
- Delivery → Address (TO_ADDRESS)

## Configuration

### Backend (.env)

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/graphdb
ANTHROPIC_API_KEY=your_key_here
LLM_MODEL=claude-haiku-4-5-20251001
QUERY_TIMEOUT=30
INITIAL_NODE_LIMIT=500
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
```

## Deployment

### 🚀 Quick Deploy

**Automated Script:**
```bash
./scripts/deploy.sh
# Interactive menu for backend, frontend, or both
```

**Manual Deployment:**

1. **Backend (Railway):** [Detailed Guide](docs/PRODUCTION_DEPLOYMENT.md#part-1-deploy-backend-to-railway-15-minutes)
   - Deploy from GitHub
   - Add PostgreSQL database
   - Set environment variables
   - Load data and build graph

2. **Frontend (Vercel):** [Detailed Guide](docs/PRODUCTION_DEPLOYMENT.md#part-2-deploy-frontend-to-vercel-10-minutes)
   - Connect GitHub repository
   - Set `VITE_API_URL` environment variable
   - Auto-deploy on push

**Resources:**
- 📖 [Complete Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md) - Step-by-step (30 min)
- ✅ [Deployment Checklist](DEPLOYMENT_CHECKLIST.md) - Printable checklist
- 💰 **Cost:** $0-20/month (Railway free trial + Vercel free tier)
- ⚡ **Result:** Live production app with auto-deployments

## Architecture

```
Frontend (React)          Backend (FastAPI)          Data Layer
┌──────────────┐         ┌──────────────────┐      ┌──────────┐
│ Graph Canvas │◄───────►│  Graph Service   │◄────►│ NetworkX │
│ (React Flow) │         │  Query Service   │      └──────────┘
│ Chat Interface│         │  Guardrail Svc   │      ┌──────────┐
└──────────────┘         │  LLM Service     │◄────►│PostgreSQL│
                         └──────────────────┘      └──────────┘
                                  │
                         ┌────────┴────────┐
                         │  Claude API     │
                         │  (Haiku)        │
                         └─────────────────┘
```

## API Endpoints

### Graph API
- `GET /api/graph/overview` - Graph statistics
- `GET /api/graph/nodes` - List nodes (paginated)
- `GET /api/graph/nodes/{id}` - Get node details
- `POST /api/graph/nodes/{id}/expand` - Expand connections
- `POST /api/graph/search` - Search nodes

### Query API
- `POST /api/query/chat` - Natural language query

### Health
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running: `docker-compose ps`
- Verify `.env` file exists with correct `DATABASE_URL`
- Check Python version: `python --version` (should be 3.11+)

### Frontend build errors
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node version: `node --version` (should be 18+)

### Query errors
- Verify `ANTHROPIC_API_KEY` is set correctly
- Check API key has credits: https://console.anthropic.com
- Review logs: Backend terminal will show detailed errors

### Database connection errors
- Restart PostgreSQL: `docker-compose restart postgres`
- Check port 5432 is available: `lsof -i :5432`

## Contributing

This project is part of an implementation plan. To contribute:

1. Create a feature branch
2. Make changes with tests
3. Ensure all tests pass
4. Submit pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Check logs in backend terminal
- Review browser console (F12) for frontend errors
- Check `/docs` endpoint for API documentation
