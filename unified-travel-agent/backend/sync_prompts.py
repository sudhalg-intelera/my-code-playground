"""
Script-level trigger to migrate/sync all Langfuse-managed prompts into Postgres.

Run manually:
    python sync_prompts.py

The same sync also happens automatically via the Langfuse webhook at
POST /api/webhooks/langfuse/prompt-sync (see main.py) whenever a prompt is
edited in the Langfuse UI - this script is the on-demand / CI equivalent.
"""

from observability.langfuse_config import langfuse
from database import upsert_prompt


def sync_all_prompts() -> int:
    prompt_meta_list = langfuse.api.prompts.list(limit=100)
    synced = 0

    for meta in prompt_meta_list.data:
        prompt = langfuse.get_prompt(meta.name)
        upsert_prompt(name=prompt.name, template=prompt.prompt, version=prompt.version)
        synced += 1
        print(f"synced '{prompt.name}' (v{prompt.version})")

    return synced


if __name__ == "__main__":
    count = sync_all_prompts()
    print(f"\nDone. {count} prompt(s) synced from Langfuse into Postgres.")
