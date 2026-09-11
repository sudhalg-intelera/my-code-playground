"""
Everything guardrail-related lives under this one folder:
- client.py talks to the NeMo service over HTTP (this is what main.py calls).
- nemo_service/ is the actual NeMo engine - a separate Python 3.11 process,
  because nemoguardrails is incompatible with the main app's Python 3.14
  (see nemo_service/app.py's docstring for the exact reason).

This re-export keeps `from guardrails import check_guardrails,
check_output_guardrails` working unchanged for main.py.
"""

from guardrails.client import check_guardrails, check_output_guardrails

__all__ = ["check_guardrails", "check_output_guardrails"]
