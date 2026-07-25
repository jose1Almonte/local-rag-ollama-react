# Local RAG con Ollama y React

Aplicación de **RAG (Retrieval-Augmented Generation)** que funciona completamente en local. Permite subir documentos (PDF, DOCX, TXT), indexarlos en una base de datos vectorial y chatear con un asistente de IA que recupera contexto de tus documentos para responder preguntas.

## Qué es y para qué sirve

Esta aplicación resuelve un problema común: **¿cómo hacer que un LLM local tenga acceso a tus documentos?**

En lugar de depender de servicios en la nube (OpenAI, etc.), usa:

- **Ollama** para ejecutar modelos de lenguaje en tu máquina
- **ChromaDB** como base de datos vectorial local
- **LangChain** como orquestador del pipeline RAG

**Casos de uso:**

- Consultar manuales técnicos, documentación o papers
- Buscar información en contratos, informes o reportes
- Resumir y analizar grandes volúmenes de documentos
- Crear un asistente personal que conozca tu documentación

## Características

- Subida de documentos con drag-and-drop (PDF, DOCX, TXT)
- Indexación automática al subir archivos
- Chat con agente IA que decide cuándo consultar los documentos
- Eliminación y re-indexación de documentos
- Interfaz completamente en español
- 100% local — sin dependencias de servicios externos

## Prerrequisitos

1. **Ollama** instalado y ejecutándose localmente

   Descarga desde: https://ollama.com

2. **Modelos de Ollama** descargados:

   ```bash
   ollama pull llama3.2:latest
   ollama pull mxbai-embed-large
   ```

3. **Python 3.10+**

4. **Node.js 18+**

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/jose1Almonte/local-rag-ollama-react.git
cd local-rag-ollama-react
```

### 2. Backend

```bash
cd backend

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

**Nota:** El `requirements.txt` está incompleto. Si faltan paquetes, instalar manualmente:

```bash
pip install langchain-ollama langchain-chroma langchain-text-splitters langchain-core python-dotenv
```

### 3. Frontend

```bash
cd frontend
npm install
```

## Ejecución

### Iniciar Ollama

Asegúrate de que Ollama esté ejecutándose:

```bash
ollama serve
```

### Iniciar Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El backend estará disponible en: `http://localhost:8000`

Documentación de la API (Swagger): `http://localhost:8000/docs`

### Iniciar Frontend

```bash
cd frontend
npm run dev
```

El frontend estará disponible en: `http://localhost:5173`

## Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto (backend o frontend) con las variables que quieras personalizar:

| Variable | Default | Descripción |
|---|---|---|
| `LLM_MODEL` | `llama3.2:latest` | Modelo de chat de Ollama |
| `EMBED_MODEL` | `mxbai-embed-large` | Modelo de embeddings de Ollama |
| `OLLAMA_URL` | `http://localhost:11434` | URL del servidor Ollama |
| `DATA_DIR` | `./data` | Directorio para almacenar documentos |
| `CHUNK_SIZE` | `800` | Tamaño de los chunks de texto |
| `CHUNK_OVERLAP` | `100` | Overlap entre chunks |
| `TOP_K` | `6` | Número de resultados de retrieval |
| `VITE_API_URL` | `http://localhost:8000` | URL del backend (frontend) |

## Cómo funciona

### Arquitectura General

```
┌─────────────┐     HTTP      ┌─────────────┐     Ollama     ┌──────────────┐
│   Frontend   │ ───────────► │   Backend    │ ────────────► │    Ollama     │
│  React/Vite  │              │   FastAPI    │               │  LLM + Embed  │
└─────────────┘              └──────┬──────┘               └──────────────┘
                                    │
                                    ▼
                             ┌─────────────┐
                             │  ChromaDB    │
                             │ (vectorial)  │
                             └─────────────┘
```

### Pipeline RAG (Paso a paso)

**1. Subida de documentos**

```
Usuario sube archivo → POST /upload → Se guarda con UUID en data/uploads/
```

**2. Indexación**

```
POST /index/{doc_id}
    │
    ├── node_extract()    → Extrae texto del PDF/DOCX/TXT
    ├── node_split()      → Divide en chunks (RecursiveCharacterTextSplitter)
    └── node_index()      → Genera embeddings y guarda en ChromaDB
```

**3. Consulta (Chat)**

```
POST /query
    │
    ├── El agente recibe la pregunta
    ├── Decide si necesita buscar en documentos (usa tool "retrieve")
    ├── Si decide buscar: similarity_search en ChromaDB (k=3)
    ├── El LLM genera respuesta con el contexto recuperado
    └── Retorna respuesta al usuario
```

### Componentes del Backend

| Archivo | Función |
|---|---|
| `main.py` | Punto de entrada FastAPI, endpoints, agente LangChain |
| `src/settings.py` | Variables de entorno y constantes de configuración |
| `src/extractor.py` | Extracción de texto de PDF (PyPDF2), DOCX (python-docx), TXT |
| `src/langgraph_nodes.py` | Pipeline RAG: extracción, división, indexación, retrieval |

### Componentes del Frontend

| Archivo | Función |
|---|---|
| `App.jsx` | Enrutamiento principal (useState, sin React Router) |
| `api.js` | Cliente Axios para comunicarse con el backend |
| `Lateralbar.jsx` | Barra lateral de navegación |
| `pages/Documents.jsx` | Subir, listar, eliminar y re-indexar documentos |
| `pages/Chat.jsx` | Interfaz de chat con el asistente IA |

### Arquitectura del Agente

El agente usa LangChain con un único tool:

```python
@tool
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = STORE.similarity_search(query, k=3)
    # ...
```

El agente decide automáticamente cuándo usar la búsqueda documental basándose en la intención del usuario. El system prompt le indica:

> "Si la intención del usuario no requiere información de los documentos, responde sin buscar en la base de datos."

## API Endpoints

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/upload` | Subir archivo. Retorna `doc_id` |
| `POST` | `/index/{doc_id}` | Indexar documento en ChromaDB |
| `GET` | `/documents` | Listar todos los documentos |
| `DELETE` | `/documents/{doc_id}` | Eliminar documento de ChromaDB y disco |
| `POST` | `/query` | Enviar pregunta al agente RAG |

### Ejemplo de uso con curl

```bash
# Subir documento
curl -X POST http://localhost:8000/upload \
  -F "file=@documento.pdf"

# Indexar (usar el doc_id retornado)
curl -X POST http://localhost:8000/index/{doc_id}

# Consultar
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "¿De qué trata el documento?"}'
```

## Stack Tecnológico

### Backend

- **FastAPI** — Framework web async
- **LangChain** — Orquestación de LLMs y agentes
- **LangChain-Ollama** — Integración con Ollama
- **LangChain-Chroma** — Integración con ChromaDB
- **ChromaDB** — Base de datos vectorial
- **PyPDF2** — Extracción de texto de PDF
- **python-docx** — Extracción de texto de DOCX

### Frontend

- **React 19** — Librería de UI
- **Vite 7** — Build tool y dev server
- **Tailwind CSS 4** — Framework CSS
- **Axios** — Cliente HTTP
- **react-icons** — Iconos

### IA (via Ollama)

- **llama3.2:latest** — Modelo de chat
- **mxbai-embed-large** — Modelo de embeddings

## Notas y Limitaciones

- **CORS abierto**: El backend permite todos los orígenes (`*`). Ajustar para producción.
- **Historial de chat**: La variable `CHAT_HISTORY` existe pero no se actualiza entre queries. El historial no persiste.
- **Modelos soportados**: PDF, DOCX y TXT. Otros formatos pueden funcionar parcialmente.
- **Configuración del LLM**: Hay una discrepancia en los defaults entre `settings.py` (`llama3.2:1b`) y `main.py` (`llama3.2:latest`). La variable de entorno `LLM_MODEL` sobreescribe ambos.
- **Página de ajustes**: El sidebar tiene un botón de "Ajustes" que no lleva a ningún componente (aún no implementado).
