"""In-memory sessions for user-supplied database connections. Credentials are never persisted."""
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

import networkx as nx
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine, URL

from app.config import settings
from app.connectors.graph_from_db import build_graph
from app.connectors.introspect import SchemaInfo, introspect
from app.connectors.url_safety import parse_and_check


@dataclass
class DbSession:
    token: str
    engine: Engine
    dialect: str          # sqlglot dialect
    backend: str          # postgresql | mysql | mssql | oracle | sqlite
    database: str
    schema: SchemaInfo
    graph: nx.DiGraph
    expires_at: float


def _connect_args(backend: str) -> dict:
    if backend == "postgresql":
        return {"connect_timeout": 10}
    if backend == "mysql":
        return {"connect_timeout": 10, "read_timeout": settings.query_timeout}
    if backend == "mssql":
        return {"login_timeout": 10, "timeout": settings.query_timeout}
    if backend == "oracle":
        return {"tcp_connect_timeout": 10}
    return {}


def _install_read_only(engine: Engine, backend: str) -> None:
    """Put every new connection into a read-only, time-limited mode where the database supports it."""
    timeout_ms = int(settings.query_timeout) * 1000

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        try:
            if backend == "postgresql":
                cur.execute("SET default_transaction_read_only = on")
                cur.execute(f"SET statement_timeout = {timeout_ms}")
            elif backend == "mysql":
                cur.execute("SET SESSION TRANSACTION READ ONLY")
                try:
                    cur.execute(f"SET SESSION MAX_EXECUTION_TIME = {timeout_ms}")
                except Exception:
                    pass  # MariaDB uses max_statement_time instead
            elif backend == "sqlite":
                cur.execute("PRAGMA query_only = ON")
            # oracle: SET TRANSACTION READ ONLY is issued per query; mssql: relies on validation + DB permissions
        finally:
            cur.close()


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, DbSession] = {}
        self._lock = threading.Lock()

    def _purge(self) -> None:
        now = time.time()
        for token in [t for t, s in self._sessions.items() if s.expires_at <= now]:
            self._sessions.pop(token).engine.dispose()

    def open(self, raw_url: str) -> DbSession:
        url, dialect, backend = parse_and_check(raw_url)
        with self._lock:
            self._purge()
            if len(self._sessions) >= settings.max_sessions:
                raise RuntimeError("The server is busy. Please try again in a few minutes.")

        engine = create_engine(
            url, pool_size=2, max_overflow=0, pool_pre_ping=True, pool_recycle=300,
            connect_args=_connect_args(backend),
        )
        _install_read_only(engine, backend)
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM DUAL" if backend == "oracle" else "SELECT 1"))
            schema = introspect(engine, settings.max_tables)
            if not schema.tables:
                raise ValueError("No tables were found in that database.")
            graph = build_graph(engine, schema, settings.max_rows_per_table, settings.max_graph_nodes)
        except Exception:
            engine.dispose()
            raise

        session = DbSession(
            token=secrets.token_urlsafe(32), engine=engine, dialect=dialect, backend=backend,
            database=url.database or backend, schema=schema, graph=graph,
            expires_at=time.time() + settings.session_ttl_minutes * 60,
        )
        with self._lock:
            self._sessions[session.token] = session
        return session

    def get(self, token: Optional[str]) -> Optional[DbSession]:
        if not token:
            return None
        with self._lock:
            self._purge()
            s = self._sessions.get(token)
            if s:
                s.expires_at = time.time() + settings.session_ttl_minutes * 60  # sliding expiry
            return s

    def close(self, token: str) -> None:
        with self._lock:
            s = self._sessions.pop(token, None)
        if s:
            s.engine.dispose()


sessions = SessionManager()
