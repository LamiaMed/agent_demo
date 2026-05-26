from dotenv import load_dotenv
from langchain.agents import create_agent

from prompt import SYSTEM_PROMPT
from tools.clients import get_client, get_client_with_name, get_client_by_email
from tools.google_calendar import create_event 
from tools.retreiver import retrieve_context
# Importation de ton nouvel outil Gmail
from tools.gmail_client import send_confirmation_email 
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

agent = create_agent(
    model="openai:gpt-5.4-mini",
    #debug=True,
    # Ajout de 'send_confirmation_email' à la liste des outils accessibles par Sophie
    tools=[
        get_client, 
        get_client_with_name, 
        get_client_by_email, 
        retrieve_context, 
        create_event, 
        send_confirmation_email
    ],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
)