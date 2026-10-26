from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator, model_validator


class TravelPaceEnum(str, Enum):
    RELAXED = "Relaxed"
    MODERATE = "Moderate"
    FAST_PACED = "Fast-paced"


class DietaryPreferenceEnum(str, Enum):
    NO_PREFERENCE = "No preference"
    VEGETARIAN = "Vegetarian"
    VEGAN = "Vegan"
    JAIN = "Jain"
    OTHER = "Other"


VALID_INTERESTS = [
    "Adventure",
    "Nature",
    "History",
    "Culture",
    "Shopping",
    "Food",
    "Beaches",
    "Spiritual places",
    "Nightlife",
    "Relaxation",
]


class TripBase(BaseModel):
    destination: str = Field(..., min_length=1, max_length=120, description="City, region, or country")
    start_date: date = Field(..., description="Trip start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="Trip end date (YYYY-MM-DD)")
    budget: float = Field(..., gt=0, description="Total estimated budget")
    currency: str = Field(default="USD", max_length=10, description="Currency code, e.g., USD, INR, EUR")
    traveller_count: int = Field(default=1, ge=1, le=50, description="Number of travellers")
    travel_style: str = Field(default="Moderate", description="E.g., Budget, Moderate, Luxury, Adventure, Cultural")
    interests: List[str] = Field(default_factory=list, description="Selected interests")
    dietary_preference: str = Field(default="No preference", description="Dietary preference")
    travel_pace: str = Field(default="Moderate", description="Relaxed, Moderate, or Fast-paced")
    mobility_requirements: str = Field(default="None", description="Mobility or accessibility notes")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Optional extra notes")

    @field_validator("destination")
    @classmethod
    def clean_destination(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Destination cannot be empty or just whitespace.")
        return cleaned

    @field_validator("interests")
    @classmethod
    def clean_interests(cls, v: List[str]) -> List[str]:
        # Strip and filter empty strings
        return [i.strip() for i in v if i and i.strip()]

    @model_validator(mode="after")
    def validate_dates(self) -> "TripBase":
        if self.end_date < self.start_date:
            raise ValueError("End date cannot be earlier than start date.")
        return self


class TripCreate(TripBase):
    user_id: Optional[str] = Field(default=None, description="Optional user ID for auth mapping")


class TripResponse(TripBase):
    id: str
    user_id: Optional[str] = None
    created_at: datetime
    duration_days: int

    class Config:
        from_attributes = True


class TripListResponse(BaseModel):
    trips: List[TripResponse]
    total: int


# Itinerary and Recommendation Schemas

class TimeSlotEnum(str, Enum):
    MORNING = "Morning"
    AFTERNOON = "Afternoon"
    EVENING = "Evening"


class ItineraryItem(BaseModel):
    id: Optional[str] = None
    day_number: int = Field(..., ge=1)
    time_slot: str = Field(default="Morning", description="Morning, Afternoon, or Evening")
    start_time: Optional[str] = Field(default=None, description="e.g. 09:00 AM")
    end_time: Optional[str] = Field(default=None, description="e.g. 11:30 AM")
    duration: Optional[str] = Field(default=None, description="e.g. 2 hours")
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = Field(default="General", description="Attraction, Dining, Nature, Culture, Adventure, Relaxation")
    estimated_cost: Optional[float] = Field(default=0.0)
    transit_info: Optional[str] = Field(default=None, description="Estimated transit time/notes to next destination")
    notes: Optional[str] = Field(default=None, description="Helpful tips, booking advice, or warnings")
    accessibility_notes: Optional[str] = Field(default=None, description="Pace/mobility compatibility")
    is_verified: bool = Field(default=False, description="Flag indicating if place/price is verified")


class ItineraryDay(BaseModel):
    day_number: int
    date: Optional[str] = None
    theme: Optional[str] = None
    items: List[ItineraryItem] = Field(default_factory=list)
    morning_items: List[ItineraryItem] = Field(default_factory=list)
    afternoon_items: List[ItineraryItem] = Field(default_factory=list)
    evening_items: List[ItineraryItem] = Field(default_factory=list)


class ItineraryResponse(BaseModel):
    trip_id: str
    destination: str
    total_days: int
    travel_pace: str
    total_estimated_cost: Optional[float] = 0.0
    currency: str = "USD"
    days: List[ItineraryDay]
    ai_generated: bool
    provider: Optional[str] = None
    model_used: Optional[str] = None
    generation_notes: Optional[str] = None
    route_optimized: bool = True


class ItineraryRefinementRequest(BaseModel):
    action: str = Field(
        ...,
        description="Action type: regenerate, regenerate_day, more_relaxed, more_adventurous, reduce_budget, more_culture, custom"
    )
    day_number: Optional[int] = Field(default=None, ge=1, description="Target day number when refining a specific day")
    feedback: Optional[str] = Field(default=None, max_length=1000, description="Specific adjustments or conversational feedback")


class ItineraryRefinementResponse(BaseModel):
    trip_id: str
    summary_of_changes: str
    action: str
    refined_day: Optional[int] = None
    itinerary: ItineraryResponse


class RecommendationItem(BaseModel):
    title: str
    category: str
    description: str
    estimated_cost: Optional[str] = None
    duration: Optional[str] = None
    location: Optional[str] = None
    match_reasons: List[str] = Field(default_factory=list)
    is_verified: bool = False


class CategorizedRecommendationsResponse(BaseModel):
    trip_id: str
    destination: str
    categories: Dict[str, List[RecommendationItem]]
    total_recommendations: int


class PromptPreviewResponse(BaseModel):
    trip_id: str
    destination: str
    duration_days: int
    system_prompt: str
    user_prompt: str
