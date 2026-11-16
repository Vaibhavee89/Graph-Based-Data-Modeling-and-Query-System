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

## Deploy

1. **Backend (Railway, from `backend/`)**. Set:
   - `ANTHROPIC_API_KEY`
   - `ACCESS_CODE` – a shared secret you give to testers (strongly recommended)
   - `TRUST_PROXY_HEADERS=true`
   - `CORS_ORIGINS=https://<your-frontend-url>`
   - `DATABASE_URL` – the app's own Postgres (only used for the built-in demo data; the app still needs it to boot)
   - Leave `ALLOW_PRIVATE_HOSTS` and `ALLOW_SQLITE_CONNECTIONS` **false**.
2. **Frontend (Vercel, from `frontend/`)**. Set `VITE_API_URL=https://<your-backend-url>`.
3. Send testers the frontend URL and the access code.

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
