"""Pydantic schemas for query API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Natural language query request."""

    query: str = Field(
        min_length=1, max_length=2000, description="Natural language query"
    )


class QueryResponse(BaseModel):
    """Query response with answer and data."""

    success: bool = Field(description="Whether query was successful")
    answer: Optional[str] = Field(default=None, description="Natural language answer")
    data: Optional[Any] = Field(default=None, description="Query result data")
    entities: Optional[List[str]] = Field(
        default=None, description="Referenced entity IDs"
    )
    message: Optional[str] = Field(default=None, description="Error or info message")
    intent: Optional[str] = Field(default=None, description="Detected query intent")


class GuardrailResult(BaseModel):
    """Result from guardrail validation."""

    is_valid: bool = Field(description="Whether query is domain-related")
    reason: str = Field(description="Reason for validation result")
    service_error: bool = Field(
        default=False,
        description="True when the check could not run (e.g. LLM unavailable)",
    )


class IntentClassification(BaseModel):
    """Intent classification result."""

    intent: str = Field(
        description="Query intent: AGGREGATION, TRAVERSAL, ANOMALY_DETECTION, ENTITY_LOOKUP"
    )
    confidence: float = Field(description="Confidence score (0-1)")
    reasoning: str = Field(description="Reasoning for classification")
