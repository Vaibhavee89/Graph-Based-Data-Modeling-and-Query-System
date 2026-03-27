"""Query API router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.graph_store import get_graph
from app.services.query_service import QueryService
from app.schemas.query import QueryRequest, QueryResponse


router = APIRouter()


def get_query_service(
    db: Session = Depends(get_db)
) -> QueryService:
    """Get query service instance."""
    graph = get_graph()
    return QueryService(db, graph)


@router.post("/chat", response_model=QueryResponse)
async def chat(
    request: QueryRequest,
    service: QueryService = Depends(get_query_service)
):
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
    - Timeout protection (30 seconds max)
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
        "llm_available": True  # TODO: Actually check LLM connectivity
    }
