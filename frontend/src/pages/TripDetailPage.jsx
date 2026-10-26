import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getTrip, getItinerary, generateItinerary, refineItinerary } from "../services/tripsAPI.js";
import { buildTripSummaryText, exportTripAsPDF, exportTripAsMarkdown } from "../utils/exportUtils.js";
import ItineraryView from "../components/TripPlanner/ItineraryView.jsx";

// ─── Icon components (no external lib needed) ────────────────────────────────
function Icon({ d, size = 16, color = "currentColor", ...rest }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true" {...rest}>
      <path d={d} />
    </svg>
  );
}
const ICONS = {
  share:    "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13",
  copy:     "M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6H8zM14 2v6h6M10 12h4M10 16h4M10 8h1",
  download: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3",
  edit:     "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z",
  refresh:  "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15",
  back:     "M19 12H5M12 19l-7-7 7-7",
  check:    "M20 6L9 17l-5-5",
  alert:    "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01",
  file:     "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6",
};

// ─── Feedback toast component ─────────────────────────────────────────────────
function Toast({ message, type, onDismiss }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 3500);
    return () => clearTimeout(t);
  }, [onDismiss]);

  const bg = type === "success" ? "#e8f5e9" : type === "error" ? "#fdecec" : "#fff8e6";
  const border = type === "success" ? "#4caf50" : type === "error" ? "#ef5350" : "#ffa726";
  const color = type === "success" ? "#1b5e20" : type === "error" ? "#8a2a2a" : "#8c5800";

  return (
    <div
      role="alert"
      aria-live="polite"
      style={{
        position: "fixed", bottom: "1.5rem", right: "1.5rem", zIndex: 9999,
        background: bg, border: `1.5px solid ${border}`, color, borderRadius: "10px",
        padding: "0.85rem 1.2rem", fontSize: "0.92rem", fontWeight: 600,
        boxShadow: "0 4px 16px rgba(0,0,0,0.12)", maxWidth: "340px",
        display: "flex", alignItems: "center", gap: "0.6rem",
        animation: "toast-in 0.25s ease",
      }}
    >
      {type === "success" && <Icon d={ICONS.check} size={16} color={color} />}
      {type === "error" && <Icon d={ICONS.alert} size={16} color={color} />}
      {message}
    </div>
  );
}

// ─── Action button ────────────────────────────────────────────────────────────
function ActionBtn({ onClick, disabled, label, iconPath, variant = "secondary", title }) {
  const isSecondary = variant === "secondary";
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={title || label}
      className={isSecondary ? "btn-secondary" : "btn-primary"}
      style={{ display: "flex", alignItems: "center", gap: "0.45rem", fontSize: "0.88rem", padding: "0.55rem 1rem" }}
    >
      <Icon d={iconPath} size={15} color={isSecondary ? "#17312f" : "#fff"} />
      {label}
    </button>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function TripDetailPage() {
  const { tripId } = useParams();
  const navigate = useNavigate();

  const [trip, setTrip] = useState(null);
  const [itinerary, setItinerary] = useState(null);
  const [loadingTrip, setLoadingTrip] = useState(true);
  const [loadingItinerary, setLoadingItinerary] = useState(false);
  const [tripError, setTripError] = useState(null);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [toast, setToast] = useState(null);    // { message, type }
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const [shareMenuOpen, setShareMenuOpen] = useState(false);

  const showToast = useCallback((message, type = "success") => {
    setToast({ message, type });
  }, []);

  const dismissToast = useCallback(() => setToast(null), []);

  // ── Fetch trip on mount ──────────────────────────────────────────────────
  useEffect(() => {
    if (!tripId) {
      setTripError("No trip ID provided in the URL.");
      setLoadingTrip(false);
      return;
    }

    async function fetchData() {
      setLoadingTrip(true);
      setTripError(null);
      try {
        const tripData = await getTrip(tripId);
        if (!tripData || !tripData.id) {
          setTripError("Trip not found. It may have been deleted or the ID is incorrect.");
          setLoadingTrip(false);
          return;
        }
        setTrip(tripData);

        // Also attempt to load a pre-existing itinerary (non-blocking)
        setLoadingItinerary(true);
        try {
          const itin = await getItinerary(tripId);
          if (itin && itin.days && itin.days.length > 0) {
            setItinerary(itin);
          }
        } catch {
          // No itinerary yet — that's fine
        } finally {
          setLoadingItinerary(false);
        }
      } catch (err) {
        const status = err.status;
        if (status === 404) {
          setTripError("Trip not found. It may have been removed or the link is invalid.");
        } else if (status >= 500) {
          setTripError("The backend server returned an error. Please try again or check that the API is running.");
        } else if (!status) {
          setTripError("Cannot reach the backend. Please ensure the FastAPI server is running on port 8000.");
        } else {
          setTripError(err.message || "Failed to load trip details.");
        }
      } finally {
        setLoadingTrip(false);
      }
    }

    fetchData();
  }, [tripId]);

  // Close menus on outside click
  useEffect(() => {
    function handleClick() {
      setExportMenuOpen(false);
      setShareMenuOpen(false);
    }
    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, []);

  // ── Share ────────────────────────────────────────────────────────────────
  async function handleShareNative() {
    if (!trip) return;
    const summary = buildTripSummaryText(trip, itinerary);
    const shareData = {
      title: `My trip to ${trip.destination}`,
      text: summary,
    };
    try {
      await navigator.share(shareData);
      showToast("Trip shared successfully!", "success");
    } catch (err) {
      if (err.name !== "AbortError") {
        // Fallback: copy to clipboard
        handleCopyToClipboard();
      }
    }
  }

  async function handleCopyToClipboard() {
    if (!trip) return;
    const summary = buildTripSummaryText(trip, itinerary);
    try {
      await navigator.clipboard.writeText(summary);
      showToast("Trip summary copied to clipboard!", "success");
    } catch {
      // Fallback for older browsers
      const ta = document.createElement("textarea");
      ta.value = summary;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      try {
        document.execCommand("copy");
        showToast("Trip summary copied to clipboard!", "success");
      } catch {
        showToast("Could not copy to clipboard. Please copy the text manually.", "error");
      }
      document.body.removeChild(ta);
    }
  }

  // ── Export ────────────────────────────────────────────────────────────────
  async function handleExportPDF() {
    if (!trip) return;
    try {
      await exportTripAsPDF(trip, itinerary);
      showToast("PDF downloaded successfully!", "success");
    } catch (err) {
      showToast("PDF export failed: " + (err.message || "Unknown error"), "error");
    }
    setExportMenuOpen(false);
  }

  function handleExportMarkdown() {
    if (!trip) return;
    try {
      exportTripAsMarkdown(trip, itinerary);
      showToast("Markdown file downloaded!", "success");
    } catch (err) {
      showToast("Export failed: " + (err.message || "Unknown error"), "error");
    }
    setExportMenuOpen(false);
  }

  // ── Regenerate ────────────────────────────────────────────────────────────
  async function handleRegenerate() {
    if (!trip) return;
    const confirmed = window.confirm(
      "Regenerate the full itinerary? This will replace the current plan with a new AI-generated one.\n\nYour trip preferences will be preserved."
    );
    if (!confirmed) return;

    setIsRegenerating(true);
    try {
      const newItin = await generateItinerary(trip.id);
      setItinerary(newItin);
      showToast("Itinerary regenerated successfully!", "success");
    } catch (err) {
      showToast("Regeneration failed: " + (err.message || "Check AI provider configuration."), "error");
    } finally {
      setIsRegenerating(false);
    }
  }

  // ── Render loading ────────────────────────────────────────────────────────
  if (loadingTrip) {
    return (
      <div style={{ maxWidth: "860px", margin: "0 auto", padding: "2rem 1rem" }}>
        <PageHeader onBack={() => navigate("/")} />
        <div className="card" style={{ marginTop: "1.5rem", textAlign: "center", padding: "3rem" }}>
          <div className="spinner" aria-label="Loading trip details…" />
          <p className="muted" style={{ marginTop: "1rem" }}>Loading trip details…</p>
        </div>
      </div>
    );
  }

  // ── Render error ──────────────────────────────────────────────────────────
  if (tripError) {
    return (
      <div style={{ maxWidth: "860px", margin: "0 auto", padding: "2rem 1rem" }}>
        <PageHeader onBack={() => navigate("/")} />
        <div className="ai-status-card error" style={{ marginTop: "1.5rem" }}>
          <div style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
            <Icon d={ICONS.alert} size={18} color="#8a2a2a" />
            <strong>Error Loading Trip</strong>
          </div>
          <p style={{ margin: "0.3rem 0 0 0", fontSize: "0.92rem" }}>{tripError}</p>
        </div>
        <div style={{ marginTop: "1rem", display: "flex", gap: "0.75rem" }}>
          <ActionBtn label="Go to Dashboard" iconPath={ICONS.back} onClick={() => navigate("/")} />
          <ActionBtn
            label="Try Again"
            iconPath={ICONS.refresh}
            variant="primary"
            onClick={() => window.location.reload()}
          />
        </div>
      </div>
    );
  }

  if (!trip) return null;

  const canShare = typeof navigator !== "undefined" && !!navigator.share;

  return (
    <div style={{ maxWidth: "860px", margin: "0 auto", padding: "1rem 0.75rem 3rem" }}>
      {/* ── Toast notification ─────────────────────────────────────────── */}
      {toast && <Toast message={toast.message} type={toast.type} onDismiss={dismissToast} />}

      {/* ── Page header ────────────────────────────────────────────────── */}
      <PageHeader onBack={() => navigate("/")} />

      {/* ── Action bar ─────────────────────────────────────────────────── */}
      <div
        style={{
          display: "flex", flexWrap: "wrap", gap: "0.6rem", margin: "1rem 0 1.5rem",
          justifyContent: "flex-end",
        }}
      >
        {/* Share button */}
        <div style={{ position: "relative" }}>
          <ActionBtn
            label="Share"
            iconPath={ICONS.share}
            onClick={(e) => { e.stopPropagation(); setShareMenuOpen((o) => !o); setExportMenuOpen(false); }}
            title="Share this trip plan"
          />
          {shareMenuOpen && (
            <DropdownMenu onClose={() => setShareMenuOpen(false)}>
              {canShare && (
                <DropdownItem iconPath={ICONS.share} label="Share via device…" onClick={handleShareNative} />
              )}
              <DropdownItem iconPath={ICONS.copy} label="Copy summary to clipboard" onClick={handleCopyToClipboard} />
            </DropdownMenu>
          )}
        </div>

        {/* Export button */}
        <div style={{ position: "relative" }}>
          <ActionBtn
            label="Download"
            iconPath={ICONS.download}
            onClick={(e) => { e.stopPropagation(); setExportMenuOpen((o) => !o); setShareMenuOpen(false); }}
            title="Export itinerary"
          />
          {exportMenuOpen && (
            <DropdownMenu onClose={() => setExportMenuOpen(false)}>
              <DropdownItem iconPath={ICONS.file} label="Download as PDF" onClick={handleExportPDF} />
              <DropdownItem iconPath={ICONS.file} label="Download as Markdown (.md)" onClick={handleExportMarkdown} />
            </DropdownMenu>
          )}
        </div>

        {/* Edit — navigates back to dashboard with trip in view */}
        <ActionBtn
          label="Edit Trip"
          iconPath={ICONS.edit}
          onClick={() => navigate("/", { state: { editTripId: trip.id } })}
          title="Return to dashboard to edit preferences"
        />

        {/* Regenerate */}
        <ActionBtn
          label={isRegenerating ? "Regenerating…" : "Regenerate"}
          iconPath={ICONS.refresh}
          variant="primary"
          disabled={isRegenerating}
          onClick={handleRegenerate}
          title="Re-generate AI itinerary (replaces current plan after confirmation)"
        />
      </div>

      {/* ── Main content — delegates to ItineraryView ───────────────────── */}
      {/*
        ItineraryView already handles:
          - Trip banner / header display
          - Tabs: itinerary / recommendations / prompt
          - Generate itinerary button
          - Refinement toolbar
          - Day-by-day timeline
        We pass the trip object and a reset callback.
        Itinerary state lives here so the Regenerate action above updates the view.
      */}
      {loadingItinerary && !itinerary ? (
        <div style={{ textAlign: "center", padding: "2rem", color: "#5c6f6d" }}>
          <div className="spinner" />
          <p>Loading saved itinerary…</p>
        </div>
      ) : (
        <ItineraryView
          trip={trip}
          initialItinerary={itinerary}
          onReset={() => navigate("/")}
        />
      )}
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────
function PageHeader({ onBack }) {
  return (
    <header
      style={{
        display: "flex", alignItems: "center", gap: "0.75rem",
        paddingBottom: "1rem", borderBottom: "1px solid #e2d7c3",
        marginBottom: "0.5rem",
      }}
    >
      <button
        onClick={onBack}
        aria-label="Back to dashboard"
        className="btn-secondary"
        style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.88rem", padding: "0.45rem 0.9rem" }}
      >
        <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        Dashboard
      </button>
      <h1 style={{ margin: 0, fontSize: "1.25rem", color: "#17312f", fontWeight: 700 }}>
        Trip Details
      </h1>
    </header>
  );
}

function DropdownMenu({ children, onClose }) {
  return (
    <div
      role="menu"
      onClick={(e) => e.stopPropagation()}
      style={{
        position: "absolute", top: "calc(100% + 6px)", right: 0, zIndex: 999,
        background: "#fff", border: "1.5px solid #e4d9c5", borderRadius: "10px",
        boxShadow: "0 8px 24px rgba(23,49,47,0.12)", padding: "0.4rem",
        minWidth: "220px", display: "flex", flexDirection: "column", gap: "0.1rem",
      }}
    >
      {children}
    </div>
  );
}

function DropdownItem({ iconPath, label, onClick }) {
  return (
    <button
      role="menuitem"
      onClick={onClick}
      style={{
        display: "flex", alignItems: "center", gap: "0.6rem",
        padding: "0.6rem 0.85rem", borderRadius: "7px",
        background: "transparent", color: "#17312f", fontSize: "0.88rem",
        fontWeight: 500, cursor: "pointer", textAlign: "left", width: "100%",
        border: "none", transition: "background 0.12s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.background = "#f4ede0")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
    >
      <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d={iconPath} />
      </svg>
      {label}
    </button>
  );
}
