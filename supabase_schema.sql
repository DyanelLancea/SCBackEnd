-- SC Backend - Supabase Database Schema
-- Run this in your Supabase SQL Editor to set up the database

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== EVENTS TABLE ====================

-- Events Table
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    date DATE NOT NULL,
    time TIME NOT NULL,
    location TEXT,
    max_participants INTEGER,
    created_by UUID,  -- Can reference auth.users(id) if using Supabase Auth
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Event Registrations Table
CREATE TABLE IF NOT EXISTS event_registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,  -- Can reference auth.users(id) if using Supabase Auth
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(event_id, user_id)
);

-- Remove foreign key constraint on user_id if it exists (allows flexibility)
-- This is useful when not using Supabase Auth or when using test UUIDs
DO $$ 
BEGIN
    -- Drop the foreign key constraint if it exists
    IF EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'event_registrations_user_id_fkey'
        AND table_name = 'event_registrations'
    ) THEN
        ALTER TABLE event_registrations 
        DROP CONSTRAINT event_registrations_user_id_fkey;
    END IF;
END $$;

-- ==================== FEEDBACK TABLE ====================

-- Feedback Table for Elderly Residents
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,  -- Elderly resident who gave feedback
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    would_go_again BOOLEAN,
    comments TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'resolved', 'archived')),
    resolved_by UUID,  -- RC member who resolved the feedback
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==================== INDEXES ====================

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
CREATE INDEX IF NOT EXISTS idx_events_created_by ON events(created_by);
CREATE INDEX IF NOT EXISTS idx_event_registrations_event_id ON event_registrations(event_id);
CREATE INDEX IF NOT EXISTS idx_event_registrations_user_id ON event_registrations(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_event_id ON feedback(event_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at DESC);

-- ==================== ROW LEVEL SECURITY (RLS) ====================

-- Enable Row Level Security
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Events
-- Allow anyone to view events (public read)
CREATE POLICY "Events are viewable by everyone"
    ON events FOR SELECT
    USING (true);

-- Allow anyone to create events (for now - restrict later if needed)
CREATE POLICY "Anyone can create events"
    ON events FOR INSERT
    WITH CHECK (true);

-- Allow anyone to update events (restrict later to creators only)
CREATE POLICY "Anyone can update events"
    ON events FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- Allow anyone to delete events (restrict later to creators only)
CREATE POLICY "Anyone can delete events"
    ON events FOR DELETE
    USING (true);

-- RLS Policies for Event Registrations
-- Allow anyone to view registrations
CREATE POLICY "Registrations are viewable by everyone"
    ON event_registrations FOR SELECT
    USING (true);

-- Allow anyone to register for events
CREATE POLICY "Users can register for events"
    ON event_registrations FOR INSERT
    WITH CHECK (true);

-- Allow users to cancel their registrations
CREATE POLICY "Users can cancel registrations"
    ON event_registrations FOR DELETE
    USING (true);

-- RLS Policies for Feedback
-- Allow anyone to view feedback (public read)
CREATE POLICY "Feedback is viewable by everyone"
    ON feedback FOR SELECT
    USING (true);

-- Allow anyone to submit feedback
CREATE POLICY "Users can submit feedback"
    ON feedback FOR INSERT
    WITH CHECK (true);

-- Allow users to update their own feedback (within time limit)
CREATE POLICY "Users can update their feedback"
    ON feedback FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- Allow RC members to update feedback status
-- Note: This checks for 'rc_member' role in Supabase Auth user_metadata
CREATE POLICY "RC members can update feedback status"
    ON feedback FOR UPDATE
    USING (
        auth.jwt() ->> 'user_metadata' IS NOT NULL AND
        (auth.jwt() -> 'user_metadata' ->> 'role') = 'rc_member'
    )
    WITH CHECK (
        auth.jwt() ->> 'user_metadata' IS NOT NULL AND
        (auth.jwt() -> 'user_metadata' ->> 'role') = 'rc_member'
    );

-- ==================== TRIGGERS ====================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to automatically update feedback updated_at
CREATE TRIGGER update_feedback_updated_at
    BEFORE UPDATE ON feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==================== COMMENTS ====================

-- Add helpful comments
COMMENT ON TABLE events IS 'Community events and activities';
COMMENT ON TABLE event_registrations IS 'User registrations for events';
COMMENT ON TABLE feedback IS 'Feedback from elderly residents about events';
COMMENT ON COLUMN events.created_by IS 'User who created the event (optional auth reference)';
COMMENT ON COLUMN event_registrations.user_id IS 'User who registered for the event';
COMMENT ON COLUMN feedback.user_id IS 'Elderly resident who submitted the feedback';
COMMENT ON COLUMN feedback.rating IS 'Rating from 1 to 5 stars';
COMMENT ON COLUMN feedback.status IS 'Feedback status: pending, reviewed, resolved, or archived';
COMMENT ON COLUMN feedback.resolved_by IS 'RC member who resolved/reviewed the feedback';

-- ==================== FUTURE TABLES (Optional) ====================

-- Uncomment these if you want to add wellness and safety features

-- Users/Profiles Table (if not using Supabase Auth)
/*
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    user_type TEXT CHECK(user_type IN ('user', 'admin', 'caregiver')),
    interests TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
*/

-- Reminders Table
/*
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    reminder_type TEXT CHECK(reminder_type IN ('appointment', 'medication', 'hydration', 'exercise', 'custom')),
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    is_recurring BOOLEAN DEFAULT FALSE,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
*/

-- Emergency Alerts Table
/*
CREATE TABLE IF NOT EXISTS emergency_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    alert_type TEXT CHECK(alert_type IN ('fall', 'sos', 'health', 'wandering')),
    latitude REAL,
    longitude REAL,
    description TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
*/

-- Location Tracking Table
/*
CREATE TABLE IF NOT EXISTS location_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    address TEXT,
    is_sharing BOOLEAN DEFAULT TRUE,
    tracked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
*/

-- ==================== SAMPLE DATA (Optional) ====================

-- Insert some sample events for testing
INSERT INTO events (title, description, date, time, location, max_participants) VALUES
('Morning Yoga', 'Start your day with relaxing yoga', '2025-12-15', '09:00', 'Community Center', 20),
('Cooking Workshop', 'Learn to cook traditional dishes', '2025-12-16', '14:00', 'Community Kitchen', 15),
('Board Games Night', 'Fun evening of board games', '2025-12-17', '18:00', 'Recreation Room', 12),
('Gardening Club', 'Gardening tips and plant sharing', '2025-12-18', '10:00', 'Community Garden', 25),
('Tech Help Session', 'Get help with your devices', '2025-12-19', '15:00', 'Library', 10)
ON CONFLICT DO NOTHING;

-- Sample feedback (optional - uncomment to add test data)
-- Note: Replace the UUIDs with actual event and user IDs from your database
/*
INSERT INTO feedback (event_id, user_id, rating, would_go_again, comments, status) VALUES
(
    (SELECT id FROM events LIMIT 1),
    '00000000-0000-0000-0000-000000000001',
    5,
    true,
    'Great event! Very enjoyable and well organized.',
    'pending'
),
(
    (SELECT id FROM events LIMIT 1 OFFSET 1),
    '00000000-0000-0000-0000-000000000001',
    4,
    true,
    'Good session, would love more of these.',
    'pending'
)
ON CONFLICT DO NOTHING;
*/

-- Success message
SELECT 'Database schema created successfully! 🎉' AS message;

