# Visual User Flow Diagrams

Quick visual reference for all user journeys.

---

## 🎯 Main Application Flow

```
                              START
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Open Application    │
                    │   localhost:3000      │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Landing Dashboard   │
                    │  • Graph (140 nodes)  │
                    │  • Chat Interface     │
                    │  • Legend & Controls  │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
        ┌────────────────────┐  ┌────────────────────┐
        │  EXPLORE GRAPH     │  │   ASK QUESTIONS    │
        │  (Visual First)    │  │   (Query First)    │
        └─────────┬──────────┘  └─────────┬──────────┘
                  │                       │
                  ▼                       ▼
        ┌────────────────────┐  ┌────────────────────┐
        │  Click/Hover Node  │  │  Type NL Query     │
        │  • See details     │  │  • Get answer      │
        │  • View metadata   │  │  • See data        │
        └─────────┬──────────┘  └─────────┬──────────┘
                  │                       │
                  ▼                       ▼
        ┌────────────────────┐  ┌────────────────────┐
        │  Expand Node       │  │  Click Entity Chip │
        │  (Double-click)    │  │  in Response       │
        │  • See connections │  │  • Jump to graph   │
        └─────────┬──────────┘  └─────────┬──────────┘
                  │                       │
                  └───────────┬───────────┘
                              │
                              ▼
                    ┌───────────────────────┐
                    │  Continue Exploring   │
                    │  • More queries       │
                    │  • More expansion     │
                    │  • Export results     │
                    └───────────────────────┘
```

---

## 📊 Query Processing Pipeline

```
USER INPUT
    │
    ▼
"Which products have most orders?"
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│                  FRONTEND (React)                         │
│                                                           │
│  1. Capture input from chat                              │
│  2. Show loading spinner                                  │
│  3. POST /api/query/chat                                 │
└───────────────────────┬───────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                        │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  STEP 1: Guardrail Check                                 │
│  ┌─────────────────────────────────────┐                 │
│  │ LLM: "Is this domain-related?"      │                 │
│  │ → YES: Continue                     │                 │
│  │ → NO: Reject with message           │                 │
│  └─────────────────────────────────────┘                 │
│                    │                                      │
│                    ▼                                      │
│  STEP 2: Intent Classification                           │
│  ┌─────────────────────────────────────┐                 │
│  │ LLM: Classify query type            │                 │
│  │ → AGGREGATION (counting/stats)      │                 │
│  │ → TRAVERSAL (flow tracing)          │                 │
│  │ → ANOMALY_DETECTION (issues)        │                 │
│  │ → ENTITY_LOOKUP (search)            │                 │
│  └─────────────────────────────────────┘                 │
│                    │                                      │
│                    ▼                                      │
│  STEP 3: Query Generation                                │
│  ┌─────────────────────────────────────┐                 │
│  │ LLM: Generate executable query      │                 │
│  │                                     │                 │
│  │ If AGGREGATION:                     │                 │
│  │   → Generate SQL                    │                 │
│  │                                     │                 │
│  │ If TRAVERSAL:                       │                 │
│  │   → Generate NetworkX code          │                 │
│  │                                     │                 │
│  │ If ANOMALY:                         │                 │
│  │   → Generate SQL + Graph hybrid     │                 │
│  └─────────────────────────────────────┘                 │
│                    │                                      │
│                    ▼                                      │
│  STEP 4: Query Execution                                 │
│  ┌─────────────────────────────────────┐                 │
│  │ Execute against:                    │                 │
│  │ • PostgreSQL (if SQL)               │                 │
│  │ • NetworkX Graph (if graph)         │                 │
│  │ • Both (if hybrid)                  │                 │
│  │                                     │                 │
│  │ Timeout: 30 seconds max             │                 │
│  └─────────────────────────────────────┘                 │
│                    │                                      │
│                    ▼                                      │
│  STEP 5: Response Formatting                             │
│  ┌─────────────────────────────────────┐                 │
│  │ LLM: Format natural language        │                 │
│  │                                     │                 │
│  │ Include:                            │                 │
│  │ • Direct answer (1-2 sentences)     │                 │
│  │ • Key insights (bullet points)      │                 │
│  │ • Data table/list                   │                 │
│  │ • Entity refs [PROD-123]            │                 │
│  └─────────────────────────────────────┘                 │
│                    │                                      │
└────────────────────┼──────────────────────────────────────┘
                     │
                     ▼
┌───────────────────────────────────────────────────────────┐
│                  RESPONSE TO FRONTEND                     │
│                                                           │
│  {                                                        │
│    "success": true,                                       │
│    "answer": "The top products by order count...",        │
│    "data": [{...}, {...}],                               │
│    "entities": ["PROD-123", "PROD-456"],                 │
│    "query_type": "AGGREGATION"                           │
│  }                                                        │
└───────────────────────┬───────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────┐
│                  DISPLAY IN UI                            │
│                                                           │
│  ┌─────────────────────────────────────────────┐         │
│  │ The top products by order count:            │         │
│  │                                              │         │
│  │ 1. Product A (PROD-123) - 45 orders         │         │
│  │ 2. Product B (PROD-456) - 38 orders         │         │
│  │ 3. Product C (PROD-789) - 31 orders         │         │
│  │                                              │         │
│  │ Key insights:                                │         │
│  │ • Product A = 15% of orders                 │         │
│  │ • Top 3 = 40% of volume                     │         │
│  │                                              │         │
│  │ [PROD-123] [PROD-456] [PROD-789] ← Chips   │         │
│  └─────────────────────────────────────────────┘         │
│                                                           │
│  User can click chips → Jump to graph node               │
└───────────────────────────────────────────────────────────┘
```

**Timing:**
- Simple queries (AGGREGATION): 2-4 seconds
- Complex queries (TRAVERSAL): 3-5 seconds
- Anomaly detection (HYBRID): 4-6 seconds

---

## 🔄 Data Integration Flow

```
┌─────────────────────────────────────────────────────────┐
│              CHOOSE DATA SOURCE                         │
└────────┬────────────────────────────┬───────────────────┘
         │                            │
    ┌────┴─────┐                 ┌────┴─────┐
    │          │                 │          │
    ▼          ▼                 ▼          ▼
┌────────┐ ┌────────┐       ┌────────┐ ┌────────┐
│  CSV   │ │Database│       │  API   │ │ Custom │
│ Files  │ │MySQL/PG│       │REST/GQL│ │ Schema │
└───┬────┘ └───┬────┘       └───┬────┘ └───┬────┘
    │          │                │          │
    ▼          ▼                ▼          ▼
┌────────────────────────────────────────────────┐
│            CONFIGURE LOADER                    │
│                                                │
│  • Set connection string (if DB)              │
│  • Map fields to schema                       │
│  • Set API credentials (if API)               │
│  • Define custom models (if custom)           │
└────────────────────┬───────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────┐
│            RUN DATA LOADER                     │
│                                                │
│  docker-compose exec backend \                 │
│    python scripts/load_from_*.py               │
│                                                │
│  • Validates data                             │
│  • Transforms to standard schema              │
│  • Loads into PostgreSQL                      │
└────────────────────┬───────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────┐
│            BUILD GRAPH                         │
│                                                │
│  docker-compose exec backend \                 │
│    python scripts/build_graph.py               │
│                                                │
│  • Reads from PostgreSQL                      │
│  • Creates NetworkX graph                     │
│  • Adds nodes (all entities)                  │
│  • Adds edges (relationships)                 │
│  • Saves to graph.pickle                      │
└────────────────────┬───────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────┐
│            RESTART BACKEND                     │
│                                                │
│  docker-compose restart backend                │
│                                                │
│  • Loads new graph.pickle                     │
│  • Updates cache                              │
│  • Ready for queries                          │
└────────────────────┬───────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────┐
│            VERIFY IN UI                        │
│                                                │
│  1. Refresh browser                           │
│  2. Check node count matches                  │
│  3. Click random node → View details          │
│  4. Try query on your data                    │
│  5. Verify results are correct                │
└────────────────────────────────────────────────┘
```

**Time Estimates:**
- CSV integration: 5 minutes
- Database integration: 10 minutes
- API integration: 15 minutes
- Custom schema: 30-60 minutes

---

## 🖱️ Graph Interaction Flow

```
                      GRAPH CANVAS
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────┐       ┌─────────┐       ┌─────────┐
   │  HOVER  │       │  CLICK  │       │ DOUBLE  │
   │  NODE   │       │  NODE   │       │  CLICK  │
   └────┬────┘       └────┬────┘       └────┬────┘
        │                 │                  │
        ▼                 ▼                  ▼
   ┌─────────┐       ┌─────────┐       ┌─────────┐
   │ Tooltip │       │ Details │       │ Expand  │
   │ Appears │       │  Panel  │       │  Node   │
   │         │       │  Opens  │       │         │
   │ Shows:  │       │         │       │ Shows:  │
   │ • Type  │       │ Shows:  │       │ • All   │
   │ • ID    │       │ • All   │       │  1-hop  │
   │ • Name  │       │  props  │       │  neighb │
   │         │       │ • Links │       │ • Edges │
   │         │       │         │       │         │
   │ 200ms   │       │ Stays   │       │ API     │
   │ delay   │       │ open    │       │ call    │
   └─────────┘       └────┬────┘       └────┬────┘
                          │                  │
                          ▼                  ▼
                     ┌─────────┐       ┌─────────┐
                     │ Actions:│       │ Animate │
                     │         │       │  new    │
                     │ [Expand]│       │  nodes  │
                     │ [Focus] │       │  into   │
                     │ [Copy]  │       │  graph  │
                     │ [View]  │       │         │
                     └─────────┘       │ Re-     │
                                       │ layout  │
                                       └─────────┘


       OTHER INTERACTIONS
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────┐       ┌─────────┐
│  SEARCH │       │ FILTER  │
│         │       │         │
│ Type in │       │ Check/  │
│ search  │       │ uncheck │
│ box     │       │ types   │
│         │       │         │
│ Matches │       │ Graph   │
│ highlt  │       │ updates │
│ Others  │       │ Show    │
│ dimmed  │       │ only    │
│         │       │ select  │
│ Client  │       │ types   │
│ side    │       │         │
└─────────┘       └─────────┘
```

**Interaction Times:**
- Hover tooltip: Instant (200ms delay)
- Click details: 200ms
- Double-click expand: 1-2 seconds
- Search/filter: Instant (client-side)

---

## 🔐 Setup & Configuration Flow

```
                    FIRST-TIME SETUP
                           │
                           ▼
                 ┌──────────────────┐
                 │  Prerequisites   │
                 │  • Docker        │
                 │  • Git           │
                 │  • Text editor   │
                 └─────────┬────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 1: Clone Repository                                │
│                                                          │
│  git clone https://github.com/Vaibhavee89/...           │
│  cd "Graph Based Data Modelling and Query System"       │
│                                                          │
│  ⏱️ Time: 1 minute                                       │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 2: Configure Backend (.env)                        │
│                                                          │
│  cd backend                                              │
│  cp .env.example .env                                    │
│  nano .env                                               │
│                                                          │
│  Required:                                               │
│  • DATABASE_URL (default OK)                            │
│  • ANTHROPIC_API_KEY or GROQ_API_KEY                    │
│  • CORS_ORIGINS (default OK)                            │
│                                                          │
│  Get keys from:                                          │
│  • https://console.anthropic.com/ (premium)             │
│  • https://console.groq.com/ (free)                     │
│                                                          │
│  ⏱️ Time: 3 minutes                                       │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 3: Configure Frontend (.env)                       │
│                                                          │
│  cd ../frontend                                          │
│  echo "VITE_API_URL=http://localhost:8000" > .env       │
│                                                          │
│  ⏱️ Time: 30 seconds                                      │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 4: Start Docker Services                           │
│                                                          │
│  cd ..                                                   │
│  docker-compose up -d                                    │
│                                                          │
│  Services starting:                                      │
│  • postgres (database) → port 5432                      │
│  • backend (API) → port 8000                            │
│  • frontend (UI) → port 3000                            │
│                                                          │
│  Verify:                                                 │
│  docker-compose ps                                       │
│  (all should show "Up")                                  │
│                                                          │
│  ⏱️ Time: 2-3 minutes (first time)                        │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 5: Load Sample Data                                │
│                                                          │
│  docker-compose exec backend \                           │
│    python scripts/load_sample_data.py                    │
│                                                          │
│  Loads:                                                  │
│  • 10 customers                                          │
│  • 20 products                                           │
│  • 30 orders with items                                  │
│  • Invoices, payments, deliveries, addresses            │
│                                                          │
│  Total: 140 nodes, 212 edges                            │
│                                                          │
│  ⏱️ Time: 30 seconds                                      │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│  STEP 6: Access Application                              │
│                                                          │
│  Open browser: http://localhost:3000                     │
│                                                          │
│  You should see:                                         │
│  • Graph with 140 colored nodes                          │
│  • Chat interface on right                               │
│  • Legend showing node types                             │
│  • Controls (zoom, pan, search)                          │
│                                                          │
│  ⏱️ Time: Instant                                         │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
                    ✅ SETUP COMPLETE
                    Total: ~7 minutes
```

---

## 🚨 Troubleshooting Decision Tree

```
                     ISSUE OCCURS
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
     ┌─────────────────┐    ┌─────────────────┐
     │ Graph not       │    │ Query not       │
     │ loading         │    │ working         │
     └────────┬────────┘    └────────┬────────┘
              │                      │
              ▼                      ▼
     Check browser console    Check API response
              │                      │
        ┌─────┴─────┐         ┌─────┴─────┐
        │           │         │           │
        ▼           ▼         ▼           ▼
    API Error   CORS Error  401      No response
        │           │       Error         │
        │           │         │           │
        ▼           ▼         ▼           ▼
    Backend    Frontend   Invalid    Backend
    not        .env       API key    down
    running    wrong                  │
        │           │         │       │
        └─────┬─────┴─────┬───┴───────┘
              │           │
              ▼           ▼
     docker-compose   Update .env
           ps          Restart
              │           │
              └─────┬─────┘
                    │
                    ▼
              Try again
                    │
              ┌─────┴─────┐
              │           │
              ▼           ▼
          ✅ Works    Still broken
                          │
                          ▼
                   Check logs:
                   docker-compose logs -f
```

---

## 📊 Performance Flow

```
USER ACTION → SYSTEM RESPONSE TIME

┌──────────────────────────────────────────┐
│  Graph Load (initial)                    │
│  ├─ Fetch graph data                     │
│  ├─ Parse JSON                           │
│  ├─ Render nodes/edges                   │
│  └─ Layout calculation                   │
│     ⏱️ 1-2 seconds                        │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Node Click                               │
│  ├─ Event handler                         │
│  ├─ Fetch details (cached)               │
│  └─ Slide panel animation                │
│     ⏱️ 200ms                               │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Node Expand (Double-click)               │
│  ├─ API call /expand                     │
│  ├─ Graph traversal (backend)            │
│  ├─ Return connected nodes               │
│  ├─ Merge into graph                     │
│  └─ Animate new nodes                    │
│     ⏱️ 1-2 seconds                        │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Simple Query (Aggregation)               │
│  ├─ Guardrail check (LLM)                │
│  ├─ Intent classification (LLM)          │
│  ├─ Generate SQL (LLM)                   │
│  ├─ Execute SQL (DB)                     │
│  └─ Format response (LLM)                │
│     ⏱️ 2-4 seconds                        │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Complex Query (Traversal)                │
│  ├─ Guardrail + Intent (LLM)             │
│  ├─ Generate graph code (LLM)            │
│  ├─ Execute NetworkX traversal           │
│  └─ Format + highlight (LLM)             │
│     ⏱️ 3-5 seconds                        │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Search/Filter (Client-side)              │
│  ├─ Filter array                          │
│  └─ Update display                        │
│     ⏱️ Instant (<100ms)                   │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Export Graph                             │
│  ├─ Serialize graph                       │
│  ├─ Generate file                         │
│  └─ Download trigger                      │
│     ⏱️ 1-2 seconds                        │
└──────────────────────────────────────────┘
```

---

## 🎓 Learning Path

```
Day 1: Getting Started
├─ Setup (7 min)
├─ Explore sample data (10 min)
└─ Try 3-5 sample queries (10 min)
    Total: ~30 minutes

Day 2: Understanding the System
├─ Read USER_FLOW.md (15 min)
├─ Test graph interactions (15 min)
├─ Try different query types (20 min)
└─ Explore node expansion (10 min)
    Total: ~60 minutes

Day 3: Your Data
├─ Read DATA_INTEGRATION_GUIDE.md (10 min)
├─ Prepare your data source (varies)
├─ Configure and load (15-60 min)
└─ Verify in UI (10 min)
    Total: ~45 min - 2 hours

Week 1+: Advanced Usage
├─ Custom schema (if needed)
├─ Real-time sync (if needed)
├─ Deploy to production
└─ Team onboarding
```

---

**Document Version:** 1.0
**Last Updated:** March 28, 2025
**Companion to:** USER_FLOW.md
