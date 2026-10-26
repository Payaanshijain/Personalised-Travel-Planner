-- Migration: 002_itinerary_refinements.sql
-- Description: Add time-slots, transit estimation, duration, notes, and refinement fields.
-- Safe and additive migration: does not drop or recreate existing tables.

-- 1. Add itinerary metadata columns to 'trips' table
ALTER TABLE trips 
  ADD COLUMN IF NOT EXISTS model_used TEXT,
  ADD COLUMN IF NOT EXISTS generation_notes TEXT,
  ADD COLUMN IF NOT EXISTS route_optimized BOOLEAN DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS total_estimated_cost NUMERIC DEFAULT 0;

-- 2. Add time-slot, timing, and transit metadata to 'itinerary_items' table
ALTER TABLE itinerary_items
  ADD COLUMN IF NOT EXISTS time_slot TEXT DEFAULT 'Morning',
  ADD COLUMN IF NOT EXISTS end_time TEXT,
  ADD COLUMN IF NOT EXISTS duration TEXT,
  ADD COLUMN IF NOT EXISTS transit_info TEXT,
  ADD COLUMN IF NOT EXISTS notes TEXT,
  ADD COLUMN IF NOT EXISTS accessibility_notes TEXT;

-- 3. Add index on time_slot for filtering
CREATE INDEX IF NOT EXISTS idx_itinerary_items_timeslot ON itinerary_items(trip_id, time_slot);
