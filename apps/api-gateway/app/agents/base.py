from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from openai import OpenAI
from anthropic import Anthropic
import json

from app.utils import sanitize_prompt
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


class BaseAgent(ABC):
    """Base class for all LLM-powered agents."""

    def __init__(self, model: str = "gpt-4", provider: str = "openai"):
        self.model = model
        self.provider = provider
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if self.provider == "openai":
                self._client = OpenAI(api_key=settings.openai_api_key)
            elif self.provider == "anthropic":
                self._client = Anthropic(api_key=settings.anthropic_api_key)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        return self._client

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call LLM with retry logic and error handling."""
        try:
            if self.provider == "openai":
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = self.client.chat.completions.create(
                    model=self.model, messages=messages, temperature=0.1
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}],
                    system=system_prompt or "",
                )
                return response.content[0].text

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM with error handling."""
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response content: {response}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")

    def _sanitize_prompt(self, prompt: str) -> str:
        """Validate and escape user-provided prompt."""
        return sanitize_prompt(prompt)

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the agent's main functionality."""
        pass
