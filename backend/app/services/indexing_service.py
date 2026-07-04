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

Interaction with other modules:
* Reads vector configurations from `vector_store.py`.
* Uses `github_loader.py` to clone repository.
* Uses `parser.py` and `code_chunker.py` to parse AST nodes.
* Computes vector mappings via `embeddings.py`.
* Builds graphs via `code_graph.py` and indexes via `repository_indexer.py`.

How it contributes to the production architecture:
Acts as the central transaction coordinator for codebase ingestion. It supports dynamic path injection,
progress callbacks, and is ready for PostgreSQL database bindings.
"""

import logging
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

logger = logging.getLogger("codegraphai.indexing_service")


def index_repository(
    repo_url: str,
    repo_id: str = None,
    repository_path: str = None,
    progress_callback = None
) -> dict:
    """
    Coordinates repository cloning, parsing, code chunking, vector embedding generation,
    Qdrant upload, knowledge graph construction, and structural indexing.

    Parameters:
        repo_url (str): The public GitHub URL of the repository.
        repo_id (str, optional): A unique identifier for the repository. Defaults to owner/repo slug.
        repository_path (str, optional): Directory path where the repository should be cloned.
        progress_callback (callable, optional): Callback function to update progress state.

    Returns:
        dict: Ingestion metrics summary containing counts of files, chunks, nodes, and edges indexed.

    Execution Flow:
        1. Resolve repo_id (owner_repo slug) and repository_path (repositories/{repo_id}).
        2. Clone repository to repository_path -> Update progress to 10%
        3. Parse Python files -> Update progress to 25%
        4. Extract code chunks -> Update progress to 40%
        5. Build and save the Knowledge Graph -> Update progress to 60%
        6. Generate embeddings using HuggingFace -> Update progress to 80%
        7. Clear and store chunks in Qdrant collections -> Update progress to 95%
        8. Build structural index -> Update progress to 100%
        9. Return consolidated metrics summary.
    """
    # 1. Parse URL to generate repository identifier and target filesystem path
    url_parts = repo_url.rstrip("/").split("/")
    owner_repo = "_".join(url_parts[-2:])
    active_repo_id = repo_id if repo_id else owner_repo
    active_repo_path = repository_path if repository_path else os.path.join("repositories", active_repo_id)

    logger.info(f"[Indexing] Starting pipeline for {repo_url} (ID: {active_repo_id})")

    # 2. Clone GitHub repository
    clone_repository(repo_url, target_path=active_repo_path)
    if progress_callback:
        progress_callback(10, "Repository cloned")

    # 3. Parse repository
    docs = parse_repository(active_repo_path)
    if progress_callback:
        progress_callback(25, "Repository parsed")

    # 4. Create code chunks using AST chunker
    chunks = create_code_chunks(active_repo_path)
    if progress_callback:
        progress_callback(40, "AST generated")

    # 5. Build and save the Knowledge Graph
    graph = build_repository_graph(active_repo_path)
    # Save tenant-specific graph representation
    save_graph(graph, graph_name=f"{active_repo_id}_graph.json")
    # Save default fallback for backwards-compatible single-tenant mode
    save_graph(graph, graph_name="active_graph.json")
    
    if progress_callback:
        progress_callback(60, "Knowledge graph generated")

    # 6. Generate embeddings and index in Qdrant
    indexed_count = 0
    if chunks:
        texts = [chunk["text"] for chunk in chunks]
        vectors = embedding_model.embed_documents(texts)
        if progress_callback:
            progress_callback(80, "Embeddings generated")
        
        # We index both into the tenant-specific collection and default collection
        target_collections = [f"repo_{active_repo_id}", COLLECTION_NAME]
        
        for col_name in target_collections:
            try:
                client.delete_collection(collection_name=col_name)
            except Exception:
                pass
            create_collection(len(vectors[0]), collection_name=col_name)
            store_chunks(chunks, vectors, collection_name=col_name)
            
        indexed_count = len(vectors)
        if progress_callback:
            progress_callback(95, "Vectors stored")
    else:
        logger.warning(f"[Indexing] No chunks found to embed for repository {active_repo_id}")
        if progress_callback:
            progress_callback(80, "Embeddings generated")
            progress_callback(95, "Vectors stored")

    # 7. Build and save the structural index
    # Save tenant-specific structural index
    build_structural_index(active_repo_path, output_file_path=f"graphs/{active_repo_id}_structural_index.json")
    # Save default fallback for single-tenant mode
    build_structural_index(active_repo_path, output_file_path="graphs/structural_index.json")

    if progress_callback:
        progress_callback(100, "Completed")

    summary = {
        "success": True,
        "repository": active_repo_id,
        "documents": len(docs),
        "chunks": len(chunks),
        "indexed": indexed_count,
        "graph_nodes": len(graph["nodes"]),
        "graph_edges": len(graph["edges"])
    }
    logger.info(f"[Indexing] Pipeline execution complete for {repo_url}. Summary: {summary}")
    return summary
