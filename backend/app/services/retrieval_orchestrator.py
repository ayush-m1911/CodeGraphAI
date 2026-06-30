"""
Purpose:
Implements the Intent-Aware Retrieval Orchestrator for CodeGraphAI.

Role in CodeGraphAI:
Replaces the static retrieval pipeline with a dynamic, intent-aware routing system.
It classifies user questions, invokes specialized retrieval strategies (including O(1)
structural index lookups), merges and ranks the contexts, and returns a high-quality consolidated context payload to the LLM.

Key Responsibilities:
* Classify user questions into 9 distinct intents: FILE_LOOKUP, IMPORT_LOOKUP, DECORATOR_LOOKUP, KEYWORD_SEARCH, SYMBOL_LOOKUP, CALL_FLOW, ARCHITECTURE, DEPENDENCY, GENERAL.
* Define and execute modular retrieval strategies (FileLookupStrategy, ImportLookupStrategy, etc.).
* Merge, deduplicate, and rank retrieved chunks using a semantic scoring algorithm.
* Provide detailed logging of the orchestration execution.
"""

import re
import logging
from abc import ABC, abstractmethod

from app.services.symbol_retriever import find_symbol_chunks
from app.services.retriever import retrieve_context
from app.services.graph_retriever import load_graph, get_neighbors
from app.services.graph_context_builder import build_graph_context
from app.services.repository_search import (
    search_symbols,
    search_files,
    search_decorators,
    search_imports,
    search_classes,
    search_functions,
    search_string
)

logger = logging.getLogger("CodeGraphAI.Orchestrator")


def detect_intent(question: str) -> str:
    """
    Analyzes the user's question using keyword heuristics to classify the query intent.
    """
    q = question.lower()
    
    # 1. DECORATOR_LOOKUP (e.g. "Find @app.post", "Locate @router.get")
    if "@" in q:
        return "DECORATOR_LOOKUP"
        
    # 2. FILE_LOOKUP (e.g. "Where is backend.py?", "Find routing.py")
    if ".py" in q or "file" in q:
        # Avoid false positives for general questions that happen to contain the word "file"
        if any(k in q for k in ["where is", "find", "locate", "which file", "what file"]):
            return "FILE_LOOKUP"
            
    # 3. IMPORT_LOOKUP (e.g. "Where is streamlit imported?", "Who imports os?")
    if any(k in q for k in ["import", "imports", "imported"]):
        if any(k in q for k in ["who", "where", "which", "what"]):
            return "IMPORT_LOOKUP"
            
    # 4. KEYWORD_SEARCH (e.g. "Search for ChatGroq", "Search for dotenv")
    if any(k in q for k in ["search for", "find keyword", "contains string", "contains keyword"]):
        return "KEYWORD_SEARCH"
        
    # 5. DEPENDENCY
    # e.g., "what depends on APIRouter", "who calls add_api_route", "which classes use Depends"
    if any(k in q for k in ["depends on", "who calls", "which classes use", "where is ... used", "used by", "caller of", "calls of"]):
        if "where is" in q and any(k in q for k in ["defined", "implemented", "located"]):
            pass
        else:
            return "DEPENDENCY"
            
    # 6. CALL_FLOW
    # e.g., "How does APIRouter.get work?", "What methods does APIRouter.get call?", "trace request lifecycle"
    if any(k in q for k in ["call flow", "trace", "lifecycle", "execution flow", "calls", "calling", "flow of", "call"]):
        return "CALL_FLOW"
    if "how does" in q and not any(topic in q for topic in ["routing", "auth", "authentication", "connection", "database", "db"]):
        return "CALL_FLOW"
        
    # 7. ARCHITECTURE
    # e.g., "How are routes registered?", "How does dependency injection work?", "How do APIRouter and FastAPI interact?"
    if any(k in q for k in ["architecture", "relationship", "interact", "registered", "registration", "structure", "design", "interaction", "dependency injection"]):
        return "ARCHITECTURE"
        
    # 8. SYMBOL_LOOKUP
    # e.g., "Explain APIRouter", "Where is APIRouter defined?", "Show FastAPI class"
    if any(k in q for k in ["defined", "definition", "implemented", "located", "show class", "where is"]):
        return "SYMBOL_LOOKUP"
    if "explain" in q:
        if any(topic in q for topic in ["routing", "auth", "authentication", "connection", "flow", "architecture", "database"]):
            return "GENERAL"
        return "SYMBOL_LOOKUP"
        
    # 9. GENERAL (Fallback)
    return "GENERAL"


def extract_query_term(intent: str, question: str) -> str:
    """
    Extracts the core search term from the question based on the detected intent.
    """
    q = question.lower()
    words = re.findall(r"\b[A-Za-z0-9_\.\-\/]+\b", question)
    
    if intent == "FILE_LOOKUP":
        for w in words:
            if w.endswith(".py"):
                return w
        match = re.search(r"(?:find|locate|where is|file)\s+([A-Za-z0-9_\.\-\/]+)", q)
        if match:
            return match.group(1)
            
    elif intent == "IMPORT_LOOKUP":
        match = re.search(r"imports?\s+([A-Za-z0-9_\.]+)", q)
        if match:
            return match.group(1)
        match = re.search(r"([A-Za-z0-9_\.]+)\s+imported", q)
        if match:
            return match.group(1)
            
    elif intent == "DECORATOR_LOOKUP":
        match = re.search(r"@[A-Za-z0-9_\.\/]+(?:\(\)?)?", question)
        if match:
            return match.group(0)
            
    elif intent == "KEYWORD_SEARCH":
        match = re.search(r"(?:search for|keyword|string)\s+([A-Za-z0-9_\.\-]+)", q)
        if match:
            start_idx = question.lower().find(match.group(1))
            if start_idx != -1:
                return question[start_idx:start_idx + len(match.group(1))]
            return match.group(1)
            
    # Fallback: find first word that is not a question word or common verb
    for w in words:
        if len(w) >= 3 and w.lower() not in ("what", "where", "how", "who", "find", "locate", "search", "explain", "defined"):
            # Return original case for symbols
            start_idx = question.lower().find(w.lower())
            if start_idx != -1:
                return question[start_idx:start_idx + len(w)]
            return w
    return question


class BaseRetrievalStrategy(ABC):
    """
    Abstract base class for all retrieval strategies.
    """
    @abstractmethod
    def retrieve(self, question: str) -> dict:
        pass


class FileLookupStrategy(BaseRetrievalStrategy):
    """
    Strategy optimized for locating files. Maps directly to the File Index.
    """
    def retrieve(self, question: str) -> dict:
        term = extract_query_term("FILE_LOOKUP", question)
        results = search_files(term)
        return {
            "chunks": results,
            "graph_context": [],
            "strategies_used": ["File Index"],
            "confidence": 0.99 if results else 0.2
        }


class ImportLookupStrategy(BaseRetrievalStrategy):
    """
    Strategy optimized for identifying imports. Maps directly to the Import Index.
    """
    def retrieve(self, question: str) -> dict:
        term = extract_query_term("IMPORT_LOOKUP", question)
        results = search_imports(term)
        return {
            "chunks": results,
            "graph_context": [],
            "strategies_used": ["Import Index"],
            "confidence": 0.99 if results else 0.2
        }


class DecoratorLookupStrategy(BaseRetrievalStrategy):
    """
    Strategy optimized for identifying decorators. Maps directly to the Decorator Index.
    """
    def retrieve(self, question: str) -> dict:
        term = extract_query_term("DECORATOR_LOOKUP", question)
        results = search_decorators(term)
        return {
            "chunks": results,
            "graph_context": [],
            "strategies_used": ["Decorator Index"],
            "confidence": 0.99 if results else 0.2
        }


class KeywordSearchStrategy(BaseRetrievalStrategy):
    """
    Strategy optimized for finding raw strings/keywords across the codebase.
    """
    def retrieve(self, question: str) -> dict:
        term = extract_query_term("KEYWORD_SEARCH", question)
        results = search_string(term)
        return {
            "chunks": results,
            "graph_context": [],
            "strategies_used": ["Repository Search"],
            "confidence": 0.9 if results else 0.1
        }


class SymbolLookupStrategy(BaseRetrievalStrategy):
    """
    Strategy optimized for symbol definitions. Maps directly to the Symbol Index.
    """
    def retrieve(self, question: str) -> dict:
        term = extract_query_term("SYMBOL_LOOKUP", question)
        results = search_symbols(term)
        
        # Enforce exact symbol retrieval and fallback to vector search if index is empty
        strategies_used = ["Symbol Index"]
        if not results:
            strategies_used.append("Vector Search (Fallback)")
            results = retrieve_context(question, top_k=2)
            
        return {
            "chunks": results,
            "graph_context": [],
            "strategies_used": strategies_used,
            "confidence": 0.95 if results else 0.1
        }


class CallFlowStrategy(BaseRetrievalStrategy):
    """
    Strategy optimized for tracing caller-callee execution paths and method lifecycles.
    """
    def retrieve(self, question: str) -> dict:
        strategies_used = ["Semantic Call Graph"]
        chunks = []
        graph_context = []
        
        term = extract_query_term("CALL_FLOW", question)
        # Find starting symbol in the Symbol Index
        sym_results = search_symbols(term)
        if sym_results:
            chunks.extend(sym_results)
            
        # Extract call graph relations around the symbol
        if sym_results:
            strategies_used.append("Graph Expansion (Calls)")
            sym_fqn = sym_results[0].get("fqn", term)
            graph_context.extend(build_graph_context(sym_fqn, max_neighbors=8))
            
        return {
            "chunks": chunks,
            "graph_context": graph_context,
            "strategies_used": strategies_used,
            "confidence": 0.9 if graph_context else 0.4
        }


class ArchitectureStrategy(BaseRetrievalStrategy):
    """
    Strategy optimized for high-level design, registration, and cross-file relationships.
    """
    def retrieve(self, question: str) -> dict:
        strategies_used = ["Knowledge Graph"]
        chunks = []
        graph_context = []
        
        term = extract_query_term("ARCHITECTURE", question)
        sym_results = search_symbols(term)
        if sym_results:
            chunks.extend(sym_results)
            sym_fqn = sym_results[0].get("fqn", term)
            graph_context.extend(build_graph_context(sym_fqn, max_neighbors=10))
            
        # Enrich with vector search to capture architectural concepts
        strategies_used.append("Vector Search")
        vector_chunks = retrieve_context(question, top_k=3)
        chunks.extend(vector_chunks)
        
        return {
            "chunks": chunks,
            "graph_context": graph_context,
            "strategies_used": strategies_used,
            "confidence": 0.85
        }


class DependencyStrategy(BaseRetrievalStrategy):
    """
    Strategy optimized for reverse dependencies. Uses reverse graph traversal.
    """
    def retrieve(self, question: str) -> dict:
        strategies_used = ["Reverse Graph Traversal"]
        chunks = []
        
        term = extract_query_term("DEPENDENCY", question)
        # Find target symbol
        sym_results = search_symbols(term)
        if sym_results:
            chunks.extend(sym_results)
            sym_fqn = sym_results[0].get("fqn", term)
            
            # Traverse incoming edges
            graph = load_graph()
            for edge in graph.get("edges", []):
                if edge["target"] == sym_fqn or edge["target"] == term:
                    # Retrieve the caller code block
                    caller_results = search_symbols(edge["source"])
                    if caller_results:
                        caller_info = caller_results[0]
                        caller_info["relation"] = f"reverse_{edge['relation']}"
                        caller_info["graph_source"] = sym_fqn
                        chunks.append(caller_info)
                        
        return {
            "chunks": chunks,
            "graph_context": [],
            "strategies_used": strategies_used,
            "confidence": 0.9 if len(chunks) > 1 else 0.3
        }


class GeneralStrategy(BaseRetrievalStrategy):
    """
    Default fallback strategy combining semantic vector search and graph neighborhood expansion.
    """
    def retrieve(self, question: str) -> dict:
        strategies_used = ["Vector Search", "Graph Expansion"]
        
        vector_chunks = retrieve_context(question, top_k=3)
        graph_context = []
        for chunk in vector_chunks:
            sym = chunk.get("symbol_name")
            if sym:
                graph_context.extend(build_graph_context(sym, max_neighbors=3))
                
        return {
            "chunks": vector_chunks,
            "graph_context": graph_context,
            "strategies_used": strategies_used,
            "confidence": 0.7
        }


class RetrievalOrchestrator:
    """
    Orchestrates the intent-aware retrieval process.
    """
    def __init__(self):
        self.strategies = {
            "FILE_LOOKUP": FileLookupStrategy(),
            "IMPORT_LOOKUP": ImportLookupStrategy(),
            "DECORATOR_LOOKUP": DecoratorLookupStrategy(),
            "KEYWORD_SEARCH": KeywordSearchStrategy(),
            "SYMBOL_LOOKUP": SymbolLookupStrategy(),
            "CALL_FLOW": CallFlowStrategy(),
            "ARCHITECTURE": ArchitectureStrategy(),
            "DEPENDENCY": DependencyStrategy(),
            "GENERAL": GeneralStrategy()
        }
        
    def score_chunk(self, chunk: dict, question: str, intent: str) -> float:
        """
        Calculates a ranking score for a retrieved chunk based on relevance and intent.
        """
        score = 0.0
        
        # Base score from vector similarity if available
        if isinstance(chunk.get("score"), (int, float)):
            score += chunk["score"]
        elif chunk.get("score") == "graph":
            score += 0.5
        else:
            score += 0.5
            
        # 1. Exact Symbol Match
        symbol_name = chunk.get("symbol_name")
        if symbol_name:
            if symbol_name.lower() in question.lower() or symbol_name.split(".")[-1].lower() in question.lower():
                score += 0.4
                
        # 2. Relation and Intent Alignment
        relation = chunk.get("relation")
        if relation:
            if intent == "CALL_FLOW" and relation in ("calls", "instantiates"):
                score += 0.3
            elif intent == "ARCHITECTURE" and relation in ("inherits", "imports"):
                score += 0.3
            elif intent == "DEPENDENCY" and relation in ("calls", "inherits", "imports", "reverse_calls", "reverse_inherits", "reverse_imports"):
                score += 0.3
                
        return score

    def orchestrate(self, question: str, max_context_size: int = 12) -> tuple:
        """
        Detects intent, runs the corresponding strategy, merges, ranks, and deduplicates the context.
        """
        # 1. Intent Detection
        intent = detect_intent(question)
        strategy = self.strategies.get(intent, self.strategies["GENERAL"])

        
        # 2. Execute Strategy
        result = strategy.retrieve(question)
        
        print(f"\nDetected Intent:\n{intent}")
        print(f"\nStrategy:\n{', '.join(result.get('strategies_used', []))}")
        
        # 3. Merge and Deduplicate
        merged = []
        seen_keys = set()
        
        # Counts for logging
        decorator_count = 0
        file_count = 0
        vector_count = 0
        symbol_count = 0
        
        def add_chunk(chunk):
            nonlocal decorator_count, file_count, vector_count, symbol_count
            key = (chunk.get("file_path"), chunk.get("symbol_name"), chunk.get("relation"))
            if key not in seen_keys:
                seen_keys.add(key)
                merged.append(chunk)
                
                # Metrics counting
                if chunk.get("chunk_type") == "file":
                    file_count += 1
                elif chunk.get("relation") and "decorated" in chunk["relation"]:
                    decorator_count += 1
                elif chunk.get("score") == "graph" or chunk.get("line"):
                    symbol_count += 1
                else:
                    vector_count += 1

        for c in result.get("chunks", []):
            add_chunk(c)
        for gc in result.get("graph_context", []):
            add_chunk(gc)
            
        # 4. Rank Chunks
        for chunk in merged:
            chunk["ranking_score"] = self.score_chunk(chunk, question, intent)
            
        merged.sort(key=lambda x: x["ranking_score"], reverse=True)
        
        # Limit to max size
        final_context = merged[:max_context_size]
        
        # Detailed Logging
        print("\nRetrieved:")
        print(f"{decorator_count} decorator")
        print(f"{file_count} file")
        print(f"{vector_count} vectors")
        print(f"\nFinal Context:\n{len(final_context)} chunks")
        
        return final_context, intent, result.get("strategies_used", []), result.get("confidence", 0.7)

