"""Destination guide - sights, food, and culture for a place."""

from google.adk.agents import Agent
from google.adk.tools import BaseTool, FunctionTool

from adk_app.agents._shared import MODEL
from adk_app.tools import get_destination_info_adk

# FunctionTool is ADK's own native subclass of BaseTool - this annotation
# makes that relationship explicit in our code, not just true by inheritance
# inside the ADK library.
DESTINATION_TOOLS: list[BaseTool] = [FunctionTool(get_destination_info_adk)]

destination_agent = Agent(
    name="destination_agent",
    model=MODEL,
    description="Answers questions about sights, food, and culture for a destination.",
    instruction=(
        "You are a destination guide. Call get_destination_info_adk with the "
        "city the user asked about. Your response must state the city name, "
        "then list every sight and every food item the tool returned and the "
        "best season to visit - without summarizing, paraphrasing, or "
        "omitting any of them. Keep it concise otherwise; avoid commentary "
        "beyond those elements."
    ),
    tools=DESTINATION_TOOLS,
)
