"""
FastAPI Trips Router (Activity 3.3).
Provides REST endpoints for trip CRUD, AI itinerary generation,
categorized recommendations, and prompt preview.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query

from app.schemas.trips import (
    TripCreate,
    TripResponse,
    TripListResponse,
    ItineraryResponse,
    CategorizedRecommendationsResponse,
    PromptPreviewResponse,
    ItineraryRefinementRequest,
    ItineraryRefinementResponse,
)
from app.services import trip_service, itinerary_service, recommendation_service, prompt_builder
from app.services.llm_provider import (
    LLMProviderError,
    LLMProviderNotConfiguredError,
    LLMTimeoutError,
    LLMRateLimitError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trips", tags=["Trips & Itineraries"])


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_new_trip(trip_in: TripCreate):
    """
    Validate travel preferences and create a new trip record (Activity 3.1 & 3.3).
    """
    try:
        created = trip_service.create_trip(trip_in)
        return created
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error("Failed to create trip: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save trip.")


@router.get("", response_model=TripListResponse, include_in_schema=False)
@router.get("/", response_model=TripListResponse)
def list_trips(user_id: Optional[str] = Query(None, description="Optional user filter")):
    """
    Retrieve trips accessible to the user (Activity 3.3).
    """
    return trip_service.list_trips(user_id)


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip_by_id(trip_id: str):
    """
    Retrieve an individual trip by ID.
    """
    trip = trip_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Trip '{trip_id}' not found.")
    return trip


@router.post("/{trip_id}/generate", response_model=ItineraryResponse)
async def generate_trip_itinerary(trip_id: str):
    """
    Generate an AI-powered travel itinerary for the specified trip.
    Uses LLMProvider (Groq by default) with schedule and route optimization.
    """
    try:
        itinerary = await itinerary_service.generate_itinerary_for_trip(trip_id)
        return itinerary
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except LLMProviderNotConfiguredError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": str(e),
                "error_code": "LLM_PROVIDER_NOT_CONFIGURED",
                "hint": "Set GROQ_API_KEY (or AI_API_KEY) in backend/.env to enable live generation.",
            }
        )
    except LLMRateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"message": str(e), "error_code": "LLM_RATE_LIMIT"}
        )
    except LLMTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"message": str(e), "error_code": "LLM_TIMEOUT"}
        )
    except LLMProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": str(e), "error_code": "LLM_PROVIDER_FAILED"}
        )
    except Exception as e:
        logger.error("Unexpected itinerary generation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating your itinerary."
        )


@router.post("/{trip_id}/refine", response_model=ItineraryRefinementResponse)
async def refine_trip_itinerary(trip_id: str, refinement_in: ItineraryRefinementRequest):
    """
    Conversational refinement / selective day regeneration for an existing itinerary.
    Preserves unaffected days and prior trip context.
    """
    try:
        refined = await itinerary_service.refine_itinerary_for_trip(trip_id, refinement_in)
        return refined
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except LLMProviderNotConfiguredError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": str(e),
                "error_code": "LLM_PROVIDER_NOT_CONFIGURED",
                "hint": "Set GROQ_API_KEY in backend/.env to enable itinerary refinement.",
            }
        )
    except LLMRateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"message": str(e), "error_code": "LLM_RATE_LIMIT"}
        )
    except LLMTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"message": str(e), "error_code": "LLM_TIMEOUT"}
        )
    except LLMProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": str(e), "error_code": "LLM_REFINEMENT_FAILED"}
        )
    except Exception as e:
        logger.error("Unexpected itinerary refinement error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while refining your itinerary."
        )


@router.get("/{trip_id}/itinerary", response_model=ItineraryResponse)
def get_trip_itinerary(trip_id: str):
    """
    Retrieve previously generated and saved itinerary for a trip.
    """
    trip = trip_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Trip '{trip_id}' not found.")

    itinerary = itinerary_service.get_saved_itinerary(trip_id)
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No itinerary has been generated for this trip yet. Call POST /api/trips/{trip_id}/generate first."
        )
    return itinerary


@router.get("/{trip_id}/recommendations", response_model=CategorizedRecommendationsResponse)
def get_trip_recommendations(trip_id: str):
    """
    Retrieve personalized, categorized recommendations based on user preferences (Activity 3.3).
    Categorized into Attractions, Dining, Nature, Culture, Adventure, and Relaxation.
    """
    trip = trip_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Trip '{trip_id}' not found.")

    return recommendation_service.generate_personalized_recommendations(trip.model_dump())


@router.get("/{trip_id}/prompt-preview", response_model=PromptPreviewResponse)
def preview_trip_prompt(trip_id: str):
    """
    Inspect the generated AI system and user prompts for Activity 3.2.
    """
    trip = trip_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Trip '{trip_id}' not found.")

    prompt_data = prompt_builder.generate_full_prompt(trip.model_dump())
    return PromptPreviewResponse(
        trip_id=trip_id,
        destination=prompt_data["destination"],
        duration_days=prompt_data["duration_days"],
        system_prompt=prompt_data["system_prompt"],
        user_prompt=prompt_data["user_prompt"],
    )
