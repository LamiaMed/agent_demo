from functools import lru_cache
import logging
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import APIConnectionError, APITimeoutError, OpenAIError

from monitor import get_dashboard, log_request

load_dotenv()

app = FastAPI(title="Agent Demo API")
logger = logging.getLogger(__name__)
chat_request_count = 0


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
    global chat_request_count
    chat_request_count += 1
    start_time = time.perf_counter()
    error = None
    tokens_in = 0
    tokens_out = 0
    try:
        result = get_agent().invoke({"messages": [payload.message]}, {"configurable": {"thread_id": payload.thread_id}})
        messages = result["messages"]
        reply = messages[-1].content if messages else ""
        if messages:
            usage_metadata = getattr(messages[-1], "usage_metadata", None)
            if usage_metadata is None and isinstance(messages[-1], dict):
                usage_metadata = messages[-1].get("usage_metadata")
            if usage_metadata:
                tokens_in = usage_metadata.get("input_tokens", 0)
                tokens_out = usage_metadata.get("output_tokens", 0)
        return ChatResponse(reply=reply)
    except Exception as exc:
        error = str(exc)
        raise HTTPException(status_code=500, detail=error) from exc
    finally:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        log_request(payload.message, elapsed_ms, tokens_in, tokens_out, error=error)
        logger.info("chat response time: %.2f ms", elapsed_ms)

@app.get("/metrics")
def dashboard():
    metrics = get_dashboard()
    metrics["nbr_requetes_chat"] = chat_request_count
    return metrics

# Résultat :
# {
# "total_requetes": 142,
# "latence_moy_ms": 2340,
# "taux_erreur": "3.5%",
# "cout_total": "1.42 $"
# }
