from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
import os
from typing import Iterator

from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler


def _is_configured() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


@lru_cache(maxsize=1)
def get_langfuse_client():
    if not _is_configured():
        return None
    return get_client()


def make_langfuse_handler():
    client = get_langfuse_client()
    if client is None:
        return None
    return CallbackHandler()


@contextmanager
def langfuse_request_trace(
    *,
    name: str,
    input_data: object,
    session_id: str,
    tags: list[str] | None = None,
) -> Iterator[object | None]:
    client = get_langfuse_client()
    if client is None:
        yield None
        return

    with client.start_as_current_observation(as_type="span", name=name) as span:
        span.update(input=input_data)
        with propagate_attributes(session_id=session_id, tags=tags or []):
            yield span


def shutdown_langfuse() -> None:
    client = get_langfuse_client()
    if client is None:
        return
    client.shutdown()
