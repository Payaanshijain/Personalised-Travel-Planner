# AI-Powered Travel Itinerary Generation, Route Optimization & Refinement Architecture

## 1. Architecture Overview

The Personalized Travel Itinerary Planner combines a responsive React (Vite) frontend with a Python (FastAPI) backend. The platform transforms multi-parameter user travel preferences (destination, dates, budget, travellers, travel style, interests, dietary restrictions, mobility needs, and pace) into structured day-by-day itineraries organized into **Morning**, **Afternoon**, and **Evening** time slots, with automated schedule optimization and conversational refinement.

```
+-----------------------------------------------------------------------------------------+
|                                    React Frontend                                       |
|  - Multi-Step Preference Form (TripPlannerForm.jsx)                                    |
|  - Day-by-Day Dashboard & Time-Slot Cards (ItineraryView.jsx)                           |
|  - Interactive Refinement Toolbar (Quick Actions & Custom Prompt Input)                 |
+-----------------------------------------------------------------------------------------+
                                      |  HTTP REST (CORS enabled)
                                      v
+-----------------------------------------------------------------------------------------+
|                                   FastAPI Backend                                       |
|  - Endpoints: /health, /api/trips, /api/trips/{id}/generate, /api/trips/{id}/refine    |
|  - Pydantic Schema Validation (trips.py)                                                |
+-----------------------------------------------------------------------------------------+
       |                                      |                                    |
       v                                      v                                    v
+-----------------------+   +------------------------------+   +--------------------------+
|  PromptBuilder Layer  |   |    Route & Schedule Optimizer|   |  Repository / Database   |
|  - Vibes & Pace Rules |   |    - Morning/Afternoon/Eve   |   |  - In-Memory Fallback    |
|  - Dietary & Mobility |   |    - Transit Buffer Est.     |   |  - Supabase PostgREST    |
|  - Refinement Prompts |   |    - No Overlaps / Meal Gaps |   |    (001 & 002 migrations)|
+-----------------------+   +------------------------------+   +--------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------------------+
|                                 LLM Provider Layer                                      |
|  - LLMProvider (Abstract Base Class)                                                    |
|  - GroqProvider (openai/gpt-oss-120b, JSON Mode, async standard HTTP)                  |
|  - GeminiProvider / OpenAIProvider / MockLLMProvider                                   |
+-----------------------------------------------------------------------------------------+
```

---

## 2. LLMProvider Interface

Located in `app/services/llm_provider.py`:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Asynchronously call the LLM and return raw JSON text."""
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if required API credentials exist in environment."""
        raise NotImplementedError

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider identifier ('groq', 'gemini', 'openai', 'mock')."""
        raise NotImplementedError

    @abstractmethod
    def get_model_name(self) -> str:
        """Return model identifier."""
        raise NotImplementedError
```

### Exception Hierarchy:
* `LLMProviderError` — Base exception.
* `LLMProviderNotConfiguredError` — Raised when `GROQ_API_KEY` or provider key is missing. Maps to HTTP `503 Service Unavailable`.
* `LLMTimeoutError` — Raised when request exceeds timeout threshold (`45s`). Maps to HTTP `504 Gateway Timeout`.
* `LLMRateLimitError` — Raised on HTTP 429. Maps to HTTP `429 Too Many Requests`.
* `LLMResponseParsingError` — Raised on invalid JSON output. Maps to HTTP `502 Bad Gateway`.

---

## 3. Groq Configuration

* **Provider Module:** `app/services/groq_provider.py`
* **API Endpoint:** `https://api.groq.com/openai/v1/chat/completions`
* **Default Model:** `openai/gpt-oss-120b`
* **Structured Output:** Enforced using `response_format={"type": "json_object"}`.
* **Network Client:** Implemented using Python standard library (`urllib.request`) executed via `asyncio.to_thread` for non-blocking asynchronous execution without external dependency conflicts.
* **Credential Safety:** Keys are read exclusively from environment variables (`GROQ_API_KEY`) and are never written to logs or sent to the frontend.

---

## 4. Prompt Engineering & Personalization

Located in `app/services/prompt_builder.py`:

1. **Travel Vibes:** Tailored guidance for:
   * **Relaxed Exploration:** Unhurried local immersion.
   * **Adventure:** Active outdoor pursuits, hiking, sports.
   * **Luxury:** High-touch venues, fine dining, premium waterfront spots.
   * **Budget:** Free walking circuits, public botanical gardens, markets, street food.
   * **Cultural & Historical:** Heritage monuments, architecture walks, artisan workshops.
   * **Family-Friendly:** Interactive exhibits, open parks, kid-friendly dining.
   * **Spiritual & Contemplative:** Sacred shrines, meditation spaces, temple etiquette.
2. **Pacing Rules:**
   * **Relaxed:** 1–2 major activities/day, 45–60 min transit buffers, leisurely mornings.
   * **Moderate:** 2–3 activities/day, 30–40 min transit buffers, balanced afternoon stops.
   * **Fast-Paced:** 3–4 activities/day, early starts, geographically clustered stops.
3. **Dietary Guidance:** Strict mandates for Vegetarian, Vegan, Jain (excludes root vegetables, onion, garlic), Halal, or custom preferences.
4. **Mobility & Accessibility:** Step-free access mandates, elevator confirmations, and avoidance of steep inclines when accessibility constraints are noted.
5. **Prompt Injection Defense:** User notes are isolated as raw literal data; delimiter tokens (`<system>`, ```` ````) and override phrases are stripped.

---

## 5. Route & Schedule Optimization Strategy

Located in `app/services/route_optimizer.py`:

* **Time Slots:** Activities are automatically sorted and grouped into three primary daylight windows:
  * **Morning Slot:** approx. 09:30 AM – 12:00 PM
  * **Lunch & Rest Pause:** 12:00 PM – 01:30 PM
  * **Afternoon Slot:** approx. 01:30 PM – 04:30 PM
  * **Dinner & Rest Pause:** 05:00 PM – 06:30 PM
  * **Evening Slot:** approx. 06:30 PM – 09:00 PM
* **Pace Caps:** Trims and spaces activities for relaxed itineraries (max 3 items/day), allowing 4 items/day for moderate, and up to 5 items/day for fast-paced.
* **Transit Buffer Transparency:** Attaches conservative, realistic transit buffer estimates between consecutive stops (e.g. `~20 mins standard transit / walking buffer (estimated)`).
* **Truthfulness Guard:** Does not fabricate road network travel times or false GPS coordinates.

---

## 6. Conversational Refinement Workflow

Located in `app/services/itinerary_service.py` (`refine_itinerary_for_trip`):

1. **User Action Selection:** The user triggers a refinement action via the UI toolbar:
   * Quick Actions: `"more_relaxed"`, `"more_adventurous"`, `"reduce_budget"`, `"more_culture"`, `"regenerate"`, or `"regenerate_day"`.
   * Conversational Input: `"custom"` with free-form text feedback.
2. **Context Retrieval:** Existing itinerary and original trip parameters are retrieved.
3. **Selective Scope:**
   * If a specific day is targeted (`day_number=X`), the prompt instructs the model to regenerate only Day X.
   * Unaffected days remain completely untouched and preserved.
4. **Optimization & Revalidation:** The updated schedule is run through the route optimizer and validated against the Pydantic schema.
5. **Safe Update:** If an LLM error occurs during refinement, the previous itinerary remains intact and unaffected.

---

## 7. REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` or `/api/health` | Health check endpoint returning backend status |
| `POST` | `/api/trips/` | Create a new trip with preferences (Activity 3.1) |
| `GET` | `/api/trips/` | List all trips accessible to user |
| `GET` | `/api/trips/{trip_id}` | Retrieve single trip details |
| `POST` | `/api/trips/{trip_id}/generate` | Generate full AI itinerary with route optimization |
| `GET` | `/api/trips/{trip_id}/itinerary` | Retrieve previously generated and saved itinerary |
| `POST` | `/api/trips/{trip_id}/refine` | Refine or regenerate an itinerary / single day |
| `GET` | `/api/trips/{trip_id}/recommendations` | Retrieve categorized recommendations (Activity 3.3) |
| `GET` | `/api/trips/{trip_id}/prompt-preview` | View structured system & user prompts (Activity 3.2) |

---

## 8. Example Request & Response

### Refinement Request (`POST /api/trips/{trip_id}/refine`):
```json
{
  "action": "more_relaxed",
  "day_number": 1,
  "feedback": "Include more tea garden stops and avoid steep steps."
}
```

### Refinement Response (`200 OK`):
```json
{
  "trip_id": "d02d8def-48c2-46fd-9da0-bea8da28f9f9",
  "summary_of_changes": "Adjusted Day 1 with leisurely garden visits and flat walking routes.",
  "action": "more_relaxed",
  "refined_day": 1,
  "itinerary": {
    "trip_id": "d02d8def-48c2-46fd-9da0-bea8da28f9f9",
    "destination": "Kyoto, Japan",
    "total_days": 4,
    "travel_pace": "Relaxed",
    "total_estimated_cost": 120.0,
    "currency": "USD",
    "route_optimized": true,
    "days": [
      {
        "day_number": 1,
        "date": "2026-11-01",
        "theme": "Serene Temple Gardens & Traditional Tea",
        "items": [
          {
            "id": "act_d1_1",
            "day_number": 1,
            "time_slot": "Morning",
            "start_time": "10:00 AM",
            "end_time": "12:00 PM",
            "duration": "2 hours",
            "title": "Tenryu-ji Sogenchi Garden",
            "description": "Historic Zen temple garden with flat paths and scenic pond views.",
            "location": "Arashiyama, Kyoto",
            "category": "Nature",
            "estimated_cost": 5.0,
            "transit_info": "~25 mins transit buffer (estimated)",
            "notes": "Accessible step-free path through North gate.",
            "accessibility_notes": "Wheelchair accessible paths.",
            "is_verified": false
          }
        ]
      }
    ]
  }
}
```

---

## 9. Environment Variables (`backend/.env`)

```ini
APP_NAME=Personalised Travel Planner
FRONTEND_URL=http://127.0.0.1:5173
DEFAULT_CURRENCY=USD

# AI Provider Configuration
AI_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
LLM_TIMEOUT_SECONDS=45

# Optional Supabase Database Connection
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

---

## 10. Database Migrations

Two additive migrations are available in `database/migrations/`:
1. `001_add_trip_preferences.sql`: Adds preferences to `trips` and metadata to `itinerary_items`.
2. `002_itinerary_refinements.sql`: Adds `time_slot`, `end_time`, `duration`, `transit_info`, `notes`, `accessibility_notes`, and metadata indexes.

To apply migrations manually:
1. Open the [Supabase Dashboard](https://supabase.com/dashboard) for your project.
2. Navigate to the **SQL Editor**.
3. Run `001_add_trip_preferences.sql` followed by `002_itinerary_refinements.sql`.

---

## 11. Automated Test Execution

Run backend tests using Python's built-in `unittest` runner:

```powershell
# From backend-backup/ or backend/:
.\.venv\Scripts\python.exe -m unittest discover tests
```
**Actual Result:** `32 tests passed in 0.027s (OK)`

Run frontend production build check:
```powershell
# From frontend/:
npm.cmd run build
```
**Actual Result:** `✓ built in 888ms (0 errors)`

---

## 12. Startup Commands

Open two terminal windows:

### Terminal 1: Backend
```powershell
cd C:\Users\payya\OneDrive\Documents\Personalised-Travel-Planner\backend-backup
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Terminal 2: Frontend
```powershell
cd C:\Users\payya\OneDrive\Documents\Personalised-Travel-Planner\frontend
npm.cmd run dev
```

Visit the app in your browser: **[http://127.0.0.1:5173/](http://127.0.0.1:5173/)**
