"""
Itinerary Generation, Orchestration, and Refinement Service (Activity 7, 9, 10).
Orchestrates prompt construction, LLMProvider calls, schema validation, route optimization,
and persistence. Supports conversational refinement and single-day regeneration while preserving
unaffected days and prior context.
"""

from typing import Optional, Dict, Any, List
import json
import logging

from app.database import repo_instance
from app.schemas.trips import (
    TripResponse,
    ItineraryResponse,
    ItineraryDay,
    ItineraryItem,
    ItineraryRefinementRequest,
    ItineraryRefinementResponse,
)
from app.services import prompt_builder, trip_service
from app.services.llm_provider import (
    LLMProvider,
    get_llm_provider,
    LLMProviderError,
    LLMProviderNotConfiguredError,
    LLMResponseParsingError,
    clean_json_markdown,
)
from app.services.route_optimizer import optimize_itinerary_schedule
from app import config

logger = logging.getLogger(__name__)


def _parse_and_map_days(raw_days: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Helper to parse raw dictionary days into standardized dicts before optimization."""
    mapped: List[Dict[str, Any]] = []
    for d in raw_days:
        day_num = int(d.get("day_number", 1))
        items_list: List[Dict[str, Any]] = []
        for it in d.get("items", []):
            cost_val = it.get("estimated_cost")
            try:
                numeric_cost = float(cost_val) if cost_val is not None else 0.0
            except (ValueError, TypeError):
                numeric_cost = 0.0

            items_list.append({
                "id": it.get("id"),
                "day_number": day_num,
                "time_slot": it.get("time_slot", "Morning"),
                "start_time": it.get("start_time"),
                "end_time": it.get("end_time"),
                "duration": it.get("duration"),
                "title": it.get("title", "Scheduled Activity"),
                "description": it.get("description"),
                "location": it.get("location"),
                "category": it.get("category", "General"),
                "estimated_cost": numeric_cost,
                "transit_info": it.get("transit_info"),
                "notes": it.get("notes"),
                "accessibility_notes": it.get("accessibility_notes"),
                "is_verified": bool(it.get("is_verified", False)),
            })
        mapped.append({
            "day_number": day_num,
            "date": d.get("date"),
            "theme": d.get("theme"),
            "items": items_list,
        })
    return mapped


async def generate_itinerary_for_trip(
    trip_id: str,
    provider: Optional[LLMProvider] = None,
) -> ItineraryResponse:
    """
    Orchestrates full AI itinerary generation:
    1. Fetches trip preferences
    2. Builds customized system and user prompts
    3. Calls configured AI provider asynchronously
    4. Parses raw JSON and validates output
    5. Applies route & schedule optimization
    6. Persists itinerary to database
    """
    trip: Optional[TripResponse] = trip_service.get_trip(trip_id)
    if not trip:
        raise ValueError(f"Trip with ID '{trip_id}' not found.")

    trip_dict = trip.model_dump()
    system_prompt = prompt_builder.build_system_prompt()
    user_prompt = prompt_builder.build_user_prompt(trip_dict)

    llm = provider or get_llm_provider()

    # Call LLM provider asynchronously
    raw_text = await llm.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
    )

    cleaned_json = clean_json_markdown(raw_text)
    try:
        ai_data = json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse AI output as JSON: %s", cleaned_json[:200])
        raise LLMResponseParsingError("The AI provider did not return valid JSON. Please retry.") from e

    # Parse days
    raw_days = ai_data.get("days", [])
    if not raw_days:
        raise LLMResponseParsingError("The AI provider generated an empty list of days.")

    parsed_days = _parse_and_map_days(raw_days)

    # Apply route and schedule optimization
    optimized_payload = optimize_itinerary_schedule(
        itinerary_data={
            "destination": trip.destination,
            "days": parsed_days,
        },
        travel_pace=trip.travel_pace,
    )

    # Convert to Pydantic models
    itinerary_days: List[ItineraryDay] = []
    for d in optimized_payload.get("days", []):
        day_items = [ItineraryItem(**it) for it in d.get("items", [])]
        morning = [ItineraryItem(**it) for it in d.get("morning_items", [])]
        afternoon = [ItineraryItem(**it) for it in d.get("afternoon_items", [])]
        evening = [ItineraryItem(**it) for it in d.get("evening_items", [])]

        itinerary_days.append(
            ItineraryDay(
                day_number=d.get("day_number", 1),
                date=d.get("date"),
                theme=d.get("theme"),
                items=day_items,
                morning_items=morning,
                afternoon_items=afternoon,
                evening_items=evening,
            )
        )

    itinerary_res = ItineraryResponse(
        trip_id=trip_id,
        destination=trip.destination,
        total_days=trip.duration_days,
        travel_pace=trip.travel_pace,
        total_estimated_cost=optimized_payload.get("total_estimated_cost", 0.0),
        currency=trip.currency,
        days=itinerary_days,
        ai_generated=True,
        provider=llm.get_provider_name(),
        model_used=llm.get_model_name(),
        generation_notes=ai_data.get("generation_notes", f"Personalized itinerary generated with {llm.get_provider_name()}."),
        route_optimized=True,
    )

    # Save to repository
    repo_instance.save_itinerary(trip_id, itinerary_res.model_dump())
    return itinerary_res


async def refine_itinerary_for_trip(
    trip_id: str,
    refinement_request: ItineraryRefinementRequest,
    provider: Optional[LLMProvider] = None,
) -> ItineraryRefinementResponse:
    """
    Refines or regenerates an existing itinerary based on user action/feedback.
    Preserves unaffected days when refining a single day.
    Guarantees previous itinerary is not lost if generation fails.
    """
    trip: Optional[TripResponse] = trip_service.get_trip(trip_id)
    if not trip:
        raise ValueError(f"Trip with ID '{trip_id}' not found.")

    current_saved = repo_instance.get_itinerary(trip_id)
    if not current_saved:
        raise ValueError(f"No existing itinerary found for trip '{trip_id}'. Please generate an initial itinerary first.")

    llm = provider or get_llm_provider()

    system_prompt = prompt_builder.build_system_prompt()
    user_prompt = prompt_builder.build_refinement_prompt(
        trip_data=trip.model_dump(),
        current_itinerary=current_saved,
        action=refinement_request.action,
        day_number=refinement_request.day_number,
        feedback=refinement_request.feedback,
    )

    # Call provider
    raw_text = await llm.generate(prompt=user_prompt, system_prompt=system_prompt)
    cleaned_json = clean_json_markdown(raw_text)

    try:
        refinement_data = json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse refinement output: %s", cleaned_json[:200])
        raise LLMResponseParsingError("Refinement response was not valid JSON.") from e

    new_raw_days = refinement_data.get("days", [])
    if not new_raw_days:
        raise LLMResponseParsingError("AI refinement did not produce any days.")

    parsed_new_days = _parse_and_map_days(new_raw_days)

    target_day = refinement_request.day_number
    existing_days = current_saved.get("days", [])

    if target_day and len(parsed_new_days) == 1:
        # Single-day refinement: replace only target day, preserve all other days
        combined_days: List[Dict[str, Any]] = []
        replaced = False
        for ex in existing_days:
            if ex.get("day_number") == target_day:
                new_day_payload = parsed_new_days[0]
                new_day_payload["day_number"] = target_day
                combined_days.append(new_day_payload)
                replaced = True
            else:
                combined_days.append(ex)
        if not replaced:
            combined_days.append(parsed_new_days[0])
        final_days_to_optimize = combined_days
    else:
        # Entire itinerary refined
        final_days_to_optimize = parsed_new_days

    # Run route optimization on the updated schedule
    optimized_payload = optimize_itinerary_schedule(
        itinerary_data={
            "destination": trip.destination,
            "days": final_days_to_optimize,
        },
        travel_pace=trip.travel_pace,
    )

    itinerary_days: List[ItineraryDay] = []
    for d in optimized_payload.get("days", []):
        day_items = [ItineraryItem(**it) for it in d.get("items", [])]
        morning = [ItineraryItem(**it) for it in d.get("morning_items", [])]
        afternoon = [ItineraryItem(**it) for it in d.get("afternoon_items", [])]
        evening = [ItineraryItem(**it) for it in d.get("evening_items", [])]

        itinerary_days.append(
            ItineraryDay(
                day_number=d.get("day_number", 1),
                date=d.get("date"),
                theme=d.get("theme"),
                items=day_items,
                morning_items=morning,
                afternoon_items=afternoon,
                evening_items=evening,
            )
        )

    updated_itinerary = ItineraryResponse(
        trip_id=trip_id,
        destination=trip.destination,
        total_days=trip.duration_days,
        travel_pace=trip.travel_pace,
        total_estimated_cost=optimized_payload.get("total_estimated_cost", 0.0),
        currency=trip.currency,
        days=itinerary_days,
        ai_generated=True,
        provider=llm.get_provider_name(),
        model_used=llm.get_model_name(),
        generation_notes=refinement_data.get("summary_of_changes", "Itinerary refined successfully."),
        route_optimized=True,
    )

    # Persist the safely updated itinerary
    repo_instance.save_itinerary(trip_id, updated_itinerary.model_dump())

    return ItineraryRefinementResponse(
        trip_id=trip_id,
        summary_of_changes=refinement_data.get("summary_of_changes", f"Successfully refined itinerary ({refinement_request.action})."),
        action=refinement_request.action,
        refined_day=target_day,
        itinerary=updated_itinerary,
    )


def get_saved_itinerary(trip_id: str) -> Optional[ItineraryResponse]:
    """Retrieve already saved itinerary from database repository."""
    saved = repo_instance.get_itinerary(trip_id)
    if not saved:
        return None
    return ItineraryResponse(**saved)
