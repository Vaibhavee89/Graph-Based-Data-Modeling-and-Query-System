"""Guardrail service - Validates queries are domain-related."""
from app.services.llm_service import LLMService
from app.schemas.query import GuardrailResult


class GuardrailService:
    """Service for validating query domain relevance."""

    def __init__(self):
        """Initialize guardrail service."""
        self.llm = LLMService()

    def validate_query(self, query: str) -> GuardrailResult:
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

        validation_prompt = f"""User query: "{query}"

Is this query related to business data analysis (customers, orders, products, invoices, payments, deliveries)?

Consider related:
- Questions about entities (customers, orders, products, invoices, payments, deliveries)
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
            print(f"Guardrail validation error: {e}")
            # Default to allowing the query in case of errors
            return GuardrailResult(
                is_valid=True,
                reason=f"Validation error, allowing query: {str(e)}"
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
