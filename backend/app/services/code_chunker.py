"""
Purpose:
Performs AST-based chunking of Python source code using Tree-sitter.

Role in CodeGraphAI:
Splits raw file contents into logical code blocks corresponding to classes, methods, and functions.
By relying on Abstract Syntax Trees (ASTs) rather than sliding character/token windows, it ensures that
code blocks remain contextually whole, preserving logical structures for retrieval and LLM context.

Key Responsibilities:
* Parse raw Python source code strings into Tree-sitter syntax trees.
* Extract class definition code blocks, assigning them class-level metadata.
* Traverse inner class blocks to extract individual method definitions, mapping them to class-scoped symbols (e.g. ClassName.method_name).
* Identify and extract top-level functions.
* Populate each chunk with its target text, chunk type, absolute symbol name, and source file path.

Interview Readiness Note:
- Why Tree-sitter instead of Regex? Regex-based splitters easily break on complex nested blocks, decorators,
  multiline docstrings, and syntax edge cases. Tree-sitter parses the concrete syntax tree, ensuring robust and grammatically accurate extraction.
- Why method-level chunking? Sliding windows cut functions in half, dropping vital variable assignments, comments, or headers.
  Chunking at definition boundaries keeps logic fully intact, yielding high-fidelity context for code generation.
"""

from tree_sitter import Language, Parser
import tree_sitter_python

PY_LANGUAGE = Language(
    tree_sitter_python.language()
)

parser = Parser()
parser.language = PY_LANGUAGE


def extract_docstring(node, code: str) -> str:
    """
    Extracts docstrings from a class or function node.
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
                    doc = code[sub.start_byte:sub.end_byte].strip()
                    if (doc.startswith('"""') and doc.endswith('"""')) or (doc.startswith("'''") and doc.endswith("'''")):
                        return doc[3:-3].strip()
                    if (doc.startswith('"') and doc.endswith('"')) or (doc.startswith("'") and doc.endswith("'")):
                        return doc[1:-1].strip()
                    return doc
    return None


def extract_decorators(node, code: str) -> list:
    """
    Extracts decorators applied to a class or function.
    """
    decorators = []
    if node.parent and node.parent.type == "decorated_definition":
        for child in node.parent.children:
            if child.type == "decorator":
                decorators.append(code[child.start_byte:child.end_byte].strip())
    return decorators


def extract_function_info(node, code: str) -> tuple:
    """
    Extracts parameters and return type annotations from a function definition.
    """
    parameters = []
    return_annotation = None
    
    params_node = node.child_by_field_name("parameters")
    if params_node:
        for child in params_node.children:
            if child.type in ("identifier", "typed_parameter", "default_parameter"):
                parameters.append(code[child.start_byte:child.end_byte].strip())
                
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
        return_annotation = code[return_node.start_byte:return_node.end_byte].strip()
        
    return parameters, return_annotation


def extract_class_inheritance(node, code: str) -> list:
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
                inheritance.append(code[arg.start_byte:arg.end_byte].strip())
    return inheritance


def extract_python_chunks(
    code,
    file_path
):
    """
    Parses Python code into syntactically-valid chunks (classes, methods, top-level functions).

    Workflow:
    1. Parse source code using the tree-sitter Python language definition.
    2. Iterate over root node children to identify class and function definitions.
    3. For class definitions, record the class chunk, then iterate over its inner block to extract and record individual method definitions.
    4. Record top-level function chunks.

    Args:
        code (str): Raw python source code content.
        file_path (str): File path where the code is located, used for metadata tracing.

    Returns:
        list of dict: A list of chunks, each structured as:
            {
                "text": str,  # The original source text of the class/method/function
                "metadata": {
                    "chunk_type": "class" | "method" | "function",
                    "symbol_name": str,  # Fully-qualified symbol representation
                    "file_path": str,
                    "line_number": int,
                    "docstring": str or None,
                    "visibility": "public" | "private",
                    "inheritance": list or None,
                    "decorators": list,
                    "parameters": list or None,
                    "return_annotation": str or None
                }
            }
    """
    tree = parser.parse(
        bytes(code, "utf8")
    )

    root = tree.root_node

    chunks = []

    for child in root.children:

        # =====================================
        # CLASS CHUNKS
        # =====================================

        if child.type == "class_definition":

            class_chunk = code[
                child.start_byte:
                child.end_byte
            ]

            name_node = child.child_by_field_name(
                "name"
            )

            class_name = (
                name_node.text.decode("utf-8")
                if name_node
                else "Unknown"
            )

            # Store entire class
            chunks.append(
                {
                    "text": class_chunk,
                    "metadata": {
                        "chunk_type": "class",
                        "symbol_name": class_name,
                        "file_path": file_path,
                        "line_number": child.start_point[0] + 1,
                        "docstring": extract_docstring(child, code),
                        "visibility": "private" if class_name.startswith("_") else "public",
                        "inheritance": extract_class_inheritance(child, code),
                        "decorators": extract_decorators(child, code),
                        "parameters": None,
                        "return_annotation": None
                    }
                }
            )

            # =====================================
            # METHOD CHUNKS
            # =====================================

            for node in child.children:

                if node.type != "block":
                    continue

                for item in node.children:

                    if (
                        item.type
                        != "function_definition"
                    ):
                        continue

                    method_name_node = (
                        item.child_by_field_name(
                            "name"
                        )
                    )

                    if not method_name_node:
                        continue

                    method_name = (
                        method_name_node
                        .text
                        .decode("utf-8")
                    )

                    method_chunk = code[
                        item.start_byte:
                        item.end_byte
                    ]

                    params, ret_ann = extract_function_info(item, code)

                    chunks.append(
                        {
                            "text": method_chunk,
                            "metadata": {
                                "chunk_type": "method",
                                "symbol_name":
                                    f"{class_name}.{method_name}",
                                "file_path": file_path,
                                "line_number": item.start_point[0] + 1,
                                "docstring": extract_docstring(item, code),
                                "visibility": "private" if method_name.startswith("_") else "public",
                                "inheritance": None,
                                "decorators": extract_decorators(item, code),
                                "parameters": params,
                                "return_annotation": ret_ann
                            }
                        }
                    )

        # =====================================
        # TOP LEVEL FUNCTIONS
        # =====================================

        elif child.type == "function_definition":

            function_chunk = code[
                child.start_byte:
                child.end_byte
            ]

            name_node = child.child_by_field_name(
                "name"
            )

            function_name = (
                name_node.text.decode("utf-8")
                if name_node
                else "Unknown"
            )

            params, ret_ann = extract_function_info(child, code)

            chunks.append(
                {
                    "text": function_chunk,
                    "metadata": {
                        "chunk_type": "function",
                        "symbol_name": function_name,
                        "file_path": file_path,
                        "line_number": child.start_point[0] + 1,
                        "docstring": extract_docstring(child, code),
                        "visibility": "private" if function_name.startswith("_") else "public",
                        "inheritance": None,
                        "decorators": extract_decorators(child, code),
                        "parameters": params,
                        "return_annotation": ret_ann
                    }
                }
            )

    return chunks
