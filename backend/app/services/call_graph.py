from app.services.code_chunker import parser


def extract_function_calls(
    code,
    file_path
):
    """
    Extract:

    function_a
        -> calls
    function_b
Q
    relationships
    """

    tree = parser.parse(
        bytes(code, "utf8")
    )

    root = tree.root_node

    call_edges = []

    current_function = None

    def walk(node):

        nonlocal current_function

        # --------------------
        # FUNCTION DEFINITION
        # --------------------

        if (
            node.type
            == "function_definition"
        ):

            name_node = (
                node.child_by_field_name(
                    "name"
                )
            )

            if name_node:

                previous_function = (
                    current_function
                )

                current_function = code[
                    name_node.start_byte:
                    name_node.end_byte
                ].strip()

                for child in node.children:
                    walk(child)

                current_function = (
                    previous_function
                )

                return

        # --------------------
        # FUNCTION CALL
        # --------------------

        if (
            node.type
            == "call"
            and current_function
        ):

            function_node = (
                node.child_by_field_name(
                    "function"
                )
            )

            if function_node:

                called_function = code[
                    function_node.start_byte:
                    function_node.end_byte
                ].strip()

                call_edges.append(
                    {
                        "source":
                        current_function,

                        "target":
                        called_function,

                        "relation":
                        "calls",

                        "file_path":
                        file_path
                    }
                )

        for child in node.children:
            walk(child)

    walk(root)

    return call_edges