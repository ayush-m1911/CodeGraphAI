import json


GRAPH_PATH = "graphs/fastapi_graph.json"


def load_graph():

    with open(
        GRAPH_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def get_neighbors(
    symbol_name: str,
    max_neighbors: int = 20
):

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