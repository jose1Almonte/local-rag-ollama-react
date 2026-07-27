import os
import uuid
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from src.langgraph_nodes import (
    node_extract,
    node_split,
    node_index,
    STORE,
)
from src.settings import DATA_DIR, LLM_MODEL
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langchain_chroma import Chroma
from dotenv import load_dotenv
from pydantic import BaseModel

# Nuestros auditores internos acaban de detectar que el departamento de producción está utilizando planos de fabricación de una versión del año pasado porque nadie les notificó que los diseños habían cambiado. Además, no existe ningún registro que demuestre quién aprobó la última versión de esos planos. Técnicamente, ¿qué requisitos específicos de nuestro sistema de gestión estamos incumpliendo según la norma? Dime el nombre de la norma ISO tambien


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
prompt = ChatPromptTemplate.from_template(
    """Eres un experto auditor en normas ISO. Responde SOLO usando el contexto proporcionado.

Si el contexto no contiene la información suficiente, di: "No tengo información en los documentos para responder con precisión."

CONTEXTO:
{context}

PREGUNTA: {input}

REGLAS DE RESPUESTA:
1. Cita siempre el nombre exacto del documento (ej: ISO 9001:2015) y la cláusula/subcláusula específica (ej: 7.5.3.1 a), no solo el número de cláusula general.
2. Distingue entre aspectos diferentes de una misma cláusula: disponibilidad vs protección vs control de cambios vs conservación de registros.
3. En ISO 9001:2015, la información documentada se divide en: 7.5.3.1 (disponibilidad e idoneidad — que la info esté disponible y sea adecuada donde y cuando se necesite) y 7.5.3.2 (control de cambios, distribución, conservación de registros — que se actualice, distribuya y mantenga evidencia). No mezcles ambas subcláusulas.
4. Si el problema involucra planos obsoletos, busca cláusulas sobre: disponibilidad e idoneidad de información documentada, control de cambios/distribución, y conservación de registros de aprobación.
5. No inventes cláusulas que no estén en el contexto. Si no encuentras la subcláusula exacta, indica cuál es la más cercana disponible.
6. Responde de forma concisa: norma + cláusula + por qué aplica al caso."""
)


def retrieve_context(query: str) -> str:
    """Retrieve and group context by source document with expanded search."""
    # Original search
    docs1 = STORE.similarity_search(query, k=6)

    # Supplementary searches for common ISO document-control topics
    extra_queries = [
        "información documentada control cambios versiones",
        "disponibilidad idoneidad información documentada",
        "aprobación registros conservación",
    ]
    docs2 = []
    for eq in extra_queries:
        docs2.extend(STORE.similarity_search(eq, k=3))

    # Merge, deduplicate by content, keep max 12 chunks
    seen = set()
    all_docs = []
    for doc in docs1 + docs2:
        content_hash = hash(doc.page_content[:200])
        if content_hash not in seen:
            seen.add(content_hash)
            all_docs.append(doc)
    all_docs = all_docs[:12]

    by_source = {}
    for doc in all_docs:
        source = doc.metadata.get("source_filename", "documento desconocido")
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(doc.page_content)

    serialized = ""
    for source, chunks in by_source.items():
        serialized += f"=== DOCUMENTO: {source} ===\n"
        for chunk in chunks:
            serialized += f"{chunk}\n\n"
        serialized += f"=== FIN DOCUMENTO: {source} ===\n\n"

    print("Contexto: ", serialized)
    return serialized


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

    names = load_names()
    original_name = names.get(doc_id, found.name)
    node_index(chunks, doc_id, original_name)
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
        out.append(
            {"doc_id": stem, "filename": original_name, "type": Path(doc_id).suffix}
        )
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
    # Pre-retrieve context grouped by document
    context = retrieve_context(request.query)

    # Build the full message with context directly
    formatted = prompt.format_messages(
        input=request.query,
        context=context,
    )
    full_message = formatted[0].content

    # Call LLM directly
    from langchain_core.messages import HumanMessage as HM

    result = llm.invoke([HM(content=full_message)])
    answer = result.content

    print(answer)
    return {
        "answer": answer,
        "contexts": result.response_metadata,
    }
