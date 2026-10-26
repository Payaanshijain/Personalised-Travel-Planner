"""
AI Provider Integration Service (Activity 3.3).
Handles API communication with Google Gemini, OpenAI, or other LLMs.
Uses Python standard library (urllib.request) to avoid broken external dependencies.
"""

import json
import logging
import re
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from app import config

logger = logging.getLogger(__name__)


class AIProviderNotConfiguredError(Exception):
    """Raised when an AI call is attempted without an API key configured."""
    pass


class AIProviderError(Exception):
    """Raised when an AI provider returns an error or produces invalid output."""
    pass


def clean_json_text(text: str) -> str:
    """Strip markdown code fence blocks if the AI model wrapped its JSON response."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def call_gemini_api(api_key: str, system_prompt: str, user_prompt: str, model_name: Optional[str] = None) -> str:
    """Call Google Gemini generateContent REST API."""
    model = model_name or "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_prompt}\n\n{user_prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
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
        with urllib.request.urlopen(req, timeout=40) as response:
            result = json.loads(response.read().decode("utf-8"))
            candidates = result.get("candidates", [])
            if not candidates:
                raise AIProviderError("Gemini returned an empty candidates list.")
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return text
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        logger.error("Gemini HTTP Error %s: %s", e.code, error_body)
        raise AIProviderError(f"Gemini API returned HTTP {e.code}. Check your API key and quota.") from e
    except urllib.error.URLError as e:
        logger.error("Network error reaching Gemini: %s", e.reason)
        raise AIProviderError(f"Network error communicating with Gemini: {e.reason}") from e


def call_openai_api(api_key: str, system_prompt: str, user_prompt: str, model_name: Optional[str] = None) -> str:
    """Call OpenAI Chat Completions REST API."""
    model = model_name or "gpt-4o-mini"
    url = "https://api.openai.com/v1/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.4,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            result = json.loads(response.read().decode("utf-8"))
            choices = result.get("choices", [])
            if not choices:
                raise AIProviderError("OpenAI returned no choices.")
            return choices[0].get("message", {}).get("content", "")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        logger.error("OpenAI HTTP Error %s: %s", e.code, error_body)
        raise AIProviderError(f"OpenAI API returned HTTP {e.code}. Check your API key.") from e
    except urllib.error.URLError as e:
        raise AIProviderError(f"Network error communicating with OpenAI: {e.reason}") from e


def generate_itinerary_with_ai(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """
    Orchestrates the AI provider call based on backend configuration.
    Validates presence of API key. Raises AIProviderNotConfiguredError if missing.
    """
    api_key = config.AI_API_KEY
    provider = config.AI_PROVIDER

    if not api_key:
        raise AIProviderNotConfiguredError(
            "AI Provider API key is not configured. "
            "Please set AI_API_KEY (or GEMINI_API_KEY / OPENAI_API_KEY) in backend/.env to enable live AI generation."
        )

    raw_response_text = ""
    if provider == "openai":
        raw_response_text = call_openai_api(api_key, system_prompt, user_prompt, config.AI_MODEL)
    else:
        # Default to Gemini
        raw_response_text = call_gemini_api(api_key, system_prompt, user_prompt, config.AI_MODEL)

    cleaned_text = clean_json_text(raw_response_text)
    try:
        parsed_data = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse AI output as JSON: %s", cleaned_text[:200])
        raise AIProviderError("The AI provider did not return valid JSON. Please retry.") from e

    return parsed_data
