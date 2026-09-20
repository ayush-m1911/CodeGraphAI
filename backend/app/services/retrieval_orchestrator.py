"""
Purpose:
Implements a staged, intent-aware retrieval orchestrator mapping codebase knowledge graphs to query contexts.

Responsibilities:
* Detect query intent (Definition, Architecture, Call Flow, Implementation, Dependencies, Configuration, Comparison, Error Analysis).
* Extract symbol entities from the natural language question.
* Resolve extracted raw names to qualified repository FQNs in the symbol table.
* Traverse semantic caller-callee graphs recursively (relation-aware, depth-configurable, cycle-free).
* Fetch vector similarities from the Qdrant collections.
* Merge, deduplicate, rank, and consolidate code chunks for LLM context injection.

Inputs:
* User query question string and configuration parameters.

Outputs:
* Consolidated context blocks tuple (context, intent, strategies_used, confidence).

Interaction with other modules:
* Retrieves structures via `graph_retriever.py`, queries files via `repository_search.py`,
  searches collections via `retriever.py`, and drives response generation inside `chat.py`.
"""

import re
import logging
from typing import List, Tuple, Dict

from app.services.symbol_retriever import find_symbol_chunks
from app.services.retriever import retrieve_context
from app.services.graph_retriever import load_graph, get_neighbors
from app.services.repository_search import search_symbols

logger = logging.getLogger("CodeGraphAI.Orchestrator")


def detect_intent(question: str) -> str:
    """
    Stage 1: Classifies user queries into semantic intent profiles using keyword heuristics.
    """
    q = question.lower()
    
    # 1. Comparison
    if any(k in q for k in ["compare", "versus", "vs", "difference between", "contrasted with"]):
        return "Comparison"
        
    # 2. Error Analysis
    if any(k in q for k in ["error", "exception", "raises", "try", "except", "traceback", "failed", "bug", "issue", "crash"]):
        return "Error Analysis"
        
    # 3. Configuration
    if any(k in q for k in ["config", "settings", "setup", "env", "docker", "celery", "redis", "qdrant"]):
        return "Configuration"
        
    # 4. Call Flow
    if any(k in q for k in ["call flow", "trace", "lifecycle", "execution flow", "calls", "calling", "flow of", "invoke"]):
        return "Call Flow"
        
    # 5. Dependencies
    if any(k in q for k in ["depends on", "who calls", "which classes use", "used by", "caller of", "calls of", "imports", "import"]):
        return "Dependencies"
        
    # 6. Architecture
    if any(k in q for k in ["architecture", "relationship", "interact", "registered", "registration", "structure", "design", "interaction"]):
        return "Architecture"
        
    # 7. Definition
    if any(k in q for k in ["defined", "definition", "implemented", "located", "where is", "show class"]):
        return "Definition"
        
    # 8. Implementation
    if any(k in q for k in ["how do i", "how to", "implementation", "write", "create", "build", "code for"]):
        return "Implementation"
        
    # Fallback to Definition for explaining terms
    return "Definition"


def extract_entities(question: str) -> List[str]:
    """
    Stage 2: Identifies token sequences matching identifier and class/method/variable patterns.
    """
    # Extract identifiers including camelCase, snake_case, or dotted FQNs
    words = re.findall(r"\b[A-Za-z0-9_\.\-/]+\b", question)
    entities = []
    
    stop_words = {
        "what", "where", "how", "who", "find", "locate", "search", "explain",
        "defined", "the", "and", "class", "function", "method", "variable",
        "work", "calls", "trace", "lifecycle", "error", "exception", "raises"
    }
    
    for w in words:
        if len(w) >= 3 and w.lower() not in stop_words:
            entities.append(w)
            
    return entities


def resolve_symbols(entities: List[str], symbol_table: Dict[str, dict]) -> List[str]:
    """
    Stage 3: Maps raw identifier names to qualified repository symbol names in the graph.
    """
    resolved = []
    for ent in entities:
        # 1. Exact match
        if ent in symbol_table:
            resolved.append(ent)
            continue
            
        # 2. Check suffix (ends with .ent)
        matches = []
        for fqn in symbol_table:
            if fqn.endswith(f".{ent}"):
                matches.append(fqn)
                
        if len(matches) == 1:
            resolved.append(matches[0])
        elif matches:
            resolved.extend(matches[:3])
            
    return list(set(resolved))


def traverse_graph(
    start_symbols: List[str],
    graph: dict,
    max_depth: int = 2,
    allowed_relations: List[str] = None
) -> Tuple[List[dict], List[dict], Dict[str, int]]:
    """
    Stage 4: Performs relation-aware depth-limited traversal starting from resolved symbols,
    safely preventing cycles and duplicate node accumulation. Returns node mappings and distance levels.
    """
    retrieved_edges = []
    visited = set()
    graph_distances = {}
    
    queue = [(sym, 0) for sym in start_symbols]
    for sym in start_symbols:
        visited.add(sym)
        graph_distances[sym] = 0
        
    while queue:
        curr, depth = queue.pop(0)
        if depth >= max_depth:
            continue
            
        for edge in graph.get("edges", []):
            if allowed_relations and edge["relation"] not in allowed_relations:
                continue
                
            # Traverse outgoing
            if edge["source"] == curr:
                target = edge["target"]
                retrieved_edges.append(edge)
                if target not in visited:
                    visited.add(target)
                    graph_distances[target] = depth + 1
                    queue.append((target, depth + 1))
                    
            # Traverse incoming
            elif edge["target"] == curr:
                source = edge["source"]
                retrieved_edges.append(edge)
                if source not in visited:
                    visited.add(source)
                    graph_distances[source] = depth + 1
                    queue.append((source, depth + 1))
                    
    retrieved_nodes = []
    for node in graph.get("nodes", []):
        if node["id"] in visited:
            retrieved_nodes.append(node)
            
    return retrieved_nodes, retrieved_edges, graph_distances


class RetrievalOrchestrator:
    """
    Staged query context coordinator implementing intent routing and graph expansions.
    """
    
    def orchestrate(
        self,
        question: str,
        user_id: str = None,
        repository_id: str = None,
        max_context_size: int = 12
    ) -> Tuple[List[dict], str, List[str], float]:
        """
        Executes the multi-stage, intent-aware retrieval pipeline with multi-tenant filtering.
        """
        strategies_used = []
        
        # 1. Intent Detection
        intent = detect_intent(question)
        strategies_used.append(f"Intent Routing ({intent})")
        
        # 2. Entity Extraction
        entities = extract_entities(question)
        if entities:
            strategies_used.append("Entity Extraction")
            
        # 3. Symbol Resolution
        graph = load_graph()
        symbol_table = {}
        for node in graph.get("nodes", []):
            if node.get("node_type") in ("class", "method", "function", "variable"):
                symbol_table[node["id"]] = node
                
        resolved_symbols = resolve_symbols(entities, symbol_table)
        if resolved_symbols:
            strategies_used.append("Symbol Resolution")

        # 4. Graph Expansion (Relation-Aware & Cycle-Free)
        allowed_relations = None
        if intent == "Call Flow":
            allowed_relations = ["calls", "instantiates", "returns"]
        elif intent == "Dependencies":
            allowed_relations = ["imports", "inherits", "calls"]
        elif intent == "Architecture":
            allowed_relations = ["contains", "defines", "inherits", "imports"]
        elif intent == "Error Analysis":
            allowed_relations = ["raises", "calls", "references"]

        traversed_nodes, traversed_edges, graph_distances = traverse_graph(
            resolved_symbols, graph, max_depth=2, allowed_relations=allowed_relations
        )
        
        graph_chunks = []
        if traversed_nodes:
            strategies_used.append("Graph Expansion")
            for node in traversed_nodes:
                if node.get("node_type") in ("repository", "package"):
                    continue
                # Fetch original source block text dynamically
                symbol_results = search_symbols(node["id"])
                if symbol_results:
                    chunk = dict(symbol_results[0])
                    chunk["score"] = "graph"
                    # Attach node hierarchy properties to chunk for scoring
                    chunk["hierarchy_depth"] = node.get("hierarchy_depth", 3)
                    chunk["node_type"] = node.get("node_type")
                    
                    # Attach relation context
                    for edge in traversed_edges:
                        if edge["target"] == node["id"]:
                            chunk["relation"] = edge["relation"]
                            chunk["graph_source"] = edge["source"]
                            break
                    graph_chunks.append(chunk)

        # 5. Vector Retrieval with Tenant Isolation
        strategies_used.append("Vector Retrieval")
        vector_chunks = retrieve_context(
            question,
            top_k=4,
            user_id=user_id,
            repository_id=repository_id
        )

        # 6. Context Merge
        merged_chunks = []
        merged_chunks.extend(vector_chunks)
        merged_chunks.extend(graph_chunks)

        # 7. Deduplication & Score Calculation
        from app.services.ranking_engine import ScoringEngine, merge_overlapping_chunks
        scoring_engine = ScoringEngine()
        metadata = {"graph_distances": graph_distances}
        
        deduped_chunks = []
        seen = set()
        for chunk in merged_chunks:
            chunk["ranking_score"] = scoring_engine.compute_composite_score(chunk, question, intent, metadata)
            
            key = (chunk.get("file_path"), chunk.get("symbol_name"), chunk.get("relation"))
            if key not in seen:
                seen.add(key)
                deduped_chunks.append(chunk)

        # 8. Merge Overlapping Chunks
        merged_contexts = merge_overlapping_chunks(deduped_chunks)
        strategies_used.append("Context Merging")

        # 9. Sort by ranking score
        merged_contexts.sort(key=lambda x: x.get("ranking_score", 0.0), reverse=True)
        final_context = merged_contexts[:max_context_size]
        
        # Confidence calculation
        confidence = 0.95 if resolved_symbols else 0.70
        
        # Log metrics trace
        print(f"\nStaged Orchestrator Logs:")
        print(f"  Detected Intent: {intent}")
        print(f"  Entities Extracted: {entities}")
        print(f"  Resolved Symbols: {resolved_symbols}")
        print(f"  Merged size: {len(deduped_chunks)} -> Final context: {len(final_context)} chunks")
        
        return final_context, intent, strategies_used, confidence

