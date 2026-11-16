"""Validate user-supplied database URLs before the server connects to them."""

import ipaddress
import re
import socket
from typing import Tuple
from urllib.parse import quote, unquote

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


def _normalize_raw_url(raw: str) -> str:
    """
    People often paste a URL whose password contains an '@'. Because '@' also separates the
    credentials from the host, that breaks parsing. Treat the LAST '@' in the authority as the
    separator and percent-encode the password, so such URLs just work.
    """
    raw = raw.strip()
    m = re.match(r"^([A-Za-z][A-Za-z0-9+.\-]*://)([^/?#]*)(.*)$", raw, re.S)
    if not m:
        return raw
    scheme, authority, rest = m.groups()
    if authority.count("@") <= 1:
        return raw
    userinfo, host = authority.rsplit("@", 1)
    user, sep, password = userinfo.partition(":")
    if not sep:
        return raw
    return f"{scheme}{user}:{quote(unquote(password), safe='')}@{host}{rest}"


def parse_and_check(raw_url: str) -> Tuple[URL, str, str]:
    """
    Returns (sqlalchemy_url, sqlglot_dialect, backend_name).

    Raises UnsafeURL with a user-safe message.
    """
    try:
        url = make_url(_normalize_raw_url(raw_url))
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
        raise UnsafeURL(
            "Could not resolve the database host. If your password contains special characters "
            "such as @, / or #, encode them (for example @ becomes %40)."
        )
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
