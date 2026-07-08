"""
Purpose:
Implements a modular, extendable context scoring and ranking engine for CodeGraphAI.

Responsibilities:
* Compute composite relevance scores for codebase context chunks.
* Define and apply individual ranking signals (Vector Similarity, Graph Distance, Hierarchy Match, Symbol Match, Relation Importance).
* Merge overlapping or contiguous code chunks from the same file to optimize context quality.
* Deduplicate redundant contexts, prioritizing blocks with higher ranking scores.

Inputs:
* Unranked code context chunks list, query string, intent type, and graph traversal metadata.

Outputs:
* Ranked, deduplicated, and merged context chunks list.

Interaction with other modules:
* Invoked by `retrieval_orchestrator.py` during the post-retrieval ranking stage.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import os


class RankingSignal(ABC):
    """
    Abstract interface for individual ranking signals.
    """
    @abstractmethod
    def compute_score(self, chunk: dict, query: str, intent: str, metadata: dict) -> float:
        """
        Computes a score contribution between 0.0 and 1.0.
        """
        pass


class VectorSimilaritySignal(RankingSignal):
    """
    Evaluates semantic embedding cosine similarity.
    """
    def compute_score(self, chunk: dict, query: str, intent: str, metadata: dict) -> float:
        score = chunk.get("score")
        if isinstance(score, (int, float)):
            # Normalize vector score (usually similarity between 0 and 1)
            return min(max(float(score), 0.0), 1.0)
        return 0.5  # Neutral default for non-vector sources


class GraphDistanceSignal(RankingSignal):
    """
    Evaluates topological proximity in the knowledge graph from starting resolved nodes.
    """
    def compute_score(self, chunk: dict, query: str, intent: str, metadata: dict) -> float:
        graph_distances = metadata.get("graph_distances", {})
        sym_name = chunk.get("symbol_name")
        fqn = chunk.get("fqn")
        
        # Check distance from starting symbols
        dist = 999
        for key in (fqn, sym_name):
            if key in graph_distances:
                dist = min(dist, graph_distances[key])
                
        if dist == 0:
            return 1.0  # Exact matching resolved symbol
        elif dist == 1:
            return 0.7  # Direct neighbor
        elif dist == 2:
            return 0.4  # Two-hop neighbor
            
        return 0.0  # Unconnected or fallback


class HierarchyMatchSignal(RankingSignal):
    """
    Evaluates structural nesting depth compatibility based on query intent.
    """
    def compute_score(self, chunk: dict, query: str, intent: str, metadata: dict) -> float:
        depth = chunk.get("hierarchy_depth", 3)
        chunk_type = chunk.get("chunk_type") or chunk.get("node_type", "")
        
        # High-level architecture queries prefer shallower modules/packages
        if intent in ("Architecture", "Configuration"):
            if chunk_type in ("file", "package", "repository") or depth <= 3:
                return 1.0
            return 0.3
            
        # Detailed implementation queries prefer classes/methods
        if intent in ("Call Flow", "Error Analysis", "Definition", "Implementation"):
            if chunk_type in ("class", "method", "function") or depth >= 4:
                return 1.0
            return 0.4
            
        return 0.7


class SymbolMatchSignal(RankingSignal):
    """
    Evaluates query lexical matches on symbol names and file paths.
    """
    def compute_score(self, chunk: dict, query: str, intent: str, metadata: dict) -> float:
        symbol_name = chunk.get("symbol_name")
        file_path = chunk.get("file_path")
        q = query.lower()
        
        score = 0.0
        if symbol_name:
            simple_name = symbol_name.split(".")[-1].lower()
            if simple_name in q:
                score += 0.7
            if symbol_name.lower() in q:
                score += 0.3
                
        if file_path:
            file_name = os.path.basename(file_path).lower()
            if file_name in q:
                score += 0.5
                
        return min(score, 1.0)


class RelationImportanceSignal(RankingSignal):
    """
    Evaluates relationship semantic relevance matching the intent.
    """
    def compute_score(self, chunk: dict, query: str, intent: str, metadata: dict) -> float:
        relation = chunk.get("relation")
        if not relation:
            return 0.5
            
        rel = relation.lower()
        if intent == "Call Flow" and rel in ("calls", "instantiates", "returns"):
            return 1.0
        elif intent == "Architecture" and rel in ("contains", "defines", "inherits", "imports"):
            return 1.0
        elif intent == "Dependencies" and (rel in ("imports", "inherits") or "reverse" in rel):
            return 1.0
        elif intent == "Error Analysis" and rel == "raises":
            return 1.0
            
        return 0.3


class ScoringEngine:
    """
    Combines weighted signals to score and rank retrieved contexts.
    """
    def __init__(self):
        # Configurable signal listing with corresponding weights
        self.signals: List[tuple] = [
            (VectorSimilaritySignal(), 0.30),
            (GraphDistanceSignal(), 0.20),
            (HierarchyMatchSignal(), 0.15),
            (SymbolMatchSignal(), 0.20),
            (RelationImportanceSignal(), 0.15)
        ]
        
    def compute_composite_score(self, chunk: dict, query: str, intent: str, metadata: dict) -> float:
        """
        Calculates a composite normalized relevance score.
        """
        total_score = 0.0
        for signal, weight in self.signals:
            score_contrib = signal.compute_score(chunk, query, intent, metadata)
            total_score += score_contrib * weight
        return total_score


def merge_overlapping_chunks(chunks: List[dict]) -> List[dict]:
    """
    Groups chunks by filepath and merges overlapping or adjacent line blocks
    to clean the context.
    """
    by_file = {}
    for c in chunks:
        path = c.get("file_path")
        if not path:
            continue
        by_file.setdefault(path, []).append(c)
        
    merged_list = []
    for path, file_chunks in by_file.items():
        # Setup normalized start_line and end_line coordinates
        for c in file_chunks:
            if "start_line" not in c:
                c["start_line"] = c.get("line") or 1
            if "end_line" not in c:
                line_count = len(c.get("text", "").split("\n"))
                c["end_line"] = c["start_line"] + line_count - 1
                
        file_chunks.sort(key=lambda x: x["start_line"])
        
        merged: List[dict] = []
        for c in file_chunks:
            if not merged:
                merged.append(c)
            else:
                prev = merged[-1]
                # Check line range overlap or close contiguity (within 5 lines gap)
                if c["start_line"] <= prev["end_line"] + 5:
                    if c["end_line"] <= prev["end_line"]:
                        # Fully contained
                        continue
                        
                    # Rebuild combined text, avoiding duplicating overlapping lines
                    prev_lines = prev.get("text", "").split("\n")
                    c_lines = c.get("text", "").split("\n")
                    
                    overlap_offset = prev["end_line"] - c["start_line"] + 1
                    if 0 < overlap_offset < len(c_lines):
                        new_lines = c_lines[overlap_offset:]
                    else:
                        new_lines = c_lines
                        
                    prev["text"] = "\n".join(prev_lines + new_lines)
                    prev["end_line"] = c["end_line"]
                    
                    # Consolidate score and attributes
                    if c.get("ranking_score", 0.0) > prev.get("ranking_score", 0.0):
                        prev["ranking_score"] = c["ranking_score"]
                else:
                    merged.append(c)
                    
        merged_list.extend(merged)
        
    return merged_list
