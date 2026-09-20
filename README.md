# CodeGraphAI ⚡

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-Production-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/React-18.x-61DAFB?style=for-the-badge&logo=react" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql" />
  <img src="https://img.shields.io/badge/Neo4j-5.x-008CC1?style=for-the-badge&logo=neo4j" />
  <img src="https://img.shields.io/badge/Qdrant-VectorDB-DC382D?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Celery-Distributed-37814A?style=for-the-badge&logo=celery" />
  <img src="https://img.shields.io/badge/Redis-TaskQueue-DC382D?style=for-the-badge&logo=redis" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker" />
  <img src="https://img.shields.io/badge/LLM-OpenAI_GPT--OSS--120B-D4AF37?style=for-the-badge" />
</p>

> **An Enterprise-Grade, Multi-Tenant Repository Intelligence & GraphRAG Platform combining Semantic AST Analysis, Neo4j Knowledge Graphs, Qdrant Vector Payloads, Multi-Turn Conversational Memory, and High-Parameter LLM Reasoning (`openai/gpt-oss-120b`).**

CodeGraphAI automatically clones, parses, and partitions complex software repositories into rich semantic representations. Rather than treating source code as unstructured text, it constructs a **multi-tenant Knowledge Graph** capturing AST hierarchy, function call flows, symbol definitions, and cross-file dependencies. Coupled with **multi-turn conversational memory** and **hybrid vector-graph retrieval**, it delivers source-grounded answers with verifiable file citations and architectural context.

---

## 📑 Table of Contents

- [Key Architectural Highlights](#-key-architectural-highlights)
- [System Architecture](#-system-architecture)
- [Core Capabilities](#-core-capabilities)
  - [1. Multi-Tenant Authentication & PostgreSQL Persistence](#1-multi-tenant-authentication--postgresql-persistence)
  - [2. AST-Aware Parsing & GraphRAG Segregation](#2-ast-aware-parsing--graphrag-segregation)
  - [3. Conversational Memory & Co-Reference Resolution](#3-conversational-memory--co-reference-resolution)
  - [4. Multi-Model LLM Reasoning Engine](#4-multi-model-llm-reasoning-engine)
  - [5. Interactive React Frontend & Graph Visualizer](#5-interactive-react-frontend--graph-visualizer)
- [Tech Stack](#-tech-stack)
- [Docker Deployment](#-docker-deployment-recommended)
- [Local Development Setup](#-local-development-setup)
- [API Reference](#-api-reference)
- [Environment Variables](#-environment-variables)
- [License](#-license)

---

# 🚀 Key Architectural Highlights

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 CodeGraphAI Platform                                   │
├──────────────────┬───────────────────────────────┬─────────────────────────────────────┤
│ 🏢 Multi-Tenancy │ JWT Auth, User Isolation     │ PostgreSQL 16 (Users, Repos, Convs) │
│ 🕸️ GraphRAG      │ Neo4j 5.x Subgraphs + Qdrant │ Cypher BFS + Vector Payload Filters │
│ 🧠 Memory Engine │ K=6 Sliding Window + Groq LLM │ Co-Reference Query Contextualizer   │
│ 🤖 LLM Reasoning │ openai/gpt-oss-120b           │ Resilient Multi-Candidate Fallback  │
│ ⚡ Ingestion      │ Celery Workers + Redis Queue  │ AST Tree-Sitter Chunking Pipeline   │
│ 🎨 Frontend UI   │ React 18 + Tailwind + Canvas │ Interactive Graph View & Dark Theme │
└──────────────────┴───────────────────────────────┴─────────────────────────────────────┘
```

---

# 🏗️ System Architecture

```text
                          GitHub Repository URL
                                    │
                                    ▼
                ┌───────────────────────────────────────┐
                │        Celery Background Task         │
                │        (Distributed Worker)           │
                └──────────────────┬────────────────────┘
                                   │
                   ┌───────────────┴───────────────┐
                   ▼                               ▼
       ┌───────────────────────┐       ┌───────────────────────┐
       │   Tree-sitter Parser  │       │  Neo4j Knowledge Graph│
       │   AST Chunk Generator │       │  (CALLS, IMPORTS,     │
       └───────────┬───────────┘       │   INHERITS, DEFINES)  │
                   │                   └───────────┬───────────┘
                   ▼                               │
       ┌───────────────────────┐                   │
       │ HuggingFace Embeddings│                   │
       │  (all-MiniLM-L6-v2)   │                   │
       └───────────┬───────────┘                   │
                   │                               │
                   ▼                               ▼
       ┌───────────────────────┐       ┌───────────────────────┐
       │ Qdrant Vector Store   │       │ Multi-Tenant Partition│
       │ (User/Repo Tags)      │       │ (Isolated Subgraphs)  │
       └───────────┬───────────┘       └───────────┬───────────┘
                   │                               │
                   └───────────────┬───────────────┘
                                   │
                           User Chat Query
                                   │
                                   ▼
                 ┌───────────────────────────────────┐
                 │    Conversational Memory Engine   │
                 │    (K=6 Turn PostgreSQL Window)   │
                 └─────────────────┬─────────────────┘
                                   │
                                   ▼
                 ┌───────────────────────────────────┐
                 │   Query Contextualizer Engine     │
                 │  (Co-Reference & Pronoun Resolve) │
                 └─────────────────┬─────────────────┘
                                   │
                                   ▼
                 ┌───────────────────────────────────┐
                 │   Hybrid Retrieval Orchestrator   │
                 │ (Intent Routing + Graph Expansion)│
                 └─────────────────┬─────────────────┘
                                   │
                                   ▼
                 ┌───────────────────────────────────┐
                 │       LLM Generation Engine       │
                 │       (openai/gpt-oss-120b)       │
                 └─────────────────┬─────────────────┘
                                   │
                                   ▼
                 ┌───────────────────────────────────┐
                 │ Source-Grounded Architectural     │
                 │ Answer with Citations & Call Flow │
                 └───────────────────────────────────┘
```

---

# 🌟 Core Capabilities

## 1. Multi-Tenant Authentication & PostgreSQL Persistence
- **Secure JWT Authentication**: SHA-256 password hashing, token validation, and multi-tenant user scoping (`free`, `pro`, `enterprise` tiers).
- **PostgreSQL Relational Schema**:
  - `users`: Credentials, subscription tier, tenant IDs.
  - `repositories`: Git URLs, indexing timestamps, multi-tenant ownership.
  - `conversations`: Thread sessions, auto-derived titles, cascade deletion.
  - `messages`: Chronological dialogue turns, retrieval strategies, citation JSON payloads, token counts.
  - `code_symbols`: AST-extracted classes, methods, line ranges, and qualified identifiers.

## 2. AST-Aware Parsing & GraphRAG Segregation
- **Tree-sitter Parsing**: Extracts high-fidelity AST structural chunks rather than arbitrary character splits.
- **Tenant-Segregated Vector Search**: Every embedding vector uploaded to Qdrant is payload-tagged with `user_id` and `repository_id`, enforcing strict tenant boundaries during hybrid retrieval.
- **Neo4j Graph Partitioning**: Nodes and edges in Neo4j are isolated per repository with parameterized Cypher queries for symbol dependencies, class hierarchies, and execution call flows.

## 3. Conversational Memory & Co-Reference Resolution
- **Sliding-Window Memory (K=6 Turns)**: Automatically retrieves preceding dialogue turns from PostgreSQL to provide context for follow-up questions.
- **LLM Co-Reference Resolution**: Re-writes ambiguous follow-up prompts (*e.g., "What does that function return?"* $\rightarrow$ *"What does the calculate_metrics function return in analyzer.py?"*) before executing vector and graph retrieval.
- **Non-Blocking Persistence**: Chat turns, token metrics, and source citations are asynchronously persisted via FastAPI `BackgroundTasks`.

## 4. Multi-Model LLM Reasoning Engine
- **Configured Primary**: **`openai/gpt-oss-120b`** for deep architectural reasoning and call flow synthesis.
- **Resilient Fallback Hierarchy**: Automatically cascades through `openai/gpt-oss-120b` $\rightarrow$ `llama-3.3-70b-versatile` $\rightarrow$ `llama-3.1-8b-instant` if a specific provider endpoint hits rate limits.

## 5. Interactive React Frontend & Graph Visualizer
- **Dark Luxury Aesthetic**: Curated HSL Gold palette (`#D4AF37`), glassmorphism, and responsive layouts.
- **Interactive Graph View**: Live visual exploration of repository classes, methods, and relationships rendered on a high-performance 2D Canvas.
- **Thread History Switcher**: Persistent sidebar displaying saved chat threads, automatic topic titling, and seamless switching between conversations.
- **Architecture Modal**: Interactive architecture diagrams explaining the GraphRAG pipeline and tenant isolation layers.

---

# 🛠️ Tech Stack

| Domain | Technologies |
|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Framer Motion, React Markdown, Axios, React Icons |
| **Backend API** | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, Uvicorn, PyJWT, Passlib |
| **Databases** | PostgreSQL 16 (Relational), Neo4j 5.x (Knowledge Graph), Qdrant (Vector DB), Redis (Queue & Cache) |
| **Asynchronous Engine** | Celery 5.x, Redis, Celery Flower |
| **Code Intelligence** | Tree-sitter, AST Parser, HuggingFace `all-MiniLM-L6-v2` |
| **LLM Reasoning** | Groq API (`openai/gpt-oss-120b`, `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`) |
| **Containerization** | Docker, Docker Compose |

---

# 🐳 Docker Deployment (Recommended)

CodeGraphAI is orchestrated as an 8-container microservices topology.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (version 24.0+ recommended)
- Docker Compose v2

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ayush-m1911/CodeGraphAI.git
   cd CodeGraphAI
   ```

2. **Configure environment variables**:
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   LLM_MODEL=openai/gpt-oss-120b
   POSTGRES_USER=codegraph
   POSTGRES_PASSWORD=codegraph_secret
   POSTGRES_DB=codegraph_db
   SECRET_KEY=your_super_secret_jwt_key
   NEO4J_AUTH=neo4j/codegraph_secret
   ```

3. **Launch the entire stack**:
   ```bash
   docker compose up --build -d
   ```

4. **Verify running containers**:
   ```bash
   docker compose ps
   ```

---

### Service Topology

| Service | Container Name | Port | Description |
|---|---|---|---|
| **Frontend** | `codegraph_frontend` | `5173` | React/Vite UI & Graph Visualizer |
| **Backend API** | `codegraph_backend` | `8000` | FastAPI GraphRAG Engine |
| **Celery Worker** | `codegraph_celery_worker` | — | Asynchronous Indexing Worker |
| **Flower** | `codegraph_flower` | `5555` | Celery Task Monitoring Dashboard |
| **PostgreSQL** | `codegraph_postgres` | `5432` | Relational Storage (Users, Sessions) |
| **Neo4j** | `codegraph_neo4j` | `7474`, `7687` | Knowledge Graph & Cypher Browser |
| **Qdrant** | `codegraph_qdrant` | `6333`, `6334` | Multi-Tenant Vector Database |
| **Redis** | `codegraph_redis` | `6379` | Message Broker & Result Backend |

---

# 💻 Local Development Setup

### 1. Backend Setup

```bash
cd backend

# Create & activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Celery Worker (Local)

```bash
cd backend
celery -A app.workers.celery_app.celery worker --loglevel=info --concurrency=4
```

### 3. Frontend Setup

```bash
cd frontend

# Install Node modules
npm install

# Start Vite development server
npm run dev
```

The frontend will be live at `http://localhost:5173`.

---

# 📡 API Reference

### Authentication (`/api/auth`)
- `POST /api/auth/signup` — Register a new account (`email`, `password`, `tier`).
- `POST /api/auth/login` — Authenticate and receive a JWT Bearer token.
- `GET /api/auth/me` — Retrieve active user session and subscription info.

### Repositories (`/api/repositories`)
- `GET /api/repositories` — List user repositories.
- `POST /api/repositories` — Register and index a new repository.
- `GET /api/repositories/{id}` — Get repository details.
- `DELETE /api/repositories/{id}` — Delete a repository and cascade its subgraphs.

### Conversations & Memory (`/api/conversations`)
- `GET /api/conversations?repository_id={id}` — List conversation threads.
- `POST /api/conversations` — Start a new conversation thread.
- `GET /api/conversations/{id}` — Retrieve conversation details.
- `PATCH /api/conversations/{id}` — Update conversation title.
- `GET /api/conversations/{id}/messages` — Fetch chronological chat history.
- `DELETE /api/conversations/{id}` — Delete a conversation and its messages.

### Reasoning & Ingestion
- `POST /chat` — Execute multi-turn hybrid GraphRAG query with LLM reasoning.
- `POST /repositories/index` — Dispatch asynchronous repository indexing job to Celery.
- `GET /jobs/{job_id}` — Poll status and progress of an indexing task.
- `GET /graph` — Fetch interactive Neo4j graph nodes and relationship edges.

---

# ⚙️ Environment Variables

| Variable | Default Value | Purpose |
|---|---|---|
| `GROQ_API_KEY` | *(Required)* | Groq API Key for LLM inference |
| `LLM_MODEL` | `openai/gpt-oss-120b` | Target LLM model name |
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `NEO4J_URI` | `bolt://neo4j:7687` | Neo4j Bolt connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `codegraph_secret` | Neo4j password |
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant vector database URL |
| `REDIS_URL` | `redis://redis:6379/0`| Redis message broker URL |
| `SECRET_KEY` | *(Configurable)* | JWT secret signature key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24h) | JWT expiration window |

---

# 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<p align="center">
  <b>CodeGraphAI</b> — Built with HSL Gold & Multi-Tenant GraphRAG Intelligence.
</p>
