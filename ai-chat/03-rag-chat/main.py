import asyncio
from pathlib import Path
import sys

from openai import AsyncOpenAI

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.append(str(APP_DIR))

MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.append(str(MODULE_DIR))

from chatbot import RAGChatbot
from config import Settings
from data import build_documents
from retrieval import KeywordRetrievalStrategy, TiktokenTokenizer
from terminal_app import TerminalChatApp


def build_app() -> TerminalChatApp:
    settings = Settings.load()
    client = AsyncOpenAI(api_key=settings.api_key)
    tokenizer = TiktokenTokenizer(settings.model)
    retrieval_strategy = KeywordRetrievalStrategy(tokenizer)
    chatbot = RAGChatbot(
        client=client,
        model=settings.model,
        documents=build_documents(),
        retrieval_strategy=retrieval_strategy,
    )
    return TerminalChatApp(chatbot)


if __name__ == "__main__":
    asyncio.run(build_app().run())
