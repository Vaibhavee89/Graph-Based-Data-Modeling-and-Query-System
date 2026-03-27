# Deployment Guide

Complete guide for deploying the Graph Data Modeling System to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Deployment (Docker)](#local-deployment-docker)
3. [Railway Deployment (Backend)](#railway-deployment-backend)
4. [Vercel Deployment (Frontend)](#vercel-deployment-frontend)
5. [Environment Variables](#environment-variables)
6. [Database Setup](#database-setup)
7. [CI/CD Configuration](#cicd-configuration)
8. [Monitoring & Logging](#monitoring--logging)
9. [Security Checklist](#security-checklist)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts
- ✅ [GitHub](https://github.com) - Code repository
- ✅ [Railway](https://railway.app) - Backend hosting + PostgreSQL
- ✅ [Vercel](https://vercel.com) - Frontend hosting
- ✅ [Anthropic](https://console.anthropic.com) - Claude API access

### Required Tools
- Docker & Docker Compose
- Git
- Node.js 18+
- Python 3.11+

---

## Local Deployment (Docker)

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd "Graph Based Data Modelling and Query System"
```

### 2. Set Environment Variables

**Backend:**
```bash
cd backend
cp .env.example .env
# Edit .env and set:
# - ANTHROPIC_API_KEY=your_key_here
```

**Frontend:**
```bash
cd ../frontend
cp .env.example .env
# Edit .env and set:
# - VITE_API_URL=http://localhost:8000
```

### 3. Start Services

```bash
# From project root
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Load data (if needed)
docker-compose exec backend python scripts/etl_sap_o2c.py

# Build graph
docker-compose exec backend python scripts/build_graph.py
```

### 5. Verify

- **Backend API:** http://localhost:8000/docs
- **Frontend App:** http://localhost:3000
- **PostgreSQL:** localhost:5432

```bash
# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000/health
```

---

## Railway Deployment (Backend)

### 1. Install Railway CLI

```bash
npm install -g @railway/cli

# Login
railway login
```

### 2. Create New Project

```bash
cd backend

# Initialize Railway project
railway init
```

### 3. Add PostgreSQL

```bash
# Add PostgreSQL service
railway add

# Select: PostgreSQL
# Railway will automatically provision database
```

### 4. Configure Environment Variables

In Railway dashboard or via CLI:

```bash
railway variables set ANTHROPIC_API_KEY=your_key_here
railway variables set LLM_MODEL=claude-haiku-4-5-20251001
railway variables set CORS_ORIGINS=https://your-frontend.vercel.app
railway variables set ENVIRONMENT=production
```

Railway automatically sets: `DATABASE_URL`

### 5. Deploy

```bash
# Deploy backend
railway up

# Run migrations
railway run alembic upgrade head
```

### 6. Get Backend URL

```bash
railway open

# Or get URL
railway status
# Copy the URL (e.g., https://your-app.up.railway.app)
```

### 7. Load Data (First Time)

```bash
# Upload dataset
railway run python scripts/etl_sap_o2c.py

# Build graph
railway run python scripts/build_graph.py
```

---

## Vercel Deployment (Frontend)

### 1. Install Vercel CLI

```bash
npm install -g vercel

# Login
vercel login
```

### 2. Configure Frontend

```bash
cd frontend

# Initialize Vercel project
vercel init
```

### 3. Set Environment Variables

In Vercel dashboard or via CLI:

```bash
vercel env add VITE_API_URL

# Enter your Railway backend URL:
# https://your-app.up.railway.app
```

### 4. Deploy

```bash
# Deploy to production
vercel --prod
```

### 5. Custom Domain (Optional)

```bash
# Add custom domain
vercel domains add yourdomain.com
```

---

## Environment Variables

### Backend (.env)

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/dbname
ANTHROPIC_API_KEY=sk-ant-xxxxx
LLM_MODEL=claude-haiku-4-5-20251001

# Optional
CORS_ORIGINS=https://your-frontend.vercel.app
ENVIRONMENT=production
API_RATE_LIMIT=100
CACHE_TTL=300
LOG_LEVEL=INFO
MAX_WORKERS=2
```

### Frontend (.env)

```bash
# Required
VITE_API_URL=https://your-backend.up.railway.app

# Optional
VITE_ENVIRONMENT=production
VITE_ENABLE_ANALYTICS=false
```

---

## Database Setup

### Initial Setup

```bash
# 1. Create database (Railway does this automatically)
createdb graphdb

# 2. Run migrations
alembic upgrade head

# 3. Verify tables
psql $DATABASE_URL -c "\dt"
```

### Loading Data

```bash
# Option 1: From SAP O2C dataset
python scripts/etl_sap_o2c.py

# Option 2: From CSV files
python scripts/init_db.py

# Option 3: From SQL dump
psql $DATABASE_URL < backup.sql
```

### Building Graph

```bash
# Build NetworkX graph from database
python scripts/build_graph.py

# Verify graph file
ls -lh graph.pickle
```

### Database Backups

```bash
# Create backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore backup
psql $DATABASE_URL < backup.sql

# Railway automatic backups
# Go to Railway dashboard → Database → Backups
```

---

## CI/CD Configuration

### GitHub Secrets

Add these secrets in GitHub repository settings:

```
RAILWAY_TOKEN=your_railway_token
VERCEL_TOKEN=your_vercel_token
BACKEND_URL=https://your-backend.up.railway.app
FRONTEND_URL=https://your-frontend.vercel.app
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### Automated Deployments

**On Pull Request:**
- Run tests (backend + frontend)
- Build Docker images
- Check code quality

**On Merge to Main:**
- Deploy backend to Railway
- Deploy frontend to Vercel
- Run database migrations
- Verify deployments

### Manual Deployment

```bash
# Trigger deploy manually
gh workflow run deploy-backend.yml
gh workflow run deploy-frontend.yml
```

---

## Monitoring & Logging

### Railway Monitoring

```bash
# View logs
railway logs

# Follow logs
railway logs --follow

# Filter by service
railway logs --service backend
```

### Health Checks

**Backend:** `GET /health`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "graph": "loaded"
}
```

**Frontend:** `GET /health`
```
OK
```

### Performance Monitoring

**Backend Metrics:**
- Response times (target: <500ms p95)
- Error rates (target: <1%)
- Database query times
- Cache hit rates

**Frontend Metrics:**
- Page load time (target: <3s)
- Time to Interactive (target: <5s)
- Core Web Vitals

### Logging

**Backend (Python):**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Message")
```

**Log Levels:**
- DEBUG - Development only
- INFO - General information
- WARNING - Warning messages
- ERROR - Error messages
- CRITICAL - Critical issues

---

## Security Checklist

### Before Deployment

- [ ] Change default secret keys
- [ ] Set strong database passwords
- [ ] Enable HTTPS only
- [ ] Configure CORS properly
- [ ] Set rate limiting
- [ ] Enable security headers
- [ ] Validate all inputs
- [ ] Use environment variables (never commit secrets)
- [ ] Enable database SSL
- [ ] Review API permissions

### Backend Security

```python
# CORS configuration (main.py)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.get("/api/query/chat")
@limiter.limit("10/minute")
async def chat(request: Request):
    ...
```

### Frontend Security

```typescript
// API requests with credentials
axios.defaults.withCredentials = true;

// XSS prevention
import DOMPurify from 'dompurify';
const clean = DOMPurify.sanitize(userInput);
```

### Database Security

```bash
# Enable SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Read-only user for queries
CREATE USER readonly WITH PASSWORD 'password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
```

---

## Troubleshooting

### Backend Won't Start

**Issue:** `DATABASE_URL not found`
```bash
# Solution: Set environment variable
export DATABASE_URL=postgresql://...
```

**Issue:** `Module not found`
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Issue:** `Port 8000 already in use`
```bash
# Solution: Kill process or change port
lsof -ti:8000 | xargs kill -9
# Or change PORT in .env
```

### Frontend Won't Build

**Issue:** `Module not found`
```bash
# Solution: Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue:** `API_URL not defined`
```bash
# Solution: Set environment variable
echo "VITE_API_URL=http://localhost:8000" > .env
```

### Database Connection Failed

**Issue:** `Connection refused`
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL
docker-compose up postgres
```

**Issue:** `Authentication failed`
```bash
# Verify credentials
psql $DATABASE_URL

# Reset password if needed
```

### Deployment Failed

**Railway:**
```bash
# Check logs
railway logs

# Verify environment variables
railway variables

# Redeploy
railway up
```

**Vercel:**
```bash
# Check build logs
vercel logs

# Verify environment variables
vercel env ls

# Redeploy
vercel --prod
```

---

## Rollback Procedures

### Railway Rollback

```bash
# View deployments
railway status

# Rollback to previous deployment
railway rollback
```

### Vercel Rollback

```bash
# List deployments
vercel ls

# Promote previous deployment
vercel promote <deployment-url>
```

### Database Rollback

```bash
# Rollback migrations
alembic downgrade -1

# Or restore from backup
psql $DATABASE_URL < backup.sql
```

---

## Production Checklist

Before going live:

**Infrastructure:**
- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] Database provisioned and migrated
- [ ] Custom domains configured (if applicable)
- [ ] SSL/HTTPS enabled
- [ ] Health checks passing

**Configuration:**
- [ ] Environment variables set
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Caching configured
- [ ] Logging enabled

**Security:**
- [ ] Secrets rotated
- [ ] Database SSL enabled
- [ ] Security headers configured
- [ ] API key restrictions set
- [ ] Backup strategy in place

**Monitoring:**
- [ ] Health checks automated
- [ ] Error tracking enabled
- [ ] Performance monitoring set up
- [ ] Alerts configured

**Testing:**
- [ ] All tests passing
- [ ] End-to-end testing complete
- [ ] Load testing performed
- [ ] Security audit done

**Documentation:**
- [ ] Deployment guide updated
- [ ] API documentation current
- [ ] Runbook created
- [ ] Team trained

---

## Cost Estimation

### Railway (Backend + Database)

**Hobby Plan:** $5/month
- 500 hours execution
- 512 MB RAM
- 1 GB PostgreSQL storage

**Pro Plan:** $20/month
- 2000 hours execution
- 8 GB RAM
- 10 GB PostgreSQL storage

**Estimated:** $5-20/month

### Vercel (Frontend)

**Hobby Plan:** Free
- 100 GB bandwidth
- Unlimited deployments

**Pro Plan:** $20/month
- 1 TB bandwidth
- Advanced analytics

**Estimated:** $0-20/month

### Anthropic (LLM API)

**Claude Haiku:** ~$0.25 per million input tokens

**Estimated Usage:** 1000 queries/day
- Input: ~500 tokens/query
- Output: ~200 tokens/query
- Cost: ~$0.18/day = $5.40/month

**With caching (60% reduction):** ~$2.16/month

**Total Estimated Cost:** $7-42/month

---

## Support

**Issues:** https://github.com/your-repo/issues
**Docs:** https://your-docs-site.com
**Email:** support@yourdomain.com

---

## Additional Resources

- [Railway Docs](https://docs.railway.app)
- [Vercel Docs](https://vercel.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Deployment](https://vitejs.dev/guide/static-deploy.html)
