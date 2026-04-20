import re
import subprocess
import sys
from pathlib import Path

import pytest


LIVE_PROMPT = "In one short sentence, what does the remote work policy say?"
LIVE_INPUT = f"{LIVE_PROMPT}\nbye\n"

LIVE_CASES = [
    (
        "history",
        lambda repo_root: [
            sys.executable,
            str(repo_root / "ai-chat" / "01-chat-app-with-history.py"),
        ],
    ),
    (
        "stream",
        lambda repo_root: [
            sys.executable,
            str(repo_root / "ai-chat" / "02-chat-app-with-stream.py"),
        ],
    ),
    (
        "rag-keyword",
        lambda repo_root: [
            sys.executable,
            str(repo_root / "ai-chat" / "03-rag-chat" / "main.py"),
            "--strategy",
            "keyword",
        ],
    ),
    (
        "rag-embedding",
        lambda repo_root: [
            sys.executable,
            str(repo_root / "ai-chat" / "03-rag-chat" / "main.py"),
            "--strategy",
            "embedding",
        ],
    ),
]


def _extract_ai_messages(stdout: str) -> list[str]:
    segments = re.findall(r"AI:\s*(.*?)(?=You:\s|AI:\s|$)", stdout, flags=re.DOTALL)
    messages = [segment.strip() for segment in segments]
    return [
        message
        for message in messages
        if message
        and message != "Hello! Type 'bye' to exit."
        and message != "Goodbye!"
    ]


@pytest.mark.parametrize("case_name,command_builder", LIVE_CASES, ids=[case[0] for case in LIVE_CASES])
def test_live_happy_paths_return_a_non_empty_response(
    case_name: str,
    command_builder,
    repo_root: Path,
    live_test_env: dict[str, str],
    live_timeout_seconds: int,
) -> None:
    completed = subprocess.run(
        command_builder(repo_root),
        cwd=repo_root,
        input=LIVE_INPUT,
        capture_output=True,
        text=True,
        check=False,
        timeout=live_timeout_seconds,
        env=live_test_env,
    )

    assert completed.returncode == 0, (
        f"{case_name} exited with {completed.returncode}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert "AI: Hello! Type 'bye' to exit." in completed.stdout
    assert "AI: Goodbye!" in completed.stdout

    ai_messages = _extract_ai_messages(completed.stdout)
    assert ai_messages, (
        f"{case_name} did not emit a non-empty assistant response\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
