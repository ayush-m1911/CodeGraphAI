"""
Purpose:
Builds structural indexes (Symbol, File, Import, Decorator, Class Hierarchy, Global Function) during repository parsing.

Role in CodeGraphAI:
Provides the O(1) deterministic search capability. It parses AST structures at ingestion time
and stores them in a queryable JSON index, eliminating the need for vector search on exact lookup questions.

Key Responsibilities:
* Traverses repository files to build 6 specialized indexes.
* Extracts imports, decorators, aliases, parameters, return annotations, inheritance, line numbers, docstrings, and visibility.
* Saves the consolidated index to graphs/structural_index.json.
* Exposes O(1) loading and lookup interfaces.
"""

import os
import json
import re
from tree_sitter import Language, Parser
import tree_sitter_python
from app.services.parser import parse_repository
from app.services.code_chunker import PY_LANGUAGE, parser
from app.services.code_graph import get_module_name, resolve_relative_module, extract_file_imports

# Structural index file path
INDEX_FILE_PATH = "graphs/structural_index.json"


def extract_docstring(node, code_bytes: bytes) -> str:
    """
    Extracts the docstring from a class or function block if present.
    """
    block_node = None
    for child in node.children:
        if child.type == "block":
            block_node = child
            break
    if not block_node:
        return None
        
    if block_node.children:
        first_child = block_node.children[0]
        if first_child.type == "expression_statement":
            for sub in first_child.children:
                if sub.type == "string":
                    doc = code_bytes[sub.start_byte:sub.end_byte].decode("utf-8", errors="ignore").strip()
                    if (doc.startswith('"""') and doc.endswith('"""')) or (doc.startswith("'''") and doc.endswith("'''")):
                        return doc[3:-3].strip()
                    if (doc.startswith('"') and doc.endswith('"')) or (doc.startswith("'") and doc.endswith("'")):
                        return doc[1:-1].strip()
                    return doc
    return None


def extract_decorators(node, code_bytes: bytes) -> list:
    """
    Extracts decorators applied to a class or function.
    """
    decorators = []
    if node.parent and node.parent.type == "decorated_definition":
        for child in node.parent.children:
            if child.type == "decorator":
                dec_text = code_bytes[child.start_byte:child.end_byte].decode("utf-8", errors="ignore").strip()
                decorators.append(dec_text)
    return decorators


def extract_function_info(node, code_bytes: bytes) -> tuple:
    """
    Extracts parameters and return type annotations from a function definition.
    """
    parameters = []
    return_annotation = None
    
    params_node = node.child_by_field_name("parameters")
    if params_node:
        for child in params_node.children:
            if child.type in ("identifier", "typed_parameter", "default_parameter"):
                p_text = code_bytes[child.start_byte:child.end_byte].decode("utf-8", errors="ignore").strip()
                parameters.append(p_text)
                
    return_node = node.child_by_field_name("return_type")
    if not return_node:
        found_arrow = False
        for child in node.children:
            if child.type == "->":
                found_arrow = True
            elif found_arrow and child.type != " ":
                return_node = child
                break
    if return_node:
        return_annotation = code_bytes[return_node.start_byte:return_node.end_byte].decode("utf-8", errors="ignore").strip()
        
    return parameters, return_annotation


def extract_class_inheritance(node, code_bytes: bytes) -> list:
    """
    Extracts superclasses for a class definition.
    """
    inheritance = []
    arg_list = node.child_by_field_name("superclasses")
    if not arg_list:
        for child in node.children:
            if child.type == "argument_list":
                arg_list = child
                break
    if arg_list:
        for arg in arg_list.children:
            if arg.type in ("identifier", "attribute", "dotted_name"):
                inheritance.append(code_bytes[arg.start_byte:arg.end_byte].decode("utf-8", errors="ignore").strip())
    return inheritance


def build_structural_index(repo_path: str) -> dict:
    """
    Ingests and parses all Python files to construct the 6 structural indexes.
    """
    print("Building structural repository indexes...")
    docs = parse_repository(repo_path)
    
    # Initialize indexes
    symbol_index = {}
    file_index = []
    import_index = {}
    decorator_index = {}
    class_hierarchy = {}
    global_functions = {}
    
    for doc in docs:
        file_path = doc["file_path"]
        # Convert to relative path for portability
        try:
            rel_file_path = os.path.relpath(file_path, repo_path).replace(os.sep, "/")
        except ValueError:
            rel_file_path = os.path.basename(file_path)
            
        file_index.append(rel_file_path)
        
        if not file_path.endswith(".py"):
            continue
            
        code = doc["content"]
        code_bytes = bytes(code, "utf8")
        module_name = get_module_name(file_path, repo_path)
        
        tree = parser.parse(code_bytes)
        root = tree.root_node
        
        # 1. Extract imports for the Import Index
        imports_map = extract_file_imports(root, module_name, code_bytes)
        import_index[rel_file_path] = []
        for local_name, (imported_fqn, import_type) in imports_map.items():
            import_index[rel_file_path].append({
                "local_name": local_name,
                "imported_fqn": imported_fqn,
                "type": import_type
            })
            
        def get_text(node):
            return code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore").strip()
            
        # Recursive walker to populate Symbol, Decorator, Class Hierarchy, and Global Function Indexes
        def walk(node, current_class_name=None, current_class_fqn=None):
            if node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    c_name = get_text(name_node)
                    c_fqn = f"{current_class_fqn}.{c_name}" if current_class_fqn else f"{module_name}.{c_name}"
                    line_num = node.start_point[0] + 1
                    visibility = "private" if c_name.startswith("_") else "public"
                    docstring = extract_docstring(node, code_bytes)
                    inheritance = extract_class_inheritance(node, code_bytes)
                    decorators = extract_decorators(node, code_bytes)
                    
                    # Symbol Index
                    symbol_index[c_fqn] = {
                        "name": c_name,
                        "fqn": c_fqn,
                        "type": "class",
                        "class": current_class_name,
                        "module": module_name,
                        "file": rel_file_path,
                        "line": line_num,
                        "visibility": visibility,
                        "docstring": docstring,
                        "inheritance": inheritance,
                        "decorators": decorators
                    }
                    
                    # Class Hierarchy Index
                    class_hierarchy[c_fqn] = {
                        "base_classes": inheritance,
                        "subclasses": []
                    }
                    
                    # Decorator Index
                    for dec in decorators:
                        dec_clean = dec.split("(")[0].strip()
                        if dec_clean.startswith("@"):
                            dec_clean = dec_clean[1:]
                        if dec_clean not in decorator_index:
                            decorator_index[dec_clean] = []
                        decorator_index[dec_clean].append({
                            "target": c_fqn,
                            "type": "class",
                            "file": rel_file_path,
                            "line": line_num
                        })
                        
                    for child in node.children:
                        walk(child, c_name, c_fqn)
                    return
                    
            elif node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    f_name = get_text(name_node)
                    f_fqn = f"{current_class_fqn}.{f_name}" if current_class_fqn else f"{module_name}.{f_name}"
                    line_num = node.start_point[0] + 1
                    visibility = "private" if f_name.startswith("_") else "public"
                    docstring = extract_docstring(node, code_bytes)
                    decorators = extract_decorators(node, code_bytes)
                    params, ret_ann = extract_function_info(node, code_bytes)
                    
                    # Symbol Index
                    symbol_type = "method" if current_class_fqn else "function"
                    symbol_index[f_fqn] = {
                        "name": f_name,
                        "fqn": f_fqn,
                        "type": symbol_type,
                        "class": current_class_name,
                        "module": module_name,
                        "file": rel_file_path,
                        "line": line_num,
                        "visibility": visibility,
                        "docstring": docstring,
                        "parameters": params,
                        "return_annotation": ret_ann,
                        "decorators": decorators
                    }
                    
                    # Global Function Index
                    if not current_class_fqn:
                        global_functions[f_fqn] = {
                            "name": f_name,
                            "file": rel_file_path,
                            "line": line_num,
                            "parameters": params,
                            "return_annotation": ret_ann
                        }
                        
                    # Decorator Index
                    for dec in decorators:
                        dec_clean = dec.split("(")[0].strip()
                        if dec_clean.startswith("@"):
                            dec_clean = dec_clean[1:]
                        if dec_clean not in decorator_index:
                            decorator_index[dec_clean] = []
                        decorator_index[dec_clean].append({
                            "target": f_fqn,
                            "type": symbol_type,
                            "file": rel_file_path,
                            "line": line_num
                        })
                    return
                    
            for child in node.children:
                walk(child, current_class_name, current_class_fqn)
                
        walk(root)
        
    # Populate subclasses in Class Hierarchy
    for child_class, info in class_hierarchy.items():
        for base in info["base_classes"]:
            # Find base class FQN
            base_fqn = base
            # Resolve relative/simple base class names
            for possible_fqn in class_hierarchy:
                if possible_fqn == base or possible_fqn.endswith(f".{base}"):
                    base_fqn = possible_fqn
                    break
            if base_fqn in class_hierarchy:
                class_hierarchy[base_fqn]["subclasses"].append(child_class)
                
    index_data = {
        "symbol_index": symbol_index,
        "file_index": file_index,
        "import_index": import_index,
        "decorator_index": decorator_index,
        "class_hierarchy": class_hierarchy,
        "global_functions": global_functions
    }
    
    # Save index
    os.makedirs(os.path.dirname(INDEX_FILE_PATH), exist_ok=True)
    with open(INDEX_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=4)
        
    print(f"Structural indexes created. Saved to {INDEX_FILE_PATH}")
    return index_data


def load_indexes() -> dict:
    """
    Loads the saved structural index JSON from disk.
    """
    if not os.path.exists(INDEX_FILE_PATH):
        return {
            "symbol_index": {},
            "file_index": [],
            "import_index": {},
            "decorator_index": {},
            "class_hierarchy": {},
            "global_functions": {}
        }
    with open(INDEX_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
