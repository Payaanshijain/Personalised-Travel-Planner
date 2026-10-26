"""
Database Layer for Trips and Itineraries.
Provides an abstract repository with:
1. Supabase REST API client (when SUPABASE_URL and SUPABASE_KEY are provided).
2. Thread-safe in-memory repository fallback (when Supabase credentials are not yet configured).
Ensures zero runtime crashes while preserving full functionality for testing and demonstrations.
"""

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any

from app import config

logger = logging.getLogger(__name__)


class TripRepository:
    """Base repository interface for Trip and Itinerary persistence."""

    def create_trip(self, trip_dict: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def get_trip(self, trip_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def list_trips(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def save_itinerary(self, trip_id: str, itinerary_data: Dict[str, Any]) -> None:
        raise NotImplementedError

    def get_itinerary(self, trip_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError


class InMemoryTripRepository(TripRepository):
    """
    In-memory thread-safe implementation.
    Used for local execution when live Supabase credentials have not been configured.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._trips: Dict[str, Dict[str, Any]] = {}
        self._itineraries: Dict[str, Dict[str, Any]] = {}

    def create_trip(self, trip_dict: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            trip_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            record = dict(trip_dict)
            record["id"] = trip_id
            record["created_at"] = now
            self._trips[trip_id] = record
            logger.info("Created in-memory trip with ID: %s", trip_id)
            return record

    def get_trip(self, trip_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._trips.get(trip_id)

    def list_trips(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._trips.values())
            if user_id:
                items = [t for t in items if t.get("user_id") == user_id]
            # Sort newest first
            return sorted(items, key=lambda x: x.get("created_at", datetime.min), reverse=True)

    def save_itinerary(self, trip_id: str, itinerary_data: Dict[str, Any]) -> None:
        with self._lock:
            self._itineraries[trip_id] = itinerary_data
            logger.info("Saved in-memory itinerary for trip: %s", trip_id)

    def get_itinerary(self, trip_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._itineraries.get(trip_id)


class SupabaseTripRepository(TripRepository):
    """
    Connects to live Supabase project via PostgREST endpoints using standard HTTP.
    Preserves service-role credentials exclusively on backend.
    """

    def __init__(self, url: str, key: str):
        self.base_url = url.rstrip("/")
        self.key = key
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        # In-memory cache for fast lookups/fallback
        self._fallback = InMemoryTripRepository()

    def _postgrest_request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/rest/v1/{endpoint}"
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def create_trip(self, trip_dict: Dict[str, Any]) -> Dict[str, Any]:
        try:
            payload = {
                "destination": trip_dict["destination"],
                "start_date": str(trip_dict["start_date"]),
                "end_date": str(trip_dict["end_date"]),
                "budget": trip_dict["budget"],
                "currency": trip_dict.get("currency", "USD"),
                "travel_style": trip_dict.get("travel_style", "Moderate"),
                "traveller_count": trip_dict.get("traveller_count", 1),
                "interests": trip_dict.get("interests", []),
                "dietary_preference": trip_dict.get("dietary_preference", "No preference"),
                "travel_pace": trip_dict.get("travel_pace", "Moderate"),
                "mobility_requirements": trip_dict.get("mobility_requirements", "None"),
                "notes": trip_dict.get("notes"),
                "user_id": trip_dict.get("user_id"),
            }
            res = self._postgrest_request("trips", method="POST", data=payload)
            if res and isinstance(res, list):
                created = res[0]
                if "created_at" in created and isinstance(created["created_at"], str):
                    created["created_at"] = datetime.fromisoformat(created["created_at"].replace("Z", "+00:00"))
                return created
            return self._fallback.create_trip(trip_dict)
        except Exception as e:
            logger.warning("Supabase request failed, falling back to local memory: %s", e)
            return self._fallback.create_trip(trip_dict)

    def get_trip(self, trip_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = self._postgrest_request(f"trips?id=eq.{trip_id}&select=*")
            if res and isinstance(res, list) and len(res) > 0:
                record = res[0]
                if "created_at" in record and isinstance(record["created_at"], str):
                    record["created_at"] = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
                return record
        except Exception as e:
            logger.warning("Supabase get_trip error: %s", e)
        return self._fallback.get_trip(trip_id)

    def list_trips(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            endpoint = "trips?select=*&order=created_at.desc"
            if user_id:
                endpoint = f"trips?user_id=eq.{user_id}&select=*&order=created_at.desc"
            res = self._postgrest_request(endpoint)
            if isinstance(res, list):
                for record in res:
                    if "created_at" in record and isinstance(record["created_at"], str):
                        record["created_at"] = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
                return res
        except Exception as e:
            logger.warning("Supabase list_trips error: %s", e)
        return self._fallback.list_trips(user_id)

    def save_itinerary(self, trip_id: str, itinerary_data: Dict[str, Any]) -> None:
        self._fallback.save_itinerary(trip_id, itinerary_data)
        # Also attempt persisting individual items to itinerary_items table
        try:
            days = itinerary_data.get("days", [])
            for day in days:
                day_num = day.get("day_number", 1)
                for item in day.get("items", []):
                    item_payload = {
                        "trip_id": trip_id,
                        "day_number": day_num,
                        "time_slot": item.get("time_slot", "Morning"),
                        "start_time": item.get("start_time"),
                        "end_time": item.get("end_time"),
                        "duration": item.get("duration"),
                        "title": item.get("title", "Activity"),
                        "description": item.get("description"),
                        "location": item.get("location"),
                        "category": item.get("category"),
                        "estimated_cost": item.get("estimated_cost", 0.0),
                        "transit_info": item.get("transit_info"),
                        "notes": item.get("notes"),
                        "accessibility_notes": item.get("accessibility_notes"),
                        "is_verified": item.get("is_verified", False),
                    }
                    self._postgrest_request("itinerary_items", method="POST", data=item_payload)
        except Exception as e:
            logger.warning("Supabase save_itinerary item error: %s", e)

    def get_itinerary(self, trip_id: str) -> Optional[Dict[str, Any]]:
        return self._fallback.get_itinerary(trip_id)


# Global repository factory
def get_trip_repository() -> TripRepository:
    """Instantiates Supabase repository if credentials are set, otherwise in-memory repository."""
    if config.SUPABASE_URL and config.SUPABASE_KEY:
        logger.info("Using Supabase database repository.")
        return SupabaseTripRepository(config.SUPABASE_URL, config.SUPABASE_KEY)
    logger.info("Using In-Memory database repository (Supabase credentials not configured in .env).")
    return InMemoryTripRepository()


# Singleton repository instance for FastAPI lifecycle
repo_instance = get_trip_repository()
