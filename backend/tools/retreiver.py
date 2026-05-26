import os
import shutil
import tempfile
import re
from functools import lru_cache
from pathlib import Path

from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from openai import APIConnectionError

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


def _get_persist_directory() -> Path:
    if os.environ.get("VERCEL"):
        persist_dir = Path(tempfile.gettempdir()) / "chroma_langchain_db"
        source_dir = BASE_DIR / "chroma_langchain_db"
        if source_dir.exists() and not persist_dir.exists():
            shutil.copytree(source_dir, persist_dir)
        return persist_dir
    return BASE_DIR / "chroma_langchain_db"


@lru_cache(maxsize=1)
def _load_local_documents() -> list[dict[str, str]]:
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader  # type: ignore[no-redef]

    documents: list[dict[str, str]] = []
    for pdf_path in sorted(DATA_DIR.glob("*.pdf")):
        reader = PdfReader(str(pdf_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        documents.append({"source": str(pdf_path), "content": text})
    return documents


def _local_similarity_search(query: str, k: int = 3) -> list[dict[str, str]]:
    query_terms = {term for term in re.findall(r"\w+", query.lower()) if len(term) > 2}
    scored_documents: list[tuple[int, dict[str, str]]] = []

    for document in _load_local_documents():
        content = document["content"].lower()
        score = sum(content.count(term) for term in query_terms)
        if score > 0:
            scored_documents.append((score, document))

    scored_documents.sort(key=lambda item: item[0], reverse=True)
    return [document for _, document in scored_documents[:k]]


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
    try:
        vector_store = _get_vector_store()
        retrieved_docs = vector_store.similarity_search(query, k=3)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nContent: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs
    except APIConnectionError:
        retrieved_docs = _local_similarity_search(query, k=3)
        serialized = "\n\n".join(
            (
                f"Source: {doc['source']}\nContent: {doc['content']}"
            )
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs
