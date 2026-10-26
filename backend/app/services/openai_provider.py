"""
OpenAI LLM Provider Implementation.
Conforms to LLMProvider interface for OpenAI models.
"""

import asyncio
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from app import config
from app.services.llm_provider import (
    LLMProvider,
    LLMProviderError,
    LLMProviderNotConfiguredError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMResponseParsingError,
    clean_json_markdown,
)

logger = logging.getLogger(__name__)

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class OpenAIProvider(LLMProvider):

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.api_key = (api_key or config.OPENAI_API_KEY or config.AI_API_KEY or "").strip()
        self.model_name = (model_name or config.AI_MODEL or DEFAULT_OPENAI_MODEL).strip()
        self.timeout = timeout or config.LLM_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your-"))

    def get_provider_name(self) -> str:
        return "openai"

    def get_model_name(self) -> str:
        return self.model_name

    def _sync_request(self, system_prompt: str, user_prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": (options or {}).get("temperature", 0.3),
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                choices = result.get("choices", [])
                if not choices:
                    raise LLMResponseParsingError("OpenAI returned empty choices.")
                return clean_json_markdown(choices[0].get("message", {}).get("content", ""))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise LLMRateLimitError("OpenAI rate limit exceeded.") from e
            elif e.code == 401:
                raise LLMProviderError("Invalid OpenAI API key.") from e
            raise LLMProviderError(f"OpenAI API returned HTTP {e.code}.") from e
        except Exception as e:
            raise LLMProviderError(f"OpenAI request failed: {e}") from e

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self.is_configured():
            raise LLMProviderNotConfiguredError(
                "OPENAI_API_KEY is not configured in backend/.env. "
                "Set OPENAI_API_KEY=sk-... in backend/.env to use OpenAI."
            )
        sys_p = system_prompt or "You are an expert travel planner. Output valid JSON only."
        return await asyncio.to_thread(self._sync_request, sys_p, prompt, options)
