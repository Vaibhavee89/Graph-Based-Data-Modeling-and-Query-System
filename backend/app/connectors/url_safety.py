"""Validate user-supplied database URLs before the server connects to them."""

import ipaddress
import socket
from typing import Tuple

from sqlalchemy.engine import URL, make_url

from app.config import settings

# user-facing scheme -> (SQLAlchemy driver URL prefix, sqlglot dialect)
SUPPORTED = {
    "postgresql": ("postgresql+psycopg2", "postgres"),
    "postgres": ("postgresql+psycopg2", "postgres"),
    "mysql": ("mysql+pymysql", "mysql"),
    "mariadb": ("mysql+pymysql", "mysql"),
    "mssql": ("mssql+pymssql", "tsql"),
    "sqlserver": ("mssql+pymssql", "tsql"),
    "oracle": ("oracle+oracledb", "oracle"),
    "sqlite": ("sqlite", "sqlite"),
}

# Query-string options we pass through; anything else could redirect the connection.
ALLOWED_QUERY_KEYS = {
    "sslmode",
    "ssl",
    "ssl_ca",
    "charset",
    "sslrootcert",
    "service_name",
    "channel_binding",
}


class UnsafeURL(ValueError):
    """Raised when a database URL is malformed or not allowed."""


def parse_and_check(raw_url: str) -> Tuple[URL, str, str]:
    """
    Returns (sqlalchemy_url, sqlglot_dialect, backend_name).

    Raises UnsafeURL with a user-safe message.
    """
    try:
        url = make_url(raw_url.strip())
    except Exception:
        raise UnsafeURL("That doesn't look like a valid database URL.")

    scheme = url.drivername.split("+")[0].lower()
    if scheme not in SUPPORTED:
        raise UnsafeURL(
            "Unsupported database type. Supported: PostgreSQL, MySQL/MariaDB, SQL Server, Oracle."
        )
    driver, dialect = SUPPORTED[scheme]

    if scheme == "sqlite":
        if not settings.allow_sqlite_connections:
            raise UnsafeURL("SQLite connections are disabled on this server.")
        return url.set(drivername=driver), dialect, "sqlite"

    if not url.host:
        raise UnsafeURL("The database URL must include a host.")
    if not url.database and scheme != "oracle":
        raise UnsafeURL("The database URL must include a database name.")

    bad = set(url.query) - ALLOWED_QUERY_KEYS
    if bad:
        raise UnsafeURL(f"Connection option(s) not allowed: {', '.join(sorted(bad))}")

    _check_host(url.host)
    return url.set(drivername=driver), dialect, scheme


def _check_host(host: str) -> None:
    """Resolve the host and refuse internal addresses (SSRF protection)."""
    if settings.allow_private_hosts:
        return
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise UnsafeURL("Could not resolve the database host.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise UnsafeURL(
                "Connections to private or internal addresses are not allowed."
            )
