import os
from pathlib import Path

from dotenv import load_dotenv

def load_settings():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")

    if not model:
        raise ValueError("OPENAI_MODEL is not set. Add it to your .env file.")

    return api_key, model