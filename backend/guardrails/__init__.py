"""
client.py runs NeMo Guardrails in-process (this is what main.py calls).

Previously ran as a separate HTTP microservice under its own Python 3.11
venv, because nemoguardrails was incompatible with the main app's then-Python
3.14. Now that backend/venv itself runs Python 3.11.9, it runs directly here.

This re-export keeps `from guardrails import check_guardrails,
check_output_guardrails` working unchanged for main.py.
"""

from guardrails.client import check_bare_flow, check_guardrails, check_output_guardrails

__all__ = ["check_bare_flow", "check_guardrails", "check_output_guardrails"]
