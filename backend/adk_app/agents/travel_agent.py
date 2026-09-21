"""General travel fallback - anything not booking/itinerary/destination-specific."""

from google.adk.agents import Agent
from google.adk.tools import BaseTool, FunctionTool

from adk_app.agents._observability import after_model_callback, before_model_callback
from adk_app.agents._shared import MODEL
from adk_app.tools import get_destination_info_adk

# FunctionTool is ADK's own native subclass of BaseTool - this annotation
# makes that relationship explicit in our code, not just true by inheritance
# inside the ADK library.
TRAVEL_TOOLS: list[BaseTool] = [FunctionTool(get_destination_info_adk)]

travel_agent = Agent(
    name="travel_agent",
    model=MODEL,
    description=(
        "General travel questions and inspiration - the fallback agent for "
        "anything not booking/itinerary/destination-specific."
    ),
    instruction=(
        "You answer general travel questions. Call get_destination_info_adk "
        "for the city mentioned (if any) and share highlights and best time "
        "to visit."
    ),
    tools=TRAVEL_TOOLS,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
