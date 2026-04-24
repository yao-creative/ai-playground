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

from agent import AgenticRAG
from config import Settings
from data import build_documents
from retrieval import BM25RetrievalStrategy, KeywordRetrievalStrategy, TiktokenTokenizer
from terminal_app import TerminalChatApp


def build_app(strategy: str = "bm25", max_steps: int = 4) -> TerminalChatApp:
    settings = Settings.load()
    client = OpenAI(api_key=settings.api_key)
    documents = build_documents()
    tokenizer = TiktokenTokenizer(settings.chat_model)

    if strategy == "keyword":
        retrieval_strategy = KeywordRetrievalStrategy(tokenizer)
    else:
        retrieval_strategy = BM25RetrievalStrategy(tokenizer)
        retrieval_strategy.build_index(documents)

    chatbot = AgenticRAG(
        client=client,
        model=settings.chat_model,
        documents=documents,
        retrieval_strategy=retrieval_strategy,
        max_steps=max_steps,
    )
    return TerminalChatApp(chatbot)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic RAG: terminal conversation app")
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
        help="Maximum number of agent steps per user turn (default: 4).",
    )
    args = parser.parse_args()
    build_app(strategy=args.strategy, max_steps=max(1, args.max_steps)).run()
