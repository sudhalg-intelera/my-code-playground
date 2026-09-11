import os

import requests

from observability.audit import write_audit_log
from logging_config import get_logger

logger = get_logger("guardrails")

NEMO_SERVICE_URL = os.getenv("NEMO_SERVICE_URL", "http://127.0.0.1:8100")
NEMO_TIMEOUT_SECONDS = 8


def check_guardrails(text: str, user_id: str | None = None) -> dict:
    """
    Screens user input via NeMo Guardrails' self-check-input rail
    (semantic/LLM-based) before it reaches any agent. Blocks are timestamped
    in app.log and audit_logs via write_audit_log.
    """
    nemo_allowed = _call_nemo("/check_input", {"text": text})

    if nemo_allowed is None:
        result = {"allowed": False, "reason": "guardrail_service_unavailable", "matched": "self_check_input"}
        _log_block(user_id, result)
        return result

    if not nemo_allowed:
        result = {"allowed": False, "reason": "nemo_guardrails_blocked", "matched": "self_check_input"}
        _log_block(user_id, result)
        return result

    return {"allowed": True, "reason": None, "matched": None}


def check_output_guardrails(user_text: str, bot_text: str, user_id: str | None = None) -> dict:
    """
    Screens a generated bot reply before it's returned, using NeMo
    Guardrails' self-check-output rail - needs the user's message alongside
    the reply since that's the conversational pair the rail evaluates.
    """
    nemo_allowed = _call_nemo("/check_output", {"user_text": user_text, "bot_text": bot_text})

    if nemo_allowed is None:
        result = {"allowed": False, "reason": "guardrail_service_unavailable", "matched": "self_check_output"}
        _log_block(user_id, result)
        return result

    if not nemo_allowed:
        result = {"allowed": False, "reason": "nemo_guardrails_blocked", "matched": "self_check_output"}
        _log_block(user_id, result)
        return result

    return {"allowed": True, "reason": None, "matched": None}


def _call_nemo(path: str, payload: dict) -> bool | None:
    """Returns True/False from the NeMo service, or None if it's unreachable."""
    try:
        resp = requests.post(f"{NEMO_SERVICE_URL}{path}", json=payload, timeout=NEMO_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.json()["allowed"]
    except Exception:
        logger.error("NeMo Guardrails service unreachable (%s) - failing closed (blocking)", path)
        return None


def _log_block(user_id: str | None, result: dict) -> None:
    logger.warning(
        "GUARDRAIL_BLOCKED user_id=%s reason=%s matched=%s",
        user_id, result["reason"], result["matched"],
    )
    write_audit_log(user_id, "guardrail_blocked", result)
