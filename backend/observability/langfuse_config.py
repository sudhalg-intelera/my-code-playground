import os
from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Initialize Singleton Langfuse Client
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "pk-dummy"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY", "sk-dummy"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

def get_compiled_prompt(prompt_name: str, **kwargs) -> str:
    """
    Safely retrieves a prompt template from Langfuse or returns a dynamic fallback.
    """
    try:
        prompt_obj = langfuse.get_prompt(prompt_name)
        return prompt_obj.compile(**kwargs)
    except Exception as e:
        print(f"Notice: Could not fetch prompt '{prompt_name}' from Langfuse ({e}). Using live prompt generation.")

        # Fallback string generation
        city = kwargs.get("city", "the destination")
        return f"Generate dynamic live details for {city} based on user search parameters."
