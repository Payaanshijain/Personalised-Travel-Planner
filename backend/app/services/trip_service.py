"""
Trip Business Logic Service (Activity 3.3).
Handles trip creation, retrieval, and duration calculations.
"""

from datetime import date
from typing import Optional, List, Dict, Any

from app.database import repo_instance
from app.schemas.trips import TripCreate, TripResponse, TripListResponse
from app.services.prompt_builder import calculate_trip_duration


def create_trip(trip_in: TripCreate) -> TripResponse:
    duration = calculate_trip_duration(trip_in.start_date, trip_in.end_date)
    trip_dict = trip_in.model_dump()
    trip_dict["duration_days"] = duration

    saved = repo_instance.create_trip(trip_dict)
    return TripResponse(
        id=str(saved["id"]),
        destination=saved["destination"],
        start_date=saved["start_date"] if isinstance(saved["start_date"], date) else date.fromisoformat(str(saved["start_date"])),
        end_date=saved["end_date"] if isinstance(saved["end_date"], date) else date.fromisoformat(str(saved["end_date"])),
        budget=float(saved["budget"]),
        currency=saved.get("currency", "USD"),
        traveller_count=int(saved.get("traveller_count", 1)),
        travel_style=saved.get("travel_style", "Moderate"),
        interests=saved.get("interests", []),
        dietary_preference=saved.get("dietary_preference", "No preference"),
        travel_pace=saved.get("travel_pace", "Moderate"),
        mobility_requirements=saved.get("mobility_requirements", "None"),
        notes=saved.get("notes"),
        user_id=saved.get("user_id"),
        created_at=saved["created_at"],
        duration_days=duration,
    )


def get_trip(trip_id: str) -> Optional[TripResponse]:
    saved = repo_instance.get_trip(trip_id)
    if not saved:
        return None

    start_date = saved["start_date"] if isinstance(saved["start_date"], date) else date.fromisoformat(str(saved["start_date"]))
    end_date = saved["end_date"] if isinstance(saved["end_date"], date) else date.fromisoformat(str(saved["end_date"]))
    duration = calculate_trip_duration(start_date, end_date)

    return TripResponse(
        id=str(saved["id"]),
        destination=saved["destination"],
        start_date=start_date,
        end_date=end_date,
        budget=float(saved["budget"]),
        currency=saved.get("currency", "USD"),
        traveller_count=int(saved.get("traveller_count", 1)),
        travel_style=saved.get("travel_style", "Moderate"),
        interests=saved.get("interests", []),
        dietary_preference=saved.get("dietary_preference", "No preference"),
        travel_pace=saved.get("travel_pace", "Moderate"),
        mobility_requirements=saved.get("mobility_requirements", "None"),
        notes=saved.get("notes"),
        user_id=saved.get("user_id"),
        created_at=saved["created_at"],
        duration_days=duration,
    )


def list_trips(user_id: Optional[str] = None) -> TripListResponse:
    raw_list = repo_instance.list_trips(user_id)
    trips: List[TripResponse] = []
    for saved in raw_list:
        start_date = saved["start_date"] if isinstance(saved["start_date"], date) else date.fromisoformat(str(saved["start_date"]))
        end_date = saved["end_date"] if isinstance(saved["end_date"], date) else date.fromisoformat(str(saved["end_date"]))
        duration = calculate_trip_duration(start_date, end_date)

        trips.append(
            TripResponse(
                id=str(saved["id"]),
                destination=saved["destination"],
                start_date=start_date,
                end_date=end_date,
                budget=float(saved["budget"]),
                currency=saved.get("currency", "USD"),
                traveller_count=int(saved.get("traveller_count", 1)),
                travel_style=saved.get("travel_style", "Moderate"),
                interests=saved.get("interests", []),
                dietary_preference=saved.get("dietary_preference", "No preference"),
                travel_pace=saved.get("travel_pace", "Moderate"),
                mobility_requirements=saved.get("mobility_requirements", "None"),
                notes=saved.get("notes"),
                user_id=saved.get("user_id"),
                created_at=saved["created_at"],
                duration_days=duration,
            )
        )
    return TripListResponse(trips=trips, total=len(trips))
