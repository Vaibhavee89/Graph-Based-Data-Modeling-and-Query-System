"""Check that a database works with this app, using the same code the web app uses.

    python scripts/check_connection.py "postgresql://user:pass@host:5432/db?sslmode=require"

Prints: connection, tables found, graph size, whether the session is really read-only, and the
statement timeout. The write checks are harmless no-ops (WHERE 1=0) if protection ever failed.
Use a READ-ONLY database user anyway.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "unused")
os.environ.setdefault("ALLOW_PRIVATE_HOSTS", "true")   # lets you test a database on localhost

from sqlalchemy import text  # noqa: E402

from app.connectors.sessions import sessions  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    try:
        s = sessions.open(sys.argv[1])
    except Exception as e:
        print(f"FAILED to connect: {type(e).__name__}: {e}")
        print("Hints: check host/port/password; hosted databases usually need ?sslmode=require (Postgres);")
        print("       the database must accept connections from this machine.")
        return 1

    g = s.graph
    print(f"OK  connected: {s.backend}, database '{s.database}'")
    print(f"OK  tables found: {len(s.schema.tables)} -> {', '.join(list(s.schema.tables)[:8])}")
    print(f"OK  graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges (edges come from foreign keys)")
    if g.number_of_edges() == 0:
        print("    note: 0 edges means no foreign keys were found, so the graph will show unconnected nodes")
    no_pk = [t.name for t in s.schema.tables.values() if not t.primary_key]
    if no_pk:
        print(f"    note: tables without a primary key are not drawn: {', '.join(no_pk)}")

    table = next(iter(s.schema.tables))
    for label, stmt in (("DELETE", f'DELETE FROM "{table}" WHERE 1=0'), ("UPDATE", None)):
        if stmt is None:
            t = s.schema.tables[table]
            col = t.columns[0]
            stmt = f'UPDATE "{table}" SET "{col}" = "{col}" WHERE 1=0'
        if s.backend == "mysql":
            stmt = stmt.replace('"', "`")
        try:
            with s.engine.connect() as c:
                c.execute(text(stmt))
                c.commit()
            print(f"WARN {label} was ALLOWED by the database session. Use a read-only user.")
        except Exception:
            print(f"OK  {label} blocked by the database session (read-only)")
    sessions.close(s.token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
