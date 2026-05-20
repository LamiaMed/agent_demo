from langchain_chroma import Chroma
from langchain.tools import tool
from langchain_openai import OpenAIEmbeddings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory=str(BASE_DIR / "chroma_langchain_db"),
)


@tool
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vector_store.similarity_search(query, k=3)
    print("************************* ")
    print(retrieved_docs)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs
