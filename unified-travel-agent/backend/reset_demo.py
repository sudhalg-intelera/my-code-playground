"""
Resets demo state between review/demo runs, without touching the catalog.

Clears: chat_messages, bookings, itineraries, sessions, audit_logs.
Leaves alone: users (so existing logins keep working), destinations, flights,
hotels, prompts (the seeded catalog from db/seed.sql).

Run manually:
    python reset_demo.py

Note: in-memory pending bookings (agents/booking_agent.py's _pending_bookings,
held only by the running backend process) are not cleared by this script -
restart uvicorn if you need those cleared too.
"""

import psycopg
from database import DATABASE_URL

RESET_SQL = """
TRUNCATE chat_messages, bookings, itineraries, audit_logs, sessions RESTART IDENTITY CASCADE;
"""

if __name__ == "__main__":
    conn = psycopg.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(RESET_SQL)
        conn.commit()
    finally:
        conn.close()
    print("Demo state reset: chat_messages, bookings, itineraries, sessions, audit_logs cleared.")
    print("Users and the destinations/flights/hotels/prompts catalog were left untouched.")
