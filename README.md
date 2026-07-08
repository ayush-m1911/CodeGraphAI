# CodeGraphAI ⚡

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/FastAPI-Production-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Celery-Distributed-37814A?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Redis-TaskQueue-DC382D?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Qdrant-VectorDB-orange?style=for-the-badge" />
</p>

> **An AI-powered Repository Intelligence Platform that combines Semantic Code Analysis, Knowledge Graphs, Hybrid GraphRAG Retrieval, and Large Language Models to help developers understand complex Python codebases.**

CodeGraphAI automatically clones, indexes, and analyzes GitHub repositories to build a rich semantic representation of source code. Instead of treating code as plain text, it constructs a **Knowledge Graph** representing repository hierarchy, function calls, symbol relationships, and semantic dependencies. Combined with **Hybrid GraphRAG Retrieval**, it provides accurate, source-grounded explanations with architectural context.

Designed as a production-grade system, CodeGraphAI includes asynchronous indexing using **Celery + Redis**, **Dockerized deployment**, **Qdrant vector search**, and an interactive React frontend.

---

# ✨ Features

## 📂 Repository Intelligence

- Analyze any public Python GitHub repository
- Automatic repository cloning
- Background repository indexing
- Real-time indexing progress
- Repository-specific indexing namespaces
- Fault-tolerant indexing pipeline

---

## 🧠 Semantic Code Analysis

- Tree-sitter based parsing
- AST-aware code chunking
- Fully Qualified Name (FQN) resolution
- Symbol extraction
- Function call analysis
- Import analysis
- Class hierarchy extraction
- Rich symbol metadata generation

---

## 🌐 Semantic Knowledge Graph

Builds a repository-level knowledge graph containing structural and semantic relationships.

### Hierarchy

```text
Repository
    ↓
Package
    ↓
Module
    ↓
Class
    ↓
Method / Function
```

### Relationship Types

- CALLS
- IMPORTS
- DEFINES
- CONTAINS
- REFERENCES
- DECORATES
- INHERITS
- RETURNS
- RAISES
- INSTANTIATES

---

## 🔍 Hybrid GraphRAG Retrieval

Instead of relying solely on vector similarity, CodeGraphAI combines multiple retrieval strategies.

```text
User Question
      ↓
Intent Detection
      ↓
Entity Extraction
      ↓
Symbol Resolution
      ↓
Knowledge Graph Traversal
      ↓
Vector Retrieval
      ↓
Context Ranking
      ↓
Prompt Builder
      ↓
Groq LLM
      ↓
Grounded Answer
```

Supported query types include:

- Definitions
- Architecture
- Call Flow
- Dependencies
- Configuration
- Implementation Details
- Error Analysis
- Repository Exploration

---

## ⚙️ Production Infrastructure

- FastAPI REST API
- Celery Background Workers
- Redis Task Queue
- Qdrant Vector Database
- Docker Compose Deployment
- Flower Monitoring Dashboard
- Structured Logging
- Retry with Exponential Backoff
- Production-grade Error Handling

---

## 🎨 Interactive Frontend

- Premium Matte Black + Metallic Gold UI
- Repository Upload Workflow
- Live Indexing Progress
- Markdown Chat Interface
- Expandable Source References
- GraphRAG Timeline
- Responsive Design

---

# 🏗️ System Architecture

```text
                 GitHub Repository
                         │
                         ▼
                Repository Cloning
                         │
                         ▼
                Tree-sitter Parsing
                         │
                         ▼
              Symbol Extraction
                         │
                         ▼
           Semantic Knowledge Graph
                         │
                         ▼
          Hierarchical Graph Builder
                         │
                         ▼
              AST-aware Chunking
                         │
                         ▼
          HuggingFace Embeddings
                         │
                         ▼
               Qdrant Vector Database
                         │
                         ▼
        Hybrid Retrieval Orchestrator
                         │
                         ▼
            Context Ranking Engine
                         │
                         ▼
               Prompt Builder
                         │
                         ▼
                  Groq LLM
                         │
                         ▼
              Context-grounded Answer
```

---

# 🛠️ Tech Stack

## Frontend

- React (Vite)
- Tailwind CSS
- Framer Motion
- React Markdown
- Axios
- React Icons

## Backend

- FastAPI
- Python
- LangChain
- Tree-sitter
- GitPython

## AI / ML

- HuggingFace Embeddings (`BAAI/bge-small-en-v1.5`)
- Groq Llama 3.3 70B
- Hybrid GraphRAG
- Semantic Knowledge Graph

## Infrastructure

- Docker
- Docker Compose
- Celery
- Redis
- Qdrant
- Flower

  # 🚀 Running with Docker (Recommended)

CodeGraphAI is fully containerized using **Docker Compose**. The entire application stack—including the frontend, backend, Celery workers, Redis, Qdrant, and Flower—can be started with a single command.

## Prerequisites

- Docker Desktop
- Docker Compose

## Start the complete application

```bash
docker compose up --build
```

For subsequent runs:

```bash
docker compose up -d
```

Stop all services:

```bash
docker compose down
```

---

## Available Services

| Service | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| FastAPI Swagger | http://localhost:8000/docs |
| Flower Dashboard | http://localhost:5555 |
| Qdrant Dashboard | http://localhost:6333/dashboard |

---

# 💻 Local Development

## Backend

Navigate to the backend directory.

```bash
cd backend
```

Create a virtual environment.

### Windows

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Create a `.env` file.

```env
GROQ_API_KEY=your_groq_api_key

QDRANT_URL=http://localhost:6333

REDIS_URL=redis://localhost:6379/0

COLLECTION_NAME=repo_chunks
```

Run the backend.

```bash
uvicorn app.main:app --reload
```

Backend will start at

```
http://localhost:8000
```

---

## Frontend

Navigate to the frontend directory.

```bash
cd frontend
```

Install dependencies.

```bash
npm install
```

Run the frontend.

```bash
npm run dev
```

Frontend will start at

```
http://localhost:5173
```

---

# 📖 How It Works

## Repository Indexing Pipeline

```text
GitHub Repository
        │
        ▼
Repository Cloning
        │
        ▼
Tree-sitter Parsing
        │
        ▼
Symbol Extraction
        │
        ▼
Semantic Relationship Extraction
        │
        ▼
Knowledge Graph Construction
        │
        ▼
Hierarchical Graph Construction
        │
        ▼
AST-aware Chunk Generation
        │
        ▼
Embedding Generation
        │
        ▼
Qdrant Vector Storage
        │
        ▼
Repository Ready for Chat
```

---

## Question Answering Pipeline

```text
User Question
        │
        ▼
Intent Detection
        │
        ▼
Retrieval Orchestrator
        │
        ▼
Graph Retrieval
        │
        ▼
Vector Retrieval
        │
        ▼
Context Ranking
        │
        ▼
Prompt Builder
        │
        ▼
Groq LLM
        │
        ▼
Grounded Response
```

---

# 💬 Example Questions

Once a repository has been indexed, you can ask questions like:

```
How does APIRouter register GET endpoints?

Explain the authentication flow.

Where is this function used?

Which files are responsible for repository indexing?

How is hybrid retrieval implemented?

Explain the call flow of this function.

Where are embeddings generated?

How does Celery perform background indexing?

How is the knowledge graph constructed?

Explain the architecture of the project.
```

---

# 📂 Project Structure

```text
CodeGraphAI
│
├── backend
│   ├── api
│   ├── services
│   ├── workers
│   ├── tasks
│   ├── models
│   ├── schemas
│   ├── repositories
│   ├── graphs
│   ├── config.py
│   └── main.py
│
├── frontend
│   ├── components
│   ├── context
│   ├── pages
│   ├── services
│   └── assets
│
├── docker-compose.yml
└── README.md
```

---

# 📊 Production Features

- ✅ Dockerized Deployment
- ✅ Background Repository Indexing
- ✅ Celery + Redis Task Queue
- ✅ Qdrant Vector Database
- ✅ Hybrid GraphRAG Retrieval
- ✅ Intent-aware Retrieval
- ✅ Semantic Knowledge Graph
- ✅ Hierarchical Repository Graph
- ✅ Context Ranking Engine
- ✅ Fault-tolerant Graph Construction
- ✅ Structured Logging
- ✅ Retry with Exponential Backoff
- ✅ Flower Monitoring Dashboard
- ✅ Modular Backend Architecture

---

# 🎯 Future Roadmap

- Interactive Knowledge Graph Visualization
- Multi-language Repository Support
- Incremental Repository Indexing
- Graph-aware Re-ranking
- Multi-repository Workspace
- Authentication & User Management
- Repository Versioning
- Evaluation Dashboard
- Prometheus & Grafana Monitoring
- Kubernetes Deployment
- Distributed Celery Workers
- Intelligent Code Review Agent
- Automated Documentation Generation

---

# 🤝 Contributing

Contributions are welcome!

If you'd like to improve CodeGraphAI:

1. Fork the repository.
2. Create a feature branch.

```bash
git checkout -b feature/my-feature
```

3. Commit your changes.

```bash
git commit -m "Add my feature"
```

4. Push to your fork.

```bash
git push origin feature/my-feature
```

5. Open a Pull Request.

---

# 📄 License

This project is licensed under the MIT License.

---

# ⭐ Acknowledgements

This project leverages several excellent open-source technologies:

- FastAPI
- React
- Tree-sitter
- LangChain
- HuggingFace
- Groq
- Qdrant
- Celery
- Redis
- Docker

---

# 🌟 Why CodeGraphAI?

Understanding large codebases is one of the biggest challenges in software engineering. Traditional code search tools rely primarily on keyword matching or vector similarity, often missing the structural relationships that define how software works.

CodeGraphAI addresses this by combining **semantic code analysis**, **knowledge graphs**, and **hybrid GraphRAG retrieval** to deliver context-aware, source-grounded answers. Rather than treating code as plain text, it models the repository as a graph of interconnected symbols and uses that structure during retrieval.

The project is built with production-oriented engineering practices—including asynchronous indexing, containerized deployment, modular architecture, and scalable service orchestration—making it both a practical developer tool and a demonstration of modern AI system design.
