import asyncio
import time
import uuid
from contextlib import ExitStack, asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from adk_app.runner import run_turn
from auth import AuthResponse, LoginRequest, RegisterRequest, get_current_user, login_user, register_user
from database import ensure_session, get_db_connection, init_db
from guardrails import check_guardrails, check_output_guardrails
from langfuse import propagate_attributes
from observability.langfuse_config import langfuse
from logging_config import get_logger
from memory import update_session_summary
from pii import sanitize_user_input
from observability.tracing import end_span, span_id, start_span

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
                    input={"message": request.message},
                    metadata={"user_id": user_id, "session_id": session_id},
                )
            )
        except Exception:
            logger.exception("Langfuse trace creation failed for session %s", session_id)
        root_span_id = span_id(root_span)

        # Stage 1: input guardrails - run on the raw message, before anything else sees it.
        # Exactly one of these per turn - NeMo, no regex.
        guard_start = time.time()
        input_guard_span = start_span(
            langfuse, trace_id, root_span_id,
            name="input_guardrails", as_type="guardrail", input_data={"message": request.message},
        )
        guard_result = check_guardrails(request.message, user_id=user_id)
        input_guard_ms = (time.time() - guard_start) * 1000
        end_span(input_guard_span, output=guard_result, metadata={"duration_ms": input_guard_ms})
        logger.info(
            "INPUT_GUARDRAILS session=%s allowed=%s duration_ms=%.1f",
            session_id, guard_result["allowed"], input_guard_ms,
        )

        pii_result = sanitize_user_input(request.message, user_id=user_id, session_id=session_id)
        clean_message = pii_result["sanitized_text"]

        output_guard_result = {"allowed": True, "reason": None, "matched": None}

        if not guard_result["allowed"]:
            agent_response = (
                "This request was blocked by our safety guardrails "
                f"({guard_result['reason']}). Please rephrase and try again."
            )
            agent_name = "Safety Guardrails"
        else:
            # Stage 2: the ADK orchestrator (root_orchestrator) delegates to a
            # sub-agent, which uses its tool(s). ADK's own native tracing
            # (invoke_agent/call_llm/generate_content/tool spans) nests
            # directly under root_span above - see the comment there.
            agent_response, agent_name = await run_turn(
                user_id=user_id, session_id=session_id, message=clean_message,
            )

            # Stage 3: output guardrails - screen the generated response before it goes back to the user.
            # Exactly one of these per turn, same as input guardrails.
            out_guard_start = time.time()
            output_guard_span = start_span(
                langfuse, trace_id, root_span_id,
                name="output_guardrails", as_type="guardrail", input_data={"response": agent_response},
            )
            output_guard_result = check_output_guardrails(clean_message, agent_response, user_id=user_id)
            output_guard_ms = (time.time() - out_guard_start) * 1000
            end_span(output_guard_span, output=output_guard_result, metadata={"duration_ms": output_guard_ms})
            logger.info(
                "OUTPUT_GUARDRAILS session=%s allowed=%s duration_ms=%.1f",
                session_id, output_guard_result["allowed"], output_guard_ms,
            )

            if not output_guard_result["allowed"]:
                logger.warning("Output guardrail tripped for session %s (reason=%s)", session_id, output_guard_result["reason"])
                agent_response = "Our response was withheld by output safety guardrails. Please rephrase your request."
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

        total_ms = (time.time() - round_trip_start) * 1000

        if root_span:
            try:
                root_span.update(
                    output={"response": agent_response},
                    metadata={
                        "pii_flagged": pii_result["pii_detected"],
                        "guardrail_blocked": guardrail_blocked,
                        "total_duration_ms": total_ms,
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
        "response": agent_response,
        "agent_name": agent_name,
        "pii_flagged": pii_result["pii_detected"],
        "guardrail_blocked": guardrail_blocked
    }


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
