import os
import uuid
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from src.langgraph_nodes import (
    node_extract,
    node_split,
    node_index,
    node_retrieve,
    STORE,
)
from src.settings import DATA_DIR, TOP_K, LLM_MODEL
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
from langchain_chroma import Chroma
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str


load_dotenv()

CHAT_HISTORY = []

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

DOCS_DIR = Path(DATA_DIR) / "uploads"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Filename mapping file
NAMES_FILE = DOCS_DIR / "filenames.json"

def load_names() -> dict:
    if NAMES_FILE.exists():
        with open(NAMES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_names(names: dict):
    with open(NAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(names, f, ensure_ascii=False)

llm = init_chat_model(
    LLM_MODEL,
    model_provider="ollama",
    temperature=0.0,
)
# llm = init_chat_model(
#     model = 'gpt-4o-mini',
#     model_provider="azure_openai",
#     temperature=0.0,
#     api_version="2024-12-01-preview",
#     api_key=os.getenv("AZURE_API_KEY"),
# )
ollama_emb = OllamaEmbeddings(
    model=os.getenv("EMBED_MODEL", "mxbai-embed-large"),
)
STORE = Chroma(
    collection_name="data_rag",
    embedding_function=ollama_emb,
    persist_directory="chroma_db",
)

# Basic prompt
prompt = ChatPromptTemplate.from_template("""                                
Eres un asistente de inteligencia artificial que ayuda a los usuarios a encontrar información en una colección de documentos.

REGLAS ESTRICTAS:
1. Responde SOLO con información que encuentres EXPLÍCITAMENTE en el contexto proporcionado.
2. SIEMPRE cita el número exacto del capítulo, cláusula o sección del documento de donde extraes la información.
3. NUNCA inventes, supongas o agregues información que no esté en los documentos.
4. Si la información solicitada NO se encuentra en los documentos, responde EXACTAMENTE: "No tengo información sobre eso en los documentos disponibles."
5. Si mencionas una cláusula o capítulo, debe aparecer textbatim (copiado textualmente) del documento.
6. No mezcles información de diferentes cláusulas o capítulos.
7. Identifica claramente el nombre de la norma o documento de referencia.

La consulta es la siguiente:                    
{input}

El historial de chat es el siguiente:
{chat_history}

CONTEXTO DE LOS DOCUMENTOS:
Usa ÚNICAMENTE la información del contexto para responder. Si el contexto no contiene la respuesta, di que no la tienes.

Responde de manera concisa, precisa y con referencia exacta al documento fuente.
""")


# creating the retriever tool
@tool
def retrieve(query: str):
    """Retrieve information related to a query. Only when the users intent requires information from the documents."""
    retrieved_docs = STORE.similarity_search(query, k=6)

    serialized = ""

    for doc in retrieved_docs:
        serialized += f"Contexto: {doc.page_content}"
    print("Contexto: ", serialized)
    return serialized


# combining all tools
tools = [retrieve]

# initiating the agent
agent = create_agent(model=llm, tools=tools)

chain = prompt | agent


@app.post("/upload")
async def upload(file: UploadFile = File(...), title: str | None = Form(None)):
    contents = await file.read()
    ext = Path(file.filename).suffix
    doc_id = str(uuid.uuid4())
    save_path = DOCS_DIR / f"{doc_id}{ext}"
    with open(save_path, "wb") as f:
        f.write(contents)
    
    # Save original filename mapping
    names = load_names()
    names[doc_id] = file.filename
    save_names(names)
    
    return {"status": "ok", "doc_id": doc_id, "filename": file.filename}


@app.post("/index/{doc_id}")
async def index_document(doc_id: str, filename: str | None = Form(None)):
    # find file by doc_id
    found = None
    for p in DOCS_DIR.iterdir():
        if p.stem == doc_id:
            found = p
            break
    if not found:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete existing chunks if document is already indexed (re-indexing)
    try:
        existing = STORE.get(where={"doc_id": doc_id})
        if existing.get("ids"):
            STORE.delete(ids=existing["ids"])
    except:
        pass

    contents = found.read_bytes()
    text = node_extract(contents, found.name)
    chunks = node_split(text)
    node_index(chunks, doc_id, found.name)
    return JSONResponse(
        content={"status": "ok", "indexed_chunks": len(chunks)}, status_code=200
    )


@app.get("/documents")
def list_documents():
    names = load_names()
    docs_map = [f for f in os.listdir("data/uploads") if f != "filenames.json"]
    out = []
    for doc_id in docs_map:
        stem = Path(doc_id).stem
        original_name = names.get(stem, doc_id)
        out.append({"doc_id": stem, "filename": original_name, "type": Path(doc_id).suffix})
    return out


@app.get("/documents/{doc_id}/indexed")
async def check_indexed(doc_id: str):
    try:
        results = STORE.get(where={"doc_id": doc_id})
        return {
            "indexed": len(results.get("ids", [])) > 0,
            "chunks": len(results.get("ids", [])),
        }
    except:
        return {"indexed": False, "chunks": 0}


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    deleted = await STORE.adelete(doc_id)
    # Find file by doc_id stem (UUID without extension)
    for p in DOCS_DIR.iterdir():
        if p.stem == doc_id:
            os.remove(p)
            break
    
    # Remove filename mapping
    names = load_names()
    if doc_id in names:
        del names[doc_id]
        save_names(names)
    
    return {"status": "ok", "deleted_chunks": deleted}


@app.post("/query")
async def query_chat(request: QueryRequest):
    # retrieve top-k

    result = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=prompt.format_messages(
                        input=request.query,
                        chat_history="\n".join(
                            [
                                f"User: {msg['user']}\nAI: {msg['ai']}"
                                for msg in CHAT_HISTORY
                            ]
                        ),
                    )[0].content
                )
            ]
        }
    )
    print(result.get("messages", [])[-1].content)
    return {
        "answer": result.get("messages", [])[-1].content,
        "contexts": result.get("messages", [])[-1].response_metadata,
    }
