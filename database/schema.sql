-- Starter schema for Supabase.
-- This file only describes tables. It does not contain API keys, passwords, or connection secrets.
-- We have not connected the live Supabase project yet.

create table if not exists profiles (
  id uuid primary key default gen_random_uuid(),
  full_name text,
  created_at timestamptz not null default now()
);

create table if not exists trips (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles (id) on delete cascade,
  destination text not null,
  start_date date,
  end_date date,
  budget numeric,
  travel_style text,
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists itinerary_items (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid not null references trips (id) on delete cascade,
  day_number integer not null,
  title text not null,
  description text,
  location text,
  start_time time,
  created_at timestamptz not null default now()
);
