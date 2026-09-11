"""Saving a finished itinerary plan - used by itinerary_agent."""

from database import get_db_connection
from google.adk.tools import ToolContext
from logging_config import get_logger

logger = get_logger("adk_tools.itinerary")


def save_itinerary_adk(city: str, plan_text: str, tool_context: ToolContext) -> dict:
    """
    Save a finished multi-day itinerary plan against this session.

    Args:
        city: The destination the itinerary is for.
        plan_text: The full itinerary text you composed for the user.

    Returns:
        A dict confirming the itinerary was saved.
    """
    session_id = tool_context.session.id
    user_id = tool_context.user_id
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO itineraries (session_id, user_id, destination, plan_text) VALUES (%s, %s, %s, %s)",
                (session_id, user_id, city, plan_text),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Failed to persist ADK itinerary for session %s", session_id)
        return {"status": "error"}
    finally:
        conn.close()
    return {"status": "success"}
