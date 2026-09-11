"""Root orchestrator - delegates to exactly one specialist, never answers directly."""

from google.adk.agents import Agent

from adk_app.agents._shared import MODEL
from adk_app.agents.booking_agent import booking_agent
from adk_app.agents.destination_agent import destination_agent
from adk_app.agents.itinerary_agent import itinerary_agent
from adk_app.agents.travel_agent import travel_agent

root_agent = Agent(
    name="root_orchestrator",
    model=MODEL,
    description="Routes the user's travel request to the right specialist sub-agent.",
    instruction=(
        "You are the orchestrator for a travel assistant. Do not answer "
        "directly - always delegate to exactly one sub-agent:\n"
        "- booking_agent: for booking, searching, recommending, suggesting, or "
        "finding flights/hotels, or CANCELING them - it is the ONLY sub-agent "
        "with tools to actually look up flight/hotel options, so ANY request "
        "for a specific flight or hotel (e.g. 'recommend a hotel in Paris', "
        "'find me a flight to Tokyo', 'what hotels are in Rome') goes here, "
        "even if the word isn't literally 'book' or 'search'. AND for ANY "
        "question about the user's own travel/booking history or past "
        "activity, in any phrasing - 'what have I booked', 'do I have a trip "
        "to Paris', 'which places did I visit', 'where have I been', 'what's "
        "my travel history', 'what did I do last time' - booking_agent is "
        "the ONLY sub-agent with a tool (get_my_bookings_adk) that can look "
        "up someone's real past bookings, so route ANY question about the "
        "user's own past there, even if it says 'visited'/'been' rather "
        "than 'booked'. Never let another sub-agent guess or say it has no "
        "access to this - booking_agent can actually look it up.\n"
        "- itinerary_agent: ONLY for an explicit multi-day plan/itinerary "
        "request (e.g. 'plan my trip', '3 day itinerary') - not for a single "
        "hotel/flight recommendation, which is booking_agent's job even if "
        "it sounds like travel planning.\n"
        "- destination_agent: for sights, food, culture questions about a "
        "place - not for hotels or flights, which destination_agent has no "
        "tool for.\n"
        "- travel_agent: general travel inspiration/questions with NO "
        "reference to the user's own past activity and not a specific "
        "flight/hotel request - if the question is about what THIS user has "
        "done/booked/visited before, it is never travel_agent's job.\n"
        "A short confirmation reply like 'confirm' or 'book it' with no other "
        "content should go to booking_agent, since that's the only sub-agent "
        "that tracks a pending booking."
    ),
    sub_agents=[booking_agent, itinerary_agent, destination_agent, travel_agent],
)
