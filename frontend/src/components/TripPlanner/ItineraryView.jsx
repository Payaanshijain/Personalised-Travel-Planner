import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  generateItinerary,
  getItinerary,
  getRecommendations,
  getPromptPreview,
  refineItinerary,
} from "../../services/tripsAPI.js";

/**
 * ItineraryView
 *
 * Props:
 *  - trip             {Object}       Required. Trip object returned by the API.
 *  - onReset          {Function}     Called when the user clicks "Plan Another Trip".
 *  - initialItinerary {Object|null}  Optional. Pre-loaded itinerary (avoids double-fetch
 *                                   when the parent already has it, e.g. TripDetailPage).
 */
function ItineraryView({ trip, onReset, initialItinerary = null }) {
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState("itinerary");
  const [recommendations, setRecommendations] = useState(null);
  const [itinerary, setItinerary] = useState(initialItinerary);
  const [promptPreview, setPromptPreview] = useState(null);
  const [isLoadingRecs, setIsLoadingRecs] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRefining, setIsRefining] = useState(false);
  const [aiError, setAiError] = useState(null);
  const [selectedDayTab, setSelectedDayTab] = useState("all");
  const [customFeedback, setCustomFeedback] = useState("");
  const [refinementSuccess, setRefinementSuccess] = useState("");

  // When initialItinerary changes (e.g. parent regenerates), sync it down
  useEffect(() => {
    if (initialItinerary) {
      setItinerary(initialItinerary);
    }
  }, [initialItinerary]);

  // Load recommendations and saved itinerary on mount
  useEffect(() => {
    if (trip && trip.id) {
      // Only fetch from API if we did NOT receive an initialItinerary
      if (!initialItinerary) {
        loadSavedItinerary(trip.id);
      }
      loadRecommendations(trip.id);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trip]);

  async function loadRecommendations(tripId) {
    setIsLoadingRecs(true);
    try {
      const data = await getRecommendations(tripId);
      setRecommendations(data);
    } catch (err) {
      console.error("Failed to load recommendations:", err);
    } finally {
      setIsLoadingRecs(false);
    }
  }

  async function loadSavedItinerary(tripId) {
    try {
      const data = await getItinerary(tripId);
      if (data && data.days && data.days.length > 0) {
        setItinerary(data);
      }
    } catch {
      // Itinerary not generated yet — that is fine
    }
  }

  async function handleGenerateItinerary() {
    setIsGenerating(true);
    setAiError(null);
    setRefinementSuccess("");
    try {
      const data = await generateItinerary(trip.id);
      setItinerary(data);
      setActiveTab("itinerary");
    } catch (err) {
      setAiError(err.message || "Failed to generate itinerary. Check AI API key configuration.");
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleApplyRefinement(action, dayNum = null, feedbackText = null) {
    setIsRefining(true);
    setAiError(null);
    setRefinementSuccess("");

    const payload = {
      action: action,
      day_number: dayNum || (selectedDayTab !== "all" ? Number(selectedDayTab) : null),
      feedback: feedbackText || customFeedback || undefined,
    };

    try {
      const res = await refineItinerary(trip.id, payload);
      if (res && res.itinerary) {
        setItinerary(res.itinerary);
        setRefinementSuccess(res.summary_of_changes || "Itinerary refined successfully.");
        if (action === "custom") {
          setCustomFeedback("");
        }
      }
    } catch (err) {
      setAiError(err.message || "Failed to refine itinerary. Verify Groq / AI provider configuration.");
    } finally {
      setIsRefining(false);
    }
  }

  async function handleViewPrompt() {
    if (!promptPreview) {
      try {
        const data = await getPromptPreview(trip.id);
        setPromptPreview(data);
      } catch (err) {
        console.error("Failed to load prompt preview:", err);
      }
    }
    setActiveTab("prompt");
  }

  if (!trip) return null;

  const displayedDays = itinerary && itinerary.days
    ? selectedDayTab === "all"
      ? itinerary.days
      : itinerary.days.filter((d) => d.day_number === Number(selectedDayTab))
    : [];

  return (
    <div className="planner-container itinerary-container">
      {/* Trip Summary Header */}
      <div className="trip-banner">
        <div>
          <h2>✈ {trip.destination}</h2>
          <div className="trip-banner-meta">
            <span>📅 {trip.start_date} → {trip.end_date}</span>
            <span>⏱ {trip.duration_days} day{trip.duration_days !== 1 ? "s" : ""}</span>
            <span>💰 {trip.budget} {trip.currency}</span>
            <span>👥 {trip.traveller_count} traveller{trip.traveller_count !== 1 ? "s" : ""}</span>
            <span>🚶 {trip.travel_pace}</span>
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem", alignItems: "flex-end" }}>
          <button
            className="btn-secondary"
            style={{
              background: "rgba(255,255,255,0.15)", color: "#fff", border: "1px solid rgba(255,255,255,0.4)",
              fontSize: "0.82rem", padding: "0.45rem 0.9rem",
            }}
            onClick={() => navigate(`/trips/${trip.id}`)}
            title="Open full trip details page with share, export and more"
          >
            Full Details & Export →
          </button>
          {onReset && (
            <button
              className="btn-secondary"
              style={{
                background: "rgba(255,255,255,0.15)", color: "#fff", border: "1px solid rgba(255,255,255,0.4)",
                fontSize: "0.82rem", padding: "0.45rem 0.9rem",
              }}
              onClick={onReset}
            >
              ← Plan Another Trip
            </button>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ display: "flex", gap: "0.5rem", borderBottom: "2px solid #e9e1d2", paddingBottom: "0.5rem", flexWrap: "wrap" }}>
        {[
          { key: "itinerary", label: "📅 Itinerary" },
          { key: "recommendations", label: "⭐ Recommendations" },
          { key: "prompt", label: "🤖 AI Prompt" },
        ].map(({ key, label }) => (
          <button
            key={key}
            className={activeTab === key ? "btn-primary" : "btn-secondary"}
            style={{ fontSize: "0.88rem", padding: "0.5rem 1rem" }}
            onClick={() => {
              if (key === "prompt") handleViewPrompt();
              else setActiveTab(key);
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* ITINERARY TAB */}
      {activeTab === "itinerary" && (
        <div style={{ marginTop: "1rem" }}>
          {/* Error State */}
          {aiError && (
            <div className="ai-status-card error" style={{ marginBottom: "1rem" }}>
              <strong>AI Error:</strong> {aiError}
            </div>
          )}

          {/* Refinement success notice */}
          {refinementSuccess && (
            <div className="summary-notice">
              ✅ {refinementSuccess}
            </div>
          )}

          {/* Generate CTA if no itinerary yet */}
          {!itinerary && (
            <div className="ai-status-card warning">
              <strong>No itinerary generated yet.</strong>
              <p style={{ margin: "0.3rem 0 0.75rem 0", fontSize: "0.9rem" }}>
                Click the button below to generate a personalized AI-powered day-by-day travel plan.
              </p>
              <button
                className="btn-primary"
                onClick={handleGenerateItinerary}
                disabled={isGenerating}
              >
                {isGenerating ? "Generating AI Itinerary…" : "🚀 Generate Itinerary"}
              </button>
            </div>
          )}

          {/* Itinerary content */}
          {itinerary && (
            <div>
              {/* Refinement panel */}
              <div className="refinement-panel">
                <div className="refinement-header">
                  <strong>🔧 Refine Itinerary</strong>
                  {isRefining && <span className="muted" style={{ fontSize: "0.85rem" }}>Applying changes…</span>}
                </div>

                <div className="quick-actions-grid">
                  {[
                    { action: "more_relaxed", label: "😌 More Relaxed" },
                    { action: "more_adventurous", label: "🏔 More Adventurous" },
                    { action: "reduce_budget", label: "💸 Reduce Budget" },
                    { action: "more_culture", label: "🎭 More Culture" },
                    { action: "regenerate", label: "🔄 Regenerate All" },
                  ].map(({ action, label }) => (
                    <button
                      key={action}
                      className="quick-chip"
                      disabled={isRefining || isGenerating}
                      onClick={() => handleApplyRefinement(action)}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                <div className="refinement-input-row">
                  <input
                    type="text"
                    placeholder="Custom feedback, e.g. 'Add more food markets on day 2'"
                    value={customFeedback}
                    onChange={(e) => setCustomFeedback(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && customFeedback.trim()) {
                        handleApplyRefinement("custom");
                      }
                    }}
                    disabled={isRefining}
                    aria-label="Custom refinement feedback"
                  />
                  <button
                    className="btn-primary"
                    disabled={isRefining || !customFeedback.trim()}
                    onClick={() => handleApplyRefinement("custom")}
                    style={{ fontSize: "0.85rem", padding: "0.6rem 1rem" }}
                  >
                    Apply
                  </button>
                </div>
              </div>

              {/* Summary stats */}
              {itinerary.total_estimated_cost > 0 && (
                <div style={{ marginBottom: "1rem", padding: "0.75rem 1rem", background: "#eef6f4", border: "1px solid #b7ded5", borderRadius: "8px", fontSize: "0.92rem", color: "#1d4e4a", fontWeight: 600 }}>
                  Estimated Total Cost: ~{itinerary.total_estimated_cost} {itinerary.currency || trip.currency}
                  {itinerary.generation_notes && (
                    <span style={{ fontWeight: 400, color: "#5c6f6d", marginLeft: "0.75rem" }}>
                      · {itinerary.generation_notes}
                    </span>
                  )}
                </div>
              )}

              {/* Day selector bar */}
              <div className="day-selector-bar">
                <button
                  className={`day-tab-btn ${selectedDayTab === "all" ? "active" : ""}`}
                  onClick={() => setSelectedDayTab("all")}
                >
                  All Days
                </button>
                {itinerary.days.map((d) => (
                  <button
                    key={d.day_number}
                    className={`day-tab-btn ${selectedDayTab === String(d.day_number) ? "active" : ""}`}
                    onClick={() => setSelectedDayTab(String(d.day_number))}
                  >
                    Day {d.day_number}
                  </button>
                ))}
              </div>

              {/* Day cards */}
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                {displayedDays.map((day) => {
                  const hasSlotsData =
                    (day.morning_items && day.morning_items.length > 0) ||
                    (day.afternoon_items && day.afternoon_items.length > 0) ||
                    (day.evening_items && day.evening_items.length > 0);

                  return (
                    <div key={day.day_number} className="day-card">
                      <div className="day-header">
                        <h3>
                          Day {day.day_number}
                          {day.date && <span style={{ fontWeight: 400, color: "#5c6f6d", marginLeft: "0.5rem" }}>— {day.date}</span>}
                          {day.theme && <span style={{ fontWeight: 400, color: "#5c6f6d", fontSize: "0.9rem", marginLeft: "0.5rem" }}>| {day.theme}</span>}
                        </h3>
                        <button
                          className="quick-chip"
                          disabled={isRefining || isGenerating}
                          onClick={() => handleApplyRefinement("regenerate_day", day.day_number)}
                          style={{ fontSize: "0.78rem" }}
                        >
                          🔄 Regen Day
                        </button>
                      </div>

                      {hasSlotsData ? (
                        <div>
                          {[
                            { items: day.morning_items, icon: "🌅", label: "Morning" },
                            { items: day.afternoon_items, icon: "☀️", label: "Afternoon" },
                            { items: day.evening_items, icon: "🌙", label: "Evening" },
                          ].map(({ items, icon, label }) =>
                            items && items.length > 0 ? (
                              <div key={label} className="time-slot-group">
                                <div className="slot-heading">
                                  <span className="slot-icon">{icon}</span>
                                  {label}
                                </div>
                                <div className="timeline">
                                  {items.map((item, idx) => (
                                    <ActivityItemCard key={item.id || idx} item={item} currency={trip.currency} />
                                  ))}
                                </div>
                              </div>
                            ) : null
                          )}
                        </div>
                      ) : (
                        <div className="timeline">
                          {day.items.map((item, idx) => (
                            <ActivityItemCard key={item.id || idx} item={item} currency={trip.currency} />
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* RECOMMENDATIONS TAB */}
      {activeTab === "recommendations" && (
        <div style={{ marginTop: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem", flexWrap: "wrap", gap: "0.5rem" }}>
            <div>
              <h3 style={{ margin: "0 0 0.25rem 0", color: "#1d4e4a" }}>
                Personalized Recommendations for {trip.destination}
              </h3>
              <p className="muted" style={{ margin: 0, fontSize: "0.9rem" }}>
                Filtered according to your selected interests ({trip.interests?.join(", ")}), dietary needs ({trip.dietary_preference}), and pace.
              </p>
            </div>
            {!itinerary && (
              <button
                className="btn-primary"
                onClick={handleGenerateItinerary}
                disabled={isGenerating}
              >
                {isGenerating ? "Generating..." : "🚀 Generate Full Itinerary"}
              </button>
            )}
          </div>

          {isLoadingRecs ? (
            <p className="muted">Loading personalized recommendations...</p>
          ) : recommendations && recommendations.categories ? (
            Object.entries(recommendations.categories).map(([category, items]) => (
              <div key={category} style={{ marginBottom: "1.5rem" }}>
                <h4 style={{ color: "#1d4e4a", borderBottom: "1.5px solid #e9e1d2", paddingBottom: "0.3rem" }}>
                  {category} ({items.length})
                </h4>
                <div className="recs-grid">
                  {items.map((item, idx) => (
                    <div key={idx} className="rec-card">
                      <div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem" }}>
                          <h5 className="rec-title">{item.title}</h5>
                          <span className={`badge ${item.is_verified ? "verified" : "unverified"}`}>
                            {item.is_verified ? "Verified" : "Estimated"}
                          </span>
                        </div>
                        <p className="rec-desc">{item.description}</p>
                      </div>
                      <div>
                        {item.match_reasons && item.match_reasons.length > 0 && (
                          <div style={{ display: "flex", gap: "0.3rem", flexWrap: "wrap", marginBottom: "0.4rem" }}>
                            {item.match_reasons.map((reason, rIdx) => (
                              <span key={rIdx} className="badge" style={{ fontSize: "0.72rem" }}>
                                ✓ {reason}
                              </span>
                            ))}
                          </div>
                        )}
                        <div className="rec-meta">
                          <span>📍 {item.location || trip.destination}</span>
                          <span>⏱ {item.duration || "Flexible"}</span>
                          <span>💰 {item.estimated_cost || "Free"}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <p className="muted">No recommendations available for this destination.</p>
          )}
        </div>
      )}

      {/* PROMPT PREVIEW TAB */}
      {activeTab === "prompt" && (
        <div style={{ marginTop: "1rem" }}>
          <h3 style={{ color: "#1d4e4a", marginTop: 0 }}>AI Prompt Engineering & Dynamic Context</h3>
          <p className="muted" style={{ fontSize: "0.9rem" }}>
            This reflects the structured prompt constructed by <code>app/services/prompt_builder.py</code>,
            applying deterministic pace rules ({trip.travel_pace}), dietary mandates ({trip.dietary_preference}),
            and prompt injection defenses.
          </p>
          {promptPreview ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <h4 style={{ margin: "0 0 0.3rem 0", color: "#1d4e4a" }}>System Prompt (Role, Constraints & Schema):</h4>
                <pre style={{ background: "#222", color: "#8be9fd", padding: "1rem", borderRadius: "8px", overflowX: "auto", fontSize: "0.85rem", whiteSpace: "pre-wrap" }}>
                  {promptPreview.system_prompt}
                </pre>
              </div>
              <div>
                <h4 style={{ margin: "0 0 0.3rem 0", color: "#1d4e4a" }}>User Prompt (Context & Requirements):</h4>
                <pre style={{ background: "#222", color: "#f1fa8c", padding: "1rem", borderRadius: "8px", overflowX: "auto", fontSize: "0.85rem", whiteSpace: "pre-wrap" }}>
                  {promptPreview.user_prompt}
                </pre>
              </div>
            </div>
          ) : (
            <p className="muted">Loading prompt preview...</p>
          )}
        </div>
      )}
    </div>
  );
}

// Activity Item Card Component
function ActivityItemCard({ item, currency }) {
  return (
    <div style={{ marginBottom: "0.75rem" }}>
      <div className="timeline-item">
        <div className="timeline-time">
          <div>{item.start_time || "Scheduled"}</div>
          {item.end_time && (
            <div style={{ fontSize: "0.75rem", color: "#7a8c8a", fontWeight: "normal" }}>
              until {item.end_time}
            </div>
          )}
        </div>
        <div className="timeline-content">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.5rem" }}>
            <h4>{item.title}</h4>
            <span className={`badge ${item.is_verified ? "verified" : "unverified"}`}>
              {item.is_verified ? "Verified Details" : "Estimated"}
            </span>
          </div>

          {item.description && <p>{item.description}</p>}

          <div className="item-badges">
            {item.location && <span className="badge">📍 {item.location}</span>}
            {item.category && <span className="badge">🏷 {item.category}</span>}
            {item.duration && <span className="badge">⏱ {item.duration}</span>}
            {item.estimated_cost !== undefined && (
              <span className="badge">💰 ~{item.estimated_cost} {currency}</span>
            )}
            {item.accessibility_notes && (
              <span className="badge" style={{ background: "#e8f0fe", color: "#1967d2" }}>
                ♿ {item.accessibility_notes}
              </span>
            )}
          </div>

          {item.notes && (
            <p style={{ margin: "0.4rem 0 0 0", fontSize: "0.82rem", fontStyle: "italic", color: "#5a6e6b" }}>
              💡 Tip: {item.notes}
            </p>
          )}
        </div>
      </div>

      {item.transit_info && (
        <div className="transit-banner">
          <span>🚌 Transit Buffer:</span>
          <span>{item.transit_info}</span>
        </div>
      )}
    </div>
  );
}

export default ItineraryView;
