import json
from datetime import datetime, timezone

from database import get_db_connection
from logging_config import get_logger

logger = get_logger("audit")


def write_audit_log(user_id: str | None, action: str, details=None) -> None:
    """
    Persists an audit event to the audit_logs table and to app.log, timestamped
    in UTC. Used for login/register attempts, PII redaction/de-redaction, and
    guardrail blocks so there's a queryable, timestamped trail of each.
    """
    ts = datetime.now(timezone.utc)
    details_str = details if isinstance(details, str) else json.dumps(details or {})
    logger.info("AUDIT action=%s user_id=%s details=%s", action, user_id, details_str)

    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO audit_logs (timestamp, user_id, action, details) VALUES (%s, %s, %s, %s)",
                    (ts, user_id, action, details_str),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        logger.exception("Failed to persist audit log to database (action=%s)", action)
