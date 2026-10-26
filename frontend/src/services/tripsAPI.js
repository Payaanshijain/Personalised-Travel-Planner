const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

async function handleResponse(response) {
  if (!response.ok) {
    let errorMessage = `Server returned status ${response.status}`;
    try {
      const errorJson = await response.json();
      if (typeof errorJson.detail === "string") {
        errorMessage = errorJson.detail;
      } else if (errorJson.detail && errorJson.detail.message) {
        errorMessage = errorJson.detail.message;
      } else if (Array.isArray(errorJson.detail)) {
        errorMessage = errorJson.detail.map((d) => d.msg || d.message).join(", ");
      } else if (errorJson.message) {
        errorMessage = errorJson.message;
      }
    } catch {
      // response wasn't JSON
    }
    const err = new Error(errorMessage);
    err.status = response.status;
    throw err;
  }
  return response.json();
}

export async function createTrip(tripData) {
  const response = await fetch(`${API_URL}/api/trips/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(tripData),
  });
  return handleResponse(response);
}

export async function getTrips() {
  const response = await fetch(`${API_URL}/api/trips/`);
  return handleResponse(response);
}

export async function getTrip(tripId) {
  const response = await fetch(`${API_URL}/api/trips/${tripId}`);
  return handleResponse(response);
}

export async function generateItinerary(tripId) {
  const response = await fetch(`${API_URL}/api/trips/${tripId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse(response);
}

export async function getItinerary(tripId) {
  const response = await fetch(`${API_URL}/api/trips/${tripId}/itinerary`);
  return handleResponse(response);
}

export async function getRecommendations(tripId) {
  const response = await fetch(`${API_URL}/api/trips/${tripId}/recommendations`);
  return handleResponse(response);
}

export async function getPromptPreview(tripId) {
  const response = await fetch(`${API_URL}/api/trips/${tripId}/prompt-preview`);
  return handleResponse(response);
}

export async function refineItinerary(tripId, refinementData) {
  const response = await fetch(`${API_URL}/api/trips/${tripId}/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(refinementData),
  });
  return handleResponse(response);
}

