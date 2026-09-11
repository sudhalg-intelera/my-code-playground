"""Destination facts (sights/food/best season) - used by destination_agent,
itinerary_agent, and travel_agent."""

from database import get_db_connection
from logging_config import get_logger

logger = get_logger("adk_tools.destinations")


def get_destination_info_adk(city: str) -> dict:
    """
    Get top sights, local food, and the best season to visit a city in the
    travel catalog.

    Args:
        city: The city name, e.g. "Paris" or "Tokyo".

    Returns:
        A dict with sights (list of strings), food (list of strings), and
        best_season (string), or empty/None values if the city isn't in the
        catalog.
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT sights, food, best_season FROM destinations WHERE city ILIKE %s",
                    (city,),
                )
                row = cur.fetchone()
        finally:
            conn.close()
    except Exception:
        logger.exception("Failed to fetch destination info for city %s", city)
        return {"city": city, "sights": [], "food": [], "best_season": None, "status": "error"}
    if not row:
        return {"city": city, "sights": [], "food": [], "best_season": None}
    return {"city": city, "sights": row["sights"], "food": row["food"], "best_season": row["best_season"]}
