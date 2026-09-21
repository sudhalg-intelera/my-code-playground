from logging_config import get_logger

logger = get_logger("tracing")


def start_span(langfuse_client, trace_id, parent_span_id, name, as_type, input_data=None):
    """
    Starts a Langfuse observation nested under parent_span_id (or trace-root
    if parent_span_id is None). Returns None (never raises) if langfuse_client/
    trace_id are missing or the call fails, so callers can no-op safely.
    """
    if not langfuse_client or not trace_id:
        return None
    try:
        trace_context = {"trace_id": trace_id}
        if parent_span_id:
            trace_context["parent_span_id"] = parent_span_id
        return langfuse_client.start_observation(
            trace_context=trace_context, name=name, as_type=as_type, input=input_data
        )
    except Exception:
        logger.exception("Failed to start span '%s'", name)
        return None


def end_span(span, output=None, metadata=None) -> None:
    """Closes a span started with start_span(). Safe to call with span=None."""
    if not span:
        return
    try:
        span.update(output=output, metadata=metadata)
        span.end()
    except Exception:
        logger.exception("Failed to end span")


def span_id(span):
    """Returns span.id, or None if span is None."""
    return span.id if span else None
