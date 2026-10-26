import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { checkBackendHealth } from "../services/api.js";
import { getTrips, getTrip } from "../services/tripsAPI.js";
import TripPlannerForm from "../components/TripPlanner/TripPlannerForm.jsx";
import ItineraryView from "../components/TripPlanner/ItineraryView.jsx";

function HomePage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [backendStatus, setBackendStatus] = useState(null);
  const [isCheckingBackend, setIsCheckingBackend] = useState(false);
  const [activeTrip, setActiveTrip] = useState(null);
  const [recentTrips, setRecentTrips] = useState([]);
  const [viewMode, setViewMode] = useState("form"); // 'form' or 'recent'
  const [isLoadingEditTrip, setIsLoadingEditTrip] = useState(false);

  useEffect(() => {
    checkHealth();
    loadRecentTrips();
  }, []);

  // Handle navigation state from TripDetailPage "Edit Trip" action
  useEffect(() => {
    const state = location.state;
    if (state && state.editTripId) {
      setIsLoadingEditTrip(true);
      getTrip(state.editTripId)
        .then((trip) => {
          if (trip) {
            setActiveTrip(trip);
            setViewMode("form");
          }
        })
        .catch(() => {
          // Trip may not be available; just go to form
        })
        .finally(() => setIsLoadingEditTrip(false));
      // Clear location state to prevent re-trigger on refresh
      window.history.replaceState({}, "", "/");
    }
  }, [location.state]);

  async function checkHealth() {
    setIsCheckingBackend(true);
    try {
      const data = await checkBackendHealth();
      setBackendStatus({ ok: true, message: data.message || "FastAPI Backend Online" });
    } catch {
      setBackendStatus({
        ok: false,
        message: "FastAPI Backend is offline. Start the backend with: uvicorn app.main:app --port 8000",
      });
    } finally {
      setIsCheckingBackend(false);
    }
  }

  async function loadRecentTrips() {
    try {
      const data = await getTrips();
      if (data && data.trips) {
        setRecentTrips(data.trips);
      }
    } catch {
      // Backend not reached or no trips yet
    }
  }

  const handleTripCreated = (newTrip) => {
    setActiveTrip(newTrip);
    loadRecentTrips();
  };

  const handleSelectRecentTrip = (trip) => {
    setActiveTrip(trip);
    setViewMode("form");
  };

  const handleViewTripDetails = (tripId) => {
    navigate(`/trips/${tripId}`);
  };

  const handlePlanNewTrip = () => {
    setActiveTrip(null);
    setViewMode("form");
  };

  return (
    <div style={{ maxWidth: "860px", margin: "0 auto", padding: "1rem 0" }}>
      {/* Top Navigation & Status Bar */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          marginBottom: "1.5rem",
          paddingBottom: "1rem",
          borderBottom: "1px solid #e2d7c3",
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: "1.6rem", color: "#17312f" }}>
            Personalised Travel Itinerary Planner
          </h1>
          <p className="muted" style={{ margin: "0.2rem 0 0 0", fontSize: "0.9rem" }}>
            AI-Powered Personalized Travel Schedules & Route Optimization
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {backendStatus && (
            <span
              className={`badge ${backendStatus.ok ? "verified" : "unverified"}`}
              style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}
            >
              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  background: backendStatus.ok ? "#2e7d32" : "#c62828",
                }}
              />
              {backendStatus.ok ? "API Connected" : "API Offline"}
            </span>
          )}

          <button
            className="btn-secondary"
            onClick={checkHealth}
            disabled={isCheckingBackend}
            style={{ fontSize: "0.8rem", padding: "0.4rem 0.8rem" }}
          >
            {isCheckingBackend ? "Checking..." : "Ping API"}
          </button>
        </div>
      </header>

      {/* Backend Alert if offline */}
      {backendStatus && !backendStatus.ok && (
        <div className="status error" style={{ marginBottom: "1.5rem" }}>
          <strong>Notice:</strong> {backendStatus.message}
        </div>
      )}

      {/* Loading edit trip indicator */}
      {isLoadingEditTrip && (
        <div className="status" style={{ marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <div className="spinner" style={{ width: "16px", height: "16px", borderWidth: "2px" }} />
          Loading trip for editing…
        </div>
      )}

      {/* Active Trip Results View */}
      {activeTrip ? (
        <ItineraryView trip={activeTrip} onReset={handlePlanNewTrip} />
      ) : (
        /* Form & Recent Trips Navigation */
        <div>
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
            <button
              className={viewMode === "form" ? "btn-primary" : "btn-secondary"}
              onClick={() => setViewMode("form")}
            >
              Plan a New Trip
            </button>
            <button
              className={viewMode === "recent" ? "btn-primary" : "btn-secondary"}
              onClick={() => {
                setViewMode("recent");
                loadRecentTrips();
              }}
            >
              Saved Trips ({recentTrips.length})
            </button>
          </div>

          {viewMode === "form" ? (
            <TripPlannerForm onTripCreated={handleTripCreated} />
          ) : (
            <div className="card">
              <h2>Saved Trips</h2>
              <p className="muted">Previously created trips in the current session/database:</p>
              {recentTrips.length === 0 ? (
                <p className="muted">No trips found. Use the planner to create your first trip!</p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginTop: "1rem" }}>
                  {recentTrips.map((t) => (
                    <div
                      key={t.id}
                      style={{
                        padding: "1rem",
                        border: "1.5px solid #e4d9c5",
                        borderRadius: "10px",
                        background: "#fff",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        flexWrap: "wrap",
                        gap: "0.75rem",
                      }}
                    >
                      <div>
                        <h3 style={{ margin: "0 0 0.25rem 0", color: "#1d4e4a", fontSize: "1.1rem" }}>
                          {t.destination}
                        </h3>
                        <div className="muted" style={{ fontSize: "0.85rem" }}>
                          📅 {t.start_date} to {t.end_date} ({t.duration_days} days)
                          &nbsp;·&nbsp; 💰 {t.budget} {t.currency}
                          &nbsp;·&nbsp; 🚶 {t.travel_pace} pace
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                        <button
                          className="btn-secondary"
                          style={{ fontSize: "0.85rem", padding: "0.5rem 1rem" }}
                          onClick={() => handleSelectRecentTrip(t)}
                        >
                          Quick View
                        </button>
                        <button
                          className="btn-primary"
                          style={{ fontSize: "0.85rem", padding: "0.5rem 1rem" }}
                          onClick={() => handleViewTripDetails(t.id)}
                        >
                          Full Details →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default HomePage;
