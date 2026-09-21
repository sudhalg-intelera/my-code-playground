"""
Sliding-window session memory: each session gets its own running 2-3
sentence summary (session_summaries), updated after every turn. Only the 5
most recent sessions per user are kept - as soon as a 6th session gets a
summary, the oldest of the 5 is dropped. Distinct from ADK's own per-session
conversation memory (adk_memory.db), which resets on every new conversation;
this is what lets a brand-new conversation still recall the gist of the
user's last few conversations.

Summarization runs as a direct OpenAI call, not through the ADK agent
graph, so it's reliable and doesn't depend on an agent choosing to call a
tool.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

from database import get_db_connection
from logging_config import get_logger

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
logger = get_logger("memory")

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SUMMARY_MODEL = "gpt-4o-mini"
WINDOW_SIZE = 5

SESSION_SUMMARY_SYSTEM_PROMPT = (
    "You maintain a running 2-3 sentence summary of ONE travel-app "
    "conversation session, written for a FUTURE, separate conversation to "
    "read so it can pick up where this one left off. Capture: (1) which "
    "destination(s) came up, by name, (2) durable preferences/facts "
    "(budget, travel style, dates, group size) - described in plain words, "
    "never copying any literal [TYPE_REDACTED_N] placeholder token from the "
    "conversation text into the summary, since that token is meaningless "
    "outside this session; if contact info was given, just say so, don't "
    "include the token, and (3) the STAGE the user actually reached - "
    "explicitly say whether they only asked/browsed, were shown specific "
    "flight/hotel options, chose options but did not yet confirm, or fully "
    "confirmed a booking. Stage is the most important part: it's what lets "
    "a future conversation proactively offer something like 'would you "
    "like to move forward with your booking to Italy?' instead of vaguely "
    "re-asking what the user already said - so never collapse 'showed "
    "interest in' and 'confirmed' into the same wording. Stage can also go "
    "DOWN, not just up - if the user cancels, backs out of an option they "
    "chose, or says they changed their mind, the updated summary must "
    "reflect that lower stage, not stay stuck at the highest stage ever "
    "reached. Given the CURRENT SESSION SUMMARY (may be empty) and the "
    "LATEST TURN in that same session, produce an UPDATED 2-3 sentence "
    "summary of the session so far - concise, not a transcript. Merge the "
    "new turn in; don't just append, and update the stage (up or down) if "
    "it changed this turn. Keep it under 75 words."
)


def get_recent_session_summaries(
    user_id: str, exclude_session_id: str | None = None, limit: int = WINDOW_SIZE
) -> list[str]:
    """
    Returns up to `limit` of this user's most recent session summaries,
    oldest first, ordered by when each session actually STARTED - not by
    when its summary was last touched, so a long-running current session
    doesn't distort the ordering of the others. Excludes exclude_session_id
    (normally the current session) so a conversation never sees its own
    in-progress summary reflected back at it.
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ss.summary
                    FROM session_summaries ss
                    JOIN sessions s ON s.session_id = ss.session_id
                    WHERE ss.user_id = %s AND ss.session_id != %s
                    ORDER BY s.started_at DESC
                    LIMIT %s
                    """,
                    (user_id, exclude_session_id or "", limit),
                )
                rows = cur.fetchall()
        finally:
            conn.close()
    except Exception:
        logger.exception("Failed to fetch recent session summaries for %s", user_id)
        return []

    return [r["summary"] for r in reversed(rows)]


def update_session_summary(user_id: str, session_id: str, user_message: str, agent_response: str) -> None:
    """
    Merges the latest turn into THIS session's running summary, upserts it,
    then prunes this user's session_summaries down to the WINDOW_SIZE most
    recent sessions (by when each session started). Meant to be called
    fire-and-forget (e.g. via asyncio.to_thread) - never raises.
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT summary FROM session_summaries WHERE user_id = %s AND session_id = %s",
                    (user_id, session_id),
                )
                row = cur.fetchone()
        finally:
            conn.close()
        current = row["summary"] if row else "(none yet)"

        completion = _client.chat.completions.create(
            model=SUMMARY_MODEL,
            messages=[
                {"role": "system", "content": SESSION_SUMMARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"CURRENT SESSION SUMMARY:\n{current}\n\n"
                        f"LATEST TURN:\nUser: {user_message}\nAgent: {agent_response}\n\n"
                        "UPDATED SESSION SUMMARY:"
                    ),
                },
            ],
            temperature=0,
            max_tokens=150,
        )
        updated = (completion.choices[0].message.content or "").strip()
        if not updated:
            return

        if completion.choices[0].finish_reason == "length":
            # The model ran out of tokens mid-sentence rather than
            # finishing naturally - storing a truncated summary would get
            # verbatim-injected into a future conversation's prompt as if
            # it were complete, degrading personalization instead of
            # improving it. Better to keep whatever summary was already on
            # file (if any) than overwrite it with a garbled one.
            logger.warning(
                "SESSION_SUMMARY_TRUNCATED user_id=%s session=%s - discarding, keeping prior summary",
                user_id, session_id,
            )
            return

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO session_summaries (user_id, session_id, summary) VALUES (%s, %s, %s) "
                    "ON CONFLICT (user_id, session_id) DO UPDATE SET "
                    "summary = EXCLUDED.summary, updated_at = now()",
                    (user_id, session_id, updated),
                )
                # Sliding window: keep only the WINDOW_SIZE most recent
                # sessions (by when they actually started) - drop the rest.
                cur.execute(
                    """
                    DELETE FROM session_summaries
                    WHERE user_id = %s AND session_id NOT IN (
                        SELECT ss.session_id FROM session_summaries ss
                        JOIN sessions s ON s.session_id = ss.session_id
                        WHERE ss.user_id = %s
                        ORDER BY s.started_at DESC
                        LIMIT %s
                    )
                    """,
                    (user_id, user_id, WINDOW_SIZE),
                )
            conn.commit()
        finally:
            conn.close()

        logger.info("SESSION_SUMMARY_UPDATED user_id=%s session=%s", user_id, session_id)
    except Exception:
        logger.exception("Failed to update session summary for %s / %s", user_id, session_id)
