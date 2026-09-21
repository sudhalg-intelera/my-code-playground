"""Flight search - used by booking_agent."""

from database import get_db_connection
from logging_config import get_logger

logger = get_logger("adk_tools.flights")


def search_flights_adk(destination: str, origin: str = "") -> dict:
    """
    Search available flights to a destination city in the travel catalog,
    optionally narrowed down to a specific departure city/airport.

    Args:
        destination: The destination city name, e.g. "Paris" or "Tokyo".
        origin: The departure city or airport code, e.g. "Delhi" or "JFK" -
            pass an empty string if the user hasn't said where they're
            flying from. Never put a departure city here into `destination`.

    Returns:
        A dict with the destination, the origin actually applied (empty if
        none matched this catalog), and a list of matching flights (flight
        number, airline, origin, price, departure time), ordered cheapest
        first. The flights list is empty if the city isn't in the catalog.
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                rows = []
                applied_origin = ""
                if origin:
                    cur.execute(
                        "SELECT flight_no, airline, origin, price, departure_time "
                        "FROM flights WHERE destination ILIKE %s AND origin ILIKE %s "
                        "ORDER BY price ASC",
                        (destination, origin),
                    )
                    rows = cur.fetchall()
                    applied_origin = origin

                if not rows:
                    # Either no origin was given, or this small demo catalog just
                    # doesn't have that exact origin on file for this destination -
                    # fall back to every flight to the destination rather than
                    # showing nothing.
                    cur.execute(
                        "SELECT flight_no, airline, origin, price, departure_time "
                        "FROM flights WHERE destination ILIKE %s ORDER BY price ASC",
                        (destination,),
                    )
                    rows = cur.fetchall()
                    applied_origin = ""
        finally:
            conn.close()
    except Exception:
        logger.exception("Failed to search flights for destination %s", destination)
        return {"destination": destination, "origin": origin, "flights": [], "status": "error"}
    return {
        "destination": destination,
        "origin": applied_origin,
        "flights": [
            {
                "flight_no": r["flight_no"],
                "airline": r["airline"],
                "origin": r["origin"],
                "price": float(r["price"]),
                "departure_time": r["departure_time"],
            }
            for r in rows
        ],
    }
