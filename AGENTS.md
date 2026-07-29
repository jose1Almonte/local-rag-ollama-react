# AGENTS.md

## Commands

```bash
# Backend (must use python -m on Windows)
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev    # http://localhost:5173

# Required Ollama models
ollama pull llama3.1:8b
ollama pull mxbai-embed-large
```

## Architecture

- **No React Router** — page switching via `useState("docs"|"chat")` in `App.jsx`
- **Messages state lives in App.jsx** — persists across page switches (not in Chat.jsx)
- **Chat history is in-memory** (`CHAT_HISTORY` list in `main.py`) — resets on server restart
- **No agent framework** — `/query` calls `llm.invoke()` directly with pre-retrieved context
- **ChromaDB persisted** to `backend/chroma_db/` — changing `CHUNK_SIZE`/`EMBED_MODEL` requires re-indexing from UI

## Backend Gotchas

| Gotcha | Detail |
|--------|--------|
| `node_retrieve()` dead | `main.py` calls `STORE.similarity_search()` directly, not the langgraph node |
| PDF TOC skipping | `_is_toc_page()` skips index pages (lines ending with `... NNN`) |
| UUID filenames | Files saved as `data/uploads/{uuid}.{ext}`, mapping stored in `filenames.json` |
| Multi-file upload | `POST /upload` accepts `List[UploadFile]`, returns `{uploaded: [{doc_id, filename}]}` |
| Retrieval | Primary k=6 + 3 supplementary queries k=3 each, dedup by hash, max 12 chunks |
| Prompt | 6-rule ISO auditor prompt with explicit 7.5.3.1 vs 7.5.3.2 distinction |
| Source attribution | Chunks carry `source_filename` metadata from `filenames.json` |
| No `__init__.py` | `backend/src/` has no `__init__.py` — works but unconventional |

## Frontend Gotchas

| Gotcha | Detail |
|--------|--------|
| Multi-file upload | `<input multiple>` with batch upload and progress |
| Axios timeout | 300s (was 120s) |
| Auto-scroll | `useRef` + `useEffect` on `messages` and `isLoading` |
| Typing indicator | `isLoading` state — 3 animated dots while LLM responds |

## Env Vars (all with defaults)

| Var | Default | File |
|-----|---------|------|
| `LLM_MODEL` | `llama3.1:8b` | `settings.py` |
| `EMBED_MODEL` | `mxbai-embed-large` | `settings.py` |
| `CHUNK_SIZE` | `500` | `settings.py` |
| `TOP_K` | `10` | `settings.py` |
| `VITE_API_URL` | `http://localhost:8000` | `api.js` |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/upload` | Upload multiple files → `[{doc_id, filename}]` |
| `POST` | `/index/{doc_id}` | Extract + split + index (re-indexable) |
| `GET` | `/documents` | List with original filenames |
| `GET` | `/documents/{doc_id}/indexed` | Check index status + chunk count |
| `DELETE` | `/documents/{doc_id}` | Deletes from ChromaDB + disk + mapping |
| `POST` | `/query` | RAG query → direct `llm.invoke()` |
