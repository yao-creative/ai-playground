import json

from agent import AgenticRAG
from models import AgentEvent, AgentRunResult


class TerminalChatApp:
    def __init__(self, chatbot: AgenticRAG) -> None:
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

            result = self._stream_agent_turn(user_text)
            answer = result.final_answer.strip()
            if result.supported and result.cited_doc_ids:
                answer = f"{answer}\nSources: {', '.join(result.cited_doc_ids)}"

            print(f"AI: {answer}")
            self.chat_history.append(("User", user_text))
            self.chat_history.append(("Assistant", answer))

    def _stream_agent_turn(self, user_text: str) -> AgentRunResult:
        result: AgentRunResult | None = None
        printed_stream_line = False

        for event in self.chatbot.answer_stream(user_text, self.chat_history):
            self._render_event(event, printed_stream_line)
            if event.event_type == "model_delta":
                printed_stream_line = True
            if event.event_type in {"action_selected", "observation", "step_error"} and printed_stream_line:
                print()
                printed_stream_line = False
            if event.event_type == "final_result":
                result = event.run_result

        print()
        if result is None:
            return AgentRunResult(
                final_answer="I could not complete a grounded answer from the docs.",
                cited_doc_ids=[],
                supported=False,
                steps=[],
            )
        return result

    def _render_event(self, event: AgentEvent, printed_stream_line: bool) -> None:
        if event.event_type == "step_started":
            print(f"AI: [Step {event.step_index}]")
            return

        if event.event_type == "model_delta":
            print(event.delta or "", end="", flush=True)
            return

        if event.event_type == "action_selected" and event.tool_call is not None:
            if printed_stream_line:
                print()
            print(f"AI: Action -> {event.tool_call.tool_name} {json.dumps(event.tool_call.arguments)}")
            return

        if event.event_type == "observation" and event.tool_result is not None:
            if printed_stream_line:
                print()
            observation = {
                "tool_name": event.tool_result.tool_name,
                "payload": event.tool_result.payload,
                "error": event.tool_result.error,
            }
            print(f"AI: Observation -> {json.dumps(observation, ensure_ascii=True)}")
            return

        if event.event_type == "step_error":
            if printed_stream_line:
                print()
            print(f"AI: Step warning -> {event.message or 'Unknown step warning.'}")
