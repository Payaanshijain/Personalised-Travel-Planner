# College Project Documentation: Activities 3.1, 3.2, and 3.3
**Project:** Personalized Travel Itinerary Planner  
**Date:** October 2026  
**Status:** Completed & Tested  

---

## 1. Activities Overview & Requirements

* **Activity 3.1 — Travel Preference Form:**
  Build a responsive, multi-step travel preference form in React collecting 11 distinct parameters: Destination, Start Date, End Date, Budget, Traveller Count, Travel Style, Interests (multi-select), Dietary Preferences, Travel Pace, Mobility/Accessibility Needs, and Notes. Includes client-side step validation, error handling, and API integration.
* **Activity 3.2 — Dynamic AI Prompt Engineering:**
  Implement a dedicated, reusable prompt-engineering module in FastAPI (`prompt_builder.py`) converting raw preferences into context-aware, structured prompts with deterministic rules for travel pace, dietary mandates, accessibility guidance, and prompt-injection safety defenses.
* **Activity 3.3 — REST APIs and AI-Powered Travel Recommendations:**
  Implement the FastAPI REST API layer for trip creation, trip retrieval, categorized recommendation filtering, and AI itinerary generation with clean provider abstractions (Google Gemini / OpenAI), in-memory and Supabase persistence, and Pydantic validation schemas.

---

## 2. Features Implemented

### Frontend (React 19 + Vite)
- **Multi-Step Form Wizard (`TripPlannerForm.jsx`):**
  - **Step 1 (Basics):** Destination autocomplete, start/end dates, budget & currency selector, traveller count.
  - **Step 2 (Style & Interests):** Travel style dropdown, 10 toggleable interactive interest chips.
  - **Step 3 (Pace & Accessibility):** 3 visual pace cards (Relaxed, Moderate, Fast-paced) with pace descriptions, dietary selector (No preference, Vegetarian, Vegan, Jain, Other), and accessibility input.
  - **Step 4 (Review & Notes):** Summary card of all selected preferences with notes text area and submit button.
- **Client-Side Validation (`tripValidation.js`):**
  - Enforces mandatory fields.
  - Rejects end dates earlier than start dates.
  - Rejects non-positive budgets ($ \le 0 $) and invalid traveller counts ($ < 1 $).
  - Prevents duplicate form submissions while loading.
- **Results & Timeline View (`ItineraryView.jsx`):**
  - Categorized recommendations grid (Attractions, Dining, Nature, Culture, Adventure, Relaxation).
  - Shows activity names, descriptions, estimated cost tags, duration, and verified/estimated badges.
  - Generated day-by-day itinerary timeline with time badges and location tags.
  - Live preview tab for inspecting the Activity 3.2 constructed AI prompt.
  - Friendly status alerts explaining if the AI provider key needs to be configured in `.env`.
- **Saved Trips Dashboard (`HomePage.jsx`):**
  - Real-time backend health check indicator with ping button.
  - Tab navigation between "Plan a New Trip" and "Saved Trips".

### Backend (FastAPI + Python)
- **Dynamic Prompt Builder (`app/services/prompt_builder.py`):**
  - Calculates trip duration in days from dates.
  - Applies deterministic travel pace logic:
    - *Relaxed:* 1-2 major activities/day, relaxed mornings (10:00 AM), 2-3 hour breaks, minimal transit.
    - *Moderate:* 2-3 highlights/day, balanced rhythm, standard transit buffers.
    - *Fast-paced:* 3-4 highlights/day, 8:30 AM starts, geographic clustering.
  - Applies dietary personalization:
    - *Jain:* Mandates no onion, garlic, or root vegetables.
    - *Vegan:* 100% plant-based dining recommendations.
    - *Vegetarian:* Pure-veg or veg-certified eateries.
  - Applies mobility/accessibility constraints:
    - Enforces step-free access, elevators, and minimal stairs for users with mobility concerns.
  - Defends against prompt injection by isolating user notes as data and sanitizing override patterns.
  - Enforces structured JSON output matching Pydantic response schemas.
- **AI Provider Abstraction (`app/services/ai_service.py`):**
  - Standard library HTTP implementation supporting Google Gemini (`gemini-1.5-flash`) and OpenAI (`gpt-4o-mini`).
  - Raises typed `AIProviderNotConfiguredError` (mapped to HTTP 503) when API key is missing.
  - Strips markdown code fences (` ```json `) and validates JSON output.
- **Personalized Recommendations Engine (`app/services/recommendation_service.py`):**
  - Filters and ranks experiences across 6 categories.
  - Dynamically customizes dining and activities based on diet, mobility, and interests.
  - Flags uncertain details with `is_verified: false` as required by safety rules.
- **Database Repository Layer (`app/database.py`):**
  - Dual-mode architecture: connects to Supabase REST API when credentials are provided in `.env`, or falls back seamlessly to a thread-safe in-memory store for local testing.
- **REST Router (`app/routers/trips.py`):**
  - Full REST CRUD, itinerary generation, categorized recommendations, and prompt preview endpoints.

---

## 3. Main Files Created and Modified

| Workspace Folder | File Path | Action | Description |
| :--- | :--- | :--- | :--- |
| **backend-backup** | `app/config.py` | Modified | Added Supabase, AI provider, and currency settings |
| **backend-backup** | `app/main.py` | Modified | Registered `trips.router` and enriched CORS |
| **backend-backup** | `app/database.py` | Created | Dual-mode Supabase and in-memory persistence |
| **backend-backup** | `app/schemas/trips.py` | Created | Pydantic validation schemas for trips, itineraries, recs |
| **backend-backup** | `app/services/prompt_builder.py` | Created | Activity 3.2 prompt engineering layer |
| **backend-backup** | `app/services/ai_service.py` | Created | LLM integration for Gemini and OpenAI |
| **backend-backup** | `app/services/recommendation_service.py` | Created | Categorized recommendation generator |
| **backend-backup** | `app/services/trip_service.py` | Created | Trip business logic and duration derivation |
| **backend-backup** | `app/services/itinerary_service.py` | Created | Itinerary orchestration and persistence |
| **backend-backup** | `app/routers/trips.py` | Created | FastAPI endpoints for trips, generation, recs |
| **backend-backup** | `tests/test_activities.py` | Created | Unit test suite covering all 3 activities |
| **backend-backup** | `.env.example` | Modified | Documented all environment variables |
| **database** | `migrations/001_add_trip_preferences.sql` | Created | Safe additive SQL migration for trip preferences |
| **supabase** | `migrations/20261026000000_add_trip_preferences.sql` | Created | Supabase CLI-compatible migration file |
| **frontend** | `src/services/tripsAPI.js` | Created | API client for trips, generation, recs |
| **frontend** | `src/components/TripPlanner/tripValidation.js` | Created | Multi-step client validation logic |
| **frontend** | `src/components/TripPlanner/TripPlanner.css` | Created | Responsive stylesheet for form and timeline |
| **frontend** | `src/components/TripPlanner/TripPlannerForm.jsx` | Created | Activity 3.1 multi-step preference form |
| **frontend** | `src/components/TripPlanner/ItineraryView.jsx` | Created | Itinerary timeline and recommendations view |
| **frontend** | `src/pages/HomePage.jsx` | Modified | Integrated planner, saved trips, and health check |

---

## 4. REST Endpoints Summary

| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Backend health check | `200` |
| `POST` | `/api/trips/` | Create and validate a new trip | `201`, `422` |
| `GET` | `/api/trips/` | List all saved trips | `200` |
| `GET` | `/api/trips/{trip_id}` | Retrieve trip by ID | `200`, `404` |
| `POST` | `/api/trips/{trip_id}/generate` | Generate AI itinerary | `200`, `404`, `502`, `503` |
| `GET` | `/api/trips/{trip_id}/itinerary` | Retrieve generated itinerary | `200`, `404` |
| `GET` | `/api/trips/{trip_id}/recommendations` | Retrieve categorized recommendations | `200`, `404` |
| `GET` | `/api/trips/{trip_id}/prompt-preview` | Inspect Activity 3.2 AI prompt | `200`, `404` |

---

## 5. Example Request and Response

### Create Trip (`POST /api/trips/`)
**Request Body:**
```json
{
  "destination": "Kyoto, Japan",
  "start_date": "2026-11-10",
  "end_date": "2026-11-14",
  "budget": 2000.0,
  "currency": "USD",
  "traveller_count": 2,
  "travel_style": "Cultural",
  "interests": ["Culture", "History", "Food"],
  "dietary_preference": "Vegetarian",
  "travel_pace": "Relaxed",
  "mobility_requirements": "None",
  "notes": "Interested in serene tea houses."
}
```

**Response (`201 Created`):**
```json
{
  "id": "e25b1f5a-c45a-4cb7-9db6-7a13d2f9b1b8",
  "destination": "Kyoto, Japan",
  "start_date": "2026-11-10",
  "end_date": "2026-11-14",
  "budget": 2000.0,
  "currency": "USD",
  "traveller_count": 2,
  "travel_style": "Cultural",
  "interests": ["Culture", "History", "Food"],
  "dietary_preference": "Vegetarian",
  "travel_pace": "Relaxed",
  "mobility_requirements": "None",
  "notes": "Interested in serene tea houses.",
  "user_id": null,
  "created_at": "2026-10-26T00:30:00Z",
  "duration_days": 5
}
```

---

## 6. Environment Variables (`backend/.env`)

```ini
APP_NAME=Personalised Travel Planner
FRONTEND_URL=http://127.0.0.1:5173
DEFAULT_CURRENCY=USD

# Supabase (Optional: in-memory store used if blank)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# AI Provider (Optional: Gemini or OpenAI)
AI_PROVIDER=gemini
AI_API_KEY=your-gemini-or-openai-api-key
```

---

## 7. Database Migration Steps for Supabase

When you are ready to apply the migration to your live Supabase project:
1. Open the [Supabase Dashboard](https://supabase.com/dashboard) and go to your project.
2. Navigate to **SQL Editor** in the left sidebar.
3. Open `database/migrations/001_add_trip_preferences.sql`.
4. Copy and paste the SQL content into the editor and click **Run**.
5. The `trips` and `itinerary_items` tables will be upgraded safely without data loss.

---

## 8. Commands to Run the Application

### Backend
From the backend directory:
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```
Interactive API documentation: `http://127.0.0.1:8000/docs`

### Frontend
From the frontend directory:
```powershell
npm run dev
```
Open in browser: `http://localhost:5173/`
