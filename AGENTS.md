# AGENTS.md

## Project Overview

Local RAG (Retrieval-Augmented Generation) app: FastAPI backend + React/Vite frontend. Upload documents (PDF, DOCX, TXT), index into ChromaDB, chat with Ollama-hosted LLMs that retrieve context from your docs. UI is in Spanish.

## Quick Start

### Prerequisites

- Ollama running locally with models pulled:
  ```bash
  ollama pull llama3.2:latest
  ollama pull mxbai-embed-large
  ```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

## Architecture

```
backend/
├── main.py                  # FastAPI app, LangChain agent, API endpoints
├── src/
│   ├── settings.py          # Env vars and config constants
│   ├── extractor.py         # PDF/DOCX/TXT text extraction
│   └── langgraph_nodes.py   # RAG pipeline: extract → split → index → retrieve
└── data/uploads/            # Uploaded documents (UUID-named)

frontend/
├── src/
│   ├── api.js               # Axios client → backend API
│   ├── App.jsx              # Page routing (useState, no router)
│   ├── Lateralbar.jsx       # Sidebar navigation
│   └── pages/
│       ├── Documents.jsx    # Upload, list, delete, re-index docs
│       └── Chat.jsx         # Chat interface with RAG agent
```

## Key Facts for Agents

### Backend

- **Entry point**: `backend/main.py`
- **LLM**: Ollama via `langchain_ollama`, default `llama3.2:latest` (env: `LLM_MODEL`)
- **Embeddings**: `mxbai-embed-large` (env: `EMBED_MODEL`)
- **Vector store**: ChromaDB persisted to `backend/chroma_db/`
- **Agent**: LangChain agent with a single `retrieve` tool (similarity search, k=3)
- **API base**: `http://localhost:8000`
- **CORS**: Allows all origins (dev mode)

### Frontend

- **Entry point**: `frontend/src/main.jsx`
- **No React Router** — page switching via `useState("docs"|"chat")`
- **API client**: `frontend/src/api.js` — Axios with `VITE_API_URL` or `http://localhost:8000`
- **Styling**: Tailwind CSS 4 via Vite plugin
- **Build**: Vite + SWC (`@vitejs/plugin-react-swc`)

### Environment Variables

| Var | Default | Where |
|-----|---------|-------|
| `LLM_MODEL` | `llama3.2:latest` | `main.py` (note: `settings.py` says `llama3.2:1b`) |
| `EMBED_MODEL` | `mxbai-embed-large` | both |
| `OLLAMA_URL` | `http://localhost:11434` | `settings.py` |
| `DATA_DIR` | `./data` | `settings.py` |
| `VITE_API_URL` | `http://localhost:8000` | `api.js` |

### API Endpoints

- `POST /upload` — Upload file, returns `doc_id`
- `POST /index/{doc_id}` — Extract text, split, index into ChromaDB
- `GET /documents` — List all uploaded files
- `DELETE /documents/{doc_id}` — Delete from ChromaDB + disk
- `POST /query` — Send question, agent retrieves context and answers

### Gotchas

- `requirements.txt` is incomplete — missing `langchain-ollama`, `langchain-chroma`, `langchain-text-splitters`, `langchain-core`, `python-dotenv`
- `CHAT_HISTORY` in `main.py` is never appended to after queries (in-memory only, currently broken)
- `node_retrieve()` in `langgraph_nodes.py` exists but is unused — the agent tool does its own retrieval
- No `__init__.py` in `backend/src/` — works but unconventional
- `settings.py` and `main.py` have different LLM_MODEL defaults — env var overrides both
