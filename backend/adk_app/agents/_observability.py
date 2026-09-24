"""
Logs every real LLM call any agent in this package makes as its own Langfuse
generation - exactly the system prompt, the full message list (including any
memory-recap text runner.py injected into the user's turn), and the model's
reply, all as they actually went in/out.

ADK's own OTEL auto-instrumentation already records a request/response blob
on its 'call_llm' span (see google.adk.telemetry.tracing.trace_call_llm), but
under a legacy gcp.vertex.agent.* attribute name, not Langfuse's own
input/output shape - so it doesn't render as a proper Generation in the
Langfuse UI. before_model_callback/after_model_callback are ADK's own
extension points for exactly this (run once per real LLM call, in order,
inside that same 'call_llm' span - see base_llm_flow.py's _call_llm_async),
so every agent in this package is wired to the same pair of callbacks below
rather than each hand-rolling its own logging.

Since main.py runs the whole turn inside a real OpenTelemetry span context
(langfuse.start_as_current_observation), a generation opened here - even
via start_observation, which doesn't itself become "current" - still nests
under whichever span is currently open (main.py's agent_turn), the same way
ADK's own native spans do.
"""

import contextvars
import time

from logging_config import get_logger
from observability.langfuse_config import langfuse

logger = get_logger("adk_observability")

# One real LLM call runs before_model_callback then after_model_callback back
# to back within the same asyncio task before the next one starts (ADK does
# not overlap them), so a ContextVar - scoped per asyncio task, unlike a
# plain module global - safely correlates the two across concurrent turns
# from different requests. Holds (generation, start_time) so after_model_
# callback can report duration_ms the same way main.py does for guardrails.
_current_call = contextvars.ContextVar("_current_call", default=None)


def _dump_content(content) -> dict:
    """Turns one google.genai types.Content into a small, readable dict -
    text for a normal turn, name/args or name/response for a tool step."""
    parts = []
    for part in content.parts or []:
        if part.text:
            parts.append({"text": part.text})
        elif part.function_call:
            parts.append({
                "function_call": {
                    "name": part.function_call.name,
                    "args": dict(part.function_call.args or {}),
                }
            })
        elif part.function_response:
            parts.append({
                "function_response": {
                    "name": part.function_response.name,
                    "response": part.function_response.response,
                }
            })
        else:
            parts.append({"other": type(part).__name__})
    return {"role": content.role, "parts": parts}


def before_model_callback(callback_context, llm_request):
    # Never let a Langfuse/serialization hiccup here break the actual LLM
    # call - same fail-open contract as every other observability call in
    # this app (see pii/guard.py, guardrails/client.py). Logged so a failure
    # is visible in app.log instead of just quietly missing from Langfuse.
    try:
        generation = langfuse.start_observation(
            name=f"llm_call:{callback_context.agent_name}",
            as_type="generation",
            input={
                "system_prompt": llm_request.config.system_instruction,
                "messages": [_dump_content(c) for c in llm_request.contents],
            },
            metadata={
                "agent": callback_context.agent_name,
                "invocation_id": callback_context.invocation_id,
            },
            model=llm_request.model,
        )
        _current_call.set((generation, time.time()))
    except Exception:
        logger.exception(
            "Langfuse generation logging failed (before_model_callback) for agent=%s - "
            "continuing without it", callback_context.agent_name,
        )
    return None


def after_model_callback(callback_context, llm_response):
    call = _current_call.get()
    if call is None:
        return None
    _current_call.set(None)
    generation, start_time = call

    try:
        output = _dump_content(llm_response.content) if llm_response.content else None
        duration_ms = (time.time() - start_time) * 1000
        generation.update(output=output, metadata={"duration_ms": duration_ms})
        generation.end()
    except Exception:
        logger.exception(
            "Langfuse generation logging failed (after_model_callback) for agent=%s - "
            "continuing without it", callback_context.agent_name,
        )
    return None
