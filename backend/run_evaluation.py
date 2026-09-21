"""
Script-level evaluator trigger.

1. Migrates the smoke-test conversations into a Langfuse Dataset (once).
2. Runs a Langfuse Experiment against that dataset through the real
   chat_endpoint, scored by the groundedness and tone evaluators.

Run manually:
    python run_evaluation.py

Equivalent UI-level trigger: open the dataset in Langfuse
(Datasets > unified_travel_agent_eval_set) and click "Run Experiment" -
Langfuse's Experiments feature can call this same task/evaluator pairing
via its experiments webhook for CI-triggered runs.
"""

import asyncio

from observability.langfuse_config import langfuse
from main import ChatRequest, chat_endpoint
from evaluators import groundedness_evaluator, tone_evaluator

DATASET_NAME = "unified_travel_agent_eval_set"

TEST_CASES = [
    {
        "user_id": "user_123",
        "session_id": "eval_sess_001",
        "message": "Planning a 5-day trip to Kyoto. Need boutique hotel ideas and top cultural sights.",
    },
    {
        "user_id": "user_456",
        "session_id": "eval_sess_002",
        "message": "Can you check flights to Paris?",
    },
    {
        "user_id": "user_789",
        "session_id": "eval_sess_003",
        "message": "Create a detailed 3-day itinerary for outdoor activities in Vancouver.",
    },
]


def ensure_dataset() -> None:
    try:
        langfuse.create_dataset(
            name=DATASET_NAME, description="Travel agent smoke-test conversations"
        )
    except Exception:
        pass  # dataset already exists

    existing = langfuse.get_dataset(DATASET_NAME)
    existing_messages = {
        item.input.get("message") for item in existing.items if isinstance(item.input, dict)
    }

    for case in TEST_CASES:
        if case["message"] in existing_messages:
            continue
        langfuse.create_dataset_item(dataset_name=DATASET_NAME, input=case)


def task(*, item, **kwargs):
    data = item.input
    request = ChatRequest(
        user_id=data["user_id"], session_id=data["session_id"], message=data["message"]
    )
    result = asyncio.run(chat_endpoint(request, claims={"sub": data["user_id"]}))
    return result["response"]


def run() -> None:
    ensure_dataset()
    dataset = langfuse.get_dataset(DATASET_NAME)

    result = dataset.run_experiment(
        name="Travel Agent Groundedness & Tone Check",
        task=task,
        evaluators=[groundedness_evaluator, tone_evaluator],
    )

    print(result.format())


if __name__ == "__main__":
    run()
