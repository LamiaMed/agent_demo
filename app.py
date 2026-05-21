from functools import lru_cache
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="Agent Demo API")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to send to the agent.")
    thread_id: Optional[str] = Field(None, description="Optional thread ID for maintaining conversation context.")


class ChatResponse(BaseModel):
    reply: str


@lru_cache(maxsize=1)
def get_agent():
    from agent import agent

    return agent


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    try:

        result = get_agent().invoke({"messages": [payload.message]}, {"configurable": {"thread_id": payload.thread_id}})
        messages = result["messages"]
        reply = messages[-1].content if messages else ""
        return ChatResponse(reply=reply)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
