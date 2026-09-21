"""
Each agent lives in its own file (root_agent.py, booking_agent.py,
itinerary_agent.py, destination_agent.py, travel_agent.py). This re-export
keeps `from adk_app.agents import root_agent` working unchanged for
adk_app/runner.py - the only thing outside this package that needs it.
"""

from adk_app.agents.root_agent import root_agent

__all__ = ["root_agent"]
