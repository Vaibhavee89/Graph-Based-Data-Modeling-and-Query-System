"""Unit tests for GuardrailService."""
import pytest
from unittest.mock import Mock, patch
from app.services.guardrail_service import GuardrailService


@pytest.mark.unit
class TestGuardrailService:
    """Test cases for GuardrailService."""

    @patch('app.services.guardrail_service.LLMService')
    def test_validate_domain_query_valid(self, mock_llm_class):
        """Test validation of valid domain query."""
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.generate_structured.return_value = {
            "is_valid": True,
            "reason": "Query is about orders"
        }
        mock_llm_class.return_value = mock_llm

        service = GuardrailService()
        result = service.validate_query("Which customers have the most orders?")

        assert result.is_valid is True
        assert "order" in result.reason.lower()
        mock_llm.generate_structured.assert_called_once()

    @patch('app.services.guardrail_service.LLMService')
    def test_validate_domain_query_invalid(self, mock_llm_class):
        """Test validation of invalid off-topic query."""
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.generate_structured.return_value = {
            "is_valid": False,
            "reason": "Query is about weather, not business data"
        }
        mock_llm_class.return_value = mock_llm

        service = GuardrailService()
        result = service.validate_query("What is the weather today?")

        assert result.is_valid is False
        assert "weather" in result.reason.lower()

    @patch('app.services.guardrail_service.LLMService')
    def test_validate_greeting(self, mock_llm_class):
        """Test validation of greeting query."""
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.generate_structured.return_value = {
            "is_valid": True,
            "reason": "Greeting is acceptable"
        }
        mock_llm_class.return_value = mock_llm

        service = GuardrailService()
        result = service.validate_query("Hello!")

        assert result.is_valid is True

    @patch('app.services.guardrail_service.LLMService')
    def test_validate_edge_case_sql_injection(self, mock_llm_class):
        """Test that SQL injection attempts are rejected."""
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.generate_structured.return_value = {
            "is_valid": False,
            "reason": "Query contains suspicious SQL patterns"
        }
        mock_llm_class.return_value = mock_llm

        service = GuardrailService()
        result = service.validate_query("'; DROP TABLE orders; --")

        assert result.is_valid is False

    @patch('app.services.guardrail_service.LLMService')
    def test_validate_llm_error_handling(self, mock_llm_class):
        """Test error handling when LLM fails."""
        # Mock LLM error
        mock_llm = Mock()
        mock_llm.generate_structured.side_effect = Exception("LLM API error")
        mock_llm_class.return_value = mock_llm

        service = GuardrailService()
        result = service.validate_query("Test query")

        # Should return invalid result on error
        assert result.is_valid is False
        assert "error" in result.reason.lower()

    @patch('app.services.guardrail_service.LLMService')
    def test_validate_empty_query(self, mock_llm_class):
        """Test validation of empty query."""
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.generate_structured.return_value = {
            "is_valid": False,
            "reason": "Query is empty"
        }
        mock_llm_class.return_value = mock_llm

        service = GuardrailService()
        result = service.validate_query("")

        assert result.is_valid is False

    @patch('app.services.guardrail_service.LLMService')
    def test_validate_business_entities(self, mock_llm_class):
        """Test validation of queries about business entities."""
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.generate_structured.return_value = {
            "is_valid": True,
            "reason": "Query is about business entities"
        }
        mock_llm_class.return_value = mock_llm

        service = GuardrailService()

        # Test various entity queries
        queries = [
            "Show me customer 310000108",
            "Find all orders from last month",
            "Which invoices are unpaid?",
            "Trace delivery DEL-001"
        ]

        for query in queries:
            result = service.validate_query(query)
            assert result.is_valid is True
