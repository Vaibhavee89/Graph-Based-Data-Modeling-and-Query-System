"""Validation for LLM-generated SQL: single read-only SELECT over known tables."""
from typing import Optional, Set, Tuple

import sqlglot
from sqlglot import exp

ALLOWED_TABLES: Set[str] = {
    "customers", "products", "orders", "order_items",
    "invoices", "payments", "deliveries", "addresses",
}

# Functions that read files, sleep, or reach outside the query.
BLOCKED_FUNCTIONS: Set[str] = {
    "pg_sleep", "pg_sleep_for", "pg_sleep_until", "pg_read_file",
    "pg_read_binary_file", "pg_ls_dir", "pg_stat_file", "lo_import",
    "lo_export", "lo_get", "dblink", "dblink_exec", "set_config",
    "current_setting", "pg_terminate_backend", "pg_cancel_backend",
    "pg_reload_conf", "query_to_xml", "table_to_xml", "xpath",
}


def validate_sql(sql: str, max_limit: int = 1000) -> Tuple[Optional[str], Optional[str]]:
    """
    Validate and normalise a generated query.

    Returns (safe_sql, error). On success error is None and safe_sql is the
    re-rendered query with a LIMIT no greater than max_limit.
    """
    if not sql or not sql.strip():
        return None, "Empty SQL"

    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as e:
        return None, f"SQL could not be parsed: {e}"

    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        return None, "Exactly one statement is allowed"

    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.Subquery)):
        return None, "Only SELECT queries are allowed"

    # SELECT ... INTO creates a table; FOR UPDATE/SHARE takes locks.
    if tree.find(exp.Into):
        return None, "SELECT INTO is not allowed"
    if tree.find(exp.Lock):
        return None, "Row locking is not allowed"

    # Any DML/DDL nested anywhere (e.g. data-modifying CTEs).
    forbidden = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop,
                 exp.Alter, exp.Command, exp.Merge, exp.Copy)
    for node_type in forbidden:
        if tree.find(node_type):
            return None, f"{node_type.__name__} is not allowed"

    # Only known tables (CTE names are fine).
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if table.db or table.catalog:
            return None, f"Schema-qualified table '{table.sql()}' is not allowed"
        if name not in ALLOWED_TABLES and name not in cte_names:
            return None, f"Table '{name}' is not allowed"

    for func in tree.find_all(exp.Func):
        name = (func.sql_name() if not isinstance(func, exp.Anonymous) else func.name).lower()
        if name in BLOCKED_FUNCTIONS:
            return None, f"Function '{name}' is not allowed"

    # Cap the result size.
    limit_node = tree.args.get("limit") if isinstance(tree, exp.Select) else None
    if isinstance(tree, exp.Select):
        current = None
        if limit_node is not None:
            expr = limit_node.expression
            if isinstance(expr, exp.Literal) and expr.is_int:
                current = int(expr.name)
        if current is None or current > max_limit:
            tree = tree.limit(max_limit)
    else:
        tree = exp.select("*").from_(tree.subquery("q")).limit(max_limit)

    return tree.sql(dialect="postgres"), None
