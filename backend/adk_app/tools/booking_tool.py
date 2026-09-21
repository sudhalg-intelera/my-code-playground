"""The booking lifecycle (confirm/cancel/look up history) - used by booking_agent."""

from datetime import date

from database import get_db_connection
from google.adk.tools import ToolContext
from logging_config import get_logger
from pii import deredact_for_session

logger = get_logger("adk_tools.booking")


def confirm_booking_adk(
    city: str, flight_no: str, hotel_name: str, contact_info: str, travel_date: str, tool_context: ToolContext
) -> dict:
    """
    Confirm and persist a booking. Only call this AFTER the user has
    explicitly said to confirm/book - never call this just because search
    results were shown to them.

    Args:
        city: The destination city being booked.
        flight_no: The exact flight number to book (from a prior search
            result), or "" if no flight should be booked.
        hotel_name: The exact hotel name to book (from a prior search
            result), or "" if no hotel should be booked.
        contact_info: Contact info (email/phone) the user gave in this
            conversation, or "" if none was given.
        travel_date: The date the user wants to travel, in YYYY-MM-DD
            format, or "" if they haven't given one yet - ask before calling
            this tool rather than guessing a date.

    Returns:
        A dict listing what was actually booked (matched against the
        catalog) versus what couldn't be found.
    """
    session_id = tool_context.session.id
    user_id = tool_context.user_id
    booked, not_found = [], []

    # The orchestrator only ever saw the redacted placeholder (e.g.
    # [EMAIL_REDACTED_1]) if PII was mentioned in an earlier turn - restore
    # the real value here, right before it's actually persisted.
    contact_info = deredact_for_session(contact_info, session_id, user_id=user_id) if contact_info else contact_info

    parsed_travel_date = None
    if travel_date:
        try:
            parsed_travel_date = date.fromisoformat(travel_date.strip())
        except ValueError:
            logger.warning("Ignoring unparseable travel_date %r for session %s", travel_date, session_id)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if flight_no:
                cur.execute(
                    "SELECT id FROM flights WHERE destination ILIKE %s AND flight_no = %s", (city, flight_no)
                )
                row = cur.fetchone()
                if row:
                    if _already_booked(cur, session_id, "flight", row["id"]):
                        booked.append(f"flight {flight_no} (already booked)")
                    else:
                        cur.execute(
                            "INSERT INTO bookings (session_id, user_id, booking_type, reference_id, contact_info, travel_date) "
                            "VALUES (%s, %s, 'flight', %s, %s, %s)",
                            (session_id, user_id, row["id"], contact_info or None, parsed_travel_date),
                        )
                        booked.append(f"flight {flight_no}")
                else:
                    not_found.append(f"flight {flight_no}")

            if hotel_name:
                cur.execute(
                    "SELECT id FROM hotels WHERE city ILIKE %s AND name = %s", (city, hotel_name)
                )
                row = cur.fetchone()
                if row:
                    if _already_booked(cur, session_id, "hotel", row["id"]):
                        booked.append(f"hotel '{hotel_name}' (already booked)")
                    else:
                        cur.execute(
                            "INSERT INTO bookings (session_id, user_id, booking_type, reference_id, contact_info, travel_date) "
                            "VALUES (%s, %s, 'hotel', %s, %s, %s)",
                            (session_id, user_id, row["id"], contact_info or None, parsed_travel_date),
                        )
                        booked.append(f"hotel '{hotel_name}'")
                else:
                    not_found.append(f"hotel '{hotel_name}'")
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Failed to persist ADK booking for session %s", session_id)
        return {"status": "error", "booked": [], "not_found": []}
    finally:
        conn.close()

    return {"status": "success", "booked": booked, "not_found": not_found}


def _already_booked(cur, session_id: str, booking_type: str, reference_id: int) -> bool:
    """
    Guards against the LLM calling confirm_booking_adk more than once for
    the same item in one session (observed in testing with an ambiguous
    "confirm both" - it called the tool twice and double-booked).
    """
    cur.execute(
        "SELECT 1 FROM bookings WHERE session_id = %s AND booking_type = %s AND reference_id = %s AND status = 'confirmed'",
        (session_id, booking_type, reference_id),
    )
    return cur.fetchone() is not None


def get_my_bookings_adk(tool_context: ToolContext) -> dict:
    """
    Look up this user's confirmed bookings and recent saved itineraries
    across ALL of their past conversations, not just this one. Call this
    whenever the user references something they booked/planned earlier that
    you don't see in the current conversation - e.g. "what have I booked",
    "cancel my trip" without saying which one, or "what was that itinerary
    you made me". ADK's own conversation memory resets on every new
    conversation; this tool reads the durable booking record instead.

    Returns:
        A dict with confirmed_bookings (type, city, detail, booked_at) and
        recent_itineraries (destination, created_at), most recent first.
        Both lists are empty if this user has nothing on record.
    """
    user_id = tool_context.user_id
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT b.booking_type, b.created_at, b.travel_date,
                           COALESCE(f.destination, h.city) AS city,
                           CASE WHEN b.booking_type = 'flight' THEN f.flight_no ELSE h.name END AS detail
                    FROM bookings b
                    LEFT JOIN flights f ON b.booking_type = 'flight' AND f.id = b.reference_id
                    LEFT JOIN hotels h ON b.booking_type = 'hotel' AND h.id = b.reference_id
                    WHERE b.user_id = %s AND b.status = 'confirmed'
                    ORDER BY b.created_at DESC
                    """,
                    (user_id,),
                )
                bookings = cur.fetchall()

                cur.execute(
                    "SELECT destination, created_at FROM itineraries WHERE user_id = %s ORDER BY created_at DESC LIMIT 5",
                    (user_id,),
                )
                itineraries = cur.fetchall()
        finally:
            conn.close()
    except Exception:
        logger.exception("Failed to fetch bookings/itineraries for user %s", user_id)
        return {"confirmed_bookings": [], "recent_itineraries": [], "status": "error"}

    return {
        "confirmed_bookings": [
            {
                "type": b["booking_type"],
                "city": b["city"],
                "detail": b["detail"],
                "travel_date": str(b["travel_date"]) if b["travel_date"] else None,
                "booked_at": str(b["created_at"]),
            }
            for b in bookings
        ],
        "recent_itineraries": [
            {"destination": i["destination"], "created_at": str(i["created_at"])} for i in itineraries
        ],
    }


def cancel_booking_adk(city: str, tool_context: ToolContext) -> dict:
    """
    Cancel this user's confirmed flight and/or hotel booking(s) for a city.
    Call this as soon as the user asks to cancel a trip/booking - there is no
    separate confirm step for cancellation, the request itself is the
    confirmation.

    Args:
        city: The destination city whose booking(s) should be cancelled.

    Returns:
        A dict listing what was actually cancelled (booking_type + reference),
        or an empty list if this user has no confirmed booking for that city.
    """
    user_id = tool_context.user_id
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bookings b
                SET status = 'cancelled'
                WHERE b.user_id = %(user_id)s AND b.status = 'confirmed' AND (
                    (b.booking_type = 'flight' AND EXISTS (
                        SELECT 1 FROM flights f WHERE f.id = b.reference_id AND f.destination ILIKE %(city)s
                    ))
                    OR
                    (b.booking_type = 'hotel' AND EXISTS (
                        SELECT 1 FROM hotels h WHERE h.id = b.reference_id AND h.city ILIKE %(city)s
                    ))
                )
                RETURNING b.booking_type, b.reference_id
                """,
                {"user_id": user_id, "city": city},
            )
            cancelled = [f"{r['booking_type']} #{r['reference_id']}" for r in cur.fetchall()]
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Failed to cancel bookings for user %s / city %s", user_id, city)
        return {"status": "error", "cancelled": []}
    finally:
        conn.close()

    return {"status": "success", "cancelled": cancelled}
