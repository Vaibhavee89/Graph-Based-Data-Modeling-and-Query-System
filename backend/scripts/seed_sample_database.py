"""Load the sample dataset into an EMPTY Postgres or MySQL database, to test the app against a real server.

    python scripts/seed_sample_database.py "postgresql://user:pass@host:5432/db"

Creates 8 tables (customers, products, addresses, orders, order_items, invoices, payments, deliveries).
Refuses to run if any of those tables already exist, so it never touches your real data.
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sqlalchemy import create_engine, inspect, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.connectors.demo import DDL, LOAD_ORDER  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "sample_data"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    url = make_url(sys.argv[1])
    kind = url.drivername.split("+")[0]
    if kind in ("postgres", "postgresql"):
        url, kind = url.set(drivername="postgresql+psycopg2"), "postgres"
    elif kind in ("mysql", "mariadb"):
        url, kind = url.set(drivername="mysql+pymysql"), "mysql"
    else:
        print("Only PostgreSQL and MySQL/MariaDB are supported by this script.")
        return 2

    engine = create_engine(url)
    existing = set(inspect(engine).get_table_names()) & set(LOAD_ORDER)
    if existing:
        print(f"Refusing: these tables already exist: {', '.join(sorted(existing))}")
        return 1

    with engine.begin() as c:
        for ddl in DDL:
            if kind == "mysql":  # MySQL needs key lengths and ignores inline REFERENCES
                ddl = ddl.replace("TEXT PRIMARY KEY", "VARCHAR(64) PRIMARY KEY")
                ddl = re.sub(r"(\w+_id) TEXT REFERENCES", r"\1 VARCHAR(64) REFERENCES", ddl)
                fks = re.findall(r"(\w+) VARCHAR\(64\) REFERENCES (\w+)\((\w+)\)", ddl)
                ddl = re.sub(r" REFERENCES \w+\(\w+\)", "", ddl)
                if fks:
                    ddl = ddl[:-1] + "".join(f", FOREIGN KEY ({a}) REFERENCES {b}({d})" for a, b, d in fks) + ")"
            c.execute(text(ddl))
        for t in LOAD_ORDER:
            rows = [{k: (v or None) for k, v in r.items()} for r in csv.DictReader(open(DATA / f"{t}.csv"))]
            cols = list(rows[0])
            c.execute(text(f"INSERT INTO {t} ({','.join(cols)}) VALUES ({','.join(':' + k for k in cols)})"), rows)
    print("Sample data loaded into", url.render_as_string(hide_password=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
