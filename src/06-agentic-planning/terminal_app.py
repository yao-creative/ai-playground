from orchestrator import AgenticPlanningOrchestrator
from models import AgentRunResult


class TerminalChatApp:
    def __init__(self, chatbot: AgenticPlanningOrchestrator) -> None:
        self.chatbot = chatbot
        self.chat_history: list[tuple[str, str]] = []

    def run(self) -> None:
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

            result = self.chatbot.answer(user_text, self.chat_history)
            answer = result.final_answer.strip()
            if result.supported and result.cited_doc_ids:
                answer = f"{answer}\nSources: {', '.join(result.cited_doc_ids)}"

            print(f"AI: {answer}")
            self.chat_history.append(("User", user_text))
            self.chat_history.append(("Assistant", answer))

    @staticmethod
    def fallback_result() -> AgentRunResult:
        return AgentRunResult(
            final_answer="I do not have enough support in the docs to answer confidently.",
            cited_doc_ids=[],
            supported=False,
            steps=[],
        )
