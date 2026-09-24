import os
from collections import Counter

import redis
from presidio_analyzer import AnalyzerEngine

from observability.audit import write_audit_log
from logging_config import get_logger

logger = get_logger("pii_guard")

# Presidio's NLP-based recognizers (spaCy en_core_web_lg) replace the old
# hand-written regex list - catches names, SSNs, IBANs, IP addresses, etc.
# that regex never covered, not just email/phone/card. Loaded once at import.
_analyzer = AnalyzerEngine()

# Deliberately excludes LOCATION, DATE_TIME, NRP, ORGANIZATION: a city name
# like "Paris" IS a location grammatically, but it's the exact thing the
# booking/destination agents need to read to do their job - redacting it
# would break search, not protect anyone.
ENTITIES_TO_REDACT = {
    "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "PERSON",
    "US_SSN", "IBAN_CODE", "IP_ADDRESS", "CRYPTO",
    "US_BANK_NUMBER", "US_DRIVER_LICENSE", "US_PASSPORT", "MEDICAL_LICENSE",
}
MIN_CONFIDENCE = 0.5

# Accumulates every token->original mapping seen across a session's turns.
# Needed because the ADK orchestrator's own memory can carry a redacted
# token forward into a LATER turn (e.g. a booking confirmed several turns
# after the email was mentioned), by which point that turn's own
# redaction_map from sanitize_user_input() no longer has the token.
#
# Stored in Redis (see docker-compose.yml's `redis` service) - one hash per
# session_id, field=token, value=original PII - so the map survives a
# backend restart instead of living only in this process's memory. Falls
# back to the in-memory dict below (process-lifetime only, same demo-scale
# caveat this used to carry unconditionally) if Redis is unreachable, so a
# dev machine that hasn't started the container yet doesn't lose PII
# redaction entirely - it just loses persistence across restarts.
_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_client = redis.Redis.from_url(_REDIS_URL, decode_responses=True)
_session_redaction_maps: dict[str, dict] = {}


def _redis_key(session_id: str) -> str:
    return f"pii_token_map:{session_id}"


def _get_session_map(session_id: str) -> dict:
    try:
        return _redis_client.hgetall(_redis_key(session_id))
    except Exception:
        logger.exception(
            "Redis unavailable reading token map for session %s - falling back to in-memory copy", session_id,
        )
        return _session_redaction_maps.get(session_id, {})


def _save_session_map(session_id: str, redaction_map: dict) -> None:
    # Mirrored into the in-memory dict unconditionally so a later Redis
    # outage this same process-lifetime still has this turn's tokens to
    # fall back on, even though a fresh process after a restart would not.
    _session_redaction_maps.setdefault(session_id, {}).update(redaction_map)
    try:
        _redis_client.hset(_redis_key(session_id), mapping=redaction_map)
    except Exception:
        logger.exception(
            "Redis unavailable saving token map for session %s - kept in-memory only this turn", session_id,
        )


def _resolve_overlaps(results):
    """Presidio can return overlapping spans (e.g. EMAIL_ADDRESS and URL both
    matching the domain part) - keep only the highest-confidence one per span."""
    accepted = []
    for r in sorted(results, key=lambda r: r.score, reverse=True):
        if any(r.start < a.end and a.start < r.end for a in accepted):
            continue
        accepted.append(r)
    return sorted(accepted, key=lambda r: r.start)


def sanitize_user_input(text: str, user_id: str | None = None, session_id: str | None = None) -> dict:
    """
    Scans and redacts PII using Presidio's NLP-based entity recognition.
    Each redacted span becomes a unique token (e.g. [PERSON_REDACTED_1])
    mapped back to its original value in redaction_map, so a downstream
    tool/DB write that legitimately needs the real value can call
    deredact_text() and still execute seamlessly - the LLM, Langfuse trace,
    and chat_messages log only ever see the redacted form. main.py
    de-redacts the final reply back to real values (e.g. the user's own
    email echoed back in a booking confirmation) only in the HTTP response
    actually shown to that same user - never in what gets traced or stored.
    """
    session_map = _get_session_map(session_id) if session_id else {}

    try:
        raw_results = _analyzer.analyze(text=text, language="en", entities=list(ENTITIES_TO_REDACT))
    except Exception:
        logger.exception("Presidio analysis failed for user_id=%s - passing text through unredacted", user_id)
        raw_results = []

    results = [r for r in _resolve_overlaps(raw_results) if r.score >= MIN_CONFIDENCE]

    # Continue numbering per type from what's already in this session's map,
    # so a second EMAIL_ADDRESS/etc. in a later turn doesn't collide with an
    # earlier turn's token of the same name.
    type_counts = Counter()
    for pii_type in {r.entity_type for r in results}:
        type_counts[pii_type] = sum(1 for k in session_map if k.startswith(f"[{pii_type}_REDACTED_"))

    # Dedup: the exact same real value (e.g. the user typing their email
    # twice in one message, or repeating it a turn later) should always
    # collapse onto the SAME token, not mint a new one each time - otherwise
    # one real email ends up scattered across [EMAIL_ADDRESS_REDACTED_1],
    # _2, _3... in the logs/audit trail, which both inflates the redaction
    # count and makes it look like three different people's data.
    value_to_token = {v: k for k, v in session_map.items()}

    detected_types = []
    redaction_map = {}
    new_tokens = 0
    sanitized_text = text

    # This substitution logic (unlike the analyze() call above) previously
    # had no guard of its own - a failure here would raise all the way up
    # through chat_endpoint BEFORE any Langfuse span exists, since PII
    # redaction now deliberately runs first (see main.py). Wrapping it keeps
    # the same fail-open behavior as an analyzer failure - pass the
    # original text through unredacted rather than crashing the whole turn -
    # instead of the one safety-relevant code path in the request being the
    # one with no fallback.
    try:
        offset = 0
        for r in results:
            pii_type = r.entity_type
            original_value = text[r.start:r.end]
            detected_types.append(pii_type)

            token = value_to_token.get(original_value)
            if token is None:
                type_counts[pii_type] += 1
                token = f"[{pii_type}_REDACTED_{type_counts[pii_type]}]"
                value_to_token[original_value] = token
                new_tokens += 1
            redaction_map[token] = original_value

            start, end = r.start + offset, r.end + offset
            sanitized_text = sanitized_text[:start] + token + sanitized_text[end:]
            offset += len(token) - (r.end - r.start)
    except Exception:
        logger.exception("PII redaction substitution failed for user_id=%s - passing text through unredacted", user_id)
        detected_types, redaction_map, new_tokens, sanitized_text = [], {}, 0, text

    if redaction_map:
        if session_id:
            _save_session_map(session_id, redaction_map)
        unique_types = sorted(set(detected_types))
        logger.info(
            "PII_REDACTED user_id=%s types=%s occurrences=%d new_tokens=%d",
            user_id, unique_types, len(detected_types), new_tokens,
        )
        write_audit_log(
            user_id, "pii_redacted",
            {"types": unique_types, "occurrences": len(detected_types), "new_tokens": new_tokens},
        )

    return {
        "sanitized_text": sanitized_text,
        "pii_detected": len(redaction_map) > 0,
        "pii_types": sorted(set(detected_types)),
        "redaction_map": redaction_map,
    }


def deredact_text(text: str, redaction_map: dict | None, user_id: str | None = None) -> str:
    """
    Restores original PII values into `text` using the map produced by
    sanitize_user_input. Use this only at the point where a real value is
    genuinely required (e.g. storing contact info against a confirmed
    booking) - never to feed real PII back into the LLM or a trace.
    """
    if not redaction_map:
        return text

    restored = text
    replaced = 0
    for token, original in redaction_map.items():
        if token in restored:
            restored = restored.replace(token, original)
            replaced += 1

    # Only log/audit an actual substitution - this now runs on every turn's
    # final response (see main.py), where most calls have a non-empty
    # session-wide redaction_map available but no token actually present in
    # THIS particular text, which would otherwise spam PII_DEREDACTED with a
    # count of tokens merely available, not tokens actually restored.
    if replaced:
        logger.info("PII_DEREDACTED user_id=%s count=%d", user_id, replaced)
        write_audit_log(user_id, "pii_deredacted", {"count": replaced})
    return restored


def deredact_for_session(text: str, session_id: str | None, user_id: str | None = None) -> str:
    """
    De-redacts using every PII token seen anywhere in this session so far,
    not just the current turn - for callers (like the ADK orchestrator's
    booking tool) where confirmation can happen turns after the PII was
    originally mentioned, once it's no longer in that turn's own map.
    """
    if not session_id:
        return text
    return deredact_text(text, _get_session_map(session_id), user_id=user_id)


def get_session_token_map(session_id: str) -> dict:
    """
    Public read of this session's token -> real value map (the same data
    view-token-map.ps1 reads via redis-cli) - for a caller that wants to
    show it directly rather than shelling out. Callers are responsible for
    authorizing the request; this returns whatever Redis has for the given
    session_id with no ownership check of its own.
    """
    return _get_session_map(session_id)
