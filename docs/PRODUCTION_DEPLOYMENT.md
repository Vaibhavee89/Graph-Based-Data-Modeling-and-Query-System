# Production Deployment Guide

Complete guide to deploy your Graph-Based Data Modeling System to production.

**Architecture:**
- Frontend → Vercel (React app)
- Backend + Database → Railway (FastAPI + PostgreSQL)

**Total Time:** 20-30 minutes

---

## 📋 Prerequisites

Before starting, ensure you have:

- ✅ GitHub repository (already done)
- ✅ [Railway account](https://railway.app/) (free tier available)
- ✅ [Vercel account](https://vercel.com/) (free tier available)
- ✅ Anthropic API key OR Groq API key
- ✅ All code committed and pushed to GitHub

---

## 🚂 Part 1: Deploy Backend to Railway (15 minutes)

### Step 1: Create Railway Project

1. **Go to [Railway.app](https://railway.app/)**
2. **Sign in** with GitHub
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your repository:**
   ```
   Vaibhavee89/Graph-Based-Data-Modeling-and-Query-System
   ```
6. **Railway will detect the Dockerfile automatically**

### Step 2: Add PostgreSQL Database

1. **In your Railway project, click "New"**
2. **Select "Database"**
3. **Choose "PostgreSQL"**
4. **Railway will provision a database** (takes 1-2 minutes)

### Step 3: Configure Backend Service

1. **Click on your backend service** (not the database)
2. **Go to "Settings" tab**
3. **Configure:**

   **Root Directory:**
   ```
   backend
   ```

   **Build Command:** (should auto-detect from Dockerfile)
   ```
   docker build
   ```

   **Start Command:** (from railway.json)
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
   ```

### Step 4: Set Environment Variables

1. **In backend service, go to "Variables" tab**
2. **Click "Add Variable"** for each:

```bash
# Database (will be auto-filled by Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# API Keys (use at least one)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
GROQ_API_KEY=gsk_your-key-here

# LLM Configuration
GROQ_MODEL=llama-3.3-70b-versatile
USE_GROQ_FALLBACK=true

# Security
SECRET_KEY=your-random-secret-key-here

# CORS (will update after Vercel deployment)
CORS_ORIGINS=http://localhost:3000,https://your-app.vercel.app

# App Configuration
ENVIRONMENT=production
QUERY_TIMEOUT=30
INITIAL_NODE_LIMIT=500
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

3. **Click "Save"**

### Step 5: Deploy Backend

1. **Railway will automatically deploy** after saving variables
2. **Wait for deployment** (3-5 minutes)
3. **Check logs** for any errors
4. **Get your backend URL:**
   - Go to "Settings" → "Domains"
   - Click "Generate Domain"
   - You'll get: `https://your-app.railway.app`

### Step 6: Initialize Database and Load Data

**Option A: Load Sample Data (Quick Test)**

1. **Get Railway CLI:**
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```

3. **Link to your project:**
   ```bash
   cd backend
   railway link
   # Select your project
   ```

4. **Run commands on Railway:**
   ```bash
   # Initialize database
   railway run python scripts/init_db.py

   # Load sample data
   railway run python scripts/load_sample_data.py

   # Build graph
   railway run python scripts/build_graph.py
   ```

**Option B: Load Your Own Data**

1. **Follow data integration guides** first:
   - [QUICK_START_CUSTOM_DATA.md](./QUICK_START_CUSTOM_DATA.md)
   - [DATA_INTEGRATION_GUIDE.md](./DATA_INTEGRATION_GUIDE.md)

2. **Load via Railway CLI:**
   ```bash
   # Load from CSV
   railway run python scripts/load_from_api.py csv /path/to/files/

   # Or from existing database
   railway run python scripts/load_from_existing_db.py

   # Build graph
   railway run python scripts/build_graph.py
   ```

### Step 7: Verify Backend

Test your backend URL:

```bash
# Health check
curl https://your-app.railway.app/health

# Should return: {"status": "healthy"}

# Graph overview
curl https://your-app.railway.app/api/graph/overview

# Should return: {"nodes": 140, "edges": 212, ...}
```

✅ **Backend deployed successfully!**

---

## 🔷 Part 2: Deploy Frontend to Vercel (10 minutes)

### Step 1: Prepare Frontend

1. **Update environment variable reference:**

   The frontend needs to know your Railway backend URL.

   ```bash
   cd frontend
   ```

2. **Vercel will use environment variables, not .env file**

### Step 2: Deploy to Vercel

#### Method 1: Via Vercel Dashboard (Recommended)

1. **Go to [Vercel.com](https://vercel.com/)**
2. **Sign in** with GitHub
3. **Click "Add New Project"**
4. **Import your GitHub repository:**
   ```
   Vaibhavee89/Graph-Based-Data-Modeling-and-Query-System
   ```

5. **Configure project:**
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build` (auto-detected)
   - **Output Directory:** `dist` (auto-detected)

6. **Add Environment Variables:**
   - Click "Environment Variables"
   - Add:
     ```
     VITE_API_URL=https://your-app.railway.app
     ```
   - Replace `your-app.railway.app` with your actual Railway URL

7. **Click "Deploy"**

8. **Wait for deployment** (2-3 minutes)

9. **Your app will be live at:**
   ```
   https://your-app.vercel.app
   ```

#### Method 2: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy from frontend directory
cd frontend
vercel --prod

# Follow prompts:
# - Link to existing project? No
# - What's your project's name? graph-system
# - In which directory is your code? ./
# - Want to override settings? No

# Set environment variable
vercel env add VITE_API_URL production
# Enter: https://your-app.railway.app
```

### Step 3: Update CORS on Backend

Now that you have your Vercel URL, update backend CORS:

1. **Go back to Railway dashboard**
2. **Click on backend service**
3. **Go to "Variables" tab**
4. **Update CORS_ORIGINS:**
   ```
   CORS_ORIGINS=https://your-app.vercel.app,https://your-custom-domain.com
   ```
   (Remove localhost URLs for production)

5. **Save** (Railway will auto-redeploy)

### Step 4: Verify Frontend

1. **Open your Vercel URL:** `https://your-app.vercel.app`
2. **You should see:**
   - Graph visualization with nodes
   - Chat interface on the right
   - Legend and controls
3. **Test query:**
   - Type: "Which products have most orders?"
   - Should get response with data

✅ **Frontend deployed successfully!**

---

## 🔗 Part 3: Connect & Test (5 minutes)

### Full Integration Test

```bash
# 1. Test backend directly
curl https://your-app.railway.app/health

# 2. Test graph API
curl https://your-app.railway.app/api/graph/overview

# 3. Test query API
curl -X POST https://your-app.railway.app/api/query/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Which customers have most orders?"}'

# 4. Test frontend
# Open https://your-app.vercel.app in browser
# - Should load graph
# - Should be able to query
# - Should be able to expand nodes
```

### Verify Features

- ✅ Graph loads (140 nodes visible)
- ✅ Click node → Details panel opens
- ✅ Double-click node → Expands connections
- ✅ Search works
- ✅ Chat query works and returns data
- ✅ Entity chips clickable
- ✅ No CORS errors in browser console

---

## 🎨 Part 4: Custom Domain (Optional)

### Add Custom Domain to Vercel

1. **Go to Vercel dashboard**
2. **Click on your project**
3. **Go to "Settings" → "Domains"**
4. **Add your domain:** `yourdomain.com`
5. **Follow DNS configuration instructions**
6. **Update Railway CORS** with new domain

### Add Custom Domain to Railway

1. **Go to Railway dashboard**
2. **Click backend service**
3. **Go to "Settings" → "Domains"**
4. **Click "Custom Domain"**
5. **Add your domain:** `api.yourdomain.com`
6. **Update DNS with Railway's CNAME**
7. **Update Vercel's VITE_API_URL** to new domain

---

## 🔐 Security Checklist

Before going live, ensure:

- ✅ **Environment variables set** (no hardcoded secrets)
- ✅ **CORS configured** (only your domains allowed)
- ✅ **API keys valid** and have credits
- ✅ **SECRET_KEY is random** (not example value)
- ✅ **HTTPS enabled** (automatic with Railway/Vercel)
- ✅ **Database password strong** (Railway auto-generated)
- ✅ **No .env files in repository** (already in .gitignore)
- ✅ **Error messages sanitized** (no stack traces to users)

---

## 📊 Monitoring & Logs

### View Backend Logs (Railway)

1. **Go to Railway dashboard**
2. **Click backend service**
3. **Go to "Deployments" tab**
4. **Click on latest deployment**
5. **View logs in real-time**

**Common log checks:**
```bash
# Successful startup
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000

# Database connection
INFO:     Database connected

# Query processing
INFO:     Processing query: "Which products..."
```

### View Frontend Logs (Vercel)

1. **Go to Vercel dashboard**
2. **Click on your project**
3. **Go to "Functions" or "Logs" tab**
4. **View server-side logs**

**Client-side logs:**
- Open browser console (F12)
- Check for errors or warnings

### Set Up Error Alerts (Optional)

**Railway:**
- Go to "Settings" → "Notifications"
- Enable email/Slack notifications for deployment failures

**Vercel:**
- Go to "Settings" → "Notifications"
- Enable alerts for build failures and errors

---

## 🚀 Continuous Deployment

### Automatic Deployments

**Backend (Railway):**
- Every push to `main` branch → Auto-deploys backend
- Railway watches: `backend/` directory

**Frontend (Vercel):**
- Every push to `main` branch → Auto-deploys frontend
- Vercel watches: `frontend/` directory

### Manual Deployments

**Backend:**
```bash
# Via Railway CLI
railway up

# Or trigger from dashboard
# Go to service → Click "Redeploy"
```

**Frontend:**
```bash
# Via Vercel CLI
cd frontend
vercel --prod

# Or trigger from dashboard
# Go to deployments → Click "Redeploy"
```

---

## 📈 Performance Optimization

### Backend Optimizations

1. **Enable Railway's Redis** (for caching):
   ```bash
   # In Railway dashboard
   # Click "New" → "Database" → "Redis"
   # Update backend to use Redis for cache
   ```

2. **Increase worker count** (if needed):
   ```bash
   # In Railway, update start command:
   uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
   ```

3. **Database connection pooling** (already configured in SQLAlchemy)

### Frontend Optimizations

1. **Enable Vercel's Edge Network** (automatic)
2. **Image optimization** (automatic with Vercel)
3. **Automatic static asset caching** (configured in vercel.json)

---

## 🔄 Updating Your Deployment

### Deploy New Features

```bash
# 1. Make changes locally
git add .
git commit -m "Add new feature"

# 2. Push to GitHub
git push origin main

# 3. Auto-deploys:
# - Railway: backend updates in ~3 minutes
# - Vercel: frontend updates in ~2 minutes

# 4. Verify deployment
curl https://your-app.railway.app/health
# Open https://your-app.vercel.app
```

### Update Data

```bash
# Connect to Railway
railway login
cd backend
railway link

# Load new data
railway run python scripts/load_from_api.py csv /path/to/new/data/

# Rebuild graph
railway run python scripts/build_graph.py

# Restart backend (if needed)
# Railway dashboard → Service → Restart
```

### Rollback Deployment

**Railway:**
1. Go to "Deployments" tab
2. Find previous working deployment
3. Click "⋮" → "Redeploy"

**Vercel:**
1. Go to "Deployments" tab
2. Find previous working deployment
3. Click "⋮" → "Promote to Production"

---

## 💰 Cost Estimate

### Free Tier Limits

**Railway (Free Trial):**
- $5 credit (500 hours)
- Enough for ~20 days of running 1 backend + 1 database
- After trial: ~$15-20/month for hobby usage

**Vercel (Free):**
- 100GB bandwidth/month
- Unlimited deployments
- Perfect for most use cases
- Free forever for personal projects

**API Costs:**
- **Groq:** FREE unlimited (currently)
- **Anthropic Claude:** Pay per token (~$0.01-0.10 per query)

**Total Monthly Cost:**
- **With Groq:** $15-20 (Railway only)
- **With Claude:** $15-20 + API costs

---

## 🐛 Troubleshooting Production Issues

### Issue 1: Backend won't start

**Check logs:**
```bash
railway logs
```

**Common causes:**
- Missing environment variable
- Database connection failed
- Port binding issue

**Fix:**
- Verify all environment variables set
- Check DATABASE_URL is correct
- Railway auto-assigns PORT (don't hardcode)

---

### Issue 2: Frontend can't reach backend

**Symptoms:**
- Graph not loading
- "Network error" in console
- CORS errors

**Check:**
```bash
# Test backend directly
curl https://your-app.railway.app/health

# Check browser console for CORS error
```

**Fix:**
1. Verify VITE_API_URL in Vercel environment variables
2. Check CORS_ORIGINS in Railway includes Vercel URL
3. Redeploy frontend after changing VITE_API_URL

---

### Issue 3: Query not working (401/402 error)

**Check API key:**
- Go to Railway → Variables
- Verify ANTHROPIC_API_KEY or GROQ_API_KEY is set
- Check API key has credits (Anthropic console)

**Fix:**
- Update API key if expired
- Use Groq as free alternative
- Check backend logs for authentication errors

---

### Issue 4: Database connection errors

**Check:**
```bash
railway logs | grep -i database
```

**Fix:**
- Verify PostgreSQL service is running in Railway
- Check DATABASE_URL references correct service
- Restart PostgreSQL service if needed

---

### Issue 5: Graph not displaying data

**Check:**
```bash
# Verify data loaded
railway run python -c "from app.core.database import SessionLocal; from app.models import Customer; db = SessionLocal(); print(f'{db.query(Customer).count()} customers')"

# Check if graph built
railway run ls -la graph.pickle
```

**Fix:**
```bash
# Rebuild graph
railway run python scripts/build_graph.py

# Restart backend
# Railway dashboard → Service → Restart
```

---

## ✅ Deployment Checklist

### Pre-Deployment

- ✅ All code committed and pushed to GitHub
- ✅ .env files in .gitignore (not committed)
- ✅ Tests passing locally
- ✅ API keys ready (Anthropic or Groq)
- ✅ Railway and Vercel accounts created

### During Deployment

- ✅ Railway project created
- ✅ PostgreSQL added to Railway
- ✅ Backend environment variables set
- ✅ Backend deployed and healthy
- ✅ Data loaded and graph built
- ✅ Vercel project created
- ✅ Frontend environment variable set (VITE_API_URL)
- ✅ Frontend deployed
- ✅ CORS updated on backend with Vercel URL

### Post-Deployment

- ✅ Health check passes: `/health`
- ✅ Graph overview works: `/api/graph/overview`
- ✅ Frontend loads graph
- ✅ Query works in chat
- ✅ Node expansion works
- ✅ No CORS errors
- ✅ Custom domain configured (if needed)
- ✅ Monitoring set up
- ✅ Team notified of URLs

---

## 🎓 Next Steps

After successful deployment:

1. **Test thoroughly** with real users
2. **Monitor logs** for errors (first 24 hours)
3. **Set up custom domain** (optional)
4. **Configure alerts** for errors
5. **Document your specific setup** (data sources, custom schema)
6. **Train team members** on using the system
7. **Plan regular data updates** (daily/weekly sync)

---

## 📞 Support

**Deployment Issues:**
- Railway: https://railway.app/help
- Vercel: https://vercel.com/support
- Check logs first before asking for help

**Application Issues:**
- Review [USER_FLOW.md](./USER_FLOW.md)
- Check [TROUBLESHOOTING section](./USER_FLOW.md#troubleshooting-flow)
- View backend logs for detailed errors

---

## 🎉 Success!

Your Graph-Based Data Modeling System is now live in production!

**Access URLs:**
- Frontend: `https://your-app.vercel.app`
- Backend: `https://your-app.railway.app`
- API Docs: `https://your-app.railway.app/docs`

**Share with your team and start exploring your data!** 🚀

---

**Document Version:** 1.0
**Last Updated:** March 28, 2025
**Deployment Stack:** Railway + Vercel
**Total Deployment Time:** 20-30 minutes
