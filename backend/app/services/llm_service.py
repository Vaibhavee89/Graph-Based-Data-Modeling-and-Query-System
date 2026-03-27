"""LLM service - Wrapper for Claude API."""
import anthropic
from typing import Optional, Dict, Any
import json

from app.config import settings


class LLMService:
    """Service for interacting with Claude API."""

    def __init__(self):
        """Initialize LLM service."""
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature

    def generate_completion(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a completion from Claude.

        Args:
            prompt: User prompt
            system: System prompt (instructions)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=system or "",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text

        except anthropic.APIError as e:
            print(f"Claude API error: {e}")
            raise Exception(f"LLM API error: {str(e)}")

    def generate_structured(
        self,
        prompt: str,
        system: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured output (JSON) from Claude.

        Args:
            prompt: User prompt
            system: System prompt
            schema: JSON schema for structured output (optional)

        Returns:
            Parsed JSON object
        """
        try:
            # Add instruction to return JSON
            full_system = (system or "") + "\n\nReturn your response as valid JSON only, no other text."

            response_text = self.generate_completion(
                prompt=prompt,
                system=full_system,
                temperature=0.0,  # Use 0 temperature for structured output
            )

            # Parse JSON from response
            # Sometimes Claude wraps JSON in markdown code blocks
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            return json.loads(response_text)

        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Response was: {response_text}")
            raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            print(f"Structured generation error: {e}")
            raise

    def chat(
        self,
        messages: list[Dict[str, str]],
        system: Optional[str] = None,
    ) -> str:
        """
        Multi-turn chat with Claude.

        Args:
            messages: List of messages [{"role": "user"|"assistant", "content": "..."}]
            system: System prompt

        Returns:
            Assistant's response
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system or "",
                messages=messages
            )

            return message.content[0].text

        except anthropic.APIError as e:
            print(f"Claude API error: {e}")
            raise Exception(f"LLM API error: {str(e)}")
