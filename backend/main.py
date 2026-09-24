import asyncio
import time
import uuid
from contextlib import ExitStack, asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from adk_app.runner import run_turn
from auth import AuthResponse, LoginRequest, RegisterRequest, get_current_user, login_user, register_user
from database import ensure_session, get_db_connection, init_db
from guardrails import check_bare_flow, check_guardrails, check_output_guardrails
from langfuse import propagate_attributes
from observability.langfuse_config import langfuse
from logging_config import get_logger
from memory import update_session_summary
from pii import deredact_for_session, get_session_token_map, sanitize_user_input

logger = get_logger("main")

# Holds strong references to fire-and-forget background tasks (e.g. facts
# summarization) so asyncio doesn't garbage-collect them mid-flight.
_background_tasks: set = set()


def _fire_and_forget(coro) -> None:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Backend started - database ready, logging to app.log")
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/auth/register", response_model=AuthResponse)
def register_endpoint(request: RegisterRequest) -> AuthResponse:
    return register_user(request)


@app.post("/api/auth/login", response_model=AuthResponse)
def login_endpoint(request: LoginRequest) -> AuthResponse:
    return login_user(request)


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str


@app.get("/api/conversations")
def list_conversations(claims: dict = Depends(get_current_user)) -> list[dict]:
    """
    Sidebar history: every session this user has had, most recent first,
    with a one-line preview (their first message) and when it was last
    active - not limited to the 5-session memory window (session_summaries),
    since browsing past chats and what the agent still recalls are two
    different things.
    """
    user_id = claims["sub"]
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    s.session_id,
                    s.started_at,
                    (SELECT content FROM chat_messages cm
                     WHERE cm.session_id = s.session_id AND cm.role = 'user'
                     ORDER BY cm.id ASC LIMIT 1) AS preview,
                    (SELECT MAX(created_at) FROM chat_messages cm
                     WHERE cm.session_id = s.session_id) AS last_activity,
                    (SELECT COUNT(*) FROM chat_messages cm
                     WHERE cm.session_id = s.session_id) AS message_count
                FROM sessions s
                WHERE s.user_id = %s
                ORDER BY s.started_at DESC
                LIMIT 50
                """,
                (user_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [r for r in rows if r["message_count"] > 0]


@app.get("/api/conversations/{session_id}")
def get_conversation(session_id: str, claims: dict = Depends(get_current_user)) -> list[dict]:
    """Full transcript of one past session, oldest first - only if it belongs to the caller."""
    user_id = claims["sub"]
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM sessions WHERE session_id = %s", (session_id,))
            session_row = cur.fetchone()
            if not session_row or str(session_row["user_id"]) != user_id:
                raise HTTPException(status_code=404, detail="conversation not found")

            cur.execute(
                "SELECT role, content, created_at FROM chat_messages "
                "WHERE session_id = %s ORDER BY id ASC",
                (session_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return rows


@app.get("/api/memory")
def get_memory(claims: dict = Depends(get_current_user)) -> list[dict]:
    """
    What the agent currently remembers about this user: the sliding-window
    session_summaries (memory/session_summaries.py), most recent first.
    """
    user_id = claims["sub"]
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ss.summary, ss.updated_at
                FROM session_summaries ss
                JOIN sessions s ON s.session_id = ss.session_id
                WHERE ss.user_id = %s
                ORDER BY s.started_at DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return rows


@app.get("/api/pii/token-map/{session_id}")
def get_token_map(session_id: str, claims: dict = Depends(get_current_user)) -> dict:
    """
    Visibility into what real PII a session's redaction tokens actually
    stand for (stored in Redis - see pii/guard.py) - lets the frontend show
    this directly instead of needing view-token-map.ps1/redis-cli. Scoped to
    the caller's own session, same ownership check as
    /api/conversations/{session_id} - this is real PII, not something to
    hand back for an arbitrary session_id.
    """
    user_id = claims["sub"]
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM sessions WHERE session_id = %s", (session_id,))
            session_row = cur.fetchone()
            if not session_row or str(session_row["user_id"]) != user_id:
                raise HTTPException(status_code=404, detail="session not found")
    finally:
        conn.close()

    return get_session_token_map(session_id)


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, claims: dict = Depends(get_current_user)) -> dict:
    # Trust the bearer token's subject over the client-supplied user_id field.
    user_id = claims["sub"]
    session_id = request.session_id
    # Unique per turn, not per session - seeding on session_id alone made
    # every message in the same conversation collide onto one ever-growing
    # trace (a 7-turn conversation showed 14 guardrail spans and a reported
    # "latency" of the whole 21-minute conversation, not one round trip).
    # Langfuse's own Sessions view (via propagate_attributes below) already
    # groups a session's traces together, so per-turn uniqueness costs
    # nothing to look up.
    trace_id = langfuse.create_trace_id(seed=f"{session_id}:{uuid.uuid4().hex}")
    round_trip_start = time.time()

    ensure_session(session_id, user_id)

    # Redact PII BEFORE anything - including the very first Langfuse span -
    # ever sees the raw text. Doing this after opening spans (the old order)
    # meant the root/input-guardrail spans' `input` field held the
    # unredacted message, so real emails/phone numbers were being shipped to
    # Langfuse (a third-party service) despite the whole point of PII
    # handling being that the LLM/trace/log should never see them. The NeMo
    # input-check policy already tolerates redaction tokens fine (it cares
    # about intent, not literal PII presence), so checking the sanitized
    # text instead of the raw one changes nothing about what gets blocked.
    pii_result = sanitize_user_input(request.message, user_id=user_id, session_id=session_id)
    clean_message = pii_result["sanitized_text"]

    # Deterministic Colang canned replies (see guardrails/rails/*.co) for
    # bare utterances that need no real backend work - e.g. "hello" or
    # "what can you do". Checked before the guardrail LLM calls and the full
    # ADK agent round trip so those never run for these; check_bare_flow
    # itself returns (None, None) immediately for anything else, so normal
    # travel messages pay no extra latency from this check.
    flow_reply, flow_name = await check_bare_flow(clean_message)
    if flow_reply is not None:
        deredacted_reply = deredact_for_session(flow_reply, session_id, user_id=user_id)
        total_ms = (time.time() - round_trip_start) * 1000
        _log_chat_turn(session_id, user_id, clean_message, flow_reply, pii_result["pii_detected"], False)
        _log_pii_trace(trace_id, user_id, session_id, request.message, clean_message, flow_reply, deredacted_reply)
        logger.info(
            "Chat turn complete user=%s session=%s pii_flagged=%s guardrail_blocked=False "
            "total_duration_ms=%.1f colang_flow=%s",
            user_id, session_id, pii_result["pii_detected"], total_ms, flow_name,
        )
        return {
            "user_id": user_id,
            "session_id": session_id,
            "response": deredacted_reply,
            "agent_name": flow_name.capitalize(),
            "pii_flagged": pii_result["pii_detected"],
            "guardrail_blocked": False,
        }

    # propagate_attributes gives every span created below (including the
    # ones adk_app/runner.py creates for delegation/tool-use) a stable
    # trace-level name/user_id/session_id - without this, whichever span
    # happened to be flushed last silently became the trace's displayed
    # name, and user_id/session_id only ever lived in per-span metadata
    # rather than Langfuse's first-class filterable trace attributes.
    with propagate_attributes(
        trace_name="Unified_Travel_Agent_Pipeline",
        user_id=user_id,
        session_id=session_id,
    ), ExitStack() as stack:
        # start_as_current_observation (not start_observation) is the fix for
        # "guardrails showing multiple invocations": it actually pushes real
        # OpenTelemetry context, so ADK's own native auto-instrumentation
        # (invoke_agent/call_llm/generate_content/tool spans) - which asks
        # "what's the current span?" the standard OTEL way - nests inside
        # THIS trace instead of silently starting its own second, orphaned
        # trace for the same turn. That was the actual root cause: every turn
        # was producing two disconnected traces (ours, and ADK's), which is
        # what read as guardrails/spans "repeating" when reviewed side by
        # side. See adk_app/runner.py - it no longer creates its own
        # hand-rolled agent/tool spans, since ADK's native ones (now
        # correctly nested here) are the real, more detailed source of truth.
        root_span = None
        try:
            root_span = stack.enter_context(
                langfuse.start_as_current_observation(
                    trace_context={"trace_id": trace_id},
                    name="Unified_Travel_Agent_Pipeline",
                    as_type="span",
                    input={"message": clean_message},
                    metadata={"user_id": user_id, "session_id": session_id},
                )
            )
        except Exception:
            logger.exception("Langfuse trace creation failed for session %s", session_id)

        # Two attempts at making input_guardrails/agent_turn/output_guardrails
        # true SIBLINGS of root_span (so Graph would draw them side by side
        # in sequence) both failed for reasons that weren't fully diagnosable
        # without live trace data each time. Nesting depth is unambiguous in
        # a way sibling-ordering apparently isn't in Langfuse's renderer, so
        # this restructures the whole turn as a genuine containment chain
        # instead: input_guardrails is entered as current and stays open
        # around EVERYTHING else - agent_turn nests inside it, output_guardrails
        # nests inside agent_turn. There is no ambiguous "which sibling comes
        # first" left to get wrong; the tree can only be drawn one way.
        guard_start = time.time()
        with langfuse.start_as_current_observation(
            name="input_guardrails", as_type="guardrail", input={"message": clean_message},
        ) as input_guard_span:
            guard_result = await check_guardrails(clean_message, user_id=user_id)
            input_guard_ms = (time.time() - guard_start) * 1000
            input_guard_span.update(
                output=guard_result,
                metadata={"duration_ms": input_guard_ms, "pii_flagged": pii_result["pii_detected"]},
            )
            logger.info(
                "INPUT_GUARDRAILS session=%s allowed=%s duration_ms=%.1f",
                session_id, guard_result["allowed"], input_guard_ms,
            )
            # Flushing only once at the very end put every span from the whole
            # turn into one upload batch, arriving at Langfuse together - when
            # Langfuse's own tree view has to break a display tie, it falls
            # back to upload order, not true start time. Flushing right after
            # each stage sends it while it's genuinely the most recent thing
            # that happened, at the cost of a real (if small) added delay on
            # every turn - a correctness/latency tradeoff, not a free fix.
            await asyncio.to_thread(langfuse.flush)

            output_guard_result = {"allowed": True, "reason": None, "matched": None}
            injected_memory_context = None

            if not guard_result["allowed"]:
                agent_response = (
                    "This request was blocked by our safety guardrails "
                    f"({guard_result['reason']}). Please rephrase and try again."
                )
                agent_name = "Safety Guardrails"
            else:
                # Stage 2, nested inside input_guardrails (still open above) -
                # the ADK orchestrator delegates to a sub-agent, which uses
                # its tool(s). ADK's own auto-instrumentation (invoke_agent/
                # call_llm/generate_content/tool spans) attaches to whatever
                # is currently active, which is this span, not root_span - so
                # all of ADK's native detail nests inside agent_turn here.
                with langfuse.start_as_current_observation(
                    name="agent_turn", as_type="span", input={"message": clean_message},
                ) as agent_span:
                    agent_response, agent_name, injected_memory_context = await run_turn(
                        user_id=user_id, session_id=session_id, message=clean_message,
                    )
                    agent_span.update(
                        output={"response": agent_response, "agent_name": agent_name},
                        metadata={
                            "memory_injected": injected_memory_context is not None,
                            "injected_memory_context": injected_memory_context,
                        },
                    )
                    await asyncio.to_thread(langfuse.flush)

                    # Stage 3, nested inside agent_turn (still open above) -
                    # screen the generated response before it goes back to
                    # the user. Exactly one of these per turn, same as input.
                    out_guard_start = time.time()
                    with langfuse.start_as_current_observation(
                        name="output_guardrails", as_type="guardrail", input={"response": agent_response},
                    ) as output_guard_span:
                        output_guard_result = await check_output_guardrails(
                            clean_message, agent_response, user_id=user_id
                        )
                        output_guard_ms = (time.time() - out_guard_start) * 1000
                        output_guard_span.update(
                            output=output_guard_result, metadata={"duration_ms": output_guard_ms}
                        )
                        logger.info(
                            "OUTPUT_GUARDRAILS session=%s allowed=%s duration_ms=%.1f",
                            session_id, output_guard_result["allowed"], output_guard_ms,
                        )

                        if not output_guard_result["allowed"]:
                            logger.warning(
                                "Output guardrail tripped for session %s (reason=%s)",
                                session_id, output_guard_result["reason"],
                            )
                            agent_response = (
                                "Our response was withheld by output safety guardrails. "
                                "Please rephrase your request."
                            )
                            agent_name = "Safety Guardrails"

        guardrail_blocked = (not guard_result["allowed"]) or (not output_guard_result["allowed"])

        if not guardrail_blocked:
            # Fire-and-forget: merges this turn into the user's long-term
            # facts/preferences profile (memory.py) without adding latency
            # to the response the client is waiting on.
            _fire_and_forget(
                asyncio.to_thread(update_session_summary, user_id, session_id, clean_message, agent_response)
            )

        _log_chat_turn(
            session_id, user_id, clean_message, agent_response,
            pii_result["pii_detected"], guardrail_blocked,
        )

        # Restores real values (e.g. the user's own email in a booking
        # confirmation) ONLY in what's about to be returned over HTTP -
        # chat_messages above and the Langfuse trace below both already
        # captured agent_response in its still-redacted form, which is what
        # the PII design requires them to store.
        deredacted_response = deredact_for_session(agent_response, session_id, user_id=user_id)
        _log_pii_trace(trace_id, user_id, session_id, request.message, clean_message, agent_response, deredacted_response)

        total_ms = (time.time() - round_trip_start) * 1000

        if root_span:
            try:
                root_span.update(
                    output={"response": agent_response},
                    metadata={
                        "pii_flagged": pii_result["pii_detected"],
                        "guardrail_blocked": guardrail_blocked,
                        "total_duration_ms": total_ms,
                        # Also surfaced at the top level of the trace (not just
                        # buried inside the agent_turn span) so it's visible
                        # without having to drill in - directly answers "did
                        # memory get used this turn" from the trace list view.
                        "memory_injected": injected_memory_context is not None,
                        "injected_memory_context": injected_memory_context,
                    }
                )
            except Exception:
                logger.exception("Langfuse trace update failed for session %s", session_id)

    # ExitStack above has now closed root_span's context (auto-ending it) -
    # flush right after so it's visible in Langfuse immediately rather than
    # waiting on the SDK's background batching interval.
    try:
        langfuse.flush()
    except Exception:
        logger.exception("Langfuse flush failed for session %s", session_id)

    logger.info(
        "Chat turn complete user=%s session=%s pii_flagged=%s guardrail_blocked=%s total_duration_ms=%.1f",
        user_id, session_id, pii_result["pii_detected"], guardrail_blocked, total_ms,
    )

    return {
        "user_id": user_id,
        "session_id": session_id,
        "response": deredacted_response,
        "agent_name": agent_name,
        "pii_flagged": pii_result["pii_detected"],
        "guardrail_blocked": guardrail_blocked
    }


def _log_pii_trace(
    trace_id: str, user_id: str, session_id: str,
    raw_input: str, redacted_input: str, redacted_output: str, deredacted_output: str,
) -> None:
    """
    Logs the full PII redaction lifecycle for one message to app.log, in
    order, every line tagged with the same trace_id - so grepping that one
    ID (e.g. copied from this turn's Langfuse trace) surfaces exactly these
    four lines together instead of them being interleaved with every other
    concurrent turn's logging. Plain-text log lines can't render bold, so
    RAW_INPUT (like the other three tags) relies on its all-caps name for
    visual scanning rather than actual formatting.

    Runs on every turn, not just ones with PII - deredact_text/
    deredact_for_session are no-ops when there's nothing to restore, so
    redacted_output and deredacted_output are identical in that case.
    """
    logger.info("RAW_INPUT trace_id=%s user_id=%s session_id=%s text=%r", trace_id, user_id, session_id, raw_input)
    logger.info(
        "REDACTED_INPUT trace_id=%s user_id=%s session_id=%s text=%r",
        trace_id, user_id, session_id, redacted_input,
    )
    logger.info(
        "LLM_REDACTED_OUTPUT trace_id=%s user_id=%s session_id=%s text=%r",
        trace_id, user_id, session_id, redacted_output,
    )
    logger.info(
        "DEREDACTED_OUTPUT_SHOWN_TO_USER trace_id=%s user_id=%s session_id=%s text=%r",
        trace_id, user_id, session_id, deredacted_output,
    )


def _log_chat_turn(session_id, user_id, user_text, agent_text, pii_flagged, guardrail_blocked) -> None:
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_messages (session_id, user_id, role, content, pii_flagged, guardrail_blocked) "
                    "VALUES (%s, %s, 'user', %s, %s, %s)",
                    (session_id, user_id, user_text, pii_flagged, guardrail_blocked),
                )
                cur.execute(
                    "INSERT INTO chat_messages (session_id, user_id, role, content, pii_flagged, guardrail_blocked) "
                    "VALUES (%s, %s, 'agent', %s, false, %s)",
                    (session_id, user_id, agent_text, guardrail_blocked),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        logger.exception("Failed to persist chat_messages for session %s", session_id)
