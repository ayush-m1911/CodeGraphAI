import json

from app.services.parser import parse_repository
from app.services.code_chunker import parser
from app.services.call_graph import (
    extract_function_calls
)

def extract_graph(code, file_path):

    graph = {
        "nodes": [],
        "edges": []
    }

    seen_nodes = set()

    # -------------------------
    # FILE NODE
    # -------------------------

    graph["nodes"].append(
        {
            "id": file_path,
            "type": "file",
            "file_path": file_path
        }
    )

    seen_nodes.add(file_path)

    tree = parser.parse(
        bytes(code, "utf8")
    )

    root = tree.root_node

    for child in root.children:

        # =========================
        # CLASS DEFINITIONS
        # =========================

        if child.type == "class_definition":

            name_node = child.child_by_field_name(
                "name"
            )

            if not name_node:
                continue

            class_name = code[
                name_node.start_byte:
                name_node.end_byte
            ].strip()

            if not class_name:
                continue

            if class_name not in seen_nodes:

                graph["nodes"].append(
                    {
                        "id": class_name,
                        "type": "class",
                        "file_path": file_path
                    }
                )

                seen_nodes.add(class_name)

            graph["edges"].append(
                {
                    "source": file_path,
                    "target": class_name,
                    "relation": "contains"
                }
            )

            # =========================
            # METHODS
            # =========================

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

                    method_name = code[
                        method_name_node.start_byte:
                        method_name_node.end_byte
                    ].strip()

                    if (
                        not method_name
                        or "(" in method_name
                        or "\n" in method_name
                    ):
                        continue

                    method_id = (
                        f"{class_name}.{method_name}"
                    )

                    if (
                        method_id
                        not in seen_nodes
                    ):

                        graph["nodes"].append(
                            {
                                "id": method_id,
                                "type": "method",
                                "file_path": file_path
                            }
                        )

                        seen_nodes.add(
                            method_id
                        )

                    graph["edges"].append(
                        {
                            "source": class_name,
                            "target": method_id,
                            "relation": "contains"
                        }
                    )

        # =========================
        # TOP LEVEL FUNCTIONS
        # =========================

        elif (
            child.type
            == "function_definition"
        ):

            name_node = (
                child.child_by_field_name(
                    "name"
                )
            )

            if not name_node:
                continue

            function_name = code[
                name_node.start_byte:
                name_node.end_byte
            ].strip()

            if (
                not function_name
                or "(" in function_name
                or "\n" in function_name
            ):
                continue

            if (
                function_name
                not in seen_nodes
            ):

                graph["nodes"].append(
                    {
                        "id": function_name,
                        "type": "function",
                        "file_path": file_path
                    }
                )

                seen_nodes.add(
                    function_name
                )

            graph["edges"].append(
                {
                    "source": file_path,
                    "target": function_name,
                    "relation": "contains"
                }
            )

    return graph


def build_repository_graph(
    repo_path
):

    docs = parse_repository(
        repo_path
    )

    repository_graph = {
        "nodes": [],
        "edges": []
    }

    seen_nodes = set()

    for doc in docs:

        if not doc["file_path"].endswith(
            ".py"
        ):
            continue

        graph = extract_graph(
            doc["content"],
            doc["file_path"]
        )
        call_edges = extract_function_calls(
    doc["content"],
    doc["file_path"]
)
        for node in graph["nodes"]:

            if (
                node["id"]
                not in seen_nodes
            ):

                repository_graph[
                    "nodes"
                ].append(node)

                seen_nodes.add(
                    node["id"]
                )

        repository_graph[
            "edges"
        ].extend(
            graph["edges"]
        )
        repository_graph[
    "edges"
].extend(
    call_edges
)
    return repository_graph


def save_graph(
    graph,
    graph_name="fastapi_graph.json"
):

    with open(
        f"graphs/{graph_name}",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            graph,
            f,
            indent=4
        )