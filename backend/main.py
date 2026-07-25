import os
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from src.langgraph_nodes import node_extract, node_split, node_index, node_retrieve, STORE
from src.settings import DATA_DIR, TOP_K
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
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DOCS_DIR = Path(DATA_DIR) / "uploads"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

llm  = init_chat_model(
    os.getenv("LLM_MODEL", "llama3.2:latest"),
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
    persist_directory='chroma_db', 
)

# Basic prompt
prompt = ChatPromptTemplate.from_template("""                                
Eres un asistente de inteligencia artificial que ayuda a los usuarios a encontrar información en una colección de documentos.
Si la intencion del usuario no requiere información de los documentos, responde sin buscar en la base de datos.
La consulta es la siguiente:                    
{input}

El historial de chat es el siguiente:
{chat_history}

Responde de manera concisa y precisa. Si no sabes la respuesta, di que no lo sabes. Responde solo con la respuesta para el usuario.
""")
# creating the retriever tool
@tool
def retrieve(query: str):
    """Retrieve information related to a query. Only when the users intent requires information from the documents."""
    retrieved_docs = STORE.similarity_search(query, k=3)

    serialized = ""

    for doc in retrieved_docs:
        serialized += f"Contexto: {doc.page_content}"
    print('Contexto: ', serialized)
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
    return JSONResponse(content={"status": "ok", "indexed_chunks": len(chunks)}, status_code=200)

@app.get("/documents")
def list_documents():
    docs_map = os.listdir('data/uploads')
    out = []
    for doc_id in docs_map:
        out.append({"filename": doc_id, 'type': Path(doc_id).suffix})
    return out

@app.get("/documents/{doc_id}/indexed")
async def check_indexed(doc_id: str):
    try:
        results = STORE.get(where={"doc_id": doc_id})
        return {"indexed": len(results.get("ids", [])) > 0, "chunks": len(results.get("ids", []))}
    except:
        return {"indexed": False, "chunks": 0}

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    deleted = await STORE.adelete(doc_id)
    os.remove(DOCS_DIR / doc_id)
    return {"status": "ok", "deleted_chunks": deleted}

@app.post("/query")
async def query_chat(request: QueryRequest):
    # retrieve top-k

    result = agent.invoke({"messages": [
        HumanMessage(content=prompt.format_messages(input=request.query, chat_history="\n".join([f"User: {msg['user']}\nAI: {msg['ai']}" for msg in CHAT_HISTORY]))[0].content)
    ]})
    print( result.get("messages",[])[-1].content)
    return {"answer": result.get("messages",[])[-1].content, "contexts": result.get("messages",[])[-1].response_metadata}
