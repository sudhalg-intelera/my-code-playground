"""Database as one stack: the Postgres connection, self-healing init_db(),
and query helpers live in client.py; schema.sql/seed.sql are the actual
schema/catalog data, applied by Docker on first container start. Re-exported
here so `from database import ...` keeps working unchanged everywhere."""

from database.client import (
    DATABASE_URL,
    ensure_session,
    find_city_in_text,
    get_db_connection,
    init_db,
    upsert_prompt,
)

__all__ = [
    "DATABASE_URL",
    "ensure_session",
    "find_city_in_text",
    "get_db_connection",
    "init_db",
    "upsert_prompt",
]
