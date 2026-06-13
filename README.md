Here is the complete content for the **CodeGraphAI** `README.md` file. It covers what the project does, the technical architecture, and step-by-step local setup instructions.

***

# CodeGraphAI ⚡

**CodeGraphAI** is a premium, production-quality **GraphRAG-powered repository intelligence assistant** designed to help developers inspect, navigate, and chat with Python codebases. By combining Abstract Syntax Tree (AST) code slicing, semantic vector search, exact symbol lookups, and a dynamically constructed knowledge graph of relationships (e.g. calls, containment, references), it provides source-grounded answers with architectural context.

The user interface features a high-end, responsive **Matte Black + Metallic Gold** SaaS aesthetic similar to tools like Linear, Perplexity, and Cursor.

---

## Key Features

1. **Dynamic Repository Ingestion**: Input any public Python GitHub repository URL. The backend dynamically clones, cleanses, and prepares the code for analysis.
2. **AST-Aware Chunking**: Uses a parser to chunk files logically around class, method, and function boundaries rather than using arbitrary line or character limits.
3. **Local Vector Embeddings & Indexing**: Generates dense vectors using the HuggingFace `BAAI/bge-small-en-v1.5` model, stored inside a local vector database.
4. **Knowledge Graph Construction**: Evaluates containment structures and function call flows to construct a local relationship network graph.
5. **Hybrid Retrieval (GraphRAG)**: Merges semantic vector matches, exact symbol lookups, and graph neighborhood expansions to create a comprehensive prompt context.
6. **Chat Workspace & Timelines**: A triple-pane interface featuring markdown renders, copyable code snippets, expandable source attributions with raw chunks, and an animated timeline visualizing the GraphRAG connection stack.
7. **Interactive Architecture Visualizer**: An animated structural overlay highlighting the data ingest-to-synthesis pipeline.

---

## Technical Stack

* **Frontend**: React (Vite), Tailwind CSS (v4), Framer Motion, Axios, React Icons, React Markdown
* **Backend**: FastAPI, Python, Uvicorn, LangChain (HuggingFace Embeddings), Qdrant Client, Groq LLM API
* **Vector Store**: Qdrant (with automatic persistent local file fallback if no external server is running)
* **LLM**: Groq (`llama-3.3-70b-versatile`) with context-grounded fallback responses if API limits are hit.

---

## Local Setup & Ingestion Guide

### Prerequisites
* **Git CLI** (installed and added to your system `PATH`)
* **Python 3.10+**
* **Node.js 18+** & **npm**

---

### 1. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   * **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Ensure packages like `fastapi`, `uvicorn`, `qdrant-client`, `langchain-huggingface`, `groq`, and `gitpython` are installed.)*

4. **Configure Environment Variables**:
   Create a `.env` file in the `backend/` directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   QDRANT_URL=http://localhost:6333
   COLLECTION_NAME=repo_chunks
   ```
   *Note: If no Qdrant server is running on `http://localhost:6333`, the backend automatically falls back to local disk-based persistence (`qdrant_storage/` folder), so Docker/Qdrant servers are optional.*

5. **Start the FastAPI Backend**:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
   The API will be available at `http://localhost:8000`.

---

### 2. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite Dev Server**:
   ```bash
   npm run dev
   ```
   The React interface will be hosted on `http://localhost:5173`.

---

## How to Use CodeGraphAI

1. Open `http://localhost:5173` in your browser.
2. Click **Analyze Repository** from the home screen.
3. On the setup page, either click **Load FastAPI Demo** or enter your own public GitHub repository URL (e.g. `https://github.com/tiangolo/fastapi`) and click **Analyze**.
4. Watch the progress stepper clone the repository and index it into your local storage vectors and knowledge graph.
5. Once complete, click **Enter Chat Workspace**.
6. Type questions in the chat feed (e.g., *"How does APIRouter work?"*).
7. Review responses:
   * **Main Area**: Reads markdown answers compiled using hybrid GraphRAG context.
   * **Sources**: Click the cards at the bottom of the answer to expand and inspect the exact code snippet context.
   * **GraphRAG Connections**: Click the **GraphRAG** button on the right to slide open the relationship connectors and timeline flow.
   * **Architecture**: Click the **Architecture** navigation link in the top bar to inspect the system flow diagrams.
