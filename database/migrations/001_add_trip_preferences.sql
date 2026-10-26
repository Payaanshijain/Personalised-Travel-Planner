-- Migration: 001_add_trip_preferences.sql
-- Description: Add travel preference columns to the trips table and metadata to itinerary_items.
-- Safe and additive migration: does not drop or recreate existing tables.

-- 1. Add travel preference columns to the 'trips' table
ALTER TABLE trips 
  ADD COLUMN IF NOT EXISTS traveller_count INTEGER NOT NULL DEFAULT 1 CHECK (traveller_count > 0),
  ADD COLUMN IF NOT EXISTS currency TEXT NOT NULL DEFAULT 'USD',
  ADD COLUMN IF NOT EXISTS interests TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS dietary_preference TEXT DEFAULT 'No preference',
  ADD COLUMN IF NOT EXISTS travel_pace TEXT DEFAULT 'Moderate',
  ADD COLUMN IF NOT EXISTS mobility_requirements TEXT DEFAULT 'None';

-- 2. Add extra metadata fields to 'itinerary_items' table for enriched recommendations
ALTER TABLE itinerary_items
  ADD COLUMN IF NOT EXISTS category TEXT,
  ADD COLUMN IF NOT EXISTS estimated_cost NUMERIC DEFAULT 0,
  ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;

-- 3. Add performance indexes for lookups
CREATE INDEX IF NOT EXISTS idx_trips_user_id ON trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_created_at ON trips(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_itinerary_items_trip_id ON itinerary_items(trip_id);
CREATE INDEX IF NOT EXISTS idx_itinerary_items_day ON itinerary_items(trip_id, day_number);

-- 4. Enable Row Level Security (RLS) policies if running on Supabase
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE itinerary_items ENABLE ROW LEVEL SECURITY;

-- Note: In Supabase, if authentication is used:
-- CREATE POLICY "Users can manage their own trips" ON trips
--   FOR ALL USING (auth.uid() = user_id);
-- CREATE POLICY "Users can view itinerary for their trips" ON itinerary_items
--   FOR ALL USING (EXISTS (SELECT 1 FROM trips WHERE trips.id = itinerary_items.trip_id AND trips.user_id = auth.uid()));
