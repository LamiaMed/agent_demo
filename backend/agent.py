from dotenv import load_dotenv
from langchain.agents import create_agent

from backend.prompt import SYSTEM_PROMPT
from backend.tools.clients import get_client, get_client_with_name, get_client_by_email
from backend.tools.gmail_client import send_confirmation_email
from backend.tools.google_calendar import create_event
from backend.tools.retreiver import retrieve_context
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

agent = create_agent(
    model="openai:gpt-5.4-mini",
    tools=[
        get_client,
        get_client_with_name,
        get_client_by_email,
        retrieve_context,
        create_event,
        send_confirmation_email,
    ],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
)
