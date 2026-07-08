"""
Purpose:
Defines strongly typed models for the repository knowledge graph schema.

Responsibilities:
* GraphNode: Represents a node in the code intelligence graph.
* GraphEdge: Represents a semantic relationship link between nodes.
* GraphMetadata: Captures indexing metadata metrics of the constructed graph.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """
    Strongly typed model representing a code entity node.
    """
    id: str = Field(..., description="Unique identifier for the node, typically FQN or file path.")
    type: str = Field(..., description="Type of node: file, class, method, function, module, variable.")
    file_path: str = Field(..., description="Relative filesystem path where this node is located.")
    line: Optional[int] = Field(None, description="Start line number of the definition in the file.")
    visibility: Optional[str] = Field(None, description="Visibility of the symbol: public or private.")
    docstring: Optional[str] = Field(None, description="Docstring extracted from the symbol block.")


class GraphEdge(BaseModel):
    """
    Strongly typed model representing a semantic relation edge.
    """
    source: str = Field(..., description="Identifier of the source node.")
    target: str = Field(..., description="Identifier of the target node.")
    relation: str = Field(..., description="The semantic edge relationship type.")
    source_file: str = Field(..., description="Filesystem path of the source file.")
    destination_file: Optional[str] = Field(None, description="Filesystem path of the destination file if resolved.")
    line: Optional[int] = Field(None, description="Line number where the relationship occurs.")
    confidence: Optional[str] = Field("high", description="Resolution confidence: high, medium, low.")
    resolved: Optional[bool] = Field(True, description="Whether the destination node FQN was resolved.")


class GraphMetadata(BaseModel):
    """
    Strongly typed model capturing graph performance and collection stats.
    """
    repository: str = Field(..., description="Repository owner/name representation.")
    node_count: int = Field(0, description="Total node count.")
    edge_count: int = Field(0, description="Total edge count.")
    additional_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata dictionary.")
