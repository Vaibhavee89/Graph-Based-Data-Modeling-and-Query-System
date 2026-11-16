"""Query API router."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.connectors.demo import get_demo
from app.connectors.query import GenericQueryService
from app.connectors.sessions import sessions
from app.core.database import get_db
from app.core.graph_store import get_graph
from app.core.rate_limit import rate_limit_chat
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService

router = APIRouter()


def get_query_service(
    x_session_id: Optional[str] = Header(default=None),
):
    """Query service for the caller's connected database, or the default demo database."""
    if x_session_id:
        session = sessions.get(x_session_id)
        if session is None:
            raise HTTPException(
                status_code=401, detail="Session expired. Please reconnect."
            )
        return GenericQueryService(session)
    legacy = get_graph()
    if legacy.number_of_nodes() == 0:
        demo = get_demo()
        if demo is not None:
            return GenericQueryService(demo)
    db = next(get_db())
    try:
        return DemoQueryServiceHandle(QueryService(db, legacy), db)
    except Exception:
        db.close()
        raise


class DemoQueryServiceHandle:
    """Closes the demo DB session once the query has run."""

    def __init__(self, service: QueryService, db: Session):
        self._service, self._db = service, db

    def process_query(self, query: str):
        try:
            return self._service.process_query(query)
        finally:
            self._db.close()


@router.post(
    "/chat", response_model=QueryResponse, dependencies=[Depends(rate_limit_chat)]
)
def chat(request: QueryRequest, service: QueryService = Depends(get_query_service)):
    """
    Process a natural language query.

    This endpoint accepts natural language queries and returns answers
    with supporting data.

    **Supported query types:**
    - **Aggregation**: "Which products have the most orders?"
    - **Traversal**: "Trace the flow of invoice INV-0001"
    - **Anomaly Detection**: "Find orders with incomplete flows"
    - **Entity Lookup**: "Show me customer CUST-0001"

    **Example queries:**
    - "Which customers have the most orders?"
    - "Show me products in the Electronics category"
    - "Trace invoice 90504248"
    - "Find orders without invoices"
    - "What are the top 5 products by revenue?"

    **Response includes:**
    - Natural language answer
    - Structured data (if applicable)
    - Referenced entity IDs (for linking to graph)
    - Query intent classification

    **Guardrails:**
    - Only domain-related queries accepted
    - Off-topic queries are rejected with explanation
    - SQL injection prevention (read-only queries)
    - Timeout protection (QUERY_TIMEOUT seconds on SQL)
    - Rate limited per client (RATE_LIMIT_PER_MINUTE); returns 429 when exceeded
    """
    return service.process_query(request.query)


@router.get("/health")
async def query_health():
    """
    Health check for query service.

    Returns:
        Status information
    """
    return {
        "status": "healthy",
        "service": "query",
        "llm_available": True,  # TODO: Actually check LLM connectivity
    }
