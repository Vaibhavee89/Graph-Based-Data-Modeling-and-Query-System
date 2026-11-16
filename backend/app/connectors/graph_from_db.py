"""Build a NetworkX graph from any relational database: rows = nodes, foreign keys = edges."""
import datetime
import decimal
from typing import Any, Dict, List, Tuple

import networkx as nx
from sqlalchemy import MetaData, Table, select, tuple_
from sqlalchemy.engine import Engine

from app.connectors.introspect import SchemaInfo

PALETTE = [
    "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#EC4899",
    "#14B8A6", "#F97316", "#6366F1", "#84CC16", "#06B6D4", "#A855F7",
]
LABEL_HINTS = ("name", "title", "label", "email", "description", "code")
IN_CHUNK = 200


def _jsonable(v: Any) -> Any:
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
        return v.isoformat()
    if isinstance(v, (bytes, bytearray, memoryview)):
        return "<binary>"
    return str(v)


def _node_id(table: str, key: Tuple) -> str:
    return f"{table}:" + "|".join(str(k) for k in key)


def _label(table: str, row: Dict[str, Any], pk: List[str]) -> str:
    for hint in LABEL_HINTS:
        for col, val in row.items():
            if hint in col.lower() and isinstance(val, str) and val.strip():
                return val.strip()[:60]
    return f"{table} {'|'.join(str(row[c]) for c in pk)}"


def build_graph(engine: Engine, schema: SchemaInfo, rows_per_table: int, max_nodes: int) -> nx.DiGraph:
    graph = nx.DiGraph()
    metadata = MetaData()
    metadata.reflect(bind=engine, only=list(schema.tables))
    color = {name: PALETTE[i % len(PALETTE)] for i, name in enumerate(sorted(schema.tables))}

    # (table, tuple(columns)) -> {value tuple: node id}; used to resolve foreign keys
    index: Dict[Tuple[str, Tuple[str, ...]], Dict[Tuple, str]] = {}
    pending_fk_cols = {
        (fk.ref_table, tuple(fk.ref_columns))
        for t in schema.tables.values() for fk in t.foreign_keys
    }

    def add_rows(table_name: str, rows: List[Dict[str, Any]]) -> None:
        info = schema.tables[table_name]
        if not info.primary_key:
            return
        for row in rows:
            if graph.number_of_nodes() >= max_nodes:
                return
            key = tuple(row[c] for c in info.primary_key)
            nid = _node_id(table_name, key)
            if graph.has_node(nid):
                continue
            props = {k: _jsonable(v) for k, v in row.items()}
            graph.add_node(nid, type=table_name, label=_label(table_name, row, info.primary_key),
                           color=color[table_name], properties=props)
            for cols in (c for (t, c) in pending_fk_cols if t == table_name):
                index.setdefault((table_name, cols), {})[tuple(_jsonable(row[c]) for c in cols)] = nid

    with engine.connect() as conn:
        # 1) sample rows from every table
        for name, info in schema.tables.items():
            tbl: Table = metadata.tables[name]
            res = conn.execute(select(tbl).limit(rows_per_table))
            add_rows(name, [dict(r._mapping) for r in res])

        # 2) pull in referenced rows that the sample missed, so edges aren't lost
        for name, info in schema.tables.items():
            for fk in info.foreign_keys:
                ref_info = schema.tables[fk.ref_table]
                if not ref_info.primary_key:
                    continue
                have = index.get((fk.ref_table, tuple(fk.ref_columns)), {})
                missing = set()
                for nid, data in list(graph.nodes(data=True)):
                    if data["type"] != name:
                        continue
                    val = tuple(data["properties"].get(c) for c in fk.columns)
                    if None not in val and val not in have:
                        missing.add(val)
                ref_tbl = metadata.tables[fk.ref_table]
                missing_list = list(missing)[:rows_per_table]
                for i in range(0, len(missing_list), IN_CHUNK):
                    chunk = missing_list[i:i + IN_CHUNK]
                    ref_cols = [ref_tbl.c[c] for c in fk.ref_columns]
                    cond = ref_cols[0].in_([v[0] for v in chunk]) if len(ref_cols) == 1 \
                        else tuple_(*ref_cols).in_(chunk)
                    res = conn.execute(select(ref_tbl).where(cond))
                    add_rows(fk.ref_table, [dict(r._mapping) for r in res])

    # 3) edges from foreign keys
    for nid, data in list(graph.nodes(data=True)):
        info = schema.tables[data["type"]]
        for fk in info.foreign_keys:
            val = tuple(data["properties"].get(c) for c in fk.columns)
            if None in val:
                continue
            target = index.get((fk.ref_table, tuple(fk.ref_columns)), {}).get(val)
            if target:
                graph.add_edge(nid, target, type=f"{info.name}->{fk.ref_table}",
                               label=", ".join(fk.columns), properties={})
    return graph
