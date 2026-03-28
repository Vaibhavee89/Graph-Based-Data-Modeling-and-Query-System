# 🚀 Production Deployment Checklist

Quick checklist for deploying to Vercel + Railway. **Print this and check off items as you go!**

---

## ⏱️ Estimated Time: 30 minutes

---

## 🎯 Pre-Deployment

- [ ] Code committed and pushed to GitHub
- [ ] Railway account created → https://railway.app
- [ ] Vercel account created → https://vercel.com
- [ ] API key ready (Anthropic OR Groq)
  - Anthropic: https://console.anthropic.com
  - Groq (free): https://console.groq.com

---

## 🚂 Backend Deployment (Railway) - 15 min

### Create Project

- [ ] Login to Railway with GitHub
- [ ] Click "New Project"
- [ ] Choose "Deploy from GitHub repo"
- [ ] Select: `Graph-Based-Data-Modeling-and-Query-System`

### Add Database

- [ ] Click "New" → "Database" → "PostgreSQL"
- [ ] Wait for provisioning (~2 min)

### Configure Backend

- [ ] Click backend service → "Settings"
- [ ] Set Root Directory: `backend`
- [ ] Set Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`

### Environment Variables

Click "Variables" → Add each:

- [ ] `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`
- [ ] `ANTHROPIC_API_KEY` = `sk-ant-api03-...` (or leave empty)
- [ ] `GROQ_API_KEY` = `gsk_...` (free tier)
- [ ] `GROQ_MODEL` = `llama-3.3-70b-versatile`
- [ ] `USE_GROQ_FALLBACK` = `true`
- [ ] `SECRET_KEY` = (generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] `CORS_ORIGINS` = `http://localhost:3000` (will update later)
- [ ] `ENVIRONMENT` = `production`
- [ ] `QUERY_TIMEOUT` = `30`

### Deploy & Get URL

- [ ] Click "Save" (auto-deploys)
- [ ] Wait 3-5 minutes
- [ ] Settings → "Domains" → "Generate Domain"
- [ ] **Copy URL:** `https://______________.railway.app`

### Load Data

Install Railway CLI:
```bash
npm i -g @railway/cli
railway login
cd backend
railway link
```

Choose one:
- [ ] Sample data: `railway run python scripts/load_sample_data.py`
- [ ] Your CSV: `railway run python scripts/load_from_api.py csv /path/`
- [ ] Your DB: `railway run python scripts/load_from_existing_db.py`

Then:
- [ ] Build graph: `railway run python scripts/build_graph.py`

### Verify Backend

- [ ] Test: `curl https://your-app.railway.app/health`
- [ ] Should return: `{"status": "healthy"}`
- [ ] Test: `curl https://your-app.railway.app/api/graph/overview`
- [ ] Should return: `{"nodes": 140, ...}`

---

## 🔷 Frontend Deployment (Vercel) - 10 min

### Deploy to Vercel

- [ ] Login to Vercel with GitHub
- [ ] Click "Add New Project"
- [ ] Import: `Graph-Based-Data-Modeling-and-Query-System`
- [ ] Framework: `Vite`
- [ ] Root Directory: `frontend`
- [ ] Build Command: `npm run build` (auto)
- [ ] Output Directory: `dist` (auto)

### Environment Variable

- [ ] Click "Environment Variables"
- [ ] Add: `VITE_API_URL` = `https://your-app.railway.app`
- [ ] (Use your actual Railway URL from above)

### Deploy

- [ ] Click "Deploy"
- [ ] Wait 2-3 minutes
- [ ] **Copy URL:** `https://______________.vercel.app`

### Update Backend CORS

- [ ] Go back to Railway
- [ ] Backend service → "Variables"
- [ ] Update `CORS_ORIGINS` = `https://your-app.vercel.app`
- [ ] Save (auto-redeploys)

---

## ✅ Testing - 5 min

### Backend Tests

```bash
curl https://your-app.railway.app/health
curl https://your-app.railway.app/api/graph/overview
```

- [ ] Both return valid JSON

### Frontend Tests

Open: `https://your-app.vercel.app`

- [ ] Graph loads with nodes
- [ ] Click node → Details panel opens
- [ ] Double-click node → Expands
- [ ] Type query: "Which customers have most orders?"
- [ ] Get response with data
- [ ] Click entity chip → Jumps to node
- [ ] No errors in browser console (F12)

---

## 🎉 Success Criteria

- [ ] Backend health check passes
- [ ] Frontend loads without errors
- [ ] Graph displays data
- [ ] Queries work and return results
- [ ] Node expansion works
- [ ] No CORS errors

---

## 📝 Save These URLs

**Backend API:**
```
https://________________________________.railway.app
```

**Frontend App:**
```
https://________________________________.vercel.app
```

**API Docs:**
```
https://________________________________.railway.app/docs
```

---

## 🐛 Common Issues

### Graph not loading
- Check browser console (F12)
- Verify VITE_API_URL in Vercel settings
- Check CORS_ORIGINS in Railway

### Query 401/402 error
- Check API key in Railway variables
- Use Groq if Anthropic has no credits
- Verify `USE_GROQ_FALLBACK=true`

### Backend not starting
- Check Railway logs
- Verify DATABASE_URL is set
- Verify all required variables present

---

## 📚 Full Documentation

**Detailed guide:** [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)

**Quick script:** Run `./scripts/deploy.sh` for interactive deployment

---

## ✨ Next Steps After Deployment

- [ ] Test with real users
- [ ] Monitor logs (first 24 hours)
- [ ] Set up custom domain (optional)
- [ ] Configure error alerts
- [ ] Document your specific setup
- [ ] Train team on using the system

---

**Deployment Date:** _______________

**Deployed By:** _______________

**Backend URL:** _______________

**Frontend URL:** _______________

**Notes:**
```




```

---

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Complete
