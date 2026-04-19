import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str

    @classmethod
    def load(cls) -> "Settings":
        env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(env_path)

        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")

        if not model:
            raise ValueError("OPENAI_MODEL is not set. Add it to your .env file.")

        return cls(api_key=api_key, model=model)


def load_settings() -> tuple[str, str]:
    settings = Settings.load()
    return settings.api_key, settings.model
