"""
Comprehensive Test Suite for AI Itinerary Generation, Groq Provider,
Route Optimization, and Conversational Refinement.
"""

import asyncio
import json
import unittest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from app.schemas.trips import (
    TripCreate,
    ItineraryItem,
    ItineraryDay,
    ItineraryResponse,
    ItineraryRefinementRequest,
    ItineraryRefinementResponse,
)
from app.services.llm_provider import (
    LLMProvider,
    MockLLMProvider,
    LLMProviderError,
    LLMProviderNotConfiguredError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMResponseParsingError,
    get_llm_provider,
    clean_json_markdown,
)
from app.services.groq_provider import GroqProvider
from app.services import prompt_builder, route_optimizer, itinerary_service, trip_service


class TestLLMProviderArchitecture(unittest.TestCase):
    """Test LLM Provider base, factory, and error hierarchy."""

    def test_clean_json_markdown(self):
        wrapped = "```json\n{\"destination\": \"Rome\"}\n```"
        cleaned = clean_json_markdown(wrapped)
        self.assertEqual(cleaned, "{\"destination\": \"Rome\"}")

    def test_mock_llm_provider_generation(self):
        mock_p = MockLLMProvider()
        self.assertTrue(mock_p.is_configured())
        self.assertEqual(mock_p.get_provider_name(), "mock")

        res_text = asyncio.run(mock_p.generate("test prompt"))
        parsed = json.loads(res_text)
        self.assertIn("days", parsed)
        self.assertEqual(len(parsed["days"]), 1)

    def test_groq_provider_missing_key_raises_error(self):
        groq_p = GroqProvider(api_key="")
        self.assertFalse(groq_p.is_configured())
        with self.assertRaises(LLMProviderNotConfiguredError):
            asyncio.run(groq_p.generate("generate trip"))

    def test_groq_provider_placeholder_key_treated_as_unconfigured(self):
        groq_p = GroqProvider(api_key="gsk_your_groq_api_key_here")
        self.assertFalse(groq_p.is_configured())
        with self.assertRaises(LLMProviderNotConfiguredError):
            asyncio.run(groq_p.generate("generate trip"))

    def test_factory_returns_mock_provider(self):
        provider = get_llm_provider("mock")
        self.assertIsInstance(provider, MockLLMProvider)


class TestPromptEngineeringLayer(unittest.TestCase):
    """Test enhanced prompt builder with vibes, pacing, and refinement prompt."""

    def setUp(self):
        self.today = date.today()
        self.trip_data = {
            "destination": "Kyoto, Japan",
            "start_date": self.today + timedelta(days=10),
            "end_date": self.today + timedelta(days=14),
            "budget": 2000.0,
            "currency": "USD",
            "traveller_count": 2,
            "travel_style": "Cultural",
            "interests": ["Culture", "History"],
            "dietary_preference": "Vegetarian",
            "travel_pace": "Relaxed",
            "mobility_requirements": "None",
            "notes": "Looking forward to temple gardens.",
        }

    def test_prompt_includes_vibe_and_time_slots(self):
        prompt = prompt_builder.build_user_prompt(self.trip_data)
        self.assertIn("Kyoto, Japan", prompt)
        self.assertIn("TRAVEL VIBE (Cultural & Historical)", prompt)
        self.assertIn("Relaxed", prompt)
        self.assertIn("DIETARY MANDATE: The traveler is Vegetarian", prompt)
        self.assertIn("TIME-SLOT REQUIREMENTS", prompt)
        self.assertIn("Morning", prompt)
        self.assertIn("Afternoon", prompt)
        self.assertIn("Evening", prompt)

    def test_adventure_vibe(self):
        data = dict(self.trip_data)
        data["travel_style"] = "Adventure"
        prompt = prompt_builder.build_user_prompt(data)
        self.assertIn("TRAVEL VIBE (Adventure)", prompt)

    def test_refinement_prompt_builder(self):
        mock_itinerary = {
            "days": [
                {"day_number": 1, "theme": "Historic Shrines"},
                {"day_number": 2, "theme": "Bamboo Forest & River"},
            ]
        }
        ref_prompt = prompt_builder.build_refinement_prompt(
            trip_data=self.trip_data,
            current_itinerary=mock_itinerary,
            action="more_relaxed",
            day_number=1,
            feedback="Less walking on day 1",
        )
        self.assertIn("REFINEMENT REQUEST FOR KYOTO, JAPAN ITINERARY", ref_prompt)
        self.assertIn("make the schedule noticeably more relaxed", ref_prompt.lower())
        self.assertIn("Less walking on day 1", ref_prompt)
        self.assertIn("Only Day 1 is being refined", ref_prompt)


class TestRouteAndScheduleOptimizer(unittest.TestCase):
    """Test route and schedule optimizer."""

    def test_optimize_schedule_groups_time_slots(self):
        raw_itinerary = {
            "destination": "Kyoto",
            "days": [
                {
                    "day_number": 1,
                    "theme": "Historic Temples",
                    "items": [
                        {"title": "Kinkaku-ji", "time_slot": "Morning", "estimated_cost": 10.0},
                        {"title": "Gion Walk", "time_slot": "Evening", "estimated_cost": 25.0},
                        {"title": "Fushimi Inari", "time_slot": "Afternoon", "estimated_cost": 0.0},
                    ],
                }
            ],
        }

        optimized = route_optimizer.optimize_itinerary_schedule(raw_itinerary, travel_pace="Moderate")
        self.assertTrue(optimized["route_optimized"])
        self.assertEqual(optimized["total_estimated_cost"], 35.0)

        day1 = optimized["days"][0]
        # Reordered chronologically: Morning -> Afternoon -> Evening
        self.assertEqual(day1["items"][0]["title"], "Kinkaku-ji")
        self.assertEqual(day1["items"][0]["time_slot"], "Morning")
        self.assertEqual(day1["items"][1]["title"], "Fushimi Inari")
        self.assertEqual(day1["items"][1]["time_slot"], "Afternoon")
        self.assertEqual(day1["items"][2]["title"], "Gion Walk")
        self.assertEqual(day1["items"][2]["time_slot"], "Evening")

        # Check transit buffer attached
        self.assertIn("transit_info", day1["items"][0])
        self.assertTrue(len(day1["morning_items"]) == 1)
        self.assertTrue(len(day1["afternoon_items"]) == 1)
        self.assertTrue(len(day1["evening_items"]) == 1)

    def test_relaxed_pace_limits_activities(self):
        raw_itinerary = {
            "destination": "Paris",
            "days": [
                {
                    "day_number": 1,
                    "items": [{"title": f"Stop {i}"} for i in range(6)],
                }
            ],
        }
        optimized = route_optimizer.optimize_itinerary_schedule(raw_itinerary, travel_pace="Relaxed")
        day1 = optimized["days"][0]
        # Relaxed pace caps items at 3 per day
        self.assertLessEqual(len(day1["items"]), 3)


class TestItineraryServiceOrchestrationAndRefinement(unittest.TestCase):
    """Test full async orchestration and conversational refinement."""

    def setUp(self):
        self.today = date.today()
        self.trip_in = TripCreate(
            destination="Zurich, Switzerland",
            start_date=self.today + timedelta(days=20),
            end_date=self.today + timedelta(days=22),
            budget=3000.0,
            currency="CHF",
            traveller_count=2,
            travel_style="Nature-focused",
            interests=["Nature", "Relaxation"],
            dietary_preference="No preference",
            travel_pace="Moderate",
            mobility_requirements="None",
            notes="Love lakeside strolls.",
        )
        self.created_trip = trip_service.create_trip(self.trip_in)

    def test_async_generation_with_mock_provider(self):
        mock_provider = MockLLMProvider()
        itinerary = asyncio.run(
            itinerary_service.generate_itinerary_for_trip(self.created_trip.id, provider=mock_provider)
        )
        self.assertEqual(itinerary.trip_id, self.created_trip.id)
        self.assertTrue(itinerary.route_optimized)
        self.assertEqual(itinerary.provider, "mock")
        self.assertGreater(len(itinerary.days), 0)

        # Verify saved in repository
        saved = itinerary_service.get_saved_itinerary(self.created_trip.id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.trip_id, self.created_trip.id)

    def test_refine_itinerary_single_day(self):
        mock_provider = MockLLMProvider()
        # Generate initial itinerary
        asyncio.run(
            itinerary_service.generate_itinerary_for_trip(self.created_trip.id, provider=mock_provider)
        )

        # Refine day 1
        refine_req = ItineraryRefinementRequest(
            action="more_relaxed",
            day_number=1,
            feedback="Make day 1 more focused on tranquil lakeside resting.",
        )

        refine_res = asyncio.run(
            itinerary_service.refine_itinerary_for_trip(
                self.created_trip.id, refine_req, provider=mock_provider
            )
        )
        self.assertIsInstance(refine_res, ItineraryRefinementResponse)
        self.assertEqual(refine_res.trip_id, self.created_trip.id)
        self.assertIn("more_relaxed", refine_res.action)
        self.assertEqual(refine_res.refined_day, 1)


if __name__ == "__main__":
    unittest.main()
