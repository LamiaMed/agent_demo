import uuid
from dotenv import load_dotenv

load_dotenv()

from backend.agent import agent


def main():
    messages = []
    print("Chat with the agent (type 'exit' or 'quit' to stop).")
    
    # Configuration avec un identifiant unique pour toute la session de chat
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
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
        
        # Bloc try/except pour intercepter les erreurs de l'agent
        try:
            result = agent.invoke({"messages": messages}, config=config)
            messages = result["messages"]
            print(f"Agent: {messages[-1].content}")
            
        except Exception as e:
            print(f"\n❌ Erreur lors de l'exécution de l'agent : {e}")
            # En cas d'erreur, on retire le dernier message utilisateur 
            # pour éviter de polluer l'historique lors de la prochaine tentative
            # messages.pop()
            print("Vous pouvez réessayer ou formuler votre demande différemment.\n")


if __name__ == "__main__":
    main()
