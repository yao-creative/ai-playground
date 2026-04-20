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
