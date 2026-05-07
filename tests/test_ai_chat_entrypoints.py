import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATHS = [
    REPO_ROOT / "src" / "01-chat-app-with-history.py",
    REPO_ROOT / "src" / "02-chat-app-with-stream.py",
    REPO_ROOT / "src" / "03-rag-chat" / "main.py",
]


@pytest.mark.parametrize("script_path", SCRIPT_PATHS, ids=lambda path: str(path.relative_to(REPO_ROOT)))
def test_all_entrypoints_start_and_exit_cleanly(script_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=REPO_ROOT,
        input="bye\n",
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    assert completed.returncode == 0, (
        f"{script_path} exited with {completed.returncode}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert "AI: Hello! Type 'bye' to exit." in completed.stdout
    assert "AI: Goodbye!" in completed.stdout
    assert completed.stderr == ""


def test_05_agentic_rag_entrypoint_starts_and_exits_cleanly() -> None:
    script_path = REPO_ROOT / "src" / "05-agentic-rag" / "main.py"
    env = dict(os.environ)
    env.setdefault("OPENAI_API_KEY", "test-key")
    env.setdefault("OPENAI_MODEL", "gpt-5-mini")

    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=REPO_ROOT,
        input="bye\n",
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
        env=env,
    )

    assert completed.returncode == 0, (
        f"{script_path} exited with {completed.returncode}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert "AI: Hello! Type 'bye' to exit." in completed.stdout
    assert "AI: Goodbye!" in completed.stdout
    assert completed.stderr == ""


def test_06_agentic_planning_entrypoint_starts_and_exits_cleanly() -> None:
    script_path = REPO_ROOT / "src" / "06-agentic-planning" / "main.py"
    env = dict(os.environ)
    env.setdefault("OPENAI_API_KEY", "test-key")
    env.setdefault("OPENAI_MODEL", "gpt-5-mini")

    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=REPO_ROOT,
        input="bye\n",
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
        env=env,
    )

    assert completed.returncode == 0, (
        f"{script_path} exited with {completed.returncode}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert "AI: Hello! Type 'bye' to exit." in completed.stdout
    assert "AI: Goodbye!" in completed.stdout
    assert completed.stderr == ""
