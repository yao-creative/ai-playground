import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    api_key: str
    chat_model: str
    embedding_model: str
    reranker_model: str

    @classmethod
    def load(cls) -> "Settings":
        env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(env_path)

        api_key = os.getenv("OPENAI_API_KEY")
        chat_model = os.getenv("OPENAI_MODEL")
        embedding_model = os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        reranker_model = os.getenv(
            "RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L6-v2"
        )

        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")

        if not chat_model:
            raise ValueError("OPENAI_MODEL is not set. Add it to your .env file.")

        return cls(
            api_key=api_key,
            chat_model=chat_model,
            embedding_model=embedding_model,
            reranker_model=reranker_model,
        )


def load_settings() -> tuple[str, str]:
    settings = Settings.load()
    return settings.api_key, settings.chat_model
