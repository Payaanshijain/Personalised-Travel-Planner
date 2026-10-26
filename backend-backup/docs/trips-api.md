# Trips & Itineraries API Reference

The Trips API provides endpoints to create and retrieve trip preferences, inspect generated prompt payloads, fetch categorized recommendations, and trigger AI itinerary generation.

## Base URL
Default: `http://127.0.0.1:8000`

---

## Endpoints

### 1. Health Check
* **`GET /health`**
* Returns status message confirming the FastAPI server is running.

### 2. Create Trip
* **`POST /api/trips/`**
* **Request:** JSON object conforming to `TripCreate` (destination, start_date, end_date, budget, currency, traveller_count, travel_style, interests, dietary_preference, travel_pace, mobility_requirements, notes).
* **Response:** `201 Created` with full `TripResponse` including generated `id` and `duration_days`.

### 3. List Trips
* **`GET /api/trips/`**
* **Query Parameters:** `user_id` (optional).
* **Response:** `200 OK` with list of trips and total count.

### 4. Get Trip by ID
* **`GET /api/trips/{trip_id}`**
* **Response:** `200 OK` with `TripResponse`.

### 5. Categorized Recommendations
* **`GET /api/trips/{trip_id}/recommendations`**
* **Response:** `200 OK` with categorized list of attractions, dining, nature, culture, adventure, and relaxation tailored to preferences.

### 6. Generate AI Itinerary
* **`POST /api/trips/{trip_id}/generate`**
* **Response:** `200 OK` with generated day-by-day itinerary schedule.
* **Errors:** `503 Service Unavailable` if AI API key is not configured in `.env`.

### 7. Get Saved Itinerary
* **`GET /api/trips/{trip_id}/itinerary`**
* **Response:** `200 OK` with saved itinerary.

### 8. Prompt Preview (Activity 3.2)
* **`GET /api/trips/{trip_id}/prompt-preview`**
* **Response:** `200 OK` with `system_prompt` and `user_prompt` built for the trip.
