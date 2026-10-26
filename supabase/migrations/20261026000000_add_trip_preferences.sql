-- Migration: 20261026000000_add_trip_preferences.sql
-- Add travel preference columns to trips and metadata to itinerary_items

ALTER TABLE trips 
  ADD COLUMN IF NOT EXISTS traveller_count INTEGER NOT NULL DEFAULT 1 CHECK (traveller_count > 0),
  ADD COLUMN IF NOT EXISTS currency TEXT NOT NULL DEFAULT 'USD',
  ADD COLUMN IF NOT EXISTS interests TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS dietary_preference TEXT DEFAULT 'No preference',
  ADD COLUMN IF NOT EXISTS travel_pace TEXT DEFAULT 'Moderate',
  ADD COLUMN IF NOT EXISTS mobility_requirements TEXT DEFAULT 'None';

ALTER TABLE itinerary_items
  ADD COLUMN IF NOT EXISTS category TEXT,
  ADD COLUMN IF NOT EXISTS estimated_cost NUMERIC DEFAULT 0,
  ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_trips_user_id ON trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_created_at ON trips(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_itinerary_items_trip_id ON itinerary_items(trip_id);
CREATE INDEX IF NOT EXISTS idx_itinerary_items_day ON itinerary_items(trip_id, day_number);
