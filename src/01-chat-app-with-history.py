from openai import OpenAI
from pathlib import Path
import sys

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.append(str(APP_DIR))

from config import Settings


settings = Settings.load()
client = OpenAI(api_key=settings.api_key)


def build_prompt(user_input, chat_history):
    transcript = [
        "You are a concise, helpful AI conversation partner for terminal chat practice."
    ]

    for speaker, message in chat_history:
        transcript.append(f"{speaker}: {message}")

    transcript.append(f"User: {user_input}")
    transcript.append("Assistant:")
    return "\n".join(transcript)


def get_ai_response(user_input, chat_history=None):
    """Generate an AI response using the OpenAI API."""
    chat_history = chat_history or []
    prompt = build_prompt(user_input, chat_history)
    response = client.responses.create(
        model=settings.chat_model,
        input=prompt,
    )
    return response.output_text.strip()


def start_chat():
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

        response = get_ai_response(user_text, chat_history)
        chat_history.append(("User", user_text))
        chat_history.append(("Assistant", response))
        print(f"AI: {response}")


if __name__ == "__main__":
    start_chat()
