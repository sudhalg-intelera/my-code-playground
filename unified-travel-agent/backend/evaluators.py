import re

from database import find_city_in_text

NEGATIVE_TONE_MARKERS = ["stupid", "dumb", "shut up", "whatever", "idk", "ugh"]


def groundedness_evaluator(*, input, output, expected_output=None, metadata=None, **kwargs):
    """
    Checks that the agent's answer is actually about the city the user asked
    about, rather than drifting to an unrelated destination - i.e. that the
    response is grounded in the request rather than a generic/mismatched reply.
    """
    user_text = input if isinstance(input, str) else str(input.get("message", input))
    output_text = output if isinstance(output, str) else str(output)

    requested_city = find_city_in_text(user_text)

    if requested_city is None:
        return {
            "name": "groundedness",
            "value": 1.0,
            "comment": "No specific city requested; nothing to ground against.",
        }

    is_grounded = requested_city.lower() in output_text.lower()
    return {
        "name": "groundedness",
        "value": 1.0 if is_grounded else 0.0,
        "comment": (
            f"Response correctly grounded in '{requested_city}'."
            if is_grounded
            else f"User asked about '{requested_city}' but the response never mentions it."
        ),
    }


def tone_evaluator(*, input, output, expected_output=None, metadata=None, **kwargs):
    """Heuristic check that the response reads as helpful and professional."""
    output_text = (output if isinstance(output, str) else str(output)).strip()

    if not output_text:
        return {"name": "tone", "value": 0.0, "comment": "Empty response."}

    lowered = output_text.lower()
    hits = [term for term in NEGATIVE_TONE_MARKERS if term in lowered]
    is_shouting = bool(re.search(r"[A-Z]{6,}", output_text))

    if hits or is_shouting:
        reason = f"unprofessional markers: {hits}" if hits else "excessive capitalization"
        return {"name": "tone", "value": 0.0, "comment": f"Tone issue detected ({reason})."}

    return {"name": "tone", "value": 1.0, "comment": "Tone reads as helpful and professional."}
