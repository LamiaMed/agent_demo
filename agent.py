from dotenv import load_dotenv
from langchain.agents import create_agent

from prompt import SYSTEM_PROMPT
from tools.clients import get_client, get_client_with_name

load_dotenv()


agent = create_agent(
    model="openai:gpt-5.4-mini",
    tools=[get_client, get_client_with_name],
    system_prompt=SYSTEM_PROMPT,
)
