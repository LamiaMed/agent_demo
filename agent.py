from dotenv import load_dotenv
from langchain.agents import create_agent

from prompt import SYSTEM_PROMPT
from tools.clients import get_client, get_client_with_name
from tools.retreiver import retrieve_context

load_dotenv()


agent = create_agent(
    model="openai:gpt-5.4-mini",
    #debug=True,
    tools=[get_client, get_client_with_name, retrieve_context],
    system_prompt=SYSTEM_PROMPT,
)
