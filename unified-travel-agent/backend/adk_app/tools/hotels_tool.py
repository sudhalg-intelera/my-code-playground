"""Hotel search - used by booking_agent and itinerary_agent."""

from database import get_db_connection
from logging_config import get_logger

logger = get_logger("adk_tools.hotels")


def search_hotels_adk(city: str) -> dict:
    """
    Search available hotels in a city in the travel catalog.

    Args:
        city: The city name, e.g. "Paris" or "Tokyo".

    Returns:
        A dict with the city and a list of matching hotels (name, rating,
        price per night, amenities), ordered highest-rated first. The hotels
        list is empty if the city isn't in the catalog.
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT name, rating, price_per_night, amenities "
                    "FROM hotels WHERE city ILIKE %s ORDER BY rating DESC",
                    (city,),
                )
                rows = cur.fetchall()
        finally:
            conn.close()
    except Exception:
        logger.exception("Failed to search hotels for city %s", city)
        return {"city": city, "hotels": [], "status": "error"}
    return {
        "city": city,
        "hotels": [
            {
                "name": r["name"],
                "rating": float(r["rating"]),
                "price_per_night": float(r["price_per_night"]),
                "amenities": r["amenities"],
            }
            for r in rows
        ],
    }
