"""LLM service - Wrapper for Claude API with Groq fallback."""
import anthropic
from groq import Groq
from typing import Optional, Dict, Any
import json

from app.config import settings


class LLMService:
    """Service for interacting with LLM APIs (Anthropic Claude + Groq fallback)."""

    def __init__(self):
        """Initialize LLM service with both providers."""
        # Primary: Anthropic Claude
        self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.anthropic_model = settings.llm_model

        # Fallback: Groq
        self.groq_client = None
        self.groq_model = settings.groq_model
        if settings.groq_api_key and settings.use_groq_fallback:
            try:
                self.groq_client = Groq(api_key=settings.groq_api_key)
                print("✓ Groq fallback enabled")
            except Exception as e:
                print(f"Warning: Could not initialize Groq client: {e}")

        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature

    def _call_anthropic(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Call Anthropic Claude API."""
        message = self.anthropic_client.messages.create(
            model=self.anthropic_model,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
            system=system or "",
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    def _call_groq(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Call Groq API as fallback."""
        if not self.groq_client:
            raise Exception("Groq client not initialized")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        )
        return response.choices[0].message.content

    def generate_completion(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a completion with automatic fallback.

        Args:
            prompt: User prompt
            system: System prompt (instructions)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        # Try Anthropic first
        try:
            return self._call_anthropic(prompt, system, temperature, max_tokens)
        except anthropic.APIError as e:
            error_msg = str(e)
            print(f"Anthropic API error: {error_msg}")

            # Check if we should fallback to Groq
            if self.groq_client and settings.use_groq_fallback:
                # Fallback for credit issues, rate limits, or auth errors
                if any(keyword in error_msg.lower() for keyword in [
                    'credit', 'balance', 'billing', 'rate_limit',
                    'authentication', 'invalid', '401', '429', '402'
                ]):
                    print("→ Falling back to Groq...")
                    try:
                        result = self._call_groq(prompt, system, temperature, max_tokens)
                        print("✓ Groq fallback successful")
                        return result
                    except Exception as groq_error:
                        print(f"Groq fallback also failed: {groq_error}")
                        raise Exception(f"Both Anthropic and Groq failed. Anthropic: {error_msg}, Groq: {groq_error}")

            # No fallback available or shouldn't fallback
            raise Exception(f"LLM API error: {error_msg}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise Exception(f"LLM error: {str(e)}")

    def generate_structured(
        self,
        prompt: str,
        system: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured output (JSON) with fallback.

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
            # Sometimes LLMs wrap JSON in markdown code blocks
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
        Multi-turn chat with fallback.

        Args:
            messages: List of messages [{"role": "user"|"assistant", "content": "..."}]
            system: System prompt

        Returns:
            Assistant's response
        """
        # For now, just use the single-turn method with the last user message
        # This is a simplified implementation
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            raise ValueError("No user messages found")

        last_message = user_messages[-1]["content"]
        return self.generate_completion(last_message, system=system)
