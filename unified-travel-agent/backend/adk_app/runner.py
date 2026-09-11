"""
Runner + persistent session memory for the ADK orchestrator.

Memory is backed by its own SQLite file (adk_memory.db) via ADK's
DatabaseSessionService - deliberately separate from the app's own Postgres
schema (sessions/chat_messages/etc.) to avoid any table-name collision.
ADK's session stores the full turn-by-turn event history per (user_id,
session_id), which is what actually lets the orchestrator "remember" prior
turns (e.g. what it offered, for the booking confirmation step) instead of
the ad-hoc in-memory dict the pre-ADK version used.
"""

import os

from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from adk_app.agents import root_agent
from logging_config import get_logger
from memory import get_recent_session_summaries

logger = get_logger("adk_runner")

APP_NAME = "unified_travel_agent"
_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "adk_memory.db"))

_session_service = DatabaseSessionService(db_url=f"sqlite+aiosqlite:///{_DB_PATH}")

_runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=_session_service,
    auto_create_session=True,
)


async def run_turn(user_id: str, session_id: str, message: str) -> tuple[str, str]:
    """
    Runs one user message through the ADK orchestrator and returns
    (final_text, agent_display_name) - the display name is whichever
    sub-agent actually produced the final reply (e.g. "Destination Agent"),
    for the caller to show as a heading rather than baked into the text.

    Delegation/tool-use tracing is ADK's own native auto-instrumentation
    (invoke_agent/call_llm/generate_content/tool spans), not hand-rolled here
    - main.py's chat_endpoint runs this inside a real OpenTelemetry span
    context (via langfuse.start_as_current_observation), so ADK's spans nest
    directly into that same trace. This function still keeps its own
    app.log delegation trail (ADK_DELEGATION/ADK_TOOL_CALL/etc.) independent
    of Langfuse, so it's visible even without Langfuse configured.
    """
    # A brand-new conversation (no prior events in ADK's own session memory)
    # gets a recap of this user's last few sessions injected up front, so it
    # can personalize its very first answer instead of starting from zero.
    # A continuing conversation already has this in its own history from its
    # first turn, so this only fires once per conversation, not every turn.
    session = await _session_service.get_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    is_new_conversation = not session or not session.events

    effective_message = message
    if is_new_conversation:
        summaries = get_recent_session_summaries(user_id, exclude_session_id=session_id)
        if summaries:
            numbered = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(summaries))
            effective_message = (
                f"[Summary of this user's last {len(summaries)} conversation(s), oldest "
                "first - personalize your answer using them where relevant, don't just "
                f"restate them:\n{numbered}]\n\n{message}"
            )
            logger.info(
                "SESSION_SUMMARIES_INJECTED user_id=%s session=%s count=%d",
                user_id, session_id, len(summaries),
            )

    content = types.Content(role="user", parts=[types.Part(text=effective_message)])

    texts = []
    agents_seen = []
    tools_called = []
    current_author = None
    final_author = None

    async for event in _runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.author != current_author:
            current_author = event.author
            agents_seen.append(event.author)
            logger.info("ADK_DELEGATION session=%s agent_active=%s", session_id, event.author)

        for call in event.get_function_calls():
            if call.name == "transfer_to_agent":
                target = (call.args or {}).get("agent_name")
                logger.info("ADK_TRANSFER session=%s from=%s to=%s", session_id, event.author, target)
                continue
            tools_called.append(call.name)
            logger.info("ADK_TOOL_CALL session=%s agent=%s tool=%s args=%s", session_id, event.author, call.name, dict(call.args or {}))

        for resp in event.get_function_responses():
            logger.info("ADK_TOOL_RESULT session=%s agent=%s tool=%s", session_id, event.author, resp.name)

        if event.is_final_response() and event.content and event.content.parts:
            new_texts = [part.text for part in event.content.parts if getattr(part, "text", None)]
            if new_texts:
                texts.extend(new_texts)
                final_author = event.author

    final_text = "\n".join(texts) if texts else None

    logger.info(
        "ADK_TURN_COMPLETE session=%s agents=%s tools=%s final_author=%s",
        session_id, agents_seen, tools_called, final_author,
    )

    display_name = _display_agent_name(final_author)

    if not final_text:
        logger.warning("ADK orchestrator produced no final text response for session %s", session_id)
        return "Sorry, I couldn't come up with a response. Please try rephrasing.", display_name

    return final_text, display_name


def _display_agent_name(author: str | None) -> str:
    """Turns an ADK agent's internal name (e.g. 'destination_agent') into a display heading."""
    if not author:
        return "Travel Agent"
    return " ".join(word.capitalize() for word in author.split("_"))
