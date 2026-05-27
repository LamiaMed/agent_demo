from functools import lru_cache
import logging
import time
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from langfuse_tracing import make_langfuse_handler, langfuse_request_trace, shutdown_langfuse
from monitor import get_dashboard, log_request

load_dotenv()

app = FastAPI(title="Agent Demo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    session_id = payload.thread_id or str(uuid.uuid4())

    try:
        invoke_config = {"configurable": {"thread_id": session_id}}
        langfuse_handler = make_langfuse_handler()
        if langfuse_handler is not None:
            invoke_config["callbacks"] = [langfuse_handler]

        with langfuse_request_trace(
            name="chat-request",
            input_data={"message": payload.message},
            session_id=session_id,
            tags=["agent-demo", "api"],
        ) as trace:
            result = get_agent().invoke({"messages": [payload.message]}, config=invoke_config)
            messages = result["messages"]
            reply = messages[-1].content if messages else ""

            if messages:
                usage_metadata = getattr(messages[-1], "usage_metadata", None)
                if usage_metadata is None and isinstance(messages[-1], dict):
                    usage_metadata = messages[-1].get("usage_metadata")
                if usage_metadata:
                    tokens_in = usage_metadata.get("input_tokens", 0)
                    tokens_out = usage_metadata.get("output_tokens", 0)

            if trace is not None:
                trace.update(output={"reply": reply})

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


@app.on_event("shutdown")
def shutdown_tracing() -> None:
    shutdown_langfuse()
