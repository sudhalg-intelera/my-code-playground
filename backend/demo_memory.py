"""
Standalone demo script - run this yourself with the backend already running
(`uvicorn main:app --reload` or however you normally start it).

Demonstrates three things in one run, using real API calls against your own
running backend:

1. Session-summary memory actually gets reinjected: a first conversation
   mentions interest in Italy; a brand-new second conversation (new
   session_id, same user) should have the agent proactively bring Italy up
   without being asked again.
2. PII redaction: the email in message 1 never reaches the LLM/Langfuse in
   raw form - only [EMAIL_ADDRESS_REDACTED_N] does.
3. PII deduplication: the SAME email is typed twice in one message - it
   should collapse onto ONE token, not two.

Usage:
    python demo_memory.py

Then check:
    - The printed agent replies below (turn 2 should reference Italy).
    - backend/app.log for a line like:
      PII_REDACTED ... occurrences=2 new_tokens=1
      (occurrences=2 because the email appears twice, new_tokens=1 because
      dedup collapsed both onto the same token)
    - Langfuse: open turn 2's trace -> agent_turn span -> metadata should
      show memory_injected=true and the actual injected_memory_context text.
"""

import time
import uuid

import requests

API_BASE = "http://127.0.0.1:8000"
USERNAME = f"memory_demo_{uuid.uuid4().hex[:8]}"
PASSWORD = "demo-password-123"


def register_and_login() -> str:
    requests.post(
        f"{API_BASE}/api/auth/register",
        json={"username": USERNAME, "email": f"{USERNAME}@example.com", "password": PASSWORD, "role": "user"},
    )
    resp = requests.post(f"{API_BASE}/api/auth/login", json={"username": USERNAME, "password": PASSWORD})
    resp.raise_for_status()
    return resp.json()["token"]


def send(token: str, session_id: str, message: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": USERNAME, "session_id": session_id, "message": message},
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    token = register_and_login()
    print(f"Demo user: {USERNAME}\n")

    session_a = str(uuid.uuid4())
    turn1_message = (
        "Hi, I'm planning a trip to Italy - I love art and my budget is "
        "around $2000. My email is anna.rossi@example.com, and just to make "
        "sure you got it, that's anna.rossi@example.com again."
    )
    print("--- Conversation 1, turn 1 (mentions Italy + repeats the same email twice) ---")
    print("User:", turn1_message)
    result1 = send(token, session_a, turn1_message)
    print("Agent:", result1["response"])
    print("pii_flagged:", result1["pii_flagged"], "\n")

    # Give update_session_summary's fire-and-forget background task a moment
    # to finish writing session_summaries before the next conversation reads it.
    time.sleep(4)

    session_b = str(uuid.uuid4())
    turn2_message = "Hey, what should I do next?"
    print("--- Conversation 2 (brand-new session_id), turn 1 ---")
    print("User:", turn2_message)
    result2 = send(token, session_b, turn2_message)
    print("Agent:", result2["response"])
    print(
        "\nExpected: the reply above should reference Italy/your earlier "
        "interest without you mentioning it again in this conversation."
    )
    print(f"\nCheck app.log for session={session_a} to see the redaction/dedup lines.")
    print(f"Check Langfuse for session={session_b}'s agent_turn span metadata for injected_memory_context.")


if __name__ == "__main__":
    main()
