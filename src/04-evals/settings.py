import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    model: str
    api_key: str | None
    retrieval_limit: int
    max_concurrency: int
    runs_dir: Path


def load_settings(*, max_concurrency: int | None = None, runs_dir: Path | None = None) -> Settings:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_path)
    default_runs_dir = Path(__file__).resolve().parents[2] / ".eval-runs" / "04-evals"
    configured_max_concurrency = max_concurrency or int(os.getenv("EVAL_MAX_CONCURRENCY", "4"))

    if configured_max_concurrency < 1:
        raise ValueError("EVAL_MAX_CONCURRENCY must be at least 1.")

    return Settings(
        model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        retrieval_limit=int(os.getenv("EVAL_RETRIEVAL_LIMIT", "3")),
        max_concurrency=configured_max_concurrency,
        runs_dir=runs_dir or default_runs_dir,
    )
