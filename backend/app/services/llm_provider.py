"""
Provider-Based LLM Architecture (Activity 4 / Requirements).
Defines abstract LLMProvider base class, standard exceptions, and provider factory.
Supports async execution, safe error mapping, and pluggable providers (Groq, Gemini, OpenAI, Mock).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import logging
import re

from app import config

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    """Base exception for all LLM provider errors."""
    pass


class LLMProviderNotConfiguredError(LLMProviderError):
    """Raised when an LLM provider is requested but required credentials are missing."""
    pass


class LLMTimeoutError(LLMProviderError):
    """Raised when an LLM provider times out."""
    pass


class LLMRateLimitError(LLMProviderError):
    """Raised when an LLM provider rate limit is encountered (e.g. HTTP 429)."""
    pass


class LLMResponseParsingError(LLMProviderError):
    """Raised when the LLM produces unparsable or malformed output."""
    pass


def clean_json_markdown(text: str) -> str:
    """Strip markdown code fence blocks if the model wrapped its JSON response."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


class LLMProvider(ABC):
    """Abstract Base Class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Asynchronously call the LLM and return the raw generated text response.
        Should handle network timeouts, rate limits, and sanitize credentials.
        """
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if required API credentials exist in environment."""
        raise NotImplementedError

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return unique provider identifier (e.g., 'groq', 'gemini', 'openai', 'mock')."""
        raise NotImplementedError

    @abstractmethod
    def get_model_name(self) -> str:
        """Return model identifier being used."""
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider for unit tests and local verification when external credentials are absent.
    Generates structured, valid JSON itineraries matching the required schema.
    """

    def __init__(self, model_name: str = "mock-travel-planner-v1"):
        self.model_name = model_name

    def is_configured(self) -> bool:
        return True

    def get_provider_name(self) -> str:
        return "mock"

    def get_model_name(self) -> str:
        return self.model_name

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        # Generate a structured valid mock response
        mock_data = {
            "destination": "Test Destination",
            "generation_notes": "Mock generated itinerary for testing.",
            "days": [
                {
                    "day_number": 1,
                    "date": "2026-11-01",
                    "theme": "Cultural Foundations & Local Flavors",
                    "items": [
                        {
                            "id": "act_d1_1",
                            "day_number": 1,
                            "time_slot": "Morning",
                            "start_time": "09:00 AM",
                            "end_time": "11:30 AM",
                            "duration": "2.5 hours",
                            "title": "Historic City Center & Heritage Walk",
                            "description": "Guided walking tour through key historic landmarks with gentle pace.",
                            "location": "Old Town District",
                            "category": "Culture",
                            "estimated_cost": 25.0,
                            "transit_info": "~15 mins walking (estimated)",
                            "notes": "Flat terrain with accessible pedestrian paths.",
                            "accessibility_notes": "Step-free walkways available.",
                            "is_verified": False,
                        },
                        {
                            "id": "act_d1_2",
                            "day_number": 1,
                            "time_slot": "Afternoon",
                            "start_time": "01:30 PM",
                            "end_time": "04:00 PM",
                            "duration": "2.5 hours",
                            "title": "National Museum & Botanical Gardens",
                            "description": "Explore curated local exhibits followed by peaceful garden stroll.",
                            "location": "Central Cultural Park",
                            "category": "Nature",
                            "estimated_cost": 20.0,
                            "transit_info": "~20 mins by local transit (estimated)",
                            "notes": "Audio guides available; benches located throughout.",
                            "accessibility_notes": "Elevator access to all galleries.",
                            "is_verified": False,
                        },
                        {
                            "id": "act_d1_3",
                            "day_number": 1,
                            "time_slot": "Evening",
                            "start_time": "06:30 PM",
                            "end_time": "08:30 PM",
                            "duration": "2 hours",
                            "title": "Scenic Riverside Promenade & Dinner",
                            "description": "Relaxing dinner at a traditional restaurant with dietary accommodations.",
                            "location": "River Walk Promenade",
                            "category": "Dining",
                            "estimated_cost": 45.0,
                            "transit_info": "End of day activities",
                            "notes": "Vegetarian and special dietary menus confirmed on site.",
                            "accessibility_notes": "Accessible restrooms and ramp entrances.",
                            "is_verified": False,
                        },
                    ],
                }
            ],
        }
        return json.dumps(mock_data)


def get_llm_provider(provider_type: Optional[str] = None) -> LLMProvider:
    """
    Factory function to obtain the configured LLM provider instance.
    Checks:
    1. 'groq' -> GroqProvider
    2. 'gemini' -> GeminiProvider
    3. 'openai' -> OpenAIProvider
    4. 'mock' -> MockLLMProvider
    """
    selected = (provider_type or config.AI_PROVIDER).lower()

    if selected == "groq":
        from app.services.groq_provider import GroqProvider
        return GroqProvider()
    elif selected == "gemini":
        from app.services.gemini_provider import GeminiProvider
        return GeminiProvider()
    elif selected == "openai":
        from app.services.openai_provider import OpenAIProvider
        return OpenAIProvider()
    elif selected == "mock":
        return MockLLMProvider()
    else:
        # Default to Groq if groq_key exists or config says groq
        from app.services.groq_provider import GroqProvider
        return GroqProvider()
