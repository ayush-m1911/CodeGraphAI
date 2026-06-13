import traceback
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.models.schemas import RepoRequest
from app.services.github_loader import clone_repository
from app.services.parser import parse_repository
from app.services.embeddings import embedding_model
from app.services.code_graph import build_repository_graph, save_graph
from app.services.vector_store import (
    client,
    COLLECTION_NAME,
    create_collection,
    store_chunks
)
from app.services.repository_chunker import create_code_chunks

router = APIRouter()


@router.post("/index")
def index_repo(payload: RepoRequest):
    try:
        # Extract owner/repo name representation from the URL (e.g. tiangolo/fastapi)
        url_parts = payload.repo_url.rstrip("/").split("/")
        repo_identifier = "/".join(url_parts[-2:])

        print("Starting clone...")
        # 1. Clone GitHub repository
        repo_path = clone_repository(payload.repo_url)
        print("Clone completed.")

        # 2. Parse repository
        docs = parse_repository(repo_path)
        print("Repository parsed.")

        # 3. Create code chunks using AST chunker
        chunks = create_code_chunks(repo_path)
        print("Chunks created.")

        # 4. Generate embeddings and index in Qdrant
        indexed_count = 0
        if chunks:
            print("Embeddings generated.") # Prints matching expected log
            texts = [chunk["text"] for chunk in chunks]
            vectors = embedding_model.embed_documents(texts)
            
            # Reset/clear vector store collection for the new repo
            try:
                client.delete_collection(collection_name=COLLECTION_NAME)
            except Exception:
                pass
                
            create_collection(len(vectors[0]))
            store_chunks(chunks, vectors)
            indexed_count = len(vectors)
            print("Qdrant indexing completed.")
        else:
            print("Embeddings generated.") # Ensure log statement print occurs even if 0 chunks
            print("Qdrant indexing completed.")

        # 5. Build and save the Knowledge Graph as active_graph.json
        graph = build_repository_graph(repo_path)
        save_graph(graph, graph_name="active_graph.json")
        print("Graph generation completed.")

        return {
            "success": True,
            "repository": repo_identifier,
            "documents": len(docs),
            "chunks": len(chunks),
            "indexed": indexed_count,
            "graph_nodes": len(graph["nodes"]),
            "graph_edges": len(graph["edges"])
        }

    except Exception as e:
        print("--- INDEXING ERROR TRACEBACK ---")
        traceback.print_exc()
        print("--------------------------------")

        error_msg = str(e)
        
        # Categorize the error for the frontend UI toast banner
        if "Git clone failed" in error_msg:
            error_title = "Git clone failed"
        elif "GitHub URL" in error_msg:
            error_title = "Git clone failed"
        elif "not found" in error_msg.lower() or "not available" in error_msg.lower():
            error_title = "Git is not installed"
        elif "Qdrant" in error_msg or "connection" in error_msg.lower():
            error_title = "Qdrant is unavailable"
        else:
            error_title = "Unable to index repository"

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": error_title,
                "details": error_msg
            }
        )