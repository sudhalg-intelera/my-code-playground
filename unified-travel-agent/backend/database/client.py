import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://travel_agent:travel_agent_dev_password@localhost:5432/travel_agent",
)

# Same mapping seed.sql backfills with for a fresh install - kept here too
# so init_db() can self-heal an older volume that predates destinations.country.
_CITY_COUNTRY = {
    "AMMAN": "Jordan", "AMSTERDAM": "Netherlands", "ATHENS": "Greece", "AUCKLAND": "New Zealand",
    "BALI": "Indonesia", "BANGKOK": "Thailand", "BARCELONA": "Spain", "BEIJING": "China",
    "BELGRADE": "Serbia", "BERLIN": "Germany", "BRUSSELS": "Belgium", "BUCHAREST": "Romania",
    "BUDAPEST": "Hungary", "BUENOS AIRES": "Argentina", "CAIRO": "Egypt", "CAPE TOWN": "South Africa",
    "CARTAGENA": "Colombia", "COLOMBO": "Sri Lanka", "COPENHAGEN": "Denmark", "CUSCO": "Peru",
    "DELHI": "India", "DOHA": "Qatar", "DUBAI": "United Arab Emirates", "DUBLIN": "Ireland",
    "DUBROVNIK": "Croatia", "HANOI": "Vietnam", "HAVANA": "Cuba", "HELSINKI": "Finland",
    "HONG KONG": "China", "ISTANBUL": "Turkey", "JERUSALEM": "Israel", "KATHMANDU": "Nepal",
    "KUALA LUMPUR": "Malaysia", "KYIV": "Ukraine", "KYOTO": "Japan", "LA PAZ": "Bolivia",
    "LAGOS": "Nigeria", "LISBON": "Portugal", "LJUBLJANA": "Slovenia", "LONDON": "United Kingdom",
    "LUANG PRABANG": "Laos", "MANILA": "Philippines", "MARRAKESH": "Morocco", "MEXICO CITY": "Mexico",
    "MONTEGO BAY": "Jamaica", "MONTEVIDEO": "Uruguay", "MOSCOW": "Russia", "NADI": "Fiji",
    "NAIROBI": "Kenya", "NASSAU": "Bahamas", "NEW YORK": "United States", "OSLO": "Norway",
    "PANAMA CITY": "Panama", "PARIS": "France", "PRAGUE": "Czech Republic", "QUITO": "Ecuador",
    "REYKJAVIK": "Iceland", "RIO DE JANEIRO": "Brazil", "RIYADH": "Saudi Arabia", "ROME": "Italy",
    "SAN JOSE": "Costa Rica", "SANTIAGO": "Chile", "SEOUL": "South Korea", "SIEM REAP": "Cambodia",
    "SINGAPORE": "Singapore", "SOFIA": "Bulgaria", "STOCKHOLM": "Sweden", "SYDNEY": "Australia",
    "TAIPEI": "Taiwan", "TBILISI": "Georgia", "TOKYO": "Japan", "TORONTO": "Canada",
    "VALLETTA": "Malta", "VANCOUVER": "Canada", "VIENNA": "Austria", "WARSAW": "Poland",
    "YANGON": "Myanmar", "ZANZIBAR": "Tanzania", "ZURICH": "Switzerland",
}


def get_db_connection() -> psycopg.Connection:
    """Returns a Postgres connection with dict-style row access."""
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db() -> None:
    """
    Safety net for tables that may not exist yet on an older Postgres volume.
    schema.sql is the source of truth and runs automatically on first
    container start (docker-entrypoint-initdb.d); this just makes sure
    re-running against a volume created before a table was added doesn't break.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
                    user_id TEXT,
                    action TEXT NOT NULL,
                    details TEXT
                )
            """)
            # Volumes initialized before this column was added to schema.sql
            # never pick it up automatically (docker-entrypoint-initdb.d only
            # runs once against an empty volume) - patch it in on every boot.
            cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS contact_info TEXT")
            # Same story for the username -> UUID identifier switch (see
            # migrate_user_uuid.py, which handles backfilling a volume that
            # already has data) - a volume with no users.user_uuid at all yet
            # just needs the column added.
            cur.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS user_uuid UUID "
                "NOT NULL DEFAULT gen_random_uuid() UNIQUE"
            )
            # Replaced by the sliding-window session_summaries table below -
            # drop it once if it's still hanging around from before.
            cur.execute("DROP TABLE IF EXISTS user_facts")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS session_summaries (
                    id SERIAL PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(user_uuid) ON DELETE CASCADE,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                    summary TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    UNIQUE (user_id, session_id)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_session_summaries_user ON session_summaries(user_id)")
            # Same self-heal story for destinations.country (see the bottom
            # of seed.sql for the mapping fresh installs use) - a volume
            # from before this column existed just needs it added and
            # backfilled from the same mapping.
            cur.execute("ALTER TABLE destinations ADD COLUMN IF NOT EXISTS country TEXT")
            for city, country in _CITY_COUNTRY.items():
                cur.execute(
                    "UPDATE destinations SET country = %s WHERE city = %s AND country IS NULL",
                    (country, city),
                )
            # bookings.reference_id is a bare integer pointing into either
            # flights or hotels depending on booking_type - meaningless on
            # its own in a query tool. This view resolves it to the actual
            # city/flight-no/hotel-name and country, and shows both the real
            # user_id (UUID) and the resolved username side by side, for
            # direct viewing. CREATE OR REPLACE can't change a view's column
            # *type* (e.g. after bookings.user_id itself changed from TEXT to
            # UUID) - drop first so a boot after a schema change never fails.
            cur.execute("DROP VIEW IF EXISTS bookings_readable")
            cur.execute("""
                CREATE VIEW bookings_readable AS
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
                ORDER BY b.id
            """)
        conn.commit()
    finally:
        conn.close()


def ensure_session(session_id: str, user_id: str | None = None) -> None:
    """Idempotently records a session row before any chat_messages/bookings/itineraries write."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sessions (session_id, user_id) VALUES (%s, %s) "
                "ON CONFLICT (session_id) DO NOTHING",
                (session_id, user_id),
            )
        conn.commit()
    finally:
        conn.close()


def upsert_prompt(name: str, template: str, version: int) -> None:
    """Mirrors a Langfuse-managed prompt into the local prompts table (see sync_prompts.py)."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO prompts (name, template, version) VALUES (%s, %s, %s) "
                "ON CONFLICT (name) DO UPDATE SET "
                "template = EXCLUDED.template, version = EXCLUDED.version, updated_at = now()",
                (name, template, version),
            )
        conn.commit()
    finally:
        conn.close()


def find_city_in_text(text: str) -> str:
    """
    Matches the user's message against known destination city names in the
    catalog (longest match wins, so multi-word cities like "Buenos Aires" or
    "Cape Town" aren't shadowed by matching just their first word). Falls
    back to the first title-case word, then "Paris", if nothing matches.
    """
    lowered = text.lower()
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT city FROM destinations")
                known_cities = [row["city"] for row in cur.fetchall()]
        finally:
            conn.close()
    except Exception:
        known_cities = []

    matches = [city for city in known_cities if city.lower() in lowered]
    if matches:
        return max(matches, key=len)

    words = [w.strip(".,!?") for w in text.split()]
    for word in words:
        if len(word) > 3 and word.istitle():
            return word
    return "Paris"
