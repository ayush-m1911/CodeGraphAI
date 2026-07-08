"""
Purpose:
Constructs a semantic and hierarchical knowledge graph mapping codebase containment trees and call dependencies.

Responsibilities:
* Collect global symbols, docstrings, signatures, and imports maps.
* Extract structural containment, inheritance, decorator, and call relationships.
* Construct the parent-child package/module nesting tree structure.
* Validate edges and create external boundary symbol nodes.
* Serialize nodes and edges using strongly typed models (GraphNode, GraphEdge, GraphMetadata).
* Handle resolution failures defensively, recording unresolved reference statistics.

Failure handling:
* Symbol resolution lookups use `.get()` defaults to avoid KeyError propagation.
* Stage-level try-except blocks prevent file parsing or hierarchy crashes from aborting indexing.
* Unresolved references are saved in a dedicated metadata trace.

Inputs:
* Python repository root filesystem path.

Outputs:
* Serialized knowledge graph dictionary containing nested nodes and relation edges.

Interaction with other modules:
* Parses repositories via `parser.py`, drives tree-sitter structures via `code_chunker.py`,
  references caller-callee scopes via `call_graph.py`, and outputs metrics to `indexing_service.py`.
"""

import os
import json
import logging
from collections import Counter

from app.services.parser import parse_repository
from app.services.code_chunker import parser
from app.models.graph import GraphNode, GraphEdge, GraphMetadata
from typing import Optional

logger = logging.getLogger("codegraphai.code_graph")


def get_module_name(file_path: str, repo_path: str) -> str:
    """
    Translates a filesystem path into a Python dotted module name.

    Inputs:
        file_path (str): Absolute or relative file path.
        repo_path (str): Repository root path.

    Outputs:
        str: Dotted module name (e.g. app.api.index).
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

    Inputs:
        current_module (str): The active module dotted name.
        relative_import_text (str): Raw import text containing leading dots.

    Outputs:
        str: Absolute module name.
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

    Inputs:
        root_node (Node): Tree-sitter AST root node.
        current_module (str): Dotted name of current file module.
        code_bytes (bytes): Source code bytes.

    Outputs:
        dict: Mapped local aliases to their fully qualified targets.
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


def get_docstring(node, code_bytes: bytes) -> Optional[str]:
    """
    Helper to extract docstring blocks directly from function/class bodies in the AST.
    """
    body_node = node.child_by_field_name("body")
    if body_node and body_node.children:
        first_stmt = body_node.children[0]
        if first_stmt.type == "expression_statement":
            string_nodes = [c for c in first_stmt.children if c.type == "string"]
            if string_nodes:
                string_node = string_nodes[0]
                text = code_bytes[string_node.start_byte:string_node.end_byte].decode("utf-8", errors="ignore").strip()
                if text.startswith('"""') or text.startswith("'''"):
                    return text[3:-3].strip()
                elif text.startswith('"') or text.startswith("'"):
                    return text[1:-1].strip()
    return None


def get_signature(node, symbol_type: str, name: str, code_bytes: bytes) -> Optional[str]:
    """
    Helper to extract syntax signatures for classes, functions, and methods.
    """
    if symbol_type == "class":
        sig = f"class {name}"
        arg_list = node.child_by_field_name("superclasses")
        if not arg_list:
            for child in node.children:
                if child.type == "argument_list":
                    arg_list = child
                    break
        if arg_list:
            params = code_bytes[arg_list.start_byte:arg_list.end_byte].decode("utf-8", errors="ignore").strip()
            sig = f"class {name}{params}"
        return sig
    elif symbol_type in ("function", "method"):
        sig = f"def {name}()"
        params_node = node.child_by_field_name("parameters")
        if params_node:
            params = code_bytes[params_node.start_byte:params_node.end_byte].decode("utf-8", errors="ignore").strip()
            sig = f"def {name}{params}"
        return sig
    return None


def collect_symbols(repo_path: str, docs: list) -> tuple:
    """
    Stage 1: Traverses AST of all Python files in the repository to collect
    fully qualified symbol definitions (classes, functions, methods, variables)
    and file imports maps.
    """
    symbol_table = {}
    file_imports = {}
    file_modules = {}

    for doc in docs:
        try:
            if not doc["file_path"].endswith(".py"):
                continue
                
            file_path = doc["file_path"].replace("\\", "/")
            code = doc["content"]
            code_bytes = bytes(code, "utf8")
            
            module_name = get_module_name(file_path, repo_path)
            file_modules[file_path] = module_name
            
            tree = parser.parse(code_bytes)
            imports = extract_file_imports(tree.root_node, module_name, code_bytes)
            file_imports[file_path] = imports
            
            def collect_symbols_recursive(node, class_fqn=None):
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
                            "inherits": inherits,
                            "line": node.start_point[0] + 1,
                            "end_line": node.end_point[0] + 1,
                            "docstring": get_docstring(node, code_bytes),
                            "signature": get_signature(node, "class", c_name, code_bytes)
                        }
                        
                        for child in node.children:
                            collect_symbols_recursive(child, fqn)
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
                            "inherits": [],
                            "line": node.start_point[0] + 1,
                            "end_line": node.end_point[0] + 1,
                            "docstring": get_docstring(node, code_bytes),
                            "signature": get_signature(node, symbol_type, f_name, code_bytes)
                        }
                        return
                        
                elif node.type == "assignment" and not class_fqn:
                    # Track module-level global variables
                    equal_idx = -1
                    for idx, c in enumerate(node.children):
                        if c.type == "=":
                            equal_idx = idx
                            break
                    if equal_idx != -1:
                        left_side = node.children[:equal_idx]
                        for part in left_side:
                            if part.type == "identifier":
                                var_name = get_text(part)
                                fqn = f"{module_name}.{var_name}"
                                symbol_table[fqn] = {
                                    "type": "variable",
                                    "name": var_name,
                                    "file": file_path,
                                    "parent_class": None,
                                    "inherits": [],
                                    "line": node.start_point[0] + 1
                                }

                for child in node.children:
                    collect_symbols_recursive(child, class_fqn)
                    
            collect_symbols_recursive(tree.root_node)
        except Exception as e:
            logger.error(f"[Defensive] Symbol collection failed for file {doc.get('file_path')}: {e}")

    return symbol_table, file_imports, file_modules


def extract_relationships(
    docs: list,
    symbol_table: dict,
    file_imports: dict,
    file_modules: dict
) -> tuple:
    """
    Stage 2: Traverses files to extract structural containing layouts
    and semantic dependency call graphs.
    """
    nodes = []
    edges = []
    seen_nodes = set()
    total_resolved = 0
    total_unresolved = 0
    unresolved_references = []

    for doc in docs:
        try:
            if not doc["file_path"].endswith(".py"):
                continue
                
            file_path = doc["file_path"].replace("\\", "/")
            code = doc["content"]
            code_bytes = bytes(code, "utf8")
            module_name = file_modules[file_path]
            imports = file_imports[file_path]

            tree = parser.parse(code_bytes)
            root = tree.root_node

            # 1. Register File Node (Module)
            if file_path not in seen_nodes:
                file_name = os.path.basename(file_path)
                file_doc = None
                if root.children and root.children[0].type == "expression_statement":
                    string_nodes = [c for c in root.children[0].children if c.type == "string"]
                    if string_nodes:
                        string_node = string_nodes[0]
                        text = code_bytes[string_node.start_byte:string_node.end_byte].decode("utf-8", errors="ignore").strip()
                        if text.startswith('"""') or text.startswith("'''"):
                            file_doc = text[3:-3].strip()

                nodes.append(GraphNode(
                    id=file_path,
                    type="file",
                    symbol_name=file_name,
                    qualified_name=file_path,
                    file_path=file_path,
                    node_type="file",
                    docstring=file_doc,
                    start_line=1,
                    end_line=len(code.split("\n"))
                ))
                seen_nodes.add(file_path)

            # 2. Extract imports relationships
            for local_name, (imported_fqn, import_type) in imports.items():
                if import_type == "symbol":
                    # Defensively look up file in symbol table
                    dest_file = symbol_table.get(imported_fqn, {}).get("file")
                    edges.append(GraphEdge(
                        source=file_path,
                        target=imported_fqn,
                        relation="imports",
                        source_file=file_path,
                        destination_file=dest_file,
                        resolved=(imported_fqn in symbol_table)
                    ))

            def get_text(node):
                return code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore").strip()

            # Walk structural AST to capture classes, methods, and containment edges
            def walk_structural(node, current_class_fqn=None):
                if node.type == "class_definition":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        c_name = get_text(name_node)
                        class_fqn = f"{module_name}.{c_name}"
                        meta = symbol_table.get(class_fqn, {})
                        
                        if class_fqn not in seen_nodes:
                            nodes.append(GraphNode(
                                id=class_fqn,
                                type="class",
                                symbol_name=c_name,
                                qualified_name=class_fqn,
                                file_path=file_path,
                                node_type="class",
                                docstring=meta.get("docstring"),
                                signature=meta.get("signature"),
                                start_line=meta.get("line"),
                                end_line=meta.get("end_line")
                            ))
                            seen_nodes.add(class_fqn)
                            
                        parent_id = current_class_fqn if current_class_fqn else file_path
                        edges.append(GraphEdge(
                            source=parent_id,
                            target=class_fqn,
                            relation="contains",
                            source_file=file_path
                        ))
                        edges.append(GraphEdge(
                            source=parent_id,
                            target=class_fqn,
                            relation="defines",
                            source_file=file_path
                        ))

                        # Inherits Relation
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
                                    res = resolve_simple(
                                        superclass_name, imports, symbol_table, module_name
                                    )
                                    edges.append(GraphEdge(
                                        source=class_fqn,
                                        target=res.resolved_fqn,
                                        relation="inherits",
                                        source_file=file_path,
                                        destination_file=symbol_table.get(res.resolved_fqn, {}).get("file"),
                                        resolved=res.resolved,
                                        confidence=res.confidence
                                    ))

                        # Decorates Relation
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
                                    res = resolve_name(
                                        callable_name, None, imports, symbol_table, {}, module_name
                                    )
                                    edges.append(GraphEdge(
                                        source=res.resolved_fqn,
                                        target=class_fqn,
                                        relation="decorates",
                                        source_file=file_path,
                                        destination_file=symbol_table.get(res.resolved_fqn, {}).get("file"),
                                        resolved=res.resolved,
                                        confidence=res.confidence
                                    ))

                        for child in node.children:
                            walk_structural(child, class_fqn)
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
                        meta = symbol_table.get(func_fqn, {})
                            
                        if func_fqn not in seen_nodes:
                            nodes.append(GraphNode(
                                id=func_fqn,
                                type=func_type,
                                symbol_name=f_name,
                                qualified_name=func_fqn,
                                file_path=file_path,
                                node_type=func_type,
                                docstring=meta.get("docstring"),
                                signature=meta.get("signature"),
                                start_line=meta.get("line"),
                                end_line=meta.get("end_line")
                            ))
                            seen_nodes.add(func_fqn)
                            
                        parent_id = current_class_fqn if current_class_fqn else file_path
                        edges.append(GraphEdge(
                            source=parent_id,
                            target=func_fqn,
                            relation="contains",
                            source_file=file_path
                        ))
                        edges.append(GraphEdge(
                            source=parent_id,
                            target=func_fqn,
                            relation="defines",
                            source_file=file_path
                        ))

                        # Decorates Relation
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
                                    res = resolve_name(
                                        callable_name, None, imports, symbol_table, {}, module_name
                                    )
                                    edges.append(GraphEdge(
                                        source=res.resolved_fqn,
                                        target=func_fqn,
                                        relation="decorates",
                                        source_file=file_path,
                                        destination_file=symbol_table.get(res.resolved_fqn, {}).get("file"),
                                        resolved=res.resolved,
                                        confidence=res.confidence
                                    ))
                        return

                for child in node.children:
                    walk_structural(child, current_class_fqn)

            walk_structural(root)

            # 3. Extract semantic call relations
            from app.services.call_graph import extract_semantic_relations
            call_relations, res_count, unres_count, unres_list = extract_semantic_relations(
                code, file_path, module_name, imports, symbol_table
            )
            total_resolved += res_count
            total_unresolved += unres_count
            unresolved_references.extend(unres_list)

            for rel in call_relations:
                edges.append(GraphEdge(
                    source=rel["source"],
                    target=rel["target"],
                    relation=rel["relation"],
                    source_file=file_path,
                    destination_file=symbol_table.get(rel["target"], {}).get("file") if rel.get("resolved") else None,
                    line=rel.get("line"),
                    confidence=rel.get("confidence", "high"),
                    resolved=rel.get("resolved", True)
                ))

            # 4. Register variables as symbols in the nodes list and link them to container
            for fqn, meta in symbol_table.items():
                if meta["type"] == "variable" and meta["file"] == file_path:
                    if fqn not in seen_nodes:
                        nodes.append(GraphNode(
                            id=fqn,
                            type="variable",
                            symbol_name=meta["name"],
                            qualified_name=fqn,
                            file_path=file_path,
                            node_type="variable",
                            start_line=meta.get("line"),
                            end_line=meta.get("line")
                        ))
                        seen_nodes.add(fqn)
                    # Link variables using contains and defines relations
                    edges.append(GraphEdge(
                        source=file_path,
                        target=fqn,
                        relation="contains",
                        source_file=file_path
                    ))
                    edges.append(GraphEdge(
                        source=file_path,
                        target=fqn,
                        relation="defines",
                        source_file=file_path
                    ))
        except Exception as e:
            logger.error(f"[Defensive] Relationship extraction failed for file {doc.get('file_path')}: {e}")

    return nodes, edges, total_resolved, total_unresolved, unresolved_references


def build_hierarchy(nodes: list, edges: list, repo_path: str) -> list:
    """
    Constructs the parent-child nesting tree from contains relations and file directories.
    Generates Repository and Package nodes dynamically, and computes hierarchy_depth.
    """
    repo_normalized = repo_path.replace("\\", "/").rstrip("/")
    repo_name = repo_normalized.split("/")[-1]
    
    # Locate Repository node or create it
    repo_node = None
    for n in nodes:
        if n.id == repo_normalized or n.qualified_name == repo_normalized:
            repo_node = n
            break
            
    if not repo_node:
        repo_node = GraphNode(
            id=repo_normalized,
            type="repository",
            symbol_name=repo_name,
            qualified_name=repo_normalized,
            file_path=repo_normalized,
            node_type="repository",
            docstring="Root repository hierarchy node."
        )
        nodes.append(repo_node)

    # Dictionary lookup of all current nodes
    nodes_dict = {n.id: n for n in nodes}
    
    # 1. Establish parent-child references using structural containment edges
    for edge in edges:
        if edge.relation in ("contains", "defines"):
            parent_node = nodes_dict.get(edge.source)
            child_node = nodes_dict.get(edge.target)
            if parent_node and child_node:
                child_node.parent = parent_node.id
                if child_node.id not in parent_node.children:
                    parent_node.children.append(child_node.id)

    # 2. Walk up file directory paths to create Package nodes recursively
    file_nodes = [n for n in nodes if n.node_type == "file"]
    for n in file_nodes:
        child_id = n.id
        curr_dir = os.path.dirname(child_id).replace("\\", "/")
        
        while True:
            if not curr_dir or curr_dir == "." or curr_dir == repo_normalized or len(curr_dir) < len(repo_normalized):
                n_root = nodes_dict.get(repo_normalized)
                n_child = nodes_dict.get(child_id)
                if n_root and n_child:
                    n_child.parent = n_root.id
                    if n_child.id not in n_root.children:
                        n_root.children.append(n_child.id)
                break
            else:
                pkg_node = nodes_dict.get(curr_dir)
                if not pkg_node:
                    pkg_name = curr_dir.split("/")[-1]
                    pkg_node = GraphNode(
                        id=curr_dir,
                        type="package",
                        symbol_name=pkg_name,
                        qualified_name=curr_dir,
                        file_path=curr_dir,
                        node_type="package",
                        parent=None,
                        children=[],
                        docstring="Directory package node."
                    )
                    nodes.append(pkg_node)
                    nodes_dict[curr_dir] = pkg_node
                    
                n_child = nodes_dict.get(child_id)
                if n_child:
                    n_child.parent = pkg_node.id
                    if n_child.id not in pkg_node.children:
                        pkg_node.children.append(n_child.id)
                        
                child_id = curr_dir
                curr_dir = os.path.dirname(curr_dir).replace("\\", "/")

    # 3. Calculate package paths for all nodes
    for n in nodes:
        if n.node_type == "repository":
            n.package = None
            n.module = None
        elif n.node_type == "package":
            n.package = os.path.dirname(n.id).replace("\\", "/")
            n.module = None
        elif n.node_type == "file":
            n.package = os.path.dirname(n.id).replace("\\", "/")
            n.module = n.symbol_name[:-3] if n.symbol_name.endswith(".py") else n.symbol_name
        else:
            n.package = os.path.dirname(n.file_path).replace("\\", "/")
            parts = n.id.split(".")
            n.module = parts[0] if parts else None

    # 4. Resolve depth levels recursively
    memo_depth = {}
    def calculate_depth(node_id, visited=None):
        if visited is None:
            visited = set()
        if node_id in memo_depth:
            return memo_depth[node_id]
        if node_id in visited:
            return 0
            
        visited.add(node_id)
        node = nodes_dict.get(node_id)
        if not node or not node.parent:
            memo_depth[node_id] = 0
            return 0
            
        d = 1 + calculate_depth(node.parent, visited)
        memo_depth[node_id] = d
        return d

    for n in nodes:
        n.hierarchy_depth = calculate_depth(n.id)

    return nodes


def validate_edges(edges: list, nodes_set: set) -> tuple:
    """
    Stage 3: Validates edges. Ensures every edge's source and target exist in the nodes set,
    or registers fallback dummy nodes for external references/symbols to prevent broken visual linkages.
    """
    valid_edges = []
    additional_nodes = []
    seen_additional = set()

    for edge in edges:
        # Prevent self loops
        if edge.source == edge.target:
            continue
            
        # Source boundary check
        if edge.source not in nodes_set and edge.source not in seen_additional:
            name_part = edge.source.split(".")[-1]
            additional_nodes.append(GraphNode(
                id=edge.source,
                type="module" if "." in edge.source else "class",
                symbol_name=name_part,
                qualified_name=edge.source,
                file_path=edge.source_file,
                node_type="module" if "." in edge.source else "class",
                docstring="External package or dependency boundary symbol."
            ))
            seen_additional.add(edge.source)

        # Target boundary check
        if edge.target not in nodes_set and edge.target not in seen_additional:
            dest_file = edge.destination_file if edge.destination_file else "external"
            name_part = edge.target.split(".")[-1]
            additional_nodes.append(GraphNode(
                id=edge.target,
                type="module" if "." in edge.target else "class",
                symbol_name=name_part,
                qualified_name=edge.target,
                file_path=dest_file,
                node_type="module" if "." in edge.target else "class",
                docstring="External package or dependency boundary symbol."
            ))
            seen_additional.add(edge.target)

        valid_edges.append(edge)

    return valid_edges, additional_nodes


def build_graph(nodes: list, edges: list, metadata: GraphMetadata) -> dict:
    """
    Stage 4: Integrates metadata and serializes Pydantic structures into a dictionary schema.
    """
    return {
        "metadata": metadata.dict(),
        "nodes": [n.dict() for n in nodes],
        "edges": [e.dict() for e in edges]
    }


def serialize_graph(graph: dict, graph_name: str) -> None:
    """
    Stage 5: Saves the serialized graph dict into a JSON file in the graphs/ directory.
    """
    os.makedirs("graphs", exist_ok=True)
    with open(
        f"graphs/{graph_name}",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(graph, f, indent=4)


def build_repository_graph(repo_path: str) -> dict:
    """
    Coordinates modular stages to construct the complete codebase semantic knowledge graph.
    """
    # Normalize repo root path
    repo_path_normalized = repo_path.replace("\\", "/")
    logger.info(f"[Resilient Graph] Ingesting repository from: {repo_path_normalized}")
    
    try:
        docs = parse_repository(repo_path_normalized)
    except Exception as e:
        logger.error(f"[Defensive] Repository parsing failed: {e}")
        docs = []

    # 1. Collect Symbols
    try:
        symbol_table, file_imports, file_modules = collect_symbols(repo_path_normalized, docs)
        logger.info(f"Stage 1 Complete: Collected {len(symbol_table)} symbols.")
    except Exception as e:
        logger.error(f"[Defensive] Symbol collection failed: {e}")
        symbol_table, file_imports, file_modules = {}, {}, {}
    
    # 2. Extract Relationships
    try:
        nodes, edges, total_resolved, total_unresolved, unresolved_references = extract_relationships(
            docs, symbol_table, file_imports, file_modules
        )
        logger.info(f"Stage 2 Complete: Extracted {len(nodes)} raw nodes and {len(edges)} raw edges.")
    except Exception as e:
        logger.error(f"[Defensive] Relationship extraction failed: {e}")
        nodes, edges, total_resolved, total_unresolved, unresolved_references = [], [], 0, 0, []

    # 3. Validate Edges
    try:
        nodes_set = {n.id for n in nodes}
        validated_edges, boundary_nodes = validate_edges(edges, nodes_set)
        nodes.extend(boundary_nodes)
        logger.info(f"Stage 3 Complete: Validated edges, added {len(boundary_nodes)} external node fallbacks.")
    except Exception as e:
        logger.error(f"[Defensive] Edge validation failed: {e}")
        validated_edges = []

    # 3.5. Build Hierarchy tree
    try:
        nodes = build_hierarchy(nodes, validated_edges, repo_path_normalized)
        logger.info("Stage 3.5 Complete: Repository hierarchy built recursively.")
    except Exception as e:
        logger.error(f"[Defensive] Hierarchy tree construction failed: {e}")
    
    # Compile Statistics
    resolution_percentage = 100.0
    total_refs = total_resolved + total_unresolved
    if total_refs > 0:
        resolution_percentage = (total_resolved / total_refs) * 100.0
        
    # Find top unresolved modules
    unresolved_modules = []
    for ref in unresolved_references:
        sym_name = ref.get("symbol_name", "")
        if sym_name:
            unresolved_modules.append(sym_name.split(".")[0])
    top_unresolved = [m for m, count in Counter(unresolved_modules).most_common(5)]

    logger.info(f"Resilient Graph Construction stats:")
    logger.info(f"  Resolved references: {total_resolved}")
    logger.info(f"  Unresolved references: {total_unresolved}")
    logger.info(f"  Resolution rate: {resolution_percentage:.2f}%")
    logger.info(f"  Top unresolved modules: {', '.join(top_unresolved)}")

    # 4. Assemble Graph
    url_parts = repo_path_normalized.rstrip("/").split("/")
    repo_identifier = "/".join(url_parts[-2:]) if len(url_parts) >= 2 else "repository"
    
    metadata = GraphMetadata(
        repository=repo_identifier,
        node_count=len(nodes),
        edge_count=len(validated_edges),
        additional_info={
            "files_parsed": len(docs),
            "symbols_discovered": len(symbol_table),
            "relationships_extracted": len(edges),
            "resolved_references": total_resolved,
            "unresolved_references": total_unresolved,
            "resolution_percentage": round(resolution_percentage, 2),
            "top_unresolved_modules": top_unresolved,
            "unresolved_logs": unresolved_references
        }
    )
    
    graph_dict = build_graph(nodes, validated_edges, metadata)
    logger.info("Stage 4 Complete: Knowledge graph assembled resiliently.")
    
    return graph_dict


def save_graph(graph: dict, graph_name="fastapi_graph.json") -> None:
    """
    Writes the constructed knowledge graph dict to disk.
    """
    try:
        serialize_graph(graph, graph_name)
        logger.info(f"Stage 5 Complete: Saved graph to graphs/{graph_name}")
    except Exception as e:
        logger.error(f"[Defensive] Graph serialization failed: {e}")