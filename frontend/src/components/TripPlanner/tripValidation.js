/**
 * Client-side validation for the multi-step Travel Preference Form (Activity 3.1).
 */

export const AVAILABLE_INTERESTS = [
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
];

export const DIETARY_OPTIONS = [
  "No preference",
  "Vegetarian",
  "Vegan",
  "Jain",
  "Other",
];

export const TRAVEL_PACES = [
  { value: "Relaxed", label: "Relaxed", desc: "1-2 highlights/day, leisurely mornings, plenty of downtime" },
  { value: "Moderate", label: "Moderate", desc: "2-3 highlights/day, balanced rhythm with adequate rest" },
  { value: "Fast-paced", label: "Fast-paced", desc: "3-4 highlights/day, packed sightseeing, high energy" },
];

export const TRAVEL_STYLES = [
  "Budget",
  "Moderate",
  "Luxury",
  "Backpacker",
  "Cultural",
  "Adventure",
  "Family",
  "Relaxation",
];

/**
 * Validates step 1: Destination, Dates, Budget, Travellers
 */
export function validateStep1(data) {
  const errors = {};

  if (!data.destination || !data.destination.trim()) {
    errors.destination = "Destination is required (e.g., Tokyo, Japan or Paris, France).";
  }

  if (!data.start_date) {
    errors.start_date = "Start date is required.";
  }

  if (!data.end_date) {
    errors.end_date = "End date is required.";
  }

  if (data.start_date && data.end_date) {
    const start = new Date(data.start_date);
    const end = new Date(data.end_date);
    if (end < start) {
      errors.end_date = "End date cannot be earlier than start date.";
    }
  }

  const budgetNum = Number(data.budget);
  if (!data.budget || isNaN(budgetNum) || budgetNum <= 0) {
    errors.budget = "Please enter a valid positive budget greater than 0.";
  }

  const countNum = Number(data.traveller_count);
  if (!data.traveller_count || isNaN(countNum) || countNum < 1 || !Number.isInteger(countNum)) {
    errors.traveller_count = "Number of travellers must be at least 1.";
  }

  return errors;
}

/**
 * Validates step 2: Travel Style and Interests
 */
export function validateStep2(data) {
  const errors = {};

  if (!data.travel_style) {
    errors.travel_style = "Please select a travel style.";
  }

  if (!data.interests || data.interests.length === 0) {
    errors.interests = "Please select at least one interest to personalize your trip.";
  }

  return errors;
}

/**
 * Validates step 3: Dietary, Pace, Mobility
 */
export function validateStep3(data) {
  const errors = {};

  if (!data.travel_pace) {
    errors.travel_pace = "Please select your preferred travel pace.";
  }

  if (!data.dietary_preference) {
    errors.dietary_preference = "Please select your dietary preference.";
  }

  return errors;
}

/**
 * Validates entire form before API dispatch
 */
export function validateFullTrip(data) {
  return {
    ...validateStep1(data),
    ...validateStep2(data),
    ...validateStep3(data),
  };
}
