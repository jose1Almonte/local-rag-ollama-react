from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .extractor import extract_text_from_pdf_bytes, extract_text_from_docx_bytes, extract_text_from_txt_bytes
from pathlib import Path
from .settings import CHUNK_SIZE, CHUNK_OVERLAP
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()


ollama_emb = OllamaEmbeddings(
    model=os.getenv("EMBED_MODEL", "mxbai-embed-large"),
)
STORE = Chroma(
    collection_name="data_rag",
    embedding_function=ollama_emb,
    persist_directory='chroma_db', 
)

def node_extract(file_bytes: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        text = extract_text_from_pdf_bytes(file_bytes)
    elif ext == ".docx":
        text = extract_text_from_docx_bytes(file_bytes)
    else:
        text = extract_text_from_txt_bytes(file_bytes)
    return text

def node_split(text: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_text(text)
    return chunks

def node_index(chunks: list[str], doc_id: str, source_filename: str):
    docs = [Document(page_content=c, metadata={"id": f"{doc_id}::{i}", "doc_id": doc_id, "chunk_index": i, "source_filename": source_filename}) for i, c in enumerate(chunks)]
    ids = [f"{doc_id}::{i}" for i in range(len(chunks))]
    STORE.add_documents(docs, ids=ids)
    return {"indexed": len(chunks)}

def node_retrieve(query: str, top_k: int = 6):
    return STORE.query(query, top_k=top_k)
