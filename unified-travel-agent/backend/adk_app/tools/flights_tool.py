"""Flight search - used by booking_agent."""

from database import get_db_connection
from logging_config import get_logger

logger = get_logger("adk_tools.flights")


def search_flights_adk(destination: str) -> dict:
    """
    Search available flights to a destination city in the travel catalog.

    Args:
        destination: The destination city name, e.g. "Paris" or "Tokyo".

    Returns:
        A dict with the destination and a list of matching flights (flight
        number, airline, price, departure time), ordered cheapest first. The
        flights list is empty if the city isn't in the catalog.
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT flight_no, airline, price, departure_time "
                    "FROM flights WHERE destination ILIKE %s ORDER BY price ASC",
                    (destination,),
                )
                rows = cur.fetchall()
        finally:
            conn.close()
    except Exception:
        logger.exception("Failed to search flights for destination %s", destination)
        return {"destination": destination, "flights": [], "status": "error"}
    return {
        "destination": destination,
        "flights": [
            {
                "flight_no": r["flight_no"],
                "airline": r["airline"],
                "price": float(r["price"]),
                "departure_time": r["departure_time"],
            }
            for r in rows
        ],
    }
