from chatbot import RAGChatbot


class TerminalChatApp:
    def __init__(self, chatbot: RAGChatbot) -> None:
        self.chatbot = chatbot
        self.chat_history: list[tuple[str, str]] = []

    async def run(self) -> None:
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

            response_chunks: list[str] = []
            print("AI: ", end="", flush=True)
            async for chunk in self.chatbot.stream_chat_response(user_text, self.chat_history):
                response_chunks.append(chunk)
                print(chunk, end="", flush=True)
            print()

            self.chat_history.append(("User", user_text))
            self.chat_history.append(("Assistant", "".join(response_chunks).strip()))
