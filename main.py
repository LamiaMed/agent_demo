from dotenv import load_dotenv

load_dotenv()

from agent import agent


def main():
    messages = []
    print("Chat with the agent (type 'exit' or 'quit' to stop).")
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
        result = agent.invoke({"messages": messages})
        messages = result["messages"]
        print(f"Agent: {messages[-1].content}")


if __name__ == "__main__":
    main()
