"""
Purpose:
Extracts semantic relationships (calls, instantiations, exception raising, dataflow variables, and return relationships) from Python source code ASTs.

Responsibilities:
* Parse function and method bodies recursively.
* Track local variable types (e.g. `obj = MyClass()`) for resolving method calls.
* Resolve `self.method(...)` and `cls.method(...)` by traversing the class inheritance chain.
* Resolve imported symbols to their fully qualified package names.
* Extract relationship types: `calls`, `instantiates`, `returns`, `raises`, `reads_variable`, `writes_variable`, `uses_global`, and `references` with confidence metrics.
* Distinguish repository symbols from external, builtin, stdlib, or unknown symbols defensively.

Failure handling:
* Avoids direct indexing of the symbol table that can produce KeyError.
* Only repository classes (present in `symbol_table`) are propagated into `local_vars` to prevent external noise.
* Self/cls method candidates and attribute calls are verified against `symbol_table` before being considered resolved.
* Unresolved or external library references do not create graph edges; instead, they are appended to the unresolved reference logs.

Inputs:
* Python source code code-bytes, local file imports dictionary, and repository symbol table mappings.

Outputs:
* Extracted semantic relationship lists with resolved FQNs and verification tags.
"""

import re
from app.services.code_chunker import parser


class ResolutionResult(dict):
    """
    Structured resolution result representing resolved status, FQN, confidence,
    reason, symbol type, and candidate matches.

    Inherits from dict and overrides __iter__ to support unpacking:
    resolved_fqn, resolved_status, confidence = resolve_name(...)
    """
    def __init__(self, resolved: bool, resolved_fqn: str, confidence: str, reason: str = "", symbol_type: str = "unknown", candidate_matches: list = None):
        super().__init__({
            "resolved": resolved,
            "resolved_fqn": resolved_fqn,
            "confidence": confidence,
            "reason": reason,
            "symbol_type": symbol_type, # "repository", "external", "builtin", "stdlib", "unknown"
            "candidate_matches": candidate_matches or []
        })
        self.resolved = resolved
        self.resolved_fqn = resolved_fqn
        self.confidence = confidence
        self.reason = reason
        self.symbol_type = symbol_type
        self.candidate_matches = candidate_matches or []

    def __iter__(self):
        # Support legacy 3-tuple unpacking
        return iter([self.resolved_fqn, self.resolved, self.confidence])


def classify_symbol(name: str, symbol_table: dict) -> str:
    """
    Classifies a symbol name to check its origin: repository, builtin, stdlib, external, or unknown.
    """
    if name in symbol_table:
        return "repository"
        
    import builtins
    if name in dir(builtins):
        return "builtin"
        
    parts = name.split(".")
    first_part = parts[0]
    
    stdlib_modules = {
        "os", "sys", "pathlib", "collections", "typing", "json", "re", "math", 
        "datetime", "time", "shutil", "stat", "subprocess", "logging", "hashlib",
        "io", "abc", "typing_extensions", "ast", "inspect", "importlib", "traceback"
    }
    if first_part in stdlib_modules:
        return "stdlib"
        
    external_prefixes = {
        "langchain_groq", "langchain", "fastapi", "torch", "transformers", "numpy",
        "pydantic", "qdrant_client", "celery", "redis", "fastapi_limiter", "starlette",
        "tree_sitter", "groq", "requests", "urllib3", "jinja2", "yaml", "httpx", "sqlalchemy"
    }
    if first_part in external_prefixes:
        return "external"
        
    if len(parts) > 1:
        return "external"
        
    return "unknown"


def resolve_simple(name: str, local_imports: dict, symbol_table: dict, current_module: str) -> ResolutionResult:
    """
    Resolves a simple or dotted name using local imports, current module, or global symbol table.
    Ensures resolved status is ONLY True if the resolved FQN exists in the symbol table.
    """
    # A. Check if the name is already a fully qualified symbol in the repository
    if name in symbol_table:
        return ResolutionResult(True, name, "high", "Exact match in symbol table", "repository")
        
    # B. Check local imports
    base_part = name.split(".", 1)[0]
    suffix = name.split(".", 1)[1] if "." in name else ""
    
    if base_part in local_imports:
        imported_fqn, import_type = local_imports[base_part]
        resolved_fqn = f"{imported_fqn}.{suffix}" if suffix else imported_fqn
        if resolved_fqn in symbol_table:
            return ResolutionResult(True, resolved_fqn, "high", "Resolved via local imports mapping to repository symbol", "repository")
        else:
            sym_type = classify_symbol(resolved_fqn, symbol_table)
            return ResolutionResult(False, resolved_fqn, "low", f"Imported symbol resolves to {sym_type} but is not defined in repository", sym_type)
            
    # C. Check wildcard imports
    for key, val in local_imports.items():
        if len(val) == 2 and val[1] == "wildcard":
            wildcard_module = val[0]
            potential_fqn = f"{wildcard_module}.{name}"
            if potential_fqn in symbol_table:
                return ResolutionResult(True, potential_fqn, "high", f"Resolved via wildcard import from {wildcard_module}", "repository")
                
    # D. Check if defined in the current module
    local_fqn = f"{current_module}.{name}"
    if local_fqn in symbol_table:
        return ResolutionResult(True, local_fqn, "high", "Resolved via local module match", "repository")
        
    # E. Check global symbol table fallback (unique simple name matching)
    matching_fqns = []
    for fqn in symbol_table:
        if fqn == name or fqn.endswith(f".{name}"):
            matching_fqns.append(fqn)
    if len(matching_fqns) == 1:
        return ResolutionResult(True, matching_fqns[0], "medium", "Resolved via fallback unique name suffix match", "repository")
    elif len(matching_fqns) > 1:
        sym_type = classify_symbol(name, symbol_table)
        return ResolutionResult(False, name, "low", "Ambiguous suffix matches found", sym_type, matching_fqns)
        
    # F. Unresolved / External fallback
    sym_type = classify_symbol(name, symbol_table)
    return ResolutionResult(False, name, "low", f"Symbol name not found in local scopes or imports ({sym_type})", sym_type)


def resolve_name(
    name: str,
    current_class_fqn: str,
    local_imports: dict,
    symbol_table: dict,
    local_vars: dict,
    current_module: str
) -> ResolutionResult:
    """
    Resolves any callable name in the context of a class method or function.
    Verifies existence inside symbol table before returning resolved status.
    """
    # 1. Check self. / cls.
    if name.startswith("self.") or name.startswith("cls."):
        if not current_class_fqn:
            return ResolutionResult(False, name, "low", "Access on self/cls outside class scope", "unknown")
        attr_name = name.split(".", 1)[1]
        
        # Traverse inheritance chain of current_class_fqn
        class_to_check = current_class_fqn
        visited = set()
        while class_to_check and class_to_check not in visited:
            visited.add(class_to_check)
            method_fqn = f"{class_to_check}.{attr_name}"
            if method_fqn in symbol_table:
                return ResolutionResult(True, method_fqn, "high", f"Resolved self/cls reference in class {class_to_check}", "repository")
            # Get parent classes
            class_meta = symbol_table.get(class_to_check)
            if class_meta and class_meta.get("inherits"):
                parent_resolved = None
                for parent_name in class_meta["inherits"]:
                    res = resolve_simple(parent_name, local_imports, symbol_table, current_module)
                    if res.resolved:
                        parent_resolved = res.resolved_fqn
                        break
                class_to_check = parent_resolved
            else:
                break
        # Fallback class resolution - but verify it exists in symbol_table
        fallback_fqn = f"{current_class_fqn}.{attr_name}"
        if fallback_fqn in symbol_table:
            return ResolutionResult(True, fallback_fqn, "high", "Fallback self/cls resolved to current class FQN", "repository")
        else:
            return ResolutionResult(False, fallback_fqn, "low", "Method does not exist on self/cls hierarchy", "unknown")

    # 2. Check local variable types (simple type propagation, e.g., obj.method)
    if "." in name:
        parts = name.split(".", 1)
        obj_name = parts[0]
        attr_name = parts[1]
        if local_vars and obj_name in local_vars:
            class_fqn = local_vars[obj_name]
            method_fqn = f"{class_fqn}.{attr_name}"
            if method_fqn in symbol_table:
                return ResolutionResult(True, method_fqn, "high", f"Resolved attribute call on variable of type {class_fqn}", "repository")
            else:
                return ResolutionResult(False, method_fqn, "low", f"Attribute {attr_name} does not exist in class {class_fqn}", "unknown")

    # 3. Resolve using simple name resolver
    return resolve_simple(name, local_imports, symbol_table, current_module)


def extract_semantic_relations(
    code: str,
    file_path: str,
    module_name: str,
    local_imports: dict,
    symbol_table: dict
) -> tuple:
    """
    Traverses the Python code AST to identify semantic caller-callee, instantiation, and return relationships.
    Only creates relationships when target resolved FQN exists inside the symbol table.
    """
    code_bytes = bytes(code, "utf8")
    tree = parser.parse(code_bytes)
    root = tree.root_node

    relations = []
    resolved_count = 0
    unresolved_count = 0
    unresolved_list = []

    # Scopes
    current_class_fqn = None
    current_function_fqn = None
    local_vars = {} # var_name -> class_fqn

    def get_text(node):
        return code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore").strip()

    def walk(node):
        nonlocal current_class_fqn, current_function_fqn, local_vars, resolved_count, unresolved_count, unresolved_list

        # --------------------
        # CLASS DEFINITION
        # --------------------
        if node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                c_name = get_text(name_node)
                prev_class = current_class_fqn
                current_class_fqn = f"{module_name}.{c_name}"
                
                for child in node.children:
                    walk(child)
                    
                current_class_fqn = prev_class
                return

        # --------------------
        # FUNCTION DEFINITION
        # --------------------
        elif node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                f_name = get_text(name_node)
                prev_func = current_function_fqn
                prev_vars = dict(local_vars)
                
                if current_class_fqn:
                    current_function_fqn = f"{current_class_fqn}.{f_name}"
                else:
                    current_function_fqn = f"{module_name}.{f_name}"
                local_vars = {} # Reset local variables for this function scope
                
                for child in node.children:
                    walk(child)
                    
                current_function_fqn = prev_func
                local_vars = prev_vars
                return

        # --------------------
        # ASSIGNMENT (TYPE PROPAGATION AND DATAFLOW)
        # --------------------
        if node.type == "assignment" and current_function_fqn:
            left_node = None
            right_node = None
            for child in node.children:
                if child.type == "identifier" and not left_node:
                    left_node = child
                elif child.type == "call":
                    right_node = child
            if left_node and right_node:
                var_name = get_text(left_node)
                callable_node = right_node.child_by_field_name("function")
                if callable_node:
                    callable_name = get_text(callable_node)
                    res = resolve_name(
                        callable_name, current_class_fqn, local_imports, symbol_table, local_vars, module_name
                    )
                    # Only propagate if class is defined inside the repository
                    if res.resolved and res.resolved_fqn in symbol_table:
                        meta = symbol_table.get(res.resolved_fqn)
                        if meta and meta.get("type") == "class":
                            local_vars[var_name] = res.resolved_fqn

            # Extract reads_variable, writes_variable, and uses_global relations
            equal_idx = -1
            for idx, c in enumerate(node.children):
                if c.type == "=":
                    equal_idx = idx
                    break
            if equal_idx != -1:
                left_side = node.children[:equal_idx]
                right_side = node.children[equal_idx+1:]
                
                def find_all_identifiers(subnode):
                    idents = []
                    if subnode.type == "identifier":
                        idents.append(subnode)
                    for ch in subnode.children:
                        idents.extend(find_all_identifiers(ch))
                    return idents

                # Written variables (writes_variable)
                for part in left_side:
                    for ident_node in find_all_identifiers(part):
                        var_name = get_text(ident_node)
                        res_fqn = f"{module_name}.{var_name}"
                        if res_fqn in symbol_table and symbol_table[res_fqn].get("type") == "variable":
                            relations.append({
                                "source": current_function_fqn,
                                "target": res_fqn,
                                "relation": "writes_variable",
                                "resolved": True,
                                "confidence": "high",
                                "file_path": file_path,
                                "line": ident_node.start_point[0] + 1
                            })
                            relations.append({
                                "source": current_function_fqn,
                                "target": res_fqn,
                                "relation": "uses_global",
                                "resolved": True,
                                "confidence": "high",
                                "file_path": file_path,
                                "line": ident_node.start_point[0] + 1
                            })
                        else:
                            unresolved_list.append({
                                "symbol_name": var_name,
                                "resolved_name": res_fqn,
                                "file": file_path,
                                "line": ident_node.start_point[0] + 1,
                                "reason": "Variable not defined in repository global scope",
                                "resolution_attempt": "writes_variable",
                                "context": get_text(ident_node)
                            })
                            unresolved_count += 1
                            
                # Read variables (reads_variable)
                for part in right_side:
                    for ident_node in find_all_identifiers(part):
                        var_name = get_text(ident_node)
                        res = resolve_name(
                            var_name, current_class_fqn, local_imports, symbol_table, local_vars, module_name
                        )
                        if res.resolved and res.resolved_fqn in symbol_table:
                            if symbol_table[res.resolved_fqn].get("type") == "variable":
                                relations.append({
                                    "source": current_function_fqn,
                                    "target": res.resolved_fqn,
                                    "relation": "reads_variable",
                                    "resolved": True,
                                    "confidence": res.confidence,
                                    "file_path": file_path,
                                    "line": ident_node.start_point[0] + 1
                                })
                                relations.append({
                                    "source": current_function_fqn,
                                    "target": res.resolved_fqn,
                                    "relation": "uses_global",
                                    "resolved": True,
                                    "confidence": res.confidence,
                                    "file_path": file_path,
                                    "line": ident_node.start_point[0] + 1
                                })
                            resolved_count += 1
                        else:
                            unresolved_count += 1
                            unresolved_list.append({
                                "symbol_name": var_name,
                                "resolved_name": res.resolved_fqn,
                                "file": file_path,
                                "line": ident_node.start_point[0] + 1,
                                "reason": res.reason,
                                "resolution_attempt": "resolve_name",
                                "context": get_text(ident_node)
                            })

        # --------------------
        # FUNCTION CALL
        # --------------------
        if node.type == "call" and current_function_fqn:
            callable_node = node.child_by_field_name("function")
            if callable_node:
                callable_name = get_text(callable_node)
                res = resolve_name(
                    callable_name, current_class_fqn, local_imports, symbol_table, local_vars, module_name
                )
                
                relation = "calls"
                if res.resolved and res.resolved_fqn in symbol_table:
                    meta = symbol_table.get(res.resolved_fqn)
                    if meta and meta.get("type") == "class":
                        relation = "instantiates"
                    resolved_count += 1
                    relations.append({
                        "source": current_function_fqn,
                        "target": res.resolved_fqn,
                        "relation": relation,
                        "resolved": res.resolved,
                        "confidence": res.confidence,
                        "file_path": file_path,
                        "line": node.start_point[0] + 1
                    })
                else:
                    unresolved_count += 1
                    unresolved_list.append({
                        "symbol_name": callable_name,
                        "resolved_name": res.resolved_fqn,
                        "file": file_path,
                        "line": node.start_point[0] + 1,
                        "reason": res.reason,
                        "resolution_attempt": "resolve_name",
                        "context": get_text(node)
                    })

        # --------------------
        # RETURN STATEMENT
        # --------------------
        if node.type == "return_statement" and current_function_fqn:
            ret_val_node = None
            for child in node.children:
                if child.type not in ("return", " "):
                    ret_val_node = child
                    break
            if ret_val_node:
                val_text = get_text(ret_val_node)
                if ret_val_node.type == "call":
                    callable_node = ret_val_node.child_by_field_name("function")
                    if callable_node:
                        val_text = get_text(callable_node)
                
                res = resolve_name(
                    val_text, current_class_fqn, local_imports, symbol_table, local_vars, module_name
                )
                if res.resolved and res.resolved_fqn in symbol_table:
                    relations.append({
                        "source": current_function_fqn,
                        "target": res.resolved_fqn,
                        "relation": "returns",
                        "resolved": True,
                        "confidence": res.confidence,
                        "file_path": file_path,
                        "line": node.start_point[0] + 1
                    })
                    resolved_count += 1
                else:
                    unresolved_count += 1
                    unresolved_list.append({
                        "symbol_name": val_text,
                        "resolved_name": res.resolved_fqn,
                        "file": file_path,
                        "line": node.start_point[0] + 1,
                        "reason": res.reason,
                        "resolution_attempt": "resolve_name",
                        "context": get_text(ret_val_node)
                    })

        # --------------------
        # RAISES STATEMENT
        # --------------------
        if node.type == "raise_statement" and current_function_fqn:
            raised_expr = None
            for child in node.children:
                if child.type not in ("raise", " "):
                    raised_expr = child
                    break
            if raised_expr:
                expr_text = get_text(raised_expr)
                if raised_expr.type == "call":
                    func_node = raised_expr.child_by_field_name("function")
                    if func_node:
                        expr_text = get_text(func_node)
                        
                res = resolve_name(
                    expr_text, current_class_fqn, local_imports, symbol_table, local_vars, module_name
                )
                if res.resolved and res.resolved_fqn in symbol_table:
                    resolved_count += 1
                    relations.append({
                        "source": current_function_fqn,
                        "target": res.resolved_fqn,
                        "relation": "raises",
                        "resolved": res.resolved,
                        "confidence": res.confidence,
                        "file_path": file_path,
                        "line": node.start_point[0] + 1
                    })
                else:
                    unresolved_count += 1
                    unresolved_list.append({
                        "symbol_name": expr_text,
                        "resolved_name": res.resolved_fqn,
                        "file": file_path,
                        "line": node.start_point[0] + 1,
                        "reason": res.reason,
                        "resolution_attempt": "resolve_name",
                        "context": get_text(raised_expr)
                    })

        # --------------------
        # REFERENCES & VARIABLES
        # --------------------
        if node.type == "identifier" and (current_function_fqn or current_class_fqn):
            name_text = get_text(node)
            if len(name_text) > 2:
                res = resolve_name(
                    name_text, current_class_fqn, local_imports, symbol_table, local_vars, module_name
                )
                if res.resolved and res.resolved_fqn in symbol_table and res.resolved_fqn != current_function_fqn and res.resolved_fqn != current_class_fqn:
                    meta = symbol_table.get(res.resolved_fqn)
                    if meta:
                        source_id = current_function_fqn if current_function_fqn else current_class_fqn
                        m_type = meta.get("type")
                        if m_type in ("class", "method", "function"):
                            relations.append({
                                "source": source_id,
                                "target": res.resolved_fqn,
                                "relation": "references",
                                "resolved": True,
                                "confidence": res.confidence,
                                "file_path": file_path,
                                "line": node.start_point[0] + 1
                            })
                            resolved_count += 1
                        elif m_type == "variable":
                            relations.append({
                                "source": source_id,
                                "target": res.resolved_fqn,
                                "relation": "reads_variable",
                                "resolved": True,
                                "confidence": res.confidence,
                                "file_path": file_path,
                                "line": node.start_point[0] + 1
                            })
                            relations.append({
                                "source": source_id,
                                "target": res.resolved_fqn,
                                "relation": "uses_global",
                                "resolved": True,
                                "confidence": res.confidence,
                                "file_path": file_path,
                                "line": node.start_point[0] + 1
                            })
                            relations.append({
                                "source": source_id,
                                "target": res.resolved_fqn,
                                "relation": "references",
                                "resolved": True,
                                "confidence": res.confidence,
                                "file_path": file_path,
                                "line": node.start_point[0] + 1
                            })
                            resolved_count += 1
                else:
                    # Capture actual external/builtin or missing imports as unresolved
                    if res.symbol_type in ("external", "stdlib", "builtin") or (local_imports and name_text in local_imports):
                        unresolved_count += 1
                        unresolved_list.append({
                            "symbol_name": name_text,
                            "resolved_name": res.resolved_fqn,
                            "file": file_path,
                            "line": node.start_point[0] + 1,
                            "reason": res.reason,
                            "resolution_attempt": "resolve_name",
                            "context": get_text(node)
                        })

        for child in node.children:
            walk(child)

    walk(root)
    return relations, resolved_count, unresolved_count, unresolved_list


def extract_function_calls(code, file_path):
    """
    Backward-compatible wrapper. Returns a list of call dictionaries.
    """
    code_bytes = bytes(code, "utf8")
    tree = parser.parse(code_bytes)
    root = tree.root_node
    call_edges = []
    current_function = None

    def walk(node):
        nonlocal current_function
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                prev = current_function
                current_function = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8", errors="ignore").strip()
                for child in node.children:
                    walk(child)
                current_function = prev
                return
        if node.type == "call" and current_function:
            callable_node = node.child_by_field_name("function")
            if callable_node:
                called = code_bytes[callable_node.start_byte:callable_node.end_byte].decode("utf-8", errors="ignore").strip()
                call_edges.append({
                    "source": current_function,
                    "target": called,
                    "relation": "calls",
                    "resolved": False,
                    "confidence": "low",
                    "file_path": file_path
                })
        for child in node.children:
            walk(child)

    walk(root)
    return call_edges