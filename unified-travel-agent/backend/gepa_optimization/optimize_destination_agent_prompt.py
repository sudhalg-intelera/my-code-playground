"""
DSPy + GEPA prompt optimization for a real ADK SUB-AGENT (destination_agent),
not the root orchestrator - per Sudha's ask: optimize a sub-agent's prompt,
starting from a deliberately poor one, budgeted to 1-2 epochs (max_full_evals),
then present the before/after improvement.

Task mirrors destination_agent's actual job in adk_app/agents.py: given a
city plus the sights/food/best_season get_destination_info_adk would return
(real rows pulled from the destinations table, not invented), write the
travel-guide reply. This isolates prompt/response-composition quality from
tool-calling behaviour - GEPA is optimizing HOW it writes the answer, which
is exactly what an LLM instruction controls.

Deliberately bad starting instruction: "Answer the question." - no mention
of using the provided facts, no completeness requirement, no format guidance.

Metric is deterministic and cheap (no extra LLM judge call): does the reply
actually mention every sight, every food item, and the best season it was
given? Missing anything is exactly the kind of concrete, checkable failure
GEPA's reflection can act on.

Run standalone:
    cd backend
    venv/Scripts/python gepa_optimization/optimize_destination_agent_prompt.py
"""

import os

import dspy
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

TASK_MODEL = "openai/gpt-4o-mini"
MAX_FULL_EVALS = 2  # "1 or 2 epochs"


# --- The deliberately poor starting prompt for this sub-agent.
# "Give a short answer" actively conflicts with completeness (7 required
# facts per city) - unlike a merely vague instruction, this reliably causes
# the model to omit facts on every example, giving GEPA real, consistent
# headroom to fix rather than one occasional miss.
class DestinationGuide(dspy.Signature):
    """Give a short answer."""

    city: str = dspy.InputField()
    sights: str = dspy.InputField(desc="comma-separated list of top sights")
    food: str = dspy.InputField(desc="comma-separated list of local food")
    best_season: str = dspy.InputField()
    response: str = dspy.OutputField(desc="a travel guide reply to the user")


def make_example(city: str, sights: list[str], food: list[str], best_season: str) -> dspy.Example:
    return dspy.Example(
        city=city,
        sights=", ".join(sights),
        food=", ".join(food),
        best_season=best_season,
    ).with_inputs("city", "sights", "food", "best_season")


# Real rows from the destinations table (backend/db/seed.sql), not invented.
TRAIN = [
    make_example("Kyoto", ["Fushimi Inari Shrine", "Kinkaku-ji (Golden Pavilion)", "Arashiyama Bamboo Grove"],
                  ["Matcha Parfait", "Kaiseki Dining", "Yudofu"], "Spring (Cherry Blossoms) or Autumn"),
    make_example("Paris", ["Eiffel Tower", "Louvre Museum", "Montmartre & Sacre-Coeur"],
                  ["Croissants", "Duck Confit", "Macarons"], "Late Spring to Early Autumn"),
    make_example("Rome", ["Colosseum", "Vatican Museums", "Trevi Fountain"],
                  ["Carbonara", "Gelato", "Suppli"], "Spring or Autumn"),
    make_example("Athens", ["Acropolis", "Plaka District", "National Archaeological Museum"],
                  ["Moussaka", "Souvlaki", "Baklava"], "Spring or Autumn"),
    make_example("Cairo", ["Pyramids of Giza", "Egyptian Museum", "Khan el-Khalili"],
                  ["Koshari", "Falafel", "Molokhia"], "Autumn to Spring (cooler months)"),
]

VAL = [
    make_example("Bangkok", ["Grand Palace", "Wat Arun", "Chatuchak Market"],
                  ["Pad Thai", "Tom Yum", "Mango Sticky Rice"], "November to February"),
    make_example("Sydney", ["Sydney Opera House", "Harbour Bridge", "Bondi Beach"],
                  ["Meat Pies", "Barramundi", "Pavlova"], "September to November"),
    make_example("Tokyo", ["Senso-ji Temple", "Shibuya Crossing", "Tokyo Tower"],
                  ["Sushi", "Ramen", "Tempura"], "Spring (Cherry Blossoms) or Autumn"),
]


def guide_metric(gold, pred, trace=None, pred_name=None, pred_trace=None, program_trace=None):
    """Deterministic completeness check + specific feedback on what's missing."""
    response = (getattr(pred, "response", "") or "")
    resp_lower = response.lower()

    required_sights = [s.strip() for s in gold.sights.split(",")]
    required_food = [f.strip() for f in gold.food.split(",")]

    missing_sights = [s for s in required_sights if s.lower() not in resp_lower]
    missing_food = [f for f in required_food if f.lower() not in resp_lower]
    missing_season = gold.best_season.lower() not in resp_lower

    total_items = len(required_sights) + len(required_food) + 1
    missing_count = len(missing_sights) + len(missing_food) + int(missing_season)
    score = max(0.0, (total_items - missing_count) / total_items)

    if missing_count == 0:
        feedback = (
            f"Complete - mentioned all {len(required_sights)} sights, all {len(required_food)} "
            f"food items, and the best season for {gold.city}."
        )
    else:
        parts = []
        if missing_sights:
            parts.append(f"missing sights: {', '.join(missing_sights)}")
        if missing_food:
            parts.append(f"missing food items: {', '.join(missing_food)}")
        if missing_season:
            parts.append(f"never mentioned the best season to visit ({gold.best_season})")
        feedback = (
            f"Incomplete response for {gold.city}: " + "; ".join(parts) + ". A good travel guide "
            "reply must explicitly name every sight, every food item, and the best season given "
            "in the input - don't summarize, paraphrase away, or omit any of them."
        )

    return dspy.Prediction(score=score, feedback=feedback)


def _evaluate(program, examples) -> tuple[float, list[str]]:
    total = 0.0
    lines = []
    for ex in examples:
        pred = program(city=ex.city, sights=ex.sights, food=ex.food, best_season=ex.best_season)
        result = guide_metric(ex, pred)
        total += result.score
        lines.append(f"  [{result.score:.2f}] {ex.city}: {result.feedback}")
    return total, lines


def main() -> None:
    lm = dspy.LM(TASK_MODEL, api_key=os.getenv("OPENAI_API_KEY"), temperature=0.0)
    dspy.configure(lm=lm)

    program = dspy.Predict(DestinationGuide)

    print("=== BEFORE optimization ===")
    print("Instruction:", repr(program.signature.instructions))
    before_total, before_lines = _evaluate(program, VAL)
    print("\n".join(before_lines))
    print(f"Baseline val score: {before_total:.2f}/{len(VAL)}\n")

    optimizer = dspy.GEPA(
        metric=guide_metric,
        max_full_evals=MAX_FULL_EVALS,
        reflection_lm=lm,
        reflection_minibatch_size=3,
        track_stats=True,
    )

    optimized = optimizer.compile(program, trainset=TRAIN, valset=VAL)

    print("\n=== AFTER optimization ===")
    print("Instruction:", repr(optimized.signature.instructions))
    after_total, after_lines = _evaluate(optimized, VAL)
    print("\n".join(after_lines))
    print(f"Optimized val score: {after_total:.2f}/{len(VAL)}")
    print(f"\nBaseline {before_total:.2f}/{len(VAL)} -> Optimized {after_total:.2f}/{len(VAL)}")


if __name__ == "__main__":
    main()
