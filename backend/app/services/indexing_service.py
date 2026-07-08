"""
Purpose:
Coordinates the complete repository indexing pipeline defensively.

Responsibilities:
* Clones Python source repositories from GitHub.
* Traverses directories to parse Python files, capturing parser limits gracefully.
* Drives AST code chunk extraction.
* Orchestrates embedding generation and Qdrant vector storage.
* Builds resilient structural and caller-callee relationship knowledge graphs.
* Generates static O(1) query indexes.

Failure handling:
* Wraps indexing pipeline stages in error boundaries.
* Gathers comprehensive statistics for both resolved and unresolved references.
* Propagates transient infrastructure errors (like network/Qdrant issues) for retries, while absorbing deterministic parsing issues.

Inputs:
* GitHub repo URL, unique repo tenant ID, and target path coordinates.

Outputs:
* Ingestion metrics summary containing resolution percentages and counts.

Interaction with other modules:
* Drives repository clones via `github_loader.py`.
* Builds graphs via `code_graph.py` and indexes via `repository_indexer.py`.
* Performs collection embeddings via `embeddings.py` and uploads via `vector_store.py`.
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
    """
    # 1. Parse URL to generate repository identifier and target path
    url_parts = repo_url.rstrip("/").split("/")
    owner_repo = "_".join(url_parts[-2:])
    active_repo_id = repo_id if repo_id else owner_repo
    active_repo_path = repository_path if repository_path else os.path.join("repositories", active_repo_id)

    logger.info(f"[Indexing] Starting resilient pipeline for {repo_url} (ID: {active_repo_id})")

    # 2. Clone GitHub repository (transient error propagation)
    clone_repository(repo_url, target_path=active_repo_path)
    if progress_callback:
        progress_callback(10, "Repository cloned")

    # 3. Parse repository (defensively wrapped)
    docs = []
    try:
        docs = parse_repository(active_repo_path)
    except Exception as e:
        logger.error(f"[Defensive] Repository parsing stage failed: {e}")
    if progress_callback:
        progress_callback(25, "Repository parsed")

    # 4. Create code chunks using AST chunker (defensively wrapped)
    chunks = []
    try:
        chunks = create_code_chunks(active_repo_path)
    except Exception as e:
        logger.error(f"[Defensive] AST chunking generation stage failed: {e}")
    if progress_callback:
        progress_callback(40, "AST generated")

    # 5. Build and save the Knowledge Graph (defensively wrapped)
    graph = None
    try:
        graph = build_repository_graph(active_repo_path)
        # Save tenant-specific graph representation
        save_graph(graph, graph_name=f"{active_repo_id}_graph.json")
        save_graph(graph, graph_name="active_graph.json")
    except Exception as e:
        logger.error(f"[Defensive] Graph construction stage failed: {e}")
        # Build empty fallback graph
        graph = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "repository": active_repo_id,
                "node_count": 0,
                "edge_count": 0,
                "additional_info": {
                    "files_parsed": len(docs),
                    "symbols_discovered": 0,
                    "relationships_extracted": 0,
                    "resolved_references": 0,
                    "unresolved_references": 0,
                    "resolution_percentage": 100.0,
                    "top_unresolved_modules": [],
                    "unresolved_logs": []
                }
            }
        }
    
    if progress_callback:
        progress_callback(60, "Knowledge graph generated")

    # 6. Generate embeddings and index in Qdrant (transient error propagation)
    indexed_count = 0
    if chunks:
        texts = [chunk["text"] for chunk in chunks]
        vectors = embedding_model.embed_documents(texts)
        if progress_callback:
            progress_callback(80, "Embeddings generated")
        
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

    # 7. Build and save structural index (defensively wrapped)
    try:
        build_structural_index(active_repo_path, output_file_path=f"graphs/{active_repo_id}_structural_index.json")
        build_structural_index(active_repo_path, output_file_path="graphs/structural_index.json")
    except Exception as e:
        logger.error(f"[Defensive] Structural indexing stage failed: {e}")

    if progress_callback:
        progress_callback(100, "Completed")

    info = graph.get("metadata", {}).get("additional_info", {})
    
    # Calculate skipped/unvalidated edge counts
    total_extracted_edges = info.get("relationships_extracted", 0)
    graph_edges = len(graph.get("edges", []))
    skipped_edges = max(total_extracted_edges - graph_edges, 0)

    summary = {
        "success": True,
        "repository": active_repo_id,
        "files_parsed": info.get("files_parsed", len(docs)),
        "symbols_discovered": info.get("symbols_discovered", 0),
        "relationships_extracted": total_extracted_edges,
        "resolved_references": info.get("resolved_references", 0),
        "unresolved_references": info.get("unresolved_references", 0),
        "resolution_percentage": info.get("resolution_percentage", 100.0),
        "graph_nodes": len(graph.get("nodes", [])),
        "graph_edges": graph_edges,
        "skipped_edges": skipped_edges
    }
    
    logger.info(f"[Indexing] Pipeline execution complete for {repo_url}. Summary: {summary}")
    return summary
