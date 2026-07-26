# AGENTS.md

## Project Overview

Local RAG (Retrieval-Augmented Generation) app: FastAPI backend + React/Vite frontend. Upload documents (PDF, DOCX, TXT), index into ChromaDB, chat with Ollama-hosted LLMs that retrieve context from your docs. UI is in Spanish.

## Quick Start

### Prerequisites

- Ollama running locally with models pulled:
  ```bash
  ollama pull llama3.1:8b
  ollama pull mxbai-embed-large
  ```

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
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
└── data/uploads/            # Uploaded documents (UUID-named) + filenames.json

frontend/
├── src/
│   ├── api.js               # Axios client → backend API
│   ├── App.jsx              # Page routing (useState, no router), messages state
│   ├── Lateralbar.jsx       # Sidebar navigation with active state
│   └── pages/
│       ├── Documents.jsx    # Upload, list, delete, re-index docs
│       └── Chat.jsx         # Chat interface with RAG agent
```

## Key Facts for Agents

### Backend

- **Entry point**: `backend/main.py`
- **LLM**: Ollama via `langchain_ollama`, default `llama3.1:8b` (env: `LLM_MODEL`)
- **Embeddings**: `mxbai-embed-large` (env: `EMBED_MODEL`)
- **Vector store**: ChromaDB persisted to `backend/chroma_db/`
- **Agent**: Direct LLM call (no agent framework) with pre-retrieved context grouped by document
- **Prompt**: Simple, direct prompt for ISO expert role with context + question format
- **Source attribution**: Chunks include `source_filename` metadata (original filename from `filenames.json`); context is grouped by document with `=== DOCUMENTO: filename ===` headers so the LLM knows which document each chunk comes from
- **API base**: `http://localhost:8000`
- **CORS**: Allows all origins (dev mode)
- **Chat history**: In-memory `CHAT_HISTORY` list, persisted during server runtime
- **Filename mapping**: `data/uploads/filenames.json` maps UUID → original filename

### Frontend

- **Entry point**: `frontend/src/main.jsx`
- **No React Router** — page switching via `useState("docs"|"chat")`
- **Chat persistence**: Messages state lives in `App.jsx`, persists across page switches
- **API client**: `frontend/src/api.js` — Axios with `VITE_API_URL` or `http://localhost:8000`
- **Styling**: Tailwind CSS 4 via Vite plugin
- **Build**: Vite + SWC (`@vitejs/plugin-react-swc`)

### Environment Variables

| Var | Default | Where |
|-----|---------|-------|
| `LLM_MODEL` | `llama3.1:8b` | `settings.py` (used in `main.py` via constant) |
| `EMBED_MODEL` | `mxbai-embed-large` | both |
| `OLLAMA_URL` | `http://localhost:11434` | `settings.py` |
| `DATA_DIR` | `./data` | `settings.py` |
| `VITE_API_URL` | `http://localhost:8000` | `api.js` |

### API Endpoints

- `POST /upload` — Upload file, returns `doc_id` and saves original filename mapping
- `POST /index/{doc_id}` — Extract text, split, index into ChromaDB (supports re-indexing)
- `GET /documents` — List all uploaded files with original filenames
- `GET /documents/{doc_id}/indexed` — Check if document is indexed, returns chunk count
- `DELETE /documents/{doc_id}` — Delete from ChromaDB, disk, and filename mapping
- `POST /query` — Send question, agent retrieves context and answers

### Gotchas

- `node_retrieve()` in `langgraph_nodes.py` exists but is unused — the agent tool does its own retrieval
- No `__init__.py` in `backend/src/` — works but unconventional
- `settings.py` and `main.py` use consistent defaults — `main.py` imports `LLM_MODEL` from `settings.py`
- `requirements.txt` is complete — all langchain packages included
- Chat history is in-memory only — resets when server restarts
- Document delete uses stem matching — finds file by UUID without extension
- `filenames.json` stores UUID → original filename mapping — must be kept in sync with uploads
