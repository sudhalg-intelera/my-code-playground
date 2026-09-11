-- Unified Travel Agent - Postgres schema
-- Applied automatically on first container start via docker-entrypoint-initdb.d

CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    -- Stable, opaque identifier - this (not username) is what's embedded in
    -- JWTs and referenced by every other table below. Keeps a user's real
    -- identifier independent of their (changeable, human-readable) username.
    user_uuid UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per conversation. A new session_id (frontend-generated UUID) means
-- a new conversation, which is what fact-extraction/summarization key off of.
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES users(user_uuid) ON DELETE SET NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ
);

-- Every chat request/response is logged here with its session_id + user_id.
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_uuid) ON DELETE SET NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'agent')),
    content TEXT NOT NULL,
    pii_flagged BOOLEAN NOT NULL DEFAULT false,
    guardrail_blocked BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);

-- Dynamic destination knowledge base. New cities are added with an INSERT,
-- no code changes required - agents/tools read this instead of hardcoding cities.
CREATE TABLE IF NOT EXISTS destinations (
    city TEXT PRIMARY KEY,
    sights TEXT[] NOT NULL,
    food TEXT[] NOT NULL,
    best_season TEXT NOT NULL DEFAULT 'Year-round',
    -- Nullable here on purpose: seed.sql's INSERTs list only
    -- (city, sights, food, best_season) explicitly, then backfill and lock
    -- this NOT NULL once every row actually has a value - see the bottom of
    -- seed.sql. Never left null once seeding finishes.
    country TEXT
);

CREATE TABLE IF NOT EXISTS flights (
    id SERIAL PRIMARY KEY,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    flight_no TEXT NOT NULL,
    airline TEXT NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    departure_time TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hotels (
    id SERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    name TEXT NOT NULL,
    rating NUMERIC(2, 1) NOT NULL,
    price_per_night NUMERIC(10, 2) NOT NULL,
    amenities TEXT NOT NULL
);

-- Write path: every booking/cancellation action is a row here, written at the tool level.
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_uuid) ON DELETE SET NULL,
    booking_type TEXT NOT NULL CHECK (booking_type IN ('flight', 'hotel')),
    reference_id INTEGER NOT NULL,
    -- De-redacted contact info (email/phone), if the user supplied one in-chat.
    -- The chat trace/LLM only ever saw the redacted placeholder; this column
    -- holds the real value so booking execution stays seamless.
    contact_info TEXT,
    status TEXT NOT NULL DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- reference_id above is a bare integer into either flights or hotels
-- depending on booking_type - meaningless on its own in a query tool. This
-- view resolves it to the actual city/flight-no/hotel-name and country, and
-- shows both the real user_id (UUID) and the resolved username side by
-- side, for direct viewing.
CREATE OR REPLACE VIEW bookings_readable AS
SELECT
    b.id,
    b.session_id,
    b.user_id,
    u.username,
    b.booking_type,
    COALESCE(f.destination, h.city) AS city,
    d.country,
    CASE WHEN b.booking_type = 'flight' THEN f.flight_no ELSE h.name END AS detail,
    b.status,
    b.contact_info,
    b.created_at
FROM bookings b
LEFT JOIN users u ON u.user_uuid = b.user_id
LEFT JOIN flights f ON b.booking_type = 'flight' AND f.id = b.reference_id
LEFT JOIN hotels h ON b.booking_type = 'hotel' AND h.id = b.reference_id
LEFT JOIN destinations d ON d.city = COALESCE(f.destination, h.city)
ORDER BY b.id;

CREATE TABLE IF NOT EXISTS itineraries (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_uuid) ON DELETE SET NULL,
    destination TEXT NOT NULL,
    plan_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Local mirror of Langfuse-managed prompts, kept in sync via the Langfuse webhook.
CREATE TABLE IF NOT EXISTS prompts (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    template TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Timestamped audit trail: login/register attempts, PII redaction/de-redaction
-- events, and guardrail blocks. Written by audit.write_audit_log(). Left as
-- plain TEXT with no FK - some events (e.g. a failed login for a username
-- that doesn't exist) have nothing real to reference.
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id TEXT,
    action TEXT NOT NULL,
    details TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);

-- Sliding-window session memory, distinct from ADK's own per-session
-- conversation memory (adk_memory.db). One row per (user, session): a
-- running 2-3 sentence summary of that session, updated after each turn by
-- memory.update_session_summary(). Only the 5 most recent sessions per user
-- are kept - update_session_summary() prunes older ones on every write.
-- adk_app/runner.py injects the kept summaries into a brand-new conversation
-- so it isn't starting from zero.
CREATE TABLE IF NOT EXISTS session_summaries (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_uuid) ON DELETE CASCADE,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, session_id)
);

CREATE INDEX IF NOT EXISTS idx_session_summaries_user ON session_summaries(user_id);
