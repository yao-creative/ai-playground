import os
from pathlib import Path

import pytest
from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_TIMEOUT_SECONDS = 180

load_dotenv(REPO_ROOT / ".env")


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def live_timeout_seconds() -> int:
    return LIVE_TIMEOUT_SECONDS


@pytest.fixture(scope="session")
def live_test_env() -> dict[str, str]:
    if os.getenv("RUN_LIVE_TESTS") != "1":
        pytest.skip("set RUN_LIVE_TESTS=1 to run live happy-path tests")
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY must be set to run live happy-path tests")
    return os.environ.copy()
