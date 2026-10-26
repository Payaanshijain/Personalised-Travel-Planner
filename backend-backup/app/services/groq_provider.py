"""
Groq LLM Provider Implementation (Activity 6 / Requirements).
Interacts with the official Groq API endpoint (https://api.groq.com/openai/v1/chat/completions)
using asynchronous standard library HTTP execution.
Supports structured JSON output mode, configurable model, timeout handling, and safe error masking.
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

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_API_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(LLMProvider):
    """
    Groq API provider implementation conforming to the LLMProvider interface.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.api_key = (config.GROQ_API_KEY if api_key is None else api_key or "").strip()
        self.model_name = (model_name or config.GROQ_MODEL or DEFAULT_GROQ_MODEL).strip()
        self.timeout = timeout or config.LLM_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("gsk_your_"))

    def get_provider_name(self) -> str:
        return "groq"

    def get_model_name(self) -> str:
        return self.model_name

    def _sync_request(self, system_prompt: str, user_prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Synchronous HTTP call executed in a thread pool."""
        opts = options or {}
        temperature = opts.get("temperature", 0.3)
        max_tokens = opts.get("max_tokens", 4096)

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            GROQ_API_ENDPOINT,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Personalised-Travel-Planner-FastAPI/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                res_body = response.read().decode("utf-8")
                parsed = json.loads(res_body)
                choices = parsed.get("choices", [])
                if not choices:
                    raise LLMResponseParsingError("Groq returned a 200 response with empty choices.")
                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    raise LLMResponseParsingError("Groq message content was empty.")
                return clean_json_markdown(content)
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass

            logger.error("Groq API returned HTTP error %s: %s", e.code, error_body[:300])

            if e.code == 401:
                raise LLMProviderError(
                    "Invalid Groq API Key. Please verify GROQ_API_KEY in your backend/.env file."
                ) from e
            elif e.code == 429:
                raise LLMRateLimitError(
                    "Groq API rate limit or quota exceeded. Please wait a moment before retrying."
                ) from e
            elif e.code in (400, 404):
                raise LLMProviderError(
                    f"Groq API request error (HTTP {e.code}): Check if model '{self.model_name}' is supported."
                ) from e
            elif e.code in (500, 502, 503, 504):
                raise LLMProviderError(
                    f"Groq upstream service error (HTTP {e.code}). Please retry in a few moments."
                ) from e
            else:
                raise LLMProviderError(
                    f"Groq API call failed with HTTP status {e.code}."
                ) from e
        except (TimeoutError, urllib.error.URLError) as e:
            if isinstance(e, TimeoutError) or "timed out" in str(e).lower():
                raise LLMTimeoutError(
                    f"Groq API request timed out after {self.timeout} seconds."
                ) from e
            raise LLMProviderError(f"Network error communicating with Groq API: {e}") from e
        except json.JSONDecodeError as e:
            raise LLMResponseParsingError("Groq response was not valid JSON.") from e

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Asynchronously dispatch the Groq chat completion request.
        """
        if not self.is_configured():
            raise LLMProviderNotConfiguredError(
                "GROQ_API_KEY is not configured in backend/.env. "
                "To enable live AI itinerary generation, obtain a free API key from https://console.groq.com/ "
                "and set GROQ_API_KEY=gsk_... in backend/.env."
            )

        sys_p = system_prompt or "You are an expert personalized travel itinerary planner. Output valid JSON only."
        # Run sync request in a thread pool to preserve async event loop responsiveness
        raw_text = await asyncio.to_thread(self._sync_request, sys_p, prompt, options)
        return raw_text
