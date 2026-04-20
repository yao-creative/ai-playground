import asyncio
from pathlib import Path
import sys

from openai import AsyncOpenAI

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.append(str(APP_DIR))

from config import Settings


settings = Settings.load()
async_client = AsyncOpenAI(api_key=settings.api_key)


def build_prompt(user_input, chat_history):
    transcript = [
        "You are a concise, helpful AI conversation partner for terminal chat practice."
    ]

    for speaker, message in chat_history:
        transcript.append(f"{speaker}: {message}")

    transcript.append(f"User: {user_input}")
    transcript.append("Assistant:")
    return "\n".join(transcript)


async def get_ai_response_stream(user_input, chat_history=None):
    """Yield streamed text chunks for a terminal chat response."""
    chat_history = chat_history or []
    prompt = build_prompt(user_input, chat_history)
    response = await async_client.responses.create(
        model=settings.chat_model,
        input=prompt,
        stream=True,
    )

    async for event in response:
        if event.type == "response.output_text.delta":
            yield event.delta


async def chat_app_with_stream():
    chat_history = []
    print("AI: Hello! Type 'bye' to exit.")

    while True:
        try:
            user_text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAI: Goodbye!")
            break

        if not user_text:
            continue

        if user_text.lower() in {"bye", "exit", "quit"}:
            print("AI: Goodbye!")
            break

        response_chunks = []
        print("AI: ", end="", flush=True)
        async for chunk in get_ai_response_stream(user_text, chat_history):
            response_chunks.append(chunk)
            print(chunk, end="", flush=True)
        print()

        chat_history.append(("User", user_text))
        chat_history.append(("Assistant", "".join(response_chunks).strip()))


if __name__ == "__main__":
    asyncio.run(chat_app_with_stream())
