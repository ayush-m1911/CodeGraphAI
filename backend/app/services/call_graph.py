"""
Purpose:
Extracts semantic function calls, instantiations, and return relationships from Python source code ASTs.

Role in CodeGraphAI:
Builds the enriched caller-callee relationship dataset. It uses a repository-wide symbol table and
local file imports to resolve raw names (like `self.method` or `Depends`) to fully qualified symbols,
enabling precise GraphRAG queries.

Key Responsibilities:
* Parse function and method bodies recursively.
* Track local variable types (e.g. `obj = MyClass()`) for resolving method calls.
* Resolve `self.method(...)` and `cls.method(...)` by traversing the class inheritance chain.
* Resolve imported symbols to their fully qualified package names.
* Extract relationship types: `calls`, `instantiates`, and `returns` with confidence metrics.
"""

import re
from app.services.code_chunker import parser

def resolve_simple(name: str, local_imports: dict, symbol_table: dict, current_module: str) -> tuple:
    """
    Resolves a simple or dotted name using local imports, current module, or global symbol table.

    Returns:
        tuple: (resolved_fqn, resolved_status, confidence)
    """
    # A. Check if the name is already a fully qualified symbol
    if name in symbol_table:
        return name, True, "high"
        
    # B. Check local imports
    base_part = name.split(".", 1)[0]
    suffix = name.split(".", 1)[1] if "." in name else ""
    
    if base_part in local_imports:
        imported_fqn, import_type = local_imports[base_part]
        if suffix:
            resolved_fqn = f"{imported_fqn}.{suffix}"
        else:
            resolved_fqn = imported_fqn
        return resolved_fqn, True, "high"
        
    # C. Check wildcard imports
    for key, val in local_imports.items():
        if len(val) == 2 and val[1] == "wildcard":
            wildcard_module = val[0]
            potential_fqn = f"{wildcard_module}.{name}"
            if potential_fqn in symbol_table:
                return potential_fqn, True, "high"
                
    # D. Check if defined in the current module
    local_fqn = f"{current_module}.{name}"
    if local_fqn in symbol_table:
        return local_fqn, True, "high"
        
    # E. Check global symbol table fallback (unique simple name matching)
    matching_fqns = []
    for fqn in symbol_table:
        if fqn == name or fqn.endswith(f".{name}"):
            matching_fqns.append(fqn)
    if len(matching_fqns) == 1:
        return matching_fqns[0], True, "medium"
        
    # F. Unresolved
    return name, False, "low"


def resolve_name(
    name: str,
    current_class_fqn: str,
    local_imports: dict,
    symbol_table: dict,
    local_vars: dict,
    current_module: str
) -> tuple:
    """
    Resolves any callable name in the context of a class method or function.

    Returns:
        tuple: (resolved_fqn, resolved_status, confidence)
    """
    # 1. Check self. / cls.
    if name.startswith("self.") or name.startswith("cls."):
        if not current_class_fqn:
            return name, False, "low"
        attr_name = name.split(".", 1)[1]
        
        # Traverse inheritance chain of current_class_fqn
        class_to_check = current_class_fqn
        visited = set()
        while class_to_check and class_to_check not in visited:
            visited.add(class_to_check)
            method_fqn = f"{class_to_check}.{attr_name}"
            if method_fqn in symbol_table:
                return method_fqn, True, "high"
            # Get parent classes
            class_meta = symbol_table.get(class_to_check)
            if class_meta and class_meta.get("inherits"):
                parent_resolved = None
                for parent_name in class_meta["inherits"]:
                    p_fqn, p_res, _ = resolve_simple(parent_name, local_imports, symbol_table, current_module)
                    if p_res:
                        parent_resolved = p_fqn
                        break
                class_to_check = parent_resolved
            else:
                break
        # Fallback to current class
        return f"{current_class_fqn}.{attr_name}", True, "high"

    # 2. Check local variable types (simple type propagation, e.g., obj.method)
    if "." in name:
        parts = name.split(".", 1)
        obj_name = parts[0]
        attr_name = parts[1]
        if local_vars and obj_name in local_vars:
            class_fqn = local_vars[obj_name]
            method_fqn = f"{class_fqn}.{attr_name}"
            return method_fqn, True, "high"

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

    Args:
        code (str): Source code content of the Python file.
        file_path (str): File path where the code resides.
        module_name (str): Dotted Python module name of the file.
        local_imports (dict): Extracted import mappings for this file.
        symbol_table (dict): Repository-wide symbol table.

    Returns:
        tuple: (relations_list, resolved_count, unresolved_count)
    """
    code_bytes = bytes(code, "utf8")
    tree = parser.parse(code_bytes)
    root = tree.root_node

    relations = []
    resolved_count = 0
    unresolved_count = 0

    # Scopes
    current_class_fqn = None
    current_function_fqn = None
    local_vars = {} # var_name -> class_fqn

    def get_text(node):
        return code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore").strip()

    def walk(node):
        nonlocal current_class_fqn, current_function_fqn, local_vars, resolved_count, unresolved_count

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
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                f_name = get_text(name_node)
                prev_func = current_function_fqn
                prev_vars = local_vars.copy()
                
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
        # ASSIGNMENT (TYPE PROPAGATION)
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
                    res_fqn, res_status, _ = resolve_name(
                        callable_name, current_class_fqn, local_imports, symbol_table, local_vars, module_name
                    )
                    if res_status:
                        meta = symbol_table.get(res_fqn)
                        if meta and meta.get("type") == "class":
                            local_vars[var_name] = res_fqn

        # --------------------
        # FUNCTION CALL
        # --------------------
        if node.type == "call" and current_function_fqn:
            callable_node = node.child_by_field_name("function")
            if callable_node:
                callable_name = get_text(callable_node)
                res_fqn, res_status, confidence = resolve_name(
                    callable_name, current_class_fqn, local_imports, symbol_table, local_vars, module_name
                )
                
                # Check if it's class instantiation or call
                relation = "calls"
                if res_status:
                    meta = symbol_table.get(res_fqn)
                    if meta and meta.get("type") == "class":
                        relation = "instantiates"
                    resolved_count += 1
                else:
                    unresolved_count += 1
                    
                relations.append({
                    "source": current_function_fqn,
                    "target": res_fqn,
                    "relation": relation,
                    "resolved": res_status,
                    "confidence": confidence,
                    "file_path": file_path
                })

        # --------------------
        # RETURN STATEMENT
        # --------------------
        if node.type == "return_statement" and current_function_fqn:
            # Find the return expression node
            ret_val_node = None
            for child in node.children:
                if child.type not in ("return", " "):
                    ret_val_node = child
                    break
            if ret_val_node:
                val_text = get_text(ret_val_node)
                # If it's a call, resolve the callable
                if ret_val_node.type == "call":
                    callable_node = ret_val_node.child_by_field_name("function")
                    if callable_node:
                        val_text = get_text(callable_node)
                
                res_fqn, res_status, confidence = resolve_name(
                    val_text, current_class_fqn, local_imports, symbol_table, local_vars, module_name
                )
                if res_status:
                    relations.append({
                        "source": current_function_fqn,
                        "target": res_fqn,
                        "relation": "returns",
                        "resolved": True,
                        "confidence": confidence,
                        "file_path": file_path
                    })

        for child in node.children:
            walk(child)

    walk(root)
    return relations, resolved_count, unresolved_count


def extract_function_calls(code, file_path):
    """
    Backward-compatible wrapper. Returns a list of call dictionaries.
    """
    # Since we need a symbol table for full semantic resolution,
    # this wrapper executes a simple raw extraction.
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
