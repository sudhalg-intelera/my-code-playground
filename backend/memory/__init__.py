"""Memory as one stack: the sliding-window session summary logic lives in
session_summaries.py. Re-exported here so `from memory import ...` keeps
working unchanged for main.py and adk_app/runner.py."""

from memory.session_summaries import get_recent_session_summaries, update_session_summary

__all__ = ["get_recent_session_summaries", "update_session_summary"]
