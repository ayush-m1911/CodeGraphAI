"""
Purpose:
Constructs structural containment graphs, inheritance trees, import maps, and semantic call graphs for Python repositories.

Role in CodeGraphAI:
Builds the core Knowledge Graph that maps relationships between files, classes, methods, and functions.
These relations enable GraphRAG neighborhood context expansion, resolving dependencies and interactions.

GraphRAG Workflow:

Question
↓
Vector Retrieval
↓
Symbol Expansion
↓
Knowledge Graph
↓
LLM
↓
Answer

Key Responsibilities:
* Build a global repository symbol table containing FQNs, types, parent classes, and inheritance.
* Resolve relative and absolute import statements.
* Extract structural containment, class inheritance, decorator usage, and file import relationships.
* Coordinate with the semantic call retriever to extract resolved call, instantiation, and return relationships.
* Save generated graph structures to graphs/*.json.
"""

import os
import json

from app.services.parser import parse_repository
from app.services.code_chunker import parser


def get_module_name(file_path: str, repo_path: str) -> str:
    """
    Translates a filesystem path into a Python dotted module name.
    """
    abs_file = os.path.abspath(file_path)
    abs_repo = os.path.abspath(repo_path)
    
    try:
        rel_path = os.path.relpath(abs_file, abs_repo)
    except ValueError:
        rel_path = os.path.basename(abs_file)
        
    if rel_path.endswith('.py'):
        rel_path = rel_path[:-3]
        
    parts = rel_path.replace(os.sep, '/').split('/')
    if parts and parts[-1] == '__init__':
        parts = parts[:-1]
        
    return '.'.join(parts)


def resolve_relative_module(current_module: str, relative_import_text: str) -> str:
    """
    Resolves a relative module import name to its absolute dotted representation.
    """
    dots_count = 0
    for char in relative_import_text:
        if char == '.':
            dots_count += 1
        else:
            break
            
    module_suffix = relative_import_text[dots_count:]
    parts = current_module.split('.')
    
    if len(parts) >= dots_count:
        base_parts = parts[:-dots_count]
    else:
        base_parts = []
        
    base_module = '.'.join(base_parts)
    if base_module and module_suffix:
        return f"{base_module}.{module_suffix}"
    elif module_suffix:
        return module_suffix
    else:
        return base_module


def extract_file_imports(root_node, current_module: str, code_bytes: bytes) -> dict:
    """
    Traverses the AST of a file to extract all import statements.
    """
    imports = {}
    
    def get_text(node):
        return code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore").strip()

    def walk(node):
        if node.type == "import_statement":
            for child in node.children:
                if child.type == "dotted_name":
                    name = get_text(child)
                    imports[name] = (name, "module")
                elif child.type == "aliased_import":
                    real_node = None
                    alias_node = None
                    for c in child.children:
                        if c.type == "dotted_name":
                            real_node = c
                        elif c.type == "identifier":
                            alias_node = c
                    if real_node and alias_node:
                        imports[get_text(alias_node)] = (get_text(real_node), "module")
                        
        elif node.type == "import_from_statement":
            module_node = None
            is_relative = False
            
            for child in node.children:
                if child.type in ("dotted_name", "relative_import"):
                    module_node = child
                    if child.type == "relative_import":
                        is_relative = True
                    break
            
            if not module_node:
                return
                
            module_text = get_text(module_node)
            if is_relative:
                module_name = resolve_relative_module(current_module, module_text)
            else:
                module_name = module_text
                
            found_import_keyword = False
            for child in node.children:
                if child.type == "import":
                    found_import_keyword = True
                    continue
                if not found_import_keyword:
                    continue
                
                if child.type in ("dotted_name", "identifier"):
                    name = get_text(child)
                    imports[name] = (f"{module_name}.{name}", "symbol")
                elif child.type == "aliased_import":
                    real_node = None
                    alias_node = None
                    for c in child.children:
                        if c.type in ("dotted_name", "identifier"):
                            if not real_node:
                                real_node = c
                            else:
                                alias_node = c
                    if real_node and alias_node:
                        imports[get_text(alias_node)] = (f"{module_name}.{get_text(real_node)}", "symbol")
                elif child.type == "wildcard_import":
                    imports["*"] = (module_name, "wildcard")
                    
        for child in node.children:
            walk(child)
            
    walk(root_node)
    return imports


def extract_graph_semantic(code, file_path, module_name, local_imports, symbol_table):
    """
    Extracts structural nodes and containment, inheritance, decorator, and import edges.
    """
    graph = {
        "nodes": [],
        "edges": []
    }
    
    seen_nodes = set()
    code_bytes = bytes(code, "utf8")
    tree = parser.parse(code_bytes)
    root = tree.root_node

    def get_text(node):
        return code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore").strip()

    # Add File node
    graph["nodes"].append({
        "id": file_path,
        "type": "file",
        "file_path": file_path
    })
    seen_nodes.add(file_path)

    # Add Imports edges
    for local_name, (imported_fqn, import_type) in local_imports.items():
        if import_type == "symbol":
            graph["edges"].append({
                "source": file_path,
                "target": imported_fqn,
                "relation": "imports",
                "resolved": True,
                "confidence": "high"
            })

    def walk(node, current_class_fqn=None):
        if node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                c_name = get_text(name_node)
                class_fqn = f"{module_name}.{c_name}"
                
                if class_fqn not in seen_nodes:
                    graph["nodes"].append({
                        "id": class_fqn,
                        "type": "class",
                        "file_path": file_path
                    })
                    seen_nodes.add(class_fqn)
                
                parent_id = current_class_fqn if current_class_fqn else file_path
                graph["edges"].append({
                    "source": parent_id,
                    "target": class_fqn,
                    "relation": "contains"
                })
                
                # Inherits Edge
                arg_list = node.child_by_field_name("superclasses")
                if not arg_list:
                    for child in node.children:
                        if child.type == "argument_list":
                            arg_list = child
                            break
                if arg_list:
                    for arg in arg_list.children:
                        if arg.type in ("identifier", "attribute", "dotted_name"):
                            superclass_name = get_text(arg)
                            from app.services.call_graph import resolve_simple
                            resolved_parent, resolved_status, confidence = resolve_simple(
                                superclass_name, local_imports, symbol_table, module_name
                            )
                            graph["edges"].append({
                                "source": class_fqn,
                                "target": resolved_parent,
                                "relation": "inherits",
                                "resolved": resolved_status,
                                "confidence": confidence
                            })

                # Decorates Edge
                if node.parent and node.parent.type == "decorated_definition":
                    for child in node.parent.children:
                        if child.type == "decorator":
                            dec_text = get_text(child)
                            if dec_text.startswith("@"):
                                dec_text = dec_text[1:]
                            callable_name = dec_text
                            for subchild in child.children:
                                if subchild.type == "call":
                                    call_func = subchild.child_by_field_name("function")
                                    if call_func:
                                        callable_name = get_text(call_func)
                                elif subchild.type in ("identifier", "attribute"):
                                    callable_name = get_text(subchild)
                            
                            from app.services.call_graph import resolve_name
                            resolved_dec, resolved_status, confidence = resolve_name(
                                callable_name, None, local_imports, symbol_table, {}, module_name
                            )
                            graph["edges"].append({
                                "source": resolved_dec,
                                "target": class_fqn,
                                "relation": "decorates",
                                "resolved": resolved_status,
                                "confidence": confidence
                            })

                for child in node.children:
                    walk(child, class_fqn)
                return

        elif node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                f_name = get_text(name_node)
                
                if current_class_fqn:
                    func_fqn = f"{current_class_fqn}.{f_name}"
                    func_type = "method"
                else:
                    func_fqn = f"{module_name}.{f_name}"
                    func_type = "function"
                    
                if func_fqn not in seen_nodes:
                    graph["nodes"].append({
                        "id": func_fqn,
                        "type": func_type,
                        "file_path": file_path
                    })
                    seen_nodes.add(func_fqn)
                    
                parent_id = current_class_fqn if current_class_fqn else file_path
                graph["edges"].append({
                    "source": parent_id,
                    "target": func_fqn,
                    "relation": "contains"
                })

                # Decorates Edge
                if node.parent and node.parent.type == "decorated_definition":
                    for child in node.parent.children:
                        if child.type == "decorator":
                            dec_text = get_text(child)
                            if dec_text.startswith("@"):
                                dec_text = dec_text[1:]
                            callable_name = dec_text
                            for subchild in child.children:
                                if subchild.type == "call":
                                    call_func = subchild.child_by_field_name("function")
                                    if call_func:
                                        callable_name = get_text(call_func)
                                elif subchild.type in ("identifier", "attribute"):
                                    callable_name = get_text(subchild)
                                    
                            from app.services.call_graph import resolve_name
                            resolved_dec, resolved_status, confidence = resolve_name(
                                callable_name, None, local_imports, symbol_table, {}, module_name
                            )
                            graph["edges"].append({
                                "source": resolved_dec,
                                "target": func_fqn,
                                "relation": "decorates",
                                "resolved": resolved_status,
                                "confidence": confidence
                            })
                return

        for child in node.children:
            walk(child, current_class_fqn)

    walk(root)
    return graph


def extract_graph(code, file_path):
    """
    Legacy structural graph extractor.
    """
    return extract_graph_semantic(code, file_path, "legacy", {}, {})


def build_repository_graph(repo_path):
    """
    Builds the complete knowledge graph by first constructing a global symbol table
    and then resolving relationships semantically.
    """
    print("Building symbol table...")
    
    docs = parse_repository(repo_path)
    
    symbol_table = {}
    file_imports = {}
    file_modules = {}
    
    # Pass 1: Build the symbol table and imports map
    for doc in docs:
        if not doc["file_path"].endswith(".py"):
            continue
            
        file_path = doc["file_path"]
        code = doc["content"]
        code_bytes = bytes(code, "utf8")
        
        module_name = get_module_name(file_path, repo_path)
        file_modules[file_path] = module_name
        
        tree = parser.parse(code_bytes)
        imports = extract_file_imports(tree.root_node, module_name, code_bytes)
        file_imports[file_path] = imports
        
        def collect_symbols(node, class_fqn=None):
            def get_text(n):
                return code_bytes[n.start_byte:n.end_byte].decode("utf-8", errors="ignore").strip()
                
            if node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    c_name = get_text(name_node)
                    fqn = f"{class_fqn}.{c_name}" if class_fqn else f"{module_name}.{c_name}"
                    
                    inherits = []
                    arg_list = node.child_by_field_name("superclasses")
                    if not arg_list:
                        for child in node.children:
                            if child.type == "argument_list":
                                arg_list = child
                                break
                    if arg_list:
                        for arg in arg_list.children:
                            if arg.type in ("identifier", "attribute", "dotted_name"):
                                inherits.append(get_text(arg))
                                
                    symbol_table[fqn] = {
                        "type": "class",
                        "name": c_name,
                        "file": file_path,
                        "parent_class": class_fqn,
                        "inherits": inherits
                    }
                    
                    for child in node.children:
                        collect_symbols(child, fqn)
                    return
                    
            elif node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    f_name = get_text(name_node)
                    if class_fqn:
                        fqn = f"{class_fqn}.{f_name}"
                        symbol_type = "method"
                    else:
                        fqn = f"{module_name}.{f_name}"
                        symbol_type = "function"
                        
                    symbol_table[fqn] = {
                        "type": symbol_type,
                        "name": f_name,
                        "file": file_path,
                        "parent_class": class_fqn,
                        "inherits": []
                    }
                    return
                    
            for child in node.children:
                collect_symbols(child, class_fqn)
                
        collect_symbols(tree.root_node)
        
    print(f"Collected {len(symbol_table)} symbols")
    print("Resolving function calls...")
    
    repository_graph = {
        "nodes": [],
        "edges": []
    }
    seen_nodes = set()
    
    total_resolved = 0
    total_unresolved = 0
    
    # Pass 2: Extract structural nodes/edges and resolve calls
    for doc in docs:
        if not doc["file_path"].endswith(".py"):
            continue
            
        file_path = doc["file_path"]
        code = doc["content"]
        module_name = file_modules[file_path]
        imports = file_imports[file_path]
        
        # 1. Extract structural graph (nodes, contains, inherits, decorates, imports)
        file_graph = extract_graph_semantic(
            code, file_path, module_name, imports, symbol_table
        )
        
        # 2. Extract semantic call relations (calls, instantiates, returns)
        from app.services.call_graph import extract_semantic_relations
        call_edges, resolved, unresolved = extract_semantic_relations(
            code, file_path, module_name, imports, symbol_table
        )
        
        total_resolved += resolved
        total_unresolved += unresolved
        
        # Merge nodes
        for node in file_graph["nodes"]:
            if node["id"] not in seen_nodes:
                repository_graph["nodes"].append(node)
                seen_nodes.add(node["id"])
                
        # Merge edges
        repository_graph["edges"].extend(file_graph["edges"])
        repository_graph["edges"].extend(call_edges)
        
    print(f"Resolved:\n{total_resolved}")
    print(f"Unresolved:\n{total_unresolved}")
    print("Call graph generation completed.")
    
    return repository_graph


def save_graph(
    graph,
    graph_name="fastapi_graph.json"
):
    """
    Writes the constructed knowledge graph object into a JSON file in the graphs/ directory.
    """
    os.makedirs("graphs", exist_ok=True)
    with open(
        f"graphs/{graph_name}",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(graph, f, indent=4)
