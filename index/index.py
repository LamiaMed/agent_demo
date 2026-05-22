import os
import shutil
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is missing from .env")

BASE_DIR = Path(__file__).resolve().parent.parent


def _get_persist_directory() -> Path:
    if os.environ.get("VERCEL"):
        persist_dir = Path(tempfile.gettempdir()) / "chroma_langchain_db"
        source_dir = BASE_DIR / "chroma_langchain_db"
        if source_dir.exists() and not persist_dir.exists():
            shutil.copytree(source_dir, persist_dir)
        return persist_dir
    return BASE_DIR / "chroma_langchain_db"


embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory=str(_get_persist_directory()),  # Where to save data locally, remove if not necessary
)

def load_pdf_file(pdf_path: Path) -> Document:
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError as exc:
            raise ImportError(
                "Install `pypdf` or `PyPDF2` to read local PDF files."
            ) from exc

    reader = PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return Document(page_content=text, metadata={"source": str(pdf_path)})


def load_pdfs_from_data(data_dir: str = "data") -> list[Document]:
    pdf_paths = sorted((BASE_DIR / data_dir).glob("*.pdf"))
    return [load_pdf_file(pdf_path) for pdf_path in pdf_paths]


if __name__ == "__main__":
    # lire le pdf
    docs = load_pdfs_from_data("data")

    assert len(docs) >= 1
    print(f"Loaded {len(docs)} PDF file(s) from data/")
    print(f"Total characters: {sum(len(doc.page_content) for doc in docs)}")

    # chunk
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # chunk size (characters)
        chunk_overlap=200,  # chunk overlap (characters)
        add_start_index=True,  # track index in original document
    )
    all_splits = text_splitter.split_documents(docs)

    print(f"Split blog post into {len(all_splits)} sub-documents.")

    # index dans chromadb
    document_ids = vector_store.add_documents(documents=all_splits)

    print(document_ids[:3])
