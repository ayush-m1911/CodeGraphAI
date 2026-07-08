"""
Purpose:
Constructs a semantic knowledge graph mapping structural and call dependencies in Python codebases.

Responsibilities:
* Collect global symbols and imports maps across all codebase files.
* Extract structural relationships (contains, defines, inherits, decorates, imports).
* Resolve semantic call, return, raising, and dataflow connections.
* Validate edge connections, creating boundary external symbol nodes where required.
* Serialize nodes and edges using strongly typed models (GraphNode, GraphEdge, GraphMetadata).

Inputs:
* Python repository root filesystem path.

Outputs:
* Serialized knowledge graph dictionary containing lists of nodes and edges matching schema.

Interaction with other modules:
* Reads code files via `parser.py`, uses tree-sitter bindings from `code_chunker.py`, imports semantic resolutions from `call_graph.py`, and is orchestrated by the `indexing_service.py` ingestion loop.
"""

import os
import json

from app.services.parser import parse_repository
from app.services.code_chunker import parser
from app.models.graph import GraphNode, GraphEdge, GraphMetadata


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


def collect_symbols(repo_path: str, docs: list) -> tuple:
    """
    Stage 1: Traverses AST of all Python files in the repository to collect
    fully qualified symbol definitions (classes, functions, methods, variables)
    and file imports maps.
    
    Inputs:
        repo_path (str): Local filesystem path of the repository.
        docs (list): List of parsed documents with file_path and content.
        
    Outputs:
        tuple: (symbol_table, file_imports, file_modules)
    """
    symbol_table = {}
    file_imports = {}
    file_modules = {}

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
                        "line": node.start_point[0] + 1
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
                        "line": node.start_point[0] + 1
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
    
    Inputs:
        docs (list): Ingested repository document models list.
        symbol_table (dict): Module and symbol metadata definitions list.
        file_imports (dict): Extracted file imports dictionary.
        file_modules (dict): Dotted module name lookup mapping.

    Outputs:
        tuple: (list of GraphNode, list of GraphEdge)
    """
    nodes = []
    edges = []
    seen_nodes = set()

    for doc in docs:
        if not doc["file_path"].endswith(".py"):
            continue
            
        file_path = doc["file_path"]
        code = doc["content"]
        code_bytes = bytes(code, "utf8")
        module_name = file_modules[file_path]
        imports = file_imports[file_path]

        # 1. Register File Node
        if file_path not in seen_nodes:
            nodes.append(GraphNode(
                id=file_path,
                type="file",
                file_path=file_path
            ))
            seen_nodes.add(file_path)

        # 2. Extract imports relationships
        for local_name, (imported_fqn, import_type) in imports.items():
            if import_type == "symbol":
                edges.append(GraphEdge(
                    source=file_path,
                    target=imported_fqn,
                    relation="imports",
                    source_file=file_path,
                    destination_file=symbol_table.get(imported_fqn, {}).get("file"),
                    resolved=True
                ))

        tree = parser.parse(code_bytes)
        root = tree.root_node

        def get_text(node):
            return code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore").strip()

        # Walk structural AST to capture classes, methods, and containment edges
        def walk_structural(node, current_class_fqn=None):
            if node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    c_name = get_text(name_node)
                    class_fqn = f"{module_name}.{c_name}"
                    
                    if class_fqn not in seen_nodes:
                        nodes.append(GraphNode(
                            id=class_fqn,
                            type="class",
                            file_path=file_path,
                            line=node.start_point[0] + 1
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
                                resolved_parent, resolved_status, confidence = resolve_simple(
                                    superclass_name, imports, symbol_table, module_name
                                )
                                edges.append(GraphEdge(
                                    source=class_fqn,
                                    target=resolved_parent,
                                    relation="inherits",
                                    source_file=file_path,
                                    destination_file=symbol_table.get(resolved_parent, {}).get("file"),
                                    resolved=resolved_status,
                                    confidence=confidence
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
                                resolved_dec, resolved_status, confidence = resolve_name(
                                    callable_name, None, imports, symbol_table, {}, module_name
                                )
                                edges.append(GraphEdge(
                                    source=resolved_dec,
                                    target=class_fqn,
                                    relation="decorates",
                                    source_file=file_path,
                                    destination_file=symbol_table.get(resolved_dec, {}).get("file"),
                                    resolved=resolved_status,
                                    confidence=confidence
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
                        
                    if func_fqn not in seen_nodes:
                        nodes.append(GraphNode(
                            id=func_fqn,
                            type=func_type,
                            file_path=file_path,
                            line=node.start_point[0] + 1
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
                                resolved_dec, resolved_status, confidence = resolve_name(
                                    callable_name, None, imports, symbol_table, {}, module_name
                                )
                                edges.append(GraphEdge(
                                    source=resolved_dec,
                                    target=func_fqn,
                                    relation="decorates",
                                    source_file=file_path,
                                    destination_file=symbol_table.get(resolved_dec, {}).get("file"),
                                    resolved=resolved_status,
                                    confidence=confidence
                                ))
                    return

            for child in node.children:
                walk_structural(child, current_class_fqn)

        walk_structural(root)

        # 3. Extract semantic call relations (calls, instantiates, returns, raises, reads_variable, writes_variable, uses_global, references)
        from app.services.call_graph import extract_semantic_relations
        call_relations, _, _ = extract_semantic_relations(
            code, file_path, module_name, imports, symbol_table
        )

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

        # 4. Register variables as symbols in the nodes list
        for fqn, meta in symbol_table.items():
            if meta["type"] == "variable" and meta["file"] == file_path:
                if fqn not in seen_nodes:
                    nodes.append(GraphNode(
                        id=fqn,
                        type="variable",
                        file_path=file_path,
                        line=meta.get("line")
                    ))
                    seen_nodes.add(fqn)

    return nodes, edges


def validate_edges(edges: list, nodes_set: set) -> tuple:
    """
    Stage 3: Validates edges. Ensures every edge's source and target exist in the nodes set,
    or registers fallback dummy nodes for external references/symbols to prevent broken visual linkages.

    Inputs:
        edges (list of GraphEdge): Raw edge models list.
        nodes_set (set of str): Collected FQN node IDs.

    Outputs:
        tuple: (list of GraphEdge, list of GraphNode)
    """
    valid_edges = []
    additional_nodes = []
    seen_additional = set()

    for edge in edges:
        # Prevent duplicates
        if edge.source == edge.target:
            continue
            
        # Source boundary check
        if edge.source not in nodes_set and edge.source not in seen_additional:
            additional_nodes.append(GraphNode(
                id=edge.source,
                type="module" if "." in edge.source else "class",
                file_path=edge.source_file,
                docstring="External package or dependency boundary symbol."
            ))
            seen_additional.add(edge.source)

        # Target boundary check
        if edge.target not in nodes_set and edge.target not in seen_additional:
            dest_file = edge.destination_file if edge.destination_file else "external"
            additional_nodes.append(GraphNode(
                id=edge.target,
                type="module" if "." in edge.target else "class",
                file_path=dest_file,
                docstring="External package or dependency boundary symbol."
            ))
            seen_additional.add(edge.target)

        valid_edges.append(edge)

    return valid_edges, additional_nodes


def build_graph(nodes: list, edges: list, metadata: GraphMetadata) -> dict:
    """
    Stage 4: Integrates metadata and serializes Pydantic structures into a dictionary schema.

    Inputs:
        nodes (list of GraphNode): Unified node models list.
        edges (list of GraphEdge): Validated edge models list.
        metadata (GraphMetadata): Graph metadata model.

    Outputs:
        dict: Standardized nodes and edges dictionary.
    """
    return {
        "metadata": metadata.dict(),
        "nodes": [n.dict() for n in nodes],
        "edges": [e.dict() for e in edges]
    }


def serialize_graph(graph: dict, graph_name: str) -> None:
    """
    Stage 5: Saves the serialized graph dict into a JSON file in the graphs/ directory.

    Inputs:
        graph (dict): Serialized repository graph dict.
        graph_name (str): Destination file name.
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

    Inputs:
        repo_path (str): Root filesystem folder of the Python repository.

    Outputs:
        dict: Standardized knowledge graph containing nodes list and edges list.
    """
    print(f"Ingesting repository from: {repo_path}")
    docs = parse_repository(repo_path)
    
    # 1. Collect Symbols
    symbol_table, file_imports, file_modules = collect_symbols(repo_path, docs)
    print(f"Stage 1 Complete: Collected {len(symbol_table)} symbols.")
    
    # 2. Extract Relationships
    nodes, edges = extract_relationships(docs, symbol_table, file_imports, file_modules)
    print(f"Stage 2 Complete: Extracted {len(nodes)} raw nodes and {len(edges)} raw edges.")
    
    # 3. Validate Edges
    nodes_set = {n.id for n in nodes}
    validated_edges, boundary_nodes = validate_edges(edges, nodes_set)
    nodes.extend(boundary_nodes)
    print(f"Stage 3 Complete: Validated edges, added {len(boundary_nodes)} external node fallbacks.")
    
    # 4. Assemble Graph
    url_parts = repo_path.replace(os.sep, '/').rstrip("/").split("/")
    repo_identifier = "/".join(url_parts[-2:]) if len(url_parts) >= 2 else "repository"
    
    metadata = GraphMetadata(
        repository=repo_identifier,
        node_count=len(nodes),
        edge_count=len(validated_edges),
        additional_info={
            "resolved_symbols": len(symbol_table)
        }
    )
    
    graph_dict = build_graph(nodes, validated_edges, metadata)
    print("Stage 4 Complete: Knowledge graph assembled.")
    
    return graph_dict


def save_graph(graph: dict, graph_name="fastapi_graph.json") -> None:
    """
    Writes the constructed knowledge graph dict to disk.
    """
    serialize_graph(graph, graph_name)
    print(f"Stage 5 Complete: Saved graph to graphs/{graph_name}")