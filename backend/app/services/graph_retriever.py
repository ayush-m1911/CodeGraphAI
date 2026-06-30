"""
Purpose:
Provides retrieval functions to query the repository knowledge graph file.

Role in CodeGraphAI:
Enables navigation of the repository knowledge graph by querying nodes and edges.
It retrieves neighbouring symbols and call relations for any target class or function name.

Key Responsibilities:
* Load the compiled JSON knowledge graph (active_graph.json or fallback fastapi_graph.json) from disk.
* Query edge relationships to return immediately adjacent symbols (neighborhood expansion) with relationship types.
* Accumulate distinct connected symbols for a given component.
"""

import json


def load_graph():
    """
    Loads the parsed repository knowledge graph JSON file from disk.

    Returns:
        dict: Nodes and edges structure.
    """
    import os
    path = "graphs/active_graph.json"
    if not os.path.exists(path):
        path = "graphs/fastapi_graph.json"

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def get_neighbors(
    symbol_name: str,
    max_neighbors: int = 20
):
    """
    Retrieves direct neighbors for a target symbol in the repository knowledge graph.

    Args:
        symbol_name (str): Fully-qualified symbol identifier.
        max_neighbors (int): Maximum neighbor limit (defaults to 20).

    Returns:
        list of dict: Neighbor nodes and edge relation types (e.g. {"node": target_node, "relation": "calls"|"contains"}).
    """

    graph = load_graph()

    neighbors = []

    for edge in graph["edges"]:

        if edge["source"] == symbol_name:

            neighbors.append(
                {
                    "node": edge["target"],
                    "relation": edge["relation"]
                }
            )

        elif edge["target"] == symbol_name:

            neighbors.append(
                {
                    "node": edge["source"],
                    "relation": edge["relation"]
                }
            )

    return neighbors[:max_neighbors]


def get_connected_symbols(
    symbol_name: str
):
    """
    Retrieves unique connected symbol names for a target node, ignoring relation types.

    Args:
        symbol_name (str): The origin symbol identifier.

    Returns:
        list of str: Distinct connected symbol names.
    """

    graph = load_graph()

    connected = set()

    for edge in graph["edges"]:

        if edge["source"] == symbol_name:

            connected.add(
                edge["target"]
            )

        if edge["target"] == symbol_name:

            connected.add(
                edge["source"]
            )

    return list(connected)