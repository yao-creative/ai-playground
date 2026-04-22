import argparse
import importlib.util
from pathlib import Path
import sys

from openai import OpenAI

APP_DIR = Path(__file__).resolve().parent.parent
MODULE_DIR = Path(__file__).resolve().parent
RAG_DIR = APP_DIR / "03-rag-chat"

if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))
if str(APP_DIR) not in sys.path:
    sys.path.insert(1, str(APP_DIR))
if str(RAG_DIR) not in sys.path:
    sys.path.insert(2, str(RAG_DIR))

from agent import AgenticRAG
from config import Settings
from terminal_app import TerminalChatApp


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rag_data = _load_module("rag03_data", RAG_DIR / "data.py")
rag_retrieval = _load_module("rag03_retrieval", RAG_DIR / "retrieval.py")

build_documents = rag_data.build_documents
BM25RetrievalStrategy = rag_retrieval.BM25RetrievalStrategy
KeywordRetrievalStrategy = rag_retrieval.KeywordRetrievalStrategy
TiktokenTokenizer = rag_retrieval.TiktokenTokenizer


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
