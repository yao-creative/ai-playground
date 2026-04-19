import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATHS = [
    REPO_ROOT / "ai-chat" / "01-chat-app-with-history.py",
    REPO_ROOT / "ai-chat" / "02-chat-app-with-stream.py",
    REPO_ROOT / "ai-chat" / "03-rag-chat" / "main.py",
]


class AIChatEntrypointTests(unittest.TestCase):
    def test_all_entrypoints_start_and_exit_cleanly(self) -> None:
        for script_path in SCRIPT_PATHS:
            with self.subTest(script=script_path.relative_to(REPO_ROOT)):
                completed = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=REPO_ROOT,
                    input="bye\n",
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertEqual(
                    completed.returncode,
                    0,
                    msg=(
                        f"{script_path} exited with {completed.returncode}\n"
                        f"stdout:\n{completed.stdout}\n"
                        f"stderr:\n{completed.stderr}"
                    ),
                )
                self.assertIn("AI: Hello! Type 'bye' to exit.", completed.stdout)
                self.assertIn("AI: Goodbye!", completed.stdout)
                self.assertEqual(completed.stderr, "")
