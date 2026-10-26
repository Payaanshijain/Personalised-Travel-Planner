"""
Gemini LLM Provider Implementation.
Conforms to LLMProvider interface for Google Gemini models.
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

DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"


class GeminiProvider(LLMProvider):

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.api_key = (api_key or config.GEMINI_API_KEY or config.AI_API_KEY or "").strip()
        self.model_name = (model_name or config.AI_MODEL or DEFAULT_GEMINI_MODEL).strip()
        self.timeout = timeout or config.LLM_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your-"))

    def get_provider_name(self) -> str:
        return "gemini"

    def get_model_name(self) -> str:
        return self.model_name

    def _sync_request(self, system_prompt: str, user_prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_prompt}\n\n{user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": (options or {}).get("temperature", 0.3),
                "responseMimeType": "application/json",
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if not candidates:
                    raise LLMResponseParsingError("Gemini returned empty candidates list.")
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return clean_json_markdown(text)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise LLMRateLimitError("Gemini rate limit exceeded.") from e
            elif e.code == 400 or e.code == 403:
                raise LLMProviderError(f"Gemini API authentication/request error (HTTP {e.code}).") from e
            raise LLMProviderError(f"Gemini API returned HTTP {e.code}.") from e
        except Exception as e:
            raise LLMProviderError(f"Gemini request failed: {e}") from e

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self.is_configured():
            raise LLMProviderNotConfiguredError(
                "GEMINI_API_KEY is not configured in backend/.env. "
                "Set GEMINI_API_KEY=AIza... in backend/.env to use Google Gemini."
            )
        sys_p = system_prompt or "You are an expert travel planner. Output valid JSON only."
        return await asyncio.to_thread(self._sync_request, sys_p, prompt, options)
