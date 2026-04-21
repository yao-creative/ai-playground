import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    model: str
    api_key: str | None
    retrieval_limit: int
    live_model_enabled: bool
    runs_dir: Path


def load_settings(*, live_model_enabled: bool = False, runs_dir: Path | None = None) -> Settings:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_path)

    configured_live = os.getenv("RUN_LIVE_EVALS") == "1"
    live_mode = live_model_enabled or configured_live
    default_runs_dir = Path(__file__).resolve().parents[2] / ".eval-runs" / "04-evals"

    return Settings(
        model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        retrieval_limit=int(os.getenv("EVAL_RETRIEVAL_LIMIT", "3")),
        live_model_enabled=live_mode,
        runs_dir=runs_dir or default_runs_dir,
    )
