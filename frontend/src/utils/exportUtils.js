/**
 * exportUtils.js
 * Utilities for building trip summary text (share), PDF export, and Markdown export.
 * Uses jsPDF for PDF generation (installed: npm install jspdf).
 * No server-side calls. No secrets exposed. Operates entirely client-side on data
 * already loaded into the React component.
 */

// ─── Text summary (for share / clipboard) ─────────────────────────────────────

/**
 * Builds a readable plain-text trip summary suitable for sharing via
 * Web Share API or clipboard. Includes all available fields from the
 * actual database schema without exposing private data.
 *
 * @param {Object} trip      - Trip object from getTrip()
 * @param {Object|null} itinerary - Itinerary object from getItinerary(), or null
 * @returns {string}
 */
export function buildTripSummaryText(trip, itinerary) {
  if (!trip) return "";

  const lines = [];
  lines.push("✈️  MY TRAVEL ITINERARY");
  lines.push("═".repeat(40));
  lines.push(`Destination:   ${trip.destination}`);
  lines.push(`Dates:         ${trip.start_date} → ${trip.end_date} (${trip.duration_days} day${trip.duration_days !== 1 ? "s" : ""})`);
  lines.push(`Budget:        ${trip.budget} ${trip.currency}`);
  lines.push(`Travellers:    ${trip.traveller_count}`);
  lines.push(`Travel Style:  ${trip.travel_style}`);
  lines.push(`Pace:          ${trip.travel_pace}`);
  if (trip.interests && trip.interests.length > 0) {
    lines.push(`Interests:     ${trip.interests.join(", ")}`);
  }
  if (trip.dietary_preference && trip.dietary_preference !== "No preference") {
    lines.push(`Dietary:       ${trip.dietary_preference}`);
  }
  if (trip.mobility_requirements && trip.mobility_requirements !== "None") {
    lines.push(`Mobility:      ${trip.mobility_requirements}`);
  }
  if (trip.notes) {
    lines.push(`Notes:         ${trip.notes}`);
  }

  if (itinerary && itinerary.days && itinerary.days.length > 0) {
    lines.push("");
    lines.push("─".repeat(40));
    lines.push("📅  DAY-BY-DAY ITINERARY");
    lines.push("─".repeat(40));

    if (itinerary.total_estimated_cost > 0) {
      lines.push(`Estimated Cost: ~${itinerary.total_estimated_cost} ${itinerary.currency || trip.currency}`);
    }
    lines.push("");

    for (const day of itinerary.days) {
      lines.push(`DAY ${day.day_number}${day.date ? " — " + day.date : ""}${day.theme ? " | " + day.theme : ""}`);

      const allItems = [
        ...(day.morning_items || []),
        ...(day.afternoon_items || []),
        ...(day.evening_items || []),
        ...(day.items && day.morning_items == null ? day.items : []),
      ].filter(Boolean);

      // De-duplicate if both flat items and slot arrays are present
      const seen = new Set();
      const deduped = [];
      for (const item of allItems) {
        const key = item.title + (item.start_time || "");
        if (!seen.has(key)) {
          seen.add(key);
          deduped.push(item);
        }
      }

      for (const item of deduped) {
        const time = item.start_time ? `[${item.start_time}${item.end_time ? " – " + item.end_time : ""}]` : "";
        lines.push(`  ${time ? time + " " : ""}• ${item.title}${item.location ? " @ " + item.location : ""}`);
        if (item.description) {
          lines.push(`    ${item.description}`);
        }
        if (item.notes) {
          lines.push(`    💡 ${item.notes}`);
        }
        if (item.transit_info) {
          lines.push(`    🚌 ${item.transit_info}`);
        }
      }
      lines.push("");
    }
  } else {
    lines.push("");
    lines.push("(Itinerary not yet generated)");
  }

  lines.push("─".repeat(40));
  lines.push("Generated with Personalised Travel Itinerary Planner");

  return lines.join("\n");
}

// ─── PDF Export ────────────────────────────────────────────────────────────────

/**
 * Exports the trip as a formatted PDF file using jsPDF.
 * Downloads automatically; no server communication.
 *
 * @param {Object} trip
 * @param {Object|null} itinerary
 */
export async function exportTripAsPDF(trip, itinerary) {
  // Dynamic import keeps jsPDF out of the initial bundle
  const { jsPDF } = await import("jspdf");

  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });

  const PAGE_W = 210;
  const MARGIN = 18;
  const CONTENT_W = PAGE_W - MARGIN * 2;
  let y = MARGIN;

  // ── Colours ──────────────────────────────────────────────────────────────
  const DARK_GREEN = [29, 78, 74];    // #1d4e4a
  const LIGHT_GREEN = [238, 246, 244]; // #eef6f4
  const MID_GREEN = [93, 130, 126];
  const CREAM = [243, 239, 230];      // #f3efe6
  const TEXT_DARK = [23, 49, 47];
  const TEXT_MID = [90, 110, 107];
  const WHITE = [255, 255, 255];

  // ── Helpers ───────────────────────────────────────────────────────────────
  function checkPageBreak(needed = 10) {
    if (y + needed > 285) {
      doc.addPage();
      y = MARGIN;
    }
  }

  function setColor(rgb, type = "fill") {
    if (type === "fill") doc.setFillColor(...rgb);
    else doc.setTextColor(...rgb);
  }

  function addText(text, x, size = 10, style = "normal", maxWidth = null, color = TEXT_DARK) {
    doc.setFontSize(size);
    doc.setFont("helvetica", style);
    setColor(color, "text");
    if (maxWidth) {
      const lines = doc.splitTextToSize(String(text), maxWidth);
      doc.text(lines, x, y);
      return lines.length * size * 0.353 + (lines.length > 1 ? 1.5 : 0);
    }
    doc.text(String(text), x, y);
    return size * 0.353;
  }

  // ── Cover header block ────────────────────────────────────────────────────
  setColor(DARK_GREEN);
  doc.roundedRect(MARGIN, y, CONTENT_W, 40, 4, 4, "F");

  doc.setFontSize(20);
  doc.setFont("helvetica", "bold");
  setColor(WHITE, "text");
  doc.text("✈  " + trip.destination, MARGIN + 8, y + 14);

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  doc.text(`${trip.start_date}  →  ${trip.end_date}  (${trip.duration_days} day${trip.duration_days !== 1 ? "s" : ""})`, MARGIN + 8, y + 23);
  doc.text(`Budget: ${trip.budget} ${trip.currency}  •  Travellers: ${trip.traveller_count}  •  Pace: ${trip.travel_pace}`, MARGIN + 8, y + 30);
  doc.text(`Style: ${trip.travel_style}`, MARGIN + 8, y + 37);
  y += 48;

  // ── Trip details block ────────────────────────────────────────────────────
  if (trip.interests && trip.interests.length > 0) {
    checkPageBreak(10);
    const h = addText("Interests: " + trip.interests.join(", "), MARGIN, 9, "normal", CONTENT_W, MID_GREEN);
    y += h + 3;
  }
  if (trip.dietary_preference && trip.dietary_preference !== "No preference") {
    checkPageBreak(8);
    const h = addText("Dietary: " + trip.dietary_preference, MARGIN, 9, "normal", CONTENT_W, MID_GREEN);
    y += h + 2;
  }
  if (trip.mobility_requirements && trip.mobility_requirements !== "None") {
    checkPageBreak(8);
    const h = addText("Mobility: " + trip.mobility_requirements, MARGIN, 9, "normal", CONTENT_W, MID_GREEN);
    y += h + 2;
  }
  if (trip.notes) {
    checkPageBreak(12);
    const h = addText("Notes: " + trip.notes, MARGIN, 9, "italic", CONTENT_W, TEXT_MID);
    y += h + 4;
  }

  // ── Cost summary ──────────────────────────────────────────────────────────
  if (itinerary && itinerary.total_estimated_cost > 0) {
    checkPageBreak(8);
    setColor(LIGHT_GREEN);
    doc.roundedRect(MARGIN, y - 1, CONTENT_W, 9, 2, 2, "F");
    addText(`Estimated Total Cost: ~${itinerary.total_estimated_cost} ${itinerary.currency || trip.currency}`, MARGIN + 4, 10, "bold", null, DARK_GREEN);
    y += 12;
  }

  // ── Divider ───────────────────────────────────────────────────────────────
  y += 2;
  setColor(DARK_GREEN);
  doc.line(MARGIN, y, PAGE_W - MARGIN, y);
  y += 5;

  // ── Day-by-day itinerary ──────────────────────────────────────────────────
  if (itinerary && itinerary.days && itinerary.days.length > 0) {
    for (const day of itinerary.days) {
      checkPageBreak(18);

      // Day heading pill
      setColor(CREAM);
      doc.roundedRect(MARGIN, y - 3, CONTENT_W, 12, 3, 3, "F");
      doc.setFontSize(11);
      doc.setFont("helvetica", "bold");
      setColor(DARK_GREEN, "text");
      const dayLabel = `Day ${day.day_number}${day.date ? "  —  " + day.date : ""}${day.theme ? "   |   " + day.theme : ""}`;
      doc.text(dayLabel, MARGIN + 4, y + 5);
      y += 14;

      const allItems = [
        ...(day.morning_items || []),
        ...(day.afternoon_items || []),
        ...(day.evening_items || []),
        ...(day.items && !day.morning_items ? day.items : []),
      ].filter(Boolean);

      const seen = new Set();
      const deduped = [];
      for (const item of allItems) {
        const key = item.title + (item.start_time || "");
        if (!seen.has(key)) { seen.add(key); deduped.push(item); }
      }

      for (const item of deduped) {
        checkPageBreak(14);

        // Time badge
        if (item.start_time) {
          setColor([29, 78, 74]);
          doc.roundedRect(MARGIN, y - 3, 26, 7, 1.5, 1.5, "F");
          doc.setFontSize(8);
          doc.setFont("helvetica", "bold");
          setColor(WHITE, "text");
          doc.text(item.start_time, MARGIN + 2, y + 1.5);
        }

        const titleX = item.start_time ? MARGIN + 30 : MARGIN + 3;
        const titleW = item.start_time ? CONTENT_W - 30 : CONTENT_W - 3;

        // Title
        const th = addText(item.title, titleX, 10, "bold", titleW, TEXT_DARK);
        y += th + 2;

        // Location / category / cost
        const metaParts = [];
        if (item.location) metaParts.push("📍 " + item.location);
        if (item.category) metaParts.push("🏷 " + item.category);
        if (item.estimated_cost > 0) metaParts.push(`~${item.estimated_cost} ${trip.currency}`);
        if (metaParts.length > 0) {
          checkPageBreak(6);
          const mh = addText(metaParts.join("   "), MARGIN + 3, 8, "normal", CONTENT_W - 3, MID_GREEN);
          y += mh + 2;
        }

        // Description
        if (item.description) {
          checkPageBreak(8);
          const dh = addText(item.description, MARGIN + 3, 9, "normal", CONTENT_W - 3, TEXT_MID);
          y += dh + 2;
        }

        // Notes / tips
        if (item.notes) {
          checkPageBreak(8);
          const nh = addText("💡 " + item.notes, MARGIN + 3, 8, "italic", CONTENT_W - 3, TEXT_MID);
          y += nh + 2;
        }

        // Transit
        if (item.transit_info) {
          checkPageBreak(6);
          const txh = addText("🚌 " + item.transit_info, MARGIN + 3, 8, "normal", CONTENT_W - 3, TEXT_MID);
          y += txh + 2;
        }

        y += 3;
      }

      y += 4;
    }
  } else {
    checkPageBreak(12);
    addText("No itinerary generated yet. Use the app to generate your AI-powered schedule.", MARGIN, 10, "italic", CONTENT_W, TEXT_MID);
    y += 10;
  }

  // ── Footer ────────────────────────────────────────────────────────────────
  const totalPages = doc.internal.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setFont("helvetica", "normal");
    setColor(TEXT_MID, "text");
    doc.text(`Personalised Travel Itinerary Planner   •   Page ${i} of ${totalPages}`, PAGE_W / 2, 292, { align: "center" });
  }

  // ── Save ──────────────────────────────────────────────────────────────────
  const safeDestination = trip.destination.replace(/[^a-zA-Z0-9 _-]/g, "").trim().replace(/\s+/g, "-");
  doc.save(`trip-${safeDestination}-${trip.start_date}.pdf`);
}

// ─── Markdown Export ───────────────────────────────────────────────────────────

/**
 * Exports the trip as a Markdown (.md) file.
 * Triggers a browser download. No server communication.
 *
 * @param {Object} trip
 * @param {Object|null} itinerary
 */
export function exportTripAsMarkdown(trip, itinerary) {
  const lines = [];
  lines.push(`# ✈️ ${trip.destination} — Travel Itinerary`);
  lines.push("");
  lines.push("## Trip Overview");
  lines.push(`| Field | Value |`);
  lines.push(`|---|---|`);
  lines.push(`| **Destination** | ${trip.destination} |`);
  lines.push(`| **Dates** | ${trip.start_date} → ${trip.end_date} (${trip.duration_days} days) |`);
  lines.push(`| **Budget** | ${trip.budget} ${trip.currency} |`);
  lines.push(`| **Travellers** | ${trip.traveller_count} |`);
  lines.push(`| **Style** | ${trip.travel_style} |`);
  lines.push(`| **Pace** | ${trip.travel_pace} |`);
  if (trip.interests && trip.interests.length > 0) {
    lines.push(`| **Interests** | ${trip.interests.join(", ")} |`);
  }
  if (trip.dietary_preference && trip.dietary_preference !== "No preference") {
    lines.push(`| **Dietary** | ${trip.dietary_preference} |`);
  }
  if (trip.mobility_requirements && trip.mobility_requirements !== "None") {
    lines.push(`| **Mobility** | ${trip.mobility_requirements} |`);
  }
  if (trip.notes) {
    lines.push("");
    lines.push(`> **Notes:** ${trip.notes}`);
  }

  if (itinerary && itinerary.total_estimated_cost > 0) {
    lines.push("");
    lines.push(`> **Estimated Total Cost:** ~${itinerary.total_estimated_cost} ${itinerary.currency || trip.currency}`);
  }

  if (itinerary && itinerary.days && itinerary.days.length > 0) {
    lines.push("");
    lines.push("---");
    lines.push("");
    lines.push("## Day-by-Day Itinerary");

    for (const day of itinerary.days) {
      lines.push("");
      const header = `### Day ${day.day_number}${day.date ? " — " + day.date : ""}${day.theme ? " | *" + day.theme + "*" : ""}`;
      lines.push(header);
      lines.push("");

      const allItems = [
        ...(day.morning_items || []),
        ...(day.afternoon_items || []),
        ...(day.evening_items || []),
        ...(day.items && !day.morning_items ? day.items : []),
      ].filter(Boolean);

      const seen = new Set();
      const deduped = [];
      for (const item of allItems) {
        const key = item.title + (item.start_time || "");
        if (!seen.has(key)) { seen.add(key); deduped.push(item); }
      }

      for (const item of deduped) {
        const timeStr = item.start_time
          ? `\`${item.start_time}${item.end_time ? " – " + item.end_time : ""}\` `
          : "";
        lines.push(`#### ${timeStr}${item.title}`);

        const meta = [];
        if (item.location) meta.push(`📍 ${item.location}`);
        if (item.category) meta.push(`🏷 ${item.category}`);
        if (item.duration) meta.push(`⏱ ${item.duration}`);
        if (item.estimated_cost > 0) meta.push(`~${item.estimated_cost} ${trip.currency}`);
        if (meta.length > 0) {
          lines.push(meta.join("   ·   "));
          lines.push("");
        }

        if (item.description) {
          lines.push(item.description);
          lines.push("");
        }
        if (item.notes) {
          lines.push(`> 💡 **Tip:** ${item.notes}`);
          lines.push("");
        }
        if (item.transit_info) {
          lines.push(`> 🚌 **Transit:** ${item.transit_info}`);
          lines.push("");
        }
        if (item.accessibility_notes) {
          lines.push(`> ♿ **Accessibility:** ${item.accessibility_notes}`);
          lines.push("");
        }
      }
    }
  } else {
    lines.push("");
    lines.push("*No itinerary generated yet.*");
  }

  lines.push("");
  lines.push("---");
  lines.push("");
  lines.push("*Generated with Personalised Travel Itinerary Planner*");

  const content = lines.join("\n");
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const safeDestination = trip.destination.replace(/[^a-zA-Z0-9 _-]/g, "").trim().replace(/\s+/g, "-");
  a.href = url;
  a.download = `trip-${safeDestination}-${trip.start_date}.md`;
  a.click();
  URL.revokeObjectURL(url);
}
