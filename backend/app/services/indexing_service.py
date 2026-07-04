"""
Purpose:
Coordinates the complete repository indexing pipeline.

Responsibilities:
* Clones Python source repositories from GitHub.
* Traverses directories to parse Python files.
* Drives AST code chunk extraction.
* Orchestrates embedding generation and Qdrant vector storage.
* Builds structural and caller-callee relationship knowledge graphs.
* Generates static O(1) query indexes.

How it fits into the overall pipeline:
Serves as the service layer that orchestrates backend ingestion. It isolates API routing logic from
the actual work of parsing, chunking, and database uploads, allowing indexing to later be run inside
background queues (e.g. Celery workers) or CLI loaders.
"""

import os
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
from app.services.repository_indexer import build_structural_index


def index_repository(repo_url: str, repo_id: str = None) -> dict:
    """
    Coordinates repository cloning, parsing, code chunking, vector embedding generation,
    Qdrant upload, knowledge graph construction, and structural indexing.

    Inputs:
        repo_url (str): The public GitHub URL of the repository.
        repo_id (str, optional): A unique identifier for the repository. Defaults to extracting owner/repo from URL.

    Outputs:
        dict: Ingestion metrics summary containing counts of files, chunks, nodes, and edges indexed.

    Responsibilities:
        1. Parse URL to generate repository identifier.
        2. Clone repository from GitHub to local backend filesystem.
        3. Parse directories to collect Python documents.
        4. Extract logical AST code chunks from Python files.
        5. Generate vector embeddings and store chunks in Qdrant collection.
        6. Traverse code syntax to construct containment and semantic call graphs.
        7. Generate structural O(1) navigation indexes.
        8. Return consolidated metrics summary.
    """
    # 1. Parse URL to generate repository identifier
    url_parts = repo_url.rstrip("/").split("/")
    repo_identifier = repo_id if repo_id else "/".join(url_parts[-2:])

    print("Starting clone...")
    # 2. Clone GitHub repository
    repo_path = clone_repository(repo_url)
    print("Clone completed.")

    # 3. Parse repository
    docs = parse_repository(repo_path)
    print("Repository parsed.")

    # 4. Create code chunks using AST chunker
    chunks = create_code_chunks(repo_path)
    print("Chunks created.")

    # 5. Generate embeddings and index in Qdrant
    indexed_count = 0
    if chunks:
        print("Embeddings generated.")
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
        print("Embeddings generated.")
        print("Qdrant indexing completed.")

    # 6. Build and save the Knowledge Graph as active_graph.json
    graph = build_repository_graph(repo_path)
    save_graph(graph, graph_name="active_graph.json")
    print("Graph generation completed.")

    # 7. Build and save the structural index
    build_structural_index(repo_path)
    print("Structural index generation completed.")

    return {
        "success": True,
        "repository": repo_identifier,
        "documents": len(docs),
        "chunks": len(chunks),
        "indexed": indexed_count,
        "graph_nodes": len(graph["nodes"]),
        "graph_edges": len(graph["edges"])
    }
