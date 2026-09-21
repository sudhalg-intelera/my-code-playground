"""Model shared by every agent in this package - one place to change it for all of them."""

from google.adk.models.lite_llm import LiteLlm

MODEL = LiteLlm(model="openai/gpt-4o-mini")
