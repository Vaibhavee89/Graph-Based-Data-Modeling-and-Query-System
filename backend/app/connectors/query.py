"""Natural-language querying over a user-connected database (any dialect)."""
import logging
from typing import Any, Dict, List

from sqlalchemy import text

from app.config import settings
from app.connectors.sessions import DbSession
from app.schemas.query import QueryResponse
from app.services.guardrail_service import GuardrailService
from app.services.llm_service import LLMService
from app.utils.sql_safety import validate_sql

logger = logging.getLogger(__name__)

DIALECT_NAMES = {"postgres": "PostgreSQL", "mysql": "MySQL", "tsql": "Microsoft SQL Server (T-SQL)",
                 "oracle": "Oracle", "sqlite": "SQLite"}
DIALECT_HINTS = {
    "tsql": "Use TOP n instead of LIMIT. Do not end the statement with a semicolon.",
    "oracle": "Use FETCH FIRST n ROWS ONLY instead of LIMIT. Do not end the statement with a semicolon.",
    "mysql": "Use backticks only if a name needs quoting.",
    "postgres": "Quote identifiers with double quotes only if needed.",
    "sqlite": "Use SQLite-compatible functions only.",
}


def escape_binds(sql: str) -> str:
    """Stop SQLAlchemy text() from treating ':' in literals (e.g. '12:30') as bind parameters."""
    return sql.replace(":", "\\:")


def run_read_only(session: DbSession, sql: str, max_rows: int) -> List[Dict[str, Any]]:
    with session.engine.connect() as conn:
        if session.backend == "oracle":
            conn.exec_driver_sql("SET TRANSACTION READ ONLY")
        result = conn.execute(text(escape_binds(sql)))
        rows = result.fetchmany(max_rows)
        columns = list(result.keys())
        conn.rollback()
    return [dict(zip(columns, r)) for r in rows]


class GenericQueryService:
    def __init__(self, session: DbSession):
        self.session = session
        self.llm = LLMService()
        self.guardrail = GuardrailService()

    def process_query(self, query: str) -> QueryResponse:
        schema_text = self.session.schema.to_prompt()
        verdict = self.guardrail.validate_query(query, domain_description=schema_text)
        if verdict.service_error:
            return QueryResponse(
                success=False,
                message="AI service unavailable",
                answer="The AI service is temporarily unavailable. Please try again in a moment.",
            )
        if not verdict.is_valid:
            return QueryResponse(
                success=False,
                message=f"Query rejected: {verdict.reason}",
                answer="I can only answer questions about the data in the connected database.",
            )
        if verdict.reason == "Greeting or acknowledgment":
            return QueryResponse(success=True, answer="Hello! Ask me anything about your connected data.")

        dialect = self.session.dialect
        system = (
            f"You write SAFE, READ-ONLY {DIALECT_NAMES.get(dialect, dialect)} queries.\n"
            "Rules: a single SELECT statement only; use only the tables and columns listed in the schema; "
            f"include ORDER BY and a row limit. {DIALECT_HINTS.get(dialect, '')}"
        )
        prompt = f'''Database schema:
{schema_text}

User question: "{query}"

Return JSON: {{"sql": "SELECT ...", "explanation": "what the query does"}}'''

        try:
            result = self.llm.generate_structured(prompt, system)
            safe_sql, error = validate_sql(
                result.get("sql", ""), max_limit=settings.max_query_results, dialect=dialect,
                allowed_tables=set(self.session.schema.tables),
            )
            if error:
                logger.warning("Rejected generated SQL: %s", error)
                return QueryResponse(
                    success=False, message="The generated query was not safe to run",
                    answer="I couldn't build a safe query for that question. Please try rephrasing.",
                )
            data = run_read_only(self.session, safe_sql, settings.max_query_results)
        except Exception:
            logger.exception("Generic query error")
            return QueryResponse(
                success=False, message="Could not run the generated query",
                answer="I encountered an error running your query. Please try rephrasing.",
            )

        entities = self._entities(data)
        return QueryResponse(
            success=True, answer=self._format(result.get("explanation", ""), data),
            data=_serializable(data), entities=entities, intent="SQL",
        )

    def _entities(self, rows: List[Dict[str, Any]]) -> List[str]:
        """Link result rows back to graph nodes when a row carries a table's primary key."""
        graph, found = self.session.graph, []
        for row in rows[:50]:
            for t in self.session.schema.tables.values():
                if t.primary_key and all(c in row for c in t.primary_key):
                    nid = f"{t.name}:" + "|".join(str(row[c]) for c in t.primary_key)
                    if graph.has_node(nid):
                        found.append(nid)
        return found

    @staticmethod
    def _format(explanation: str, data: List[Dict[str, Any]]) -> str:
        if not data:
            return "No results found for your query."
        lines = [explanation, "\n**Results:**\n"]
        for i, row in enumerate(data[:10], 1):
            lines.append(f"{i}. " + ", ".join(f"{k}: {v}" for k, v in row.items()))
        if len(data) > 10:
            lines.append(f"\n... and {len(data) - 10} more results")
        return "\n".join(lines)


def _serializable(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from app.connectors.graph_from_db import _jsonable
    return [{k: _jsonable(v) for k, v in r.items()} for r in rows]
