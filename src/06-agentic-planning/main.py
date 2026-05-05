import argparse
from pathlib import Path
import sys

from openai import OpenAI

APP_DIR = Path(__file__).resolve().parent.parent
MODULE_DIR = Path(__file__).resolve().parent

if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))
if str(APP_DIR) not in sys.path:
    sys.path.insert(1, str(APP_DIR))

from config import Settings
from data import build_documents
from models import RevisionConfig
from orchestrator import AgenticPlanningOrchestrator
from retrieval import BM25RetrievalStrategy, KeywordRetrievalStrategy, TiktokenTokenizer
from terminal_app import TerminalChatApp



def build_app(strategy: str = "bm25", max_steps: int = 4, max_redrafts: int = 1) -> TerminalChatApp:
    settings = Settings.load()
    client = OpenAI(api_key=settings.api_key)
    documents = build_documents()
    tokenizer = TiktokenTokenizer(settings.chat_model)

    if strategy == "keyword":
        retrieval_strategy = KeywordRetrievalStrategy(tokenizer)
    else:
        retrieval_strategy = BM25RetrievalStrategy(tokenizer)
        retrieval_strategy.build_index(documents)

    chatbot = AgenticPlanningOrchestrator(
        client=client,
        model=settings.chat_model,
        documents=documents,
        retrieval_strategy=retrieval_strategy,
        max_steps=max(1, max_steps),
        revision_config=RevisionConfig(max_redrafts=max(0, min(max_redrafts, 1))),
    )
    return TerminalChatApp(chatbot)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic Planning: terminal conversation app")
    parser.add_argument(
        "--strategy",
        choices=["bm25", "keyword"],
        default="bm25",
        help="Retrieval strategy to use: 'bm25' or 'keyword' (default: bm25).",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=4,
        help="Maximum evidence-collection steps per user turn (default: 4).",
    )
    parser.add_argument(
        "--max-redrafts",
        type=int,
        default=1,
        help="Maximum redraft passes (0 or 1 for MVP).",
    )
    args = parser.parse_args()
    build_app(strategy=args.strategy, max_steps=args.max_steps, max_redrafts=args.max_redrafts).run()
