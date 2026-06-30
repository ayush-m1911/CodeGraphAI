"""
Purpose:
Implements O(1) deterministic search across structural indexes (Symbol, File, Import, Decorator, Class, Function).

Role in CodeGraphAI:
The search engine that retrieves precise code contexts for structural queries without invoking vector search.

Key Responsibilities:
* Query Symbol, File, Import, Decorator, Class Hierarchy, and Global Function Indexes.
* Perform indentation-aware local file block extraction to retrieve matching code snippets.
* Fallback to substring searches in files if exact index matches are not found.
"""

import os
import re
from app.services.repository_indexer import load_indexes

# Default repository path
REPO_PATH = "repositories/current_repo"


def get_python_block(rel_file_path: str, line_num: int) -> str:
    """
    Extracts a Python code block starting at line_num based on indentation.
    """
    abs_path = os.path.join(REPO_PATH, rel_file_path)
    if not os.path.exists(abs_path):
        return ""
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        start = line_num - 1
        if start < 0 or start >= len(lines):
            return ""
            
        first_line = lines[start]
        # Calculate base indentation
        base_indent = len(first_line) - len(first_line.lstrip())
        
        block_lines = [first_line]
        for i in range(start + 1, len(lines)):
            line = lines[i]
            # Keep empty lines
            if not line.strip():
                block_lines.append(line)
                continue
            indent = len(line) - len(line.lstrip())
            # Indentation dropped to or below base level
            if indent <= base_indent:
                # Check if it's a continuation line (like a multiline statement)
                # For simplicity, we break on class/def or same level statements
                if line.strip().startswith(("def ", "class ", "@", "import ", "from ")):
                    break
                if indent < base_indent:
                    break
            block_lines.append(line)
            
        return "".join(block_lines)
    except Exception:
        return ""


def search_symbols(query: str) -> list:
    """
    Searches the Symbol Index for exact or partial FQN matches.
    """
    indexes = load_indexes()
    symbol_index = indexes.get("symbol_index", {})
    
    results = []
    query_clean = query.strip().lower()
    
    # 1. Exact Match
    if query in symbol_index:
        info = symbol_index[query]
        code_text = get_python_block(info["file"], info["line"])
        results.append({**info, "text": code_text})
    else:
        # 2. Partial Match
        for fqn, info in symbol_index.items():
            if query_clean in fqn.lower() or query_clean in info["name"].lower():
                code_text = get_python_block(info["file"], info["line"])
                results.append({**info, "text": code_text})
                
    return results[:10]


def search_files(query: str) -> list:
    """
    Searches the File Index for matching file names.
    """
    indexes = load_indexes()
    file_index = indexes.get("file_index", [])
    
    query_clean = query.strip().lower()
    results = []
    for file_path in file_index:
        if query_clean in file_path.lower():
            results.append({
                "file_path": file_path,
                "text": f"# File: {file_path}",
                "symbol_name": file_path,
                "chunk_type": "file"
            })
    return results[:10]


def search_decorators(query: str) -> list:
    """
    Searches the Decorator Index for matching decorators.
    """
    indexes = load_indexes()
    decorator_index = indexes.get("decorator_index", {})
    
    # Strip leading '@'
    query_clean = query.strip()
    if query_clean.startswith("@"):
        query_clean = query_clean[1:]
    query_clean = query_clean.lower()
    
    results = []
    for dec, occurrences in decorator_index.items():
        if query_clean in dec.lower():
            for occ in occurrences:
                code_text = get_python_block(occ["file"], occ["line"])
                results.append({
                    "symbol_name": occ["target"],
                    "chunk_type": occ["type"],
                    "file_path": occ["file"],
                    "line": occ["line"],
                    "relation": f"decorated_by_{dec}",
                    "text": code_text
                })
    return results[:10]


def search_imports(query: str) -> list:
    """
    Finds files that import a given module or symbol.
    """
    indexes = load_indexes()
    import_index = indexes.get("import_index", {})
    
    query_clean = query.strip().lower()
    results = []
    
    for file_path, imports in import_index.items():
        for imp in imports:
            if (query_clean in imp["imported_fqn"].lower() or 
                query_clean in imp["local_name"].lower()):
                results.append({
                    "file_path": file_path,
                    "symbol_name": imp["imported_fqn"],
                    "chunk_type": "import",
                    "relation": "imports",
                    "text": f"# File: {file_path} imports {imp['imported_fqn']} as {imp['local_name']}"
                })
    return results[:10]


def search_classes(query: str) -> list:
    """
    Searches the Class Hierarchy Index.
    """
    indexes = load_indexes()
    symbol_index = indexes.get("symbol_index", {})
    
    query_clean = query.strip().lower()
    results = []
    for fqn, info in symbol_index.items():
        if info["type"] == "class" and (query_clean in fqn.lower() or query_clean in info["name"].lower()):
            code_text = get_python_block(info["file"], info["line"])
            results.append({**info, "text": code_text})
    return results[:10]


def search_functions(query: str) -> list:
    """
    Searches the Global Function Index.
    """
    indexes = load_indexes()
    symbol_index = indexes.get("symbol_index", {})
    
    query_clean = query.strip().lower()
    results = []
    for fqn, info in symbol_index.items():
        if info["type"] in ("function", "method") and (query_clean in fqn.lower() or query_clean in info["name"].lower()):
            code_text = get_python_block(info["file"], info["line"])
            results.append({**info, "text": code_text})
    return results[:10]


def search_string(query: str) -> list:
    """
    Performs a substring/keyword search across all files in the repository.
    """
    results = []
    query_clean = query.strip().lower()
    
    if not os.path.exists(REPO_PATH):
        return []
        
    for root, _, files in os.walk(REPO_PATH):
        for file in files:
            if not file.endswith(".py"):
                continue
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if query_clean in content.lower():
                    rel_file = os.path.relpath(file_path, REPO_PATH).replace(os.sep, "/")
                    # Find matching lines
                    lines = content.splitlines()
                    for idx, line in enumerate(lines):
                        if query_clean in line.lower():
                            snippet = "\n".join(lines[max(0, idx - 2):min(len(lines), idx + 15)])
                            results.append({
                                "file_path": rel_file,
                                "symbol_name": f"keyword_{query}",
                                "chunk_type": "keyword_match",
                                "text": snippet
                            })
                            break # Limit to one match per file to avoid noise
            except Exception:
                pass
            if len(results) >= 5:
                break
        if len(results) >= 5:
            break
            
    return results
