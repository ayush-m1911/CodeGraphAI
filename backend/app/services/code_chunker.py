from tree_sitter import Language, Parser
import tree_sitter_python

PY_LANGUAGE = Language(
    tree_sitter_python.language()
)

parser = Parser()
parser.language = PY_LANGUAGE


def extract_python_chunks(
    code,
    file_path
):
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
                        "file_path": file_path
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

                    chunks.append(
                        {
                            "text": method_chunk,
                            "metadata": {
                                "chunk_type": "method",
                                "symbol_name":
                                    f"{class_name}.{method_name}",
                                "file_path": file_path
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

            chunks.append(
                {
                    "text": function_chunk,
                    "metadata": {
                        "chunk_type": "function",
                        "symbol_name": function_name,
                        "file_path": file_path
                    }
                }
            )

    return chunks