# Local RAG con Ollama y React

Aplicación **RAG (Retrieval-Augmented Generation)** 100% local. Sube documentos (PDF, DOCX, TXT), indexa en ChromaDB y chatea con un asistente que recupera contexto de tus documentos para responder preguntas. UI en español.

## Requisitos

- [Ollama](https://ollama.com) instalado y ejecutándose
- Python 3.10+
- Node.js 18+

## Instalación

```bash
# Clonar
git clone https://github.com/jose1Almonte/local-rag-ollama-react.git
cd local-rag-ollama-react

# Backend
cd backend
python -m venv venv
# venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install

# Modelos Ollama
ollama pull llama3.1:8b
ollama pull mxbai-embed-large
```

## Ejecución

```bash
# Backend (http://localhost:8000)
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (http://localhost:5173)
cd frontend
npm run dev
```

## API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/upload` | Subir archivos (soporta múltiples) → `[{doc_id, filename}]` |
| `POST` | `/index/{doc_id}` | Extraer texto, dividir en chunks e indexar en ChromaDB |
| `GET` | `/documents` | Listar documentos con nombres originales |
| `GET` | `/documents/{doc_id}/indexed` | Estado de indexación + conteo de chunks |
| `DELETE` | `/documents/{doc_id}` | Eliminar de ChromaDB, disco y mapping de nombres |
| `POST` | `/query` | Consulta RAG con contexto recuperado |

## Variables de Entorno

| Variable | Default | Archivo |
|----------|---------|---------|
| `LLM_MODEL` | `llama3.1:8b` | `backend/src/settings.py` |
| `EMBED_MODEL` | `mxbai-embed-large` | `settings.py` |
| `CHUNK_SIZE` | `500` | `settings.py` |
| `CHUNK_OVERLAP` | `100` | `settings.py` |
| `TOP_K` | `10` | `settings.py` |
| `OLLAMA_URL` | `http://localhost:11434` | `settings.py` |
| `DATA_DIR` | `./data` | `settings.py` |
| `VITE_API_URL` | `http://localhost:8000` | `frontend/src/api.js` |

## Stack

- **Backend**: FastAPI, LangChain, ChromaDB, Ollama
- **Frontend**: React 19, Vite 7, Tailwind CSS 4, Axios
- **Modelos**: `llama3.1:8b` (chat), `mxbai-embed-large` (embeddings)
