"""Itinerary specialist - builds a multi-day plan combining sights and a hotel."""

from google.adk.agents import Agent
from google.adk.tools import BaseTool, FunctionTool

from adk_app.agents._observability import after_model_callback, before_model_callback
from adk_app.agents._shared import MODEL
from adk_app.tools import get_destination_info_adk, save_itinerary_adk, search_hotels_adk

# FunctionTool is ADK's own native subclass of BaseTool - this annotation
# makes that relationship explicit in our code, not just true by inheritance
# inside the ADK library.
ITINERARY_TOOLS: list[BaseTool] = [
    FunctionTool(get_destination_info_adk),
    FunctionTool(search_hotels_adk),
    FunctionTool(save_itinerary_adk),
]

itinerary_agent = Agent(
    name="itinerary_agent",
    model=MODEL,
    description="Builds a multi-day itinerary combining sights and a hotel for a destination.",
    instruction=(
        "You build short multi-day itineraries. Call get_destination_info_adk "
        "and search_hotels_adk for the destination city, then compose a "
        "concise day-by-day plan using real sights/food from the results. "
        "Once you've composed the final plan, call save_itinerary_adk with "
        "the city and the full plan text before replying to the user."
    ),
    tools=ITINERARY_TOOLS,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
