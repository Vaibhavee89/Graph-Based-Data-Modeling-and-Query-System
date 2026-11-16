"""Schema introspection that works on any SQLAlchemy-supported database."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy import inspect
from sqlalchemy.engine import Engine


@dataclass
class ForeignKey:
    columns: List[str]
    ref_table: str
    ref_columns: List[str]


@dataclass
class TableInfo:
    name: str
    columns: List[str]
    column_types: Dict[str, str]
    primary_key: List[str]
    foreign_keys: List[ForeignKey] = field(default_factory=list)


@dataclass
class SchemaInfo:
    tables: Dict[str, TableInfo]

    def to_prompt(self) -> str:
        """Compact schema description for the LLM."""
        lines = []
        for t in self.tables.values():
            cols = ", ".join(
                f"{c} {t.column_types.get(c, '')}".strip()
                + (" PK" if c in t.primary_key else "")
                for c in t.columns
            )
            lines.append(f"- {t.name} ({cols})")
            for fk in t.foreign_keys:
                lines.append(
                    f"    FK: {t.name}({', '.join(fk.columns)}) -> "
                    f"{fk.ref_table}({', '.join(fk.ref_columns)})"
                )
        return "\n".join(lines)


def introspect(engine: Engine, max_tables: int) -> SchemaInfo:
    insp = inspect(engine)
    names = sorted(insp.get_table_names())[:max_tables]
    known = set(names)
    tables: Dict[str, TableInfo] = {}
    for name in names:
        cols = insp.get_columns(name)
        pk = insp.get_pk_constraint(name).get("constrained_columns") or []
        fks = []
        for fk in insp.get_foreign_keys(name):
            ref = fk.get("referred_table")
            if (
                ref in known
                and fk.get("constrained_columns")
                and fk.get("referred_columns")
            ):
                fks.append(
                    ForeignKey(
                        columns=list(fk["constrained_columns"]),
                        ref_table=ref,
                        ref_columns=list(fk["referred_columns"]),
                    )
                )
        tables[name] = TableInfo(
            name=name,
            columns=[c["name"] for c in cols],
            column_types={c["name"]: str(c["type"]) for c in cols},
            primary_key=list(pk),
            foreign_keys=fks,
        )
    return SchemaInfo(tables=tables)
