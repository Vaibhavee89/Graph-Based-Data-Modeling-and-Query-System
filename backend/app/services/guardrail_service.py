"""Guardrail service - Validates queries are domain-related."""
import logging
from typing import Optional

from app.services.llm_service import LLMService
from app.schemas.query import GuardrailResult

logger = logging.getLogger(__name__)


class GuardrailService:
    """Service for validating query domain relevance."""

    def __init__(self):
        """Initialize guardrail service."""
        self.llm = LLMService()

    def validate_query(self, query: str, domain_description: Optional[str] = None) -> GuardrailResult:
        """
        Validate if query is related to business data domain.

        Args:
            query: User's natural language query

        Returns:
            GuardrailResult with validation decision
        """
        # Handle greetings and meta queries
        query_lower = query.lower().strip()

        # Allow greetings and basic interactions
        greetings = ['hi', 'hello', 'hey', 'thanks', 'thank you', 'ok', 'okay']
        if query_lower in greetings:
            return GuardrailResult(
                is_valid=True,
                reason="Greeting or acknowledgment"
            )

        # Create validation prompt
        system_prompt = """You are a domain validator for a business data analysis system.

The system contains data about:
- Customers (business partners)
- Products (items for sale)
- Orders (sales orders)
- Invoices (billing documents)
- Payments (payment transactions)
- Deliveries (shipments)
- Addresses (customer and delivery locations)

Your job is to determine if a user query is related to this business domain."""

        if domain_description:
            system_prompt = (
                "You are a domain validator for a data analysis system.\n\n"
                "The connected database contains these tables:\n"
                f"{domain_description}\n\n"
                "Your job is to determine if a user query can be answered from this data."
            )

        topic = (
            "the data in the connected database described above"
            if domain_description
            else "business data analysis (customers, orders, products, invoices, payments, deliveries)"
        )
        entities = (
            "the tables described above"
            if domain_description
            else "customers, orders, products, invoices, payments, deliveries"
        )

        validation_prompt = f"""User query: "{query}"

Is this query related to {topic}?

Consider related:
- Questions about entities ({entities})
- Requests to find, list, count, or analyze data
- Questions about relationships (which customer has most orders, trace invoice flow, etc.)
- Requests for statistics or aggregations
- Questions about data quality or anomalies

Consider NOT related:
- General knowledge questions (what is the capital of France?)
- Programming or technical questions unrelated to the data
- Personal questions about the user or assistant
- Questions about topics outside the business domain

Return JSON with this structure:
{{
    "is_valid": true/false,
    "reason": "Brief explanation"
}}"""

        try:
            result = self.llm.generate_structured(
                prompt=validation_prompt,
                system=system_prompt
            )

            return GuardrailResult(
                is_valid=result.get('is_valid', False),
                reason=result.get('reason', 'Unknown')
            )

        except Exception as e:
            logger.exception("Guardrail validation error")
            # Fail closed: if the domain check can't run, don't let the query through
            return GuardrailResult(
                is_valid=False,
                reason="Validation error, query rejected",
                service_error=True,
            )

    def is_domain_related(self, query: str) -> bool:
        """
        Simple boolean check if query is domain-related.

        Args:
            query: User query

        Returns:
            True if domain-related, False otherwise
        """
        result = self.validate_query(query)
        return result.is_valid
