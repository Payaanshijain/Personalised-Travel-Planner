import { useState } from "react";
import {
  AVAILABLE_INTERESTS,
  DIETARY_OPTIONS,
  TRAVEL_PACES,
  TRAVEL_STYLES,
  validateStep1,
  validateStep2,
  validateStep3,
  validateFullTrip,
} from "./tripValidation.js";
import { createTrip } from "../../services/tripsAPI.js";
import "./TripPlanner.css";

const INITIAL_FORM_STATE = {
  destination: "",
  start_date: "",
  end_date: "",
  budget: "1200",
  currency: "USD",
  traveller_count: "1",
  travel_style: "Moderate",
  interests: ["Culture", "Food"],
  dietary_preference: "No preference",
  travel_pace: "Moderate",
  mobility_requirements: "None",
  notes: "",
};

function TripPlannerForm({ onTripCreated }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState(INITIAL_FORM_STATE);
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error for the field being edited
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleInterestToggle = (interest) => {
    setFormData((prev) => {
      const exists = prev.interests.includes(interest);
      const updated = exists
        ? prev.interests.filter((i) => i !== interest)
        : [...prev.interests, interest];
      return { ...prev, interests: updated };
    });
    if (errors.interests) {
      setErrors((prev) => ({ ...prev, interests: undefined }));
    }
  };

  const handlePaceSelect = (pace) => {
    setFormData((prev) => ({ ...prev, travel_pace: pace }));
    if (errors.travel_pace) {
      setErrors((prev) => ({ ...prev, travel_pace: undefined }));
    }
  };

  const handleNext = () => {
    let stepErrors = {};
    if (currentStep === 1) stepErrors = validateStep1(formData);
    if (currentStep === 2) stepErrors = validateStep2(formData);
    if (currentStep === 3) stepErrors = validateStep3(formData);

    if (Object.keys(stepErrors).length > 0) {
      setErrors(stepErrors);
      return;
    }

    setErrors({});
    setCurrentStep((prev) => Math.min(prev + 1, 4));
  };

  const handleBack = () => {
    setErrors({});
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    const allErrors = validateFullTrip(formData);
    if (Object.keys(allErrors).length > 0) {
      setErrors(allErrors);
      // jump back to earliest step with error
      if (allErrors.destination || allErrors.start_date || allErrors.end_date || allErrors.budget || allErrors.traveller_count) {
        setCurrentStep(1);
      } else if (allErrors.travel_style || allErrors.interests) {
        setCurrentStep(2);
      } else {
        setCurrentStep(3);
      }
      return;
    }

    setIsSubmitting(true);
    setSubmitError("");

    try {
      const payload = {
        ...formData,
        budget: Number(formData.budget),
        traveller_count: Number(formData.traveller_count),
      };
      const created = await createTrip(payload);
      if (onTripCreated) {
        onTripCreated(created);
      }
    } catch (err) {
      setSubmitError(err.message || "Failed to submit trip preferences. Please ensure backend is running.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="card planner-container">
      <div className="step-indicator">
        <div className={`step-item ${currentStep === 1 ? "active" : currentStep > 1 ? "completed" : ""}`}>
          <div className="step-circle">{currentStep > 1 ? "✓" : "1"}</div>
          <span className="step-label">Basics</span>
        </div>
        <div className={`step-item ${currentStep === 2 ? "active" : currentStep > 2 ? "completed" : ""}`}>
          <div className="step-circle">{currentStep > 2 ? "✓" : "2"}</div>
          <span className="step-label">Style & Interests</span>
        </div>
        <div className={`step-item ${currentStep === 3 ? "active" : currentStep > 3 ? "completed" : ""}`}>
          <div className="step-circle">{currentStep > 3 ? "✓" : "3"}</div>
          <span className="step-label">Pace & Needs</span>
        </div>
        <div className={`step-item ${currentStep === 4 ? "active" : ""}`}>
          <div className="step-circle">4</div>
          <span className="step-label">Review</span>
        </div>
      </div>

      {submitError && (
        <div className="status error" style={{ marginBottom: "1.25rem" }}>
          <strong>Error saving trip:</strong> {submitError}
        </div>
      )}

      {/* STEP 1: Basic Trip Details */}
      {currentStep === 1 && (
        <div className="step-content">
          <h2>Step 1: Trip Basics</h2>
          <p className="muted">Where are you heading and what are your travel parameters?</p>
          <div className="form-grid">
            <div className="form-group full-width">
              <label htmlFor="destination">Destination *</label>
              <input
                id="destination"
                name="destination"
                type="text"
                placeholder="e.g. Kyoto, Japan or Florence, Italy"
                value={formData.destination}
                onChange={handleChange}
                className={errors.destination ? "has-error" : ""}
              />
              {errors.destination && <span className="error-text">{errors.destination}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="start_date">Start Date *</label>
              <input
                id="start_date"
                name="start_date"
                type="date"
                value={formData.start_date}
                onChange={handleChange}
                className={errors.start_date ? "has-error" : ""}
              />
              {errors.start_date && <span className="error-text">{errors.start_date}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="end_date">End Date *</label>
              <input
                id="end_date"
                name="end_date"
                type="date"
                value={formData.end_date}
                onChange={handleChange}
                className={errors.end_date ? "has-error" : ""}
              />
              {errors.end_date && <span className="error-text">{errors.end_date}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="budget">Total Estimated Budget *</label>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  id="budget"
                  name="budget"
                  type="number"
                  min="1"
                  step="10"
                  value={formData.budget}
                  onChange={handleChange}
                  className={errors.budget ? "has-error" : ""}
                  style={{ flex: 2 }}
                />
                <select
                  name="currency"
                  value={formData.currency}
                  onChange={handleChange}
                  style={{ flex: 1 }}
                >
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="INR">INR (₹)</option>
                  <option value="GBP">GBP (£)</option>
                  <option value="JPY">JPY (¥)</option>
                </select>
              </div>
              {errors.budget && <span className="error-text">{errors.budget}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="traveller_count">Number of Travellers *</label>
              <input
                id="traveller_count"
                name="traveller_count"
                type="number"
                min="1"
                max="50"
                value={formData.traveller_count}
                onChange={handleChange}
                className={errors.traveller_count ? "has-error" : ""}
              />
              {errors.traveller_count && <span className="error-text">{errors.traveller_count}</span>}
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: Style & Interests */}
      {currentStep === 2 && (
        <div className="step-content">
          <h2>Step 2: Travel Style & Interests</h2>
          <p className="muted">Tell us what kind of vibe and experiences you enjoy.</p>
          <div className="form-grid">
            <div className="form-group full-width">
              <label htmlFor="travel_style">Travel Style *</label>
              <select
                id="travel_style"
                name="travel_style"
                value={formData.travel_style}
                onChange={handleChange}
              >
                {TRAVEL_STYLES.map((style) => (
                  <option key={style} value={style}>
                    {style}
                  </option>
                ))}
              </select>
              {errors.travel_style && <span className="error-text">{errors.travel_style}</span>}
            </div>

            <div className="form-group full-width">
              <label>Select Your Interests (Multiple Choices) *</label>
              <div className="chips-container">
                {AVAILABLE_INTERESTS.map((interest) => {
                  const isSelected = formData.interests.includes(interest);
                  return (
                    <button
                      key={interest}
                      type="button"
                      className={`chip ${isSelected ? "selected" : ""}`}
                      onClick={() => handleInterestToggle(interest)}
                    >
                      {isSelected ? `✓ ${interest}` : `+ ${interest}`}
                    </button>
                  );
                })}
              </div>
              {errors.interests && <span className="error-text">{errors.interests}</span>}
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: Pace & Special Needs */}
      {currentStep === 3 && (
        <div className="step-content">
          <h2>Step 3: Pace & Preferences</h2>
          <p className="muted">Set your daily activity rhythm and specific dietary or accessibility needs.</p>
          <div className="form-grid">
            <div className="form-group full-width">
              <label>Travel Pace *</label>
              <div className="pace-cards">
                {TRAVEL_PACES.map((p) => {
                  const isSelected = formData.travel_pace === p.value;
                  return (
                    <div
                      key={p.value}
                      className={`pace-card ${isSelected ? "selected" : ""}`}
                      onClick={() => handlePaceSelect(p.value)}
                    >
                      <div className="pace-card-title">
                        {isSelected ? `● ${p.label}` : `○ ${p.label}`}
                      </div>
                      <div className="pace-card-desc">{p.desc}</div>
                    </div>
                  );
                })}
              </div>
              {errors.travel_pace && <span className="error-text">{errors.travel_pace}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="dietary_preference">Dietary Preference *</label>
              <select
                id="dietary_preference"
                name="dietary_preference"
                value={formData.dietary_preference}
                onChange={handleChange}
              >
                {DIETARY_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="mobility_requirements">Mobility / Accessibility Concerns</label>
              <input
                id="mobility_requirements"
                name="mobility_requirements"
                type="text"
                placeholder="e.g. None, Wheelchair accessible, Minimal stairs"
                value={formData.mobility_requirements}
                onChange={handleChange}
              />
            </div>
          </div>
        </div>
      )}

      {/* STEP 4: Review & Additional Notes */}
      {currentStep === 4 && (
        <div className="step-content">
          <h2>Step 4: Review & Submit</h2>
          <p className="muted">Review your personalized preferences before saving.</p>

          <div className="review-summary">
            <div className="review-row">
              <strong>Destination</strong>
              <span>{formData.destination}</span>
            </div>
            <div className="review-row">
              <strong>Dates & Budget</strong>
              <span>
                {formData.start_date} to {formData.end_date} | {formData.budget} {formData.currency} ({formData.traveller_count} traveler{formData.traveller_count > 1 ? "s" : ""})
              </span>
            </div>
            <div className="review-row">
              <strong>Travel Style & Pace</strong>
              <span>
                {formData.travel_style} • {formData.travel_pace} pace
              </span>
            </div>
            <div className="review-row">
              <strong>Diet & Accessibility</strong>
              <span>
                {formData.dietary_preference} • {formData.mobility_requirements || "Standard"}
              </span>
            </div>
            <div className="review-row" style={{ gridColumn: "1 / -1" }}>
              <strong>Selected Interests</strong>
              <span>{formData.interests.length > 0 ? formData.interests.join(", ") : "None"}</span>
            </div>
          </div>

          <div className="form-group" style={{ marginTop: "1.25rem" }}>
            <label htmlFor="notes">Optional Notes or Special Requests</label>
            <textarea
              id="notes"
              name="notes"
              rows={3}
              placeholder="e.g. Celebrating an anniversary, prefer morning tea walks..."
              value={formData.notes}
              onChange={handleChange}
            />
          </div>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="form-actions">
        {currentStep > 1 ? (
          <button type="button" className="btn-secondary" onClick={handleBack} disabled={isSubmitting}>
            ← Back
          </button>
        ) : (
          <div />
        )}

        {currentStep < 4 ? (
          <button type="button" className="btn-primary" onClick={handleNext}>
            Next →
          </button>
        ) : (
          <button type="button" className="btn-primary" onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? "Saving Trip..." : "Save Preferences & Continue"}
          </button>
        )}
      </div>
    </div>
  );
}

export default TripPlannerForm;
