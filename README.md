# Graph Query: ask your SQL database questions and see it as a graph

Connect a PostgreSQL or MySQL database, see its tables and foreign keys as an interactive graph, and ask questions in plain English. An LLM writes the SQL; a safety layer makes sure only read-only queries on your own tables ever run.

**[Live demo](https://graph-query-system-eight.vercel.app)** · loads with sample data, nothing to install. If it is slow the first time, the free-tier backend is waking up; give it a minute.

![Application screenshot: graph with a selected order, its connections highlighted, and the chat answering a question](docs/images/app-screenshot.png)

## What it does

- **Any relational database becomes a graph.** Rows are nodes, foreign keys are edges. The schema is read at connection time, so there is no per-database setup.
- **Natural-language questions.** "Which orders have no invoice?" becomes a validated SQL query, runs read-only, and the answer comes back as a table.
- **Answers link back to the graph.** Click an ID in an answer and the graph jumps to that row and highlights its connections.
- **Explore by hand.** Click a node for its details, expand its connections, search, and filter by table or relationship.
- **Bring your own data.** Paste a connection URL in the browser. Your data replaces the built-in sample in your view; nothing is ever written to your database.

![Connect dialog](docs/images/connect-dialog.png)

## How it works

```
Browser (React, React Flow)  ──HTTPS──▶  FastAPI backend  ──read-only──▶  your database
   graph canvas + chat                    │  schema → graph (NetworkX)      (Postgres / MySQL)
                                          │  question → LLM → SQL
                                          └─ SQL safety layer, sessions, rate limits
```

1. **Connect.** The backend validates the URL, opens a short-lived read-only session, and reads tables, columns, primary keys and foreign keys.
2. **Graph.** It samples rows from each table (best-connected tables first), pulls in the rows those rows point to, and builds a graph from the foreign keys.
3. **Ask.** Your question and the schema go to the LLM, which returns a SQL query.
4. **Check.** The query is parsed in the database's own dialect and rejected unless it is a single `SELECT` over known tables.
5. **Run.** It executes in a read-only session with a timeout and a row cap, and the result is returned with links back to graph nodes.

## Safety

Running model-written SQL against someone's database needs several independent layers:

| Layer | What it does |
|---|---|
| SQL validation | Parsed with `sqlglot` in the target dialect. One statement, `SELECT` only, known tables only, no `INTO` or locking, and file, sleep and network functions blocked. A row limit is always enforced. |
| Read-only sessions | PostgreSQL `default_transaction_read_only`, MySQL `READ ONLY`, SQLite `query_only`, Oracle read-only transactions. A statement timeout is set where the database supports it. |
| Connection URLs | Only known database types. Private, loopback and cloud-metadata addresses are refused (SSRF protection), and unknown connection options are rejected. |
| Access control | An optional shared access code protects the "connect your own database" feature. |
| Abuse limits | Per-client rate limits on questions and on connection attempts, a question length cap, and a cap on concurrent sessions. |
| Data handling | Connection URLs are held in server memory for a limited time and are never stored or logged. Error messages never include driver details. |

A read-only database user is still the strongest protection, and the app tells users to use one.

## Tech stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, NetworkX, sqlglot
- **LLM:** Anthropic Claude or Groq (either works; Groq alone is enough)
- **Frontend:** React, TypeScript, React Flow, Zustand, TanStack Query, Tailwind CSS, Vite
- **Hosting:** Vercel (frontend) and Render (backend, Docker)

## Try it

### Live

Open the [demo](https://graph-query-system-eight.vercel.app). Click **Connect your database** to use your own (it must be reachable from the internet; for hosted Postgres add `?sslmode=require`).

### Run locally

Needs Python 3.11+ and Node 20.19+ (or 22+).

```bash
# Backend
cd backend
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then set GROQ_API_KEY or ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000

# Frontend (second terminal)
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev                 # http://localhost:5173
```

To connect a database on your own machine, add `ALLOW_PRIVATE_HOSTS=true` to `backend/.env` (never on a public deployment).

### Check a database before using the app

```bash
cd backend
python scripts/check_connection.py "postgresql://user:pass@host:5432/db?sslmode=require"
```

It uses the app's own connection code and reports tables found, graph size, and whether writes are blocked. To try the app against a real server, `scripts/seed_sample_database.py` loads the sample dataset into an empty Postgres or MySQL database.

## Testing

```bash
cd backend && pytest --no-cov -q        # 93 tests
cd frontend && npm test -- --run        # 12 tests
cd frontend && npx tsc --noEmit && npm run lint
```

The backend tests cover SQL validation (including injection attempts), URL safety, connection and session handling, graph building from foreign keys, rate limiting, error redaction and the sample data. They run against SQLite and mocked LLM calls.

PostgreSQL and MySQL were also verified by hand against real servers in Docker: connecting, graph building, questions, and read-only enforcement. Dependency audits (`pip-audit`, `npm audit`) report no known vulnerabilities.

## Project structure

```
backend/
  app/
    connectors/   url_safety, introspect, graph_from_db, sessions, query, demo (sample data)
    routers/      connect, graph, query
    services/     graph_service, llm_service, guardrail_service
    utils/        sql_safety (the SQL validator)
  sample_data/    CSV files for the built-in sample dataset
  scripts/        check_connection, seed_sample_database, generate_sample_csvs, ETL helpers
  tests/
frontend/src/     components (graph canvas, chat, connect dialog), stores, services, lib
render.yaml       backend deployment blueprint
```

## API

| Endpoint | Purpose |
|---|---|
| `POST /api/connect`, `DELETE /api/connect` | Open or close a database session |
| `GET /api/connect/config` | What the UI needs before showing the connect form |
| `GET /api/graph/overview` | Node and edge counts by type |
| `GET /api/graph/starter` | A connected starting view |
| `GET /api/graph/focus/{id}` | Find a row by ID and return it with its connections |
| `GET /api/graph/nodes`, `/nodes/{id}`, `/nodes/{id}/neighbors` | Browse nodes |
| `POST /api/graph/nodes/{id}/expand`, `/search`, `/subgraph` | Expand, search, fetch a subgraph |
| `POST /api/query/chat` | Ask a question |
| `GET /health` | Health check |

Interactive docs are served at `/docs`. Requests carry an `X-Session-Id` header for a connected database; without it the built-in sample data is used.

## Configuration

Set in `backend/.env` (see `backend/.env.example`):

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` / `ANTHROPIC_API_KEY` | LLM provider (set at least one) |
| `ACCESS_CODE` | Require a code to connect your own database |
| `RATE_LIMIT_PER_MINUTE`, `CONNECT_RATE_LIMIT_PER_MINUTE` | Per-client limits |
| `MAX_ROWS_PER_TABLE`, `MAX_TABLES`, `MAX_QUERY_RESULTS`, `QUERY_TIMEOUT` | Sampling and query limits |
| `SESSION_TTL_MINUTES`, `MAX_SESSIONS` | Connection session lifetime and cap |
| `CORS_ORIGINS` | Allowed frontend origins |
| `ALLOW_PRIVATE_HOSTS`, `ALLOW_SQLITE_CONNECTIONS` | Local development only |

## Deployment

The live demo runs the frontend on Vercel and the backend as a Docker container on Render's free tier. Step-by-step instructions, including the environment variables, are in [docs/SHARING_PROTOTYPE.md](docs/SHARING_PROTOTYPE.md). The backend must run as a single process, because connection sessions are kept in memory.

## Status and limitations

This is a working prototype, not a hardened production service.

- **Databases:** PostgreSQL and MySQL are tested. MariaDB uses the MySQL driver but has not been tested. SQL Server and Oracle are supported in code but untested against real servers.
- **Schemas:** only the database's default schema is read.
- **Sampling:** the graph holds a sample of rows per table (200 by default), not the whole database. Questions run against the full database.
- **Sessions:** kept in memory, so a restart ends them. Scaling out would need a shared store such as Redis.
- **Free hosting:** the backend sleeps when idle and takes about a minute to wake.
- **SQL Server** has no session-level read-only mode, so it relies on query validation and a read-only login.

Ideas for next steps: other schemas, a persistent session store, streaming answers, and query-result charts.

## More documentation

- [docs/SHARING_PROTOTYPE.md](docs/SHARING_PROTOTYPE.md): deploying and sharing the app
- [TESTING.md](TESTING.md): running the tests
- [docs/USER_FLOW.md](docs/USER_FLOW.md): user flows
- [docs/DATA_INTEGRATION_GUIDE.md](docs/DATA_INTEGRATION_GUIDE.md) and [SAP_O2C_SETUP.md](SAP_O2C_SETUP.md): the original ETL pipeline for loading CSV or SAP exports

## License

MIT. See [LICENSE](LICENSE).
