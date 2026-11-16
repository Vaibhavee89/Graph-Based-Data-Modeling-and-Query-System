# Sharing the prototype

Anyone you share the link with can connect **their own** database, see it as a graph, and ask questions in plain English.

## What it supports

| Database | URL format |
|---|---|
| PostgreSQL | `postgresql://user:pass@host:5432/db` |
| MySQL / MariaDB | `mysql://user:pass@host:3306/db` |
| SQL Server | `mssql://user:pass@host:1433/db` |
| Oracle | `oracle://user:pass@host:1521/?service_name=SERVICE` |

Rows become nodes and foreign keys become edges (up to `MAX_ROWS_PER_TABLE` rows per table, `MAX_TABLES` tables).
Tables without a primary key are queryable but not drawn. Only the default schema is read.

## Deploy (about 15 minutes, free tiers are enough)

Run the backend as **one process**. Sessions are held in memory, so several workers or replicas would log users out at random.

### 1. Backend on Railway (or any Docker host)

1. railway.app → New Project → Deploy from GitHub repo → pick this repo → set **Root Directory** to `backend`.
2. Variables (Settings → Variables):

   | Variable | Value |
   |---|---|
   | `GROQ_API_KEY` | your Groq key (or `ANTHROPIC_API_KEY`) |
   | `GROQ_MODEL` | `openai/gpt-oss-120b` (check console.groq.com/docs/models if it errors) |
   | `DATABASE_URL` | `sqlite:///./app.db` (no Postgres needed; the app's own DB is only a scratch file) |
   | `TRUST_PROXY_HEADERS` | `true` |
   | `ACCESS_CODE` | a shared secret for connecting your own database (optional but recommended) |
   | `CORS_ORIGINS` | your frontend URL, set after step 2 (no trailing slash) |

   Leave `ALLOW_PRIVATE_HOSTS` and `ALLOW_SQLITE_CONNECTIONS` unset.
3. Settings → Networking → Generate Domain. Check `https://<backend>/health` returns `{"status":"healthy"...}`.

### 2. Frontend on Vercel

1. vercel.com → Add New Project → import the repo → **Root Directory** `frontend`.
2. Environment variable: `VITE_API_URL` = `https://<backend-domain>` (no trailing slash).
3. Deploy, then copy the Vercel URL into the backend's `CORS_ORIGINS` and redeploy the backend.

### 3. Share

Send the Vercel URL. Visitors immediately see the sample data and can ask questions about it. To use their own database they click **Connect your database** (and enter the access code, if you set one).

> Anyone with the link can use your LLM key through the chat. Chat is rate limited to 10 questions per minute per visitor, but set a spend limit on the Groq/Anthropic account, and rotate the key if it leaks.

## What testers need to know

- The database must be reachable from the public internet (allow your host's IPs / use a hosted DB). `localhost` and private addresses are blocked on purpose.
- **Use a read-only database user.** The app also validates every generated query and runs it read-only, but a read-only account is the real safety net.
- The connection URL is kept in server memory for 30 minutes (sliding), never written to disk or logged.

## Protections in place

- Connection URLs: only known database types; internal/private/loopback/link-local addresses refused (SSRF); unknown connection options refused; errors never echo driver details.
- Queries: one `SELECT` only, parsed with the database's own dialect; only tables found in the schema; file/sleep/network functions blocked; row cap enforced.
- Execution: read-only session (PostgreSQL, MySQL, SQLite), `READ ONLY` transaction (Oracle), statement timeout where supported.
- Rate limits: 5 connection attempts and `RATE_LIMIT_PER_MINUTE` questions per client per minute. Counters are per server process.

## Known limits (prototype)

- SQL Server has no session-level read-only mode: rely on a read-only login.
- A hostname could change its DNS answer between our check and the connection (DNS rebinding). Run the backend where it has no access to internal networks.
- Sessions live in one process's memory; restarts or multiple replicas log users out. Use a single instance for now.
- Automated tests only ran against SQLite. The PostgreSQL, MySQL, SQL Server and Oracle paths are written against their drivers and the SQL validator is tested for each dialect's syntax, but none has been run against a real server yet. Smoke-test each one (connect, view graph, ask a question) before sharing widely.
