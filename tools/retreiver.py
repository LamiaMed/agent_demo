import os
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

BASE_DIR = Path(__file__).resolve().parent.parent


def _get_persist_directory() -> Path:
    if os.environ.get("VERCEL"):
        persist_dir = Path(tempfile.gettempdir()) / "chroma_langchain_db"
        source_dir = BASE_DIR / "chroma_langchain_db"
        if source_dir.exists() and not persist_dir.exists():
            shutil.copytree(source_dir, persist_dir)
        return persist_dir
    return BASE_DIR / "chroma_langchain_db"


@lru_cache(maxsize=1)
def _get_vector_store() -> Chroma:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing from the environment")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        collection_name="example_collection",
        embedding_function=embeddings,
        persist_directory=str(_get_persist_directory()),
    )


@tool
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    vector_store = _get_vector_store()
    retrieved_docs = vector_store.similarity_search(query, k=3)
    print("************************* ")
    print(retrieved_docs)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs
