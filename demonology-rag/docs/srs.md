# 🧩 Software Requirements Specification (SRS)

### Project Name: **Daemonology RAG API**

### Version: 1.0

### Author: Fardeen Singh Zehen

### Date: 05-Nov-2025

---

## 1. Purpose

The **Daemonology RAG API** is a backend service that:

* Ingests and indexes PDF documents containing demonology content.
* Stores embeddings in PostgreSQL with the pgvector extension.
* Provides endpoints to query the data via LlamaIndex and an external LLM (e.g. GPT, DeepSeek).
* Runs fully containerized with FastAPI, supporting auto-reload for development.

---

## 2. System Overview

### 2.1 Features

* Upload PDF files → automatic text extraction & indexing.
* Query indexed documents → get contextual answers from LLM.
* Modular and extendable structure.
* Docker-based local development environment.
* Future-ready for multimodal support and fine-tuning.

### 2.2 High-Level Flow

```
[PDF Upload] --> [Extractor] --> [LlamaIndex] --> [Vector DB (pgvector)]
                                           |
                                           v
                                      [LLM Query Engine]
                                           |
                                           v
                                        [Response]
```

---

## 3. Functional Requirements

| ID  | Feature                   | Description                                                                                    |
| --- | ------------------------- | ---------------------------------------------------------------------------------------------- |
| FR1 | Upload PDFs               | Users can upload one or more PDF files via `/upload` API.                                      |
| FR2 | Text Extraction           | PDFs are parsed into text chunks using LlamaIndex’s `SimpleDirectoryReader`.                   |
| FR3 | Index Creation            | Each upload triggers LlamaIndex indexing to Postgres vector store.                             |
| FR4 | Query API                 | `/query` endpoint accepts a text query, retrieves context from vector DB, and queries the LLM. |
| FR5 | Persistent Vector Store   | Uses PostgreSQL with `pgvector` for embeddings and metadata.                                   |
| FR6 | Environment Configuration | Managed with `.env` (keys, DB URL, directories).                                               |
| FR7 | Hot Reload                | Docker container auto-reloads on code changes during development.                              |

---

## 4. Non-Functional Requirements

| Type            | Requirement                                               |
| --------------- | --------------------------------------------------------- |
| Performance     | Indexing under 10s for <10 PDFs. Query response under 2s. |
| Scalability     | Supports 10,000+ document chunks.                         |
| Maintainability | Modular, SOLID-compliant architecture.                    |
| Extensibility   | Can easily add multimodal/image embeddings later.         |
| Security        | No external data leak except optional LLM API usage.      |
| Portability     | Must run identically on any dev machine via Docker.       |

---

## 5. Technology Stack

| Component     | Technology                          |
| ------------- | ----------------------------------- |
| Language      | Python 3.11+                        |
| Framework     | FastAPI                             |
| RAG Engine    | LlamaIndex                          |
| Database      | PostgreSQL + pgvector               |
| ORM           | SQLAlchemy                          |
| Dev Container | Docker + uvicorn hot reload         |
| Env Mgmt      | python-dotenv                       |
| Logging       | Standard Python logging             |
| Embeddings    | OpenAI / HuggingFace (configurable) |

---

## 6. System Architecture

### 6.1 Folder Structure

```
daemonology-rag/
│
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── upload.py
│   │   │   ├── query.py
│   │   │   └── health.py
│   │   └── routes.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── embeddings.py
│   │   ├── index.py
│   │   └── utils.py
│   │
│   ├── main.py
│   └── models/
│       └── document.py
│
├── data/                    # PDFs go here
├── indexes/                 # local index storage if needed
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── TODO.md
```

---

## 7. API Design

### 7.1 `POST /upload`

**Description:** Upload one or more PDF files for ingestion and indexing.

**Request:**

* Multipart form-data with file(s).

**Response:**

```json
{
  "status": "success",
  "files_indexed": ["St_Thomas_Aquinas.pdf", "Encyclopedia_of_Demons.pdf"]
}
```

---

### 7.2 `POST /query`

**Description:** Query indexed data.

**Request:**

```json
{
  "query": "Who is Asmodeus according to demonology?"
}
```

**Response:**

```json
{
  "answer": "Asmodeus is described as one of the princes of hell...",
  "sources": ["The Encyclopedia of Demons.pdf - page 45"]
}
```

---

### 7.3 `GET /health`

**Response:**

```json
{ "status": "ok", "message": "Daemonology RAG API is running" }
```

---

## 8. Docker & Dev Setup

### 8.1 Dockerfile (Dev)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 8.2 docker-compose.yml

```yaml
version: '3.9'

services:
  api:
    build: .
    container_name: daemonology_api
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db

  db:
    image: pgvector/pgvector
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: daemonology
    ports:
      - "5432:5432"
```

---

## 9. Quickstart (30 seconds)

```bash
# 1. Clone and enter project
git clone <repo-url>
cd daemonology-rag

# 2. Set up environment
cp .env.example .env
export OPENAI_API_KEY=<your_api_key>

# 3. Start containers
docker-compose up --build

# 4. Upload PDFs
curl -F "file=@data/Demonology.pdf" http://localhost:8000/upload

# 5. Query the system
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" \
     -d '{"query": "Who is Beelzebub?"}'
```

---

## 10. Future Extensions

| Feature                 | Description                                    |
| ----------------------- | ---------------------------------------------- |
| CLIP Multimodal Support | Add image embeddings for demon illustrations.  |
| Auth Layer              | Token-based auth for endpoints.                |
| Web UI                  | Minimal Streamlit or Next.js dashboard.        |
| Async Queue             | Celery / RQ for background embedding.          |
| Fine-tuning             | Integrate LoRA pipeline for demonology domain. |

---

# ✅ TODO.md

````markdown
# TODO – Daemonology RAG API

## Core Setup
- [ ] **Initialize FastAPI app**  
  Create `app/main.py` and wire routes. Verify `/health` endpoint works.

- [ ] **Configure PostgreSQL + pgvector**  
  Use `db.py` to create connection with SQLAlchemy.  
  Enable `pgvector` extension and confirm `documents` table exists.

- [ ] **Add LlamaIndex setup**  
  Implement `index.py` to handle:
  - Loading documents from `/data`
  - Creating `VectorStoreIndex`
  - Saving to Postgres vector store

- [ ] **Create Upload Endpoint**
  - [ ] Save uploaded PDFs in `/data`
  - [ ] Trigger LlamaIndex ingestion for each new file
  - [ ] Return indexed file names

- [ ] **Create Query Endpoint**
  - [ ] Load index from Postgres
  - [ ] Execute LlamaIndex query
  - [ ] Return model’s textual answer and metadata sources

- [ ] **Add Logging & Error Handling**
  - Central logging config under `/core/utils.py`

- [ ] **Dockerize API**
  - Add Dockerfile and docker-compose with Postgres service
  - Ensure hot reload works (`--reload` flag)

- [ ] **Add .env management**
  - `.env.example` with vars:
    ```
    DATABASE_URL=postgresql://postgres:postgres@db:5432/daemonology
    OPENAI_API_KEY=yourkey
    DATA_DIR=./data
    ```

## Enhancement Roadmap
- [ ] **Add async background processing for ingestion**
- [ ] **Add CLIP multimodal embeddings**
- [ ] **Add pagination for query results**
- [ ] **Add admin CLI (manage indexes, clear DB, reindex)**
- [ ] **Integrate OpenRouter/DeepSeek option for LLM backend**
````

---

## ✅ Deliverables Summary

| Deliverable                        | Description                                                             |
| ---------------------------------- | ----------------------------------------------------------------------- |
| `app/`                             | Clean modular FastAPI project structure                                 |
| `Dockerfile`, `docker-compose.yml` | Hot-reloading dev environment                                           |
| `TODO.md`                          | Functional development guide                                            |
| `SRS.md`                           | Technical blueprint (this document)                                     |
| `.env.example`                     | Configuration template                                                  |
| `requirements.txt`                 | Dependencies (`llama-index`, `fastapi`, `pgvector`, `sqlalchemy`, etc.) |

---
