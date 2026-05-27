import uuid
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

from langfuse_tracing import make_langfuse_handler, langfuse_request_trace, shutdown_langfuse


@lru_cache(maxsize=1)
def get_agent():
    from agent import agent

    return agent


def main():
    messages = []
    print("Chat with the agent (type 'exit' or 'quit' to stop).")

    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    langfuse_handler = make_langfuse_handler()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        messages.append({"role": "user", "content": user_input})

        try:
            invoke_config = dict(config)
            if langfuse_handler is not None:
                invoke_config["callbacks"] = [langfuse_handler]

            with langfuse_request_trace(
                name="chat-turn",
                input_data={"message": user_input},
                session_id=session_id,
                tags=["agent-demo", "cli"],
            ) as trace:
                result = get_agent().invoke({"messages": messages}, config=invoke_config)

            messages = result["messages"]
            print(f"Agent: {messages[-1].content}")
            if trace is not None:
                trace.update(output={"reply": messages[-1].content})

        except Exception as e:
            print(f"\nError while running the agent: {e}")
            print("You can retry or rephrase your request.\n")

    shutdown_langfuse()


if __name__ == "__main__":
    main()
