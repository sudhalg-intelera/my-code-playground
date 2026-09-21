"""PII as one stack: Presidio-based detection/redaction lives in guard.py.
Re-exported here so `from pii import ...` works the same way `from
pii_guard import ...` used to."""

from pii.guard import deredact_for_session, deredact_text, sanitize_user_input

__all__ = ["deredact_for_session", "deredact_text", "sanitize_user_input"]
