"""
Purpose:
Defines strongly typed models for the hierarchical and semantic repository knowledge graph schema.

Responsibilities:
* GraphNode: Represents a node in the code intelligence graph with full hierarchical metadata.
* GraphEdge: Represents a semantic relationship link between nodes.
* GraphMetadata: Captures indexing metadata metrics of the constructed graph.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """
    Strongly typed model representing a code entity node with hierarchical parameters.
    """
    # Backward compatible fields
    id: str = Field(..., description="Unique identifier for the node (FQN or path).")
    type: str = Field(..., description="Type of node: file, class, method, function, module, variable, package, repository.")
    line: Optional[int] = Field(None, description="Legacy start line helper.")
    visibility: Optional[str] = Field(None, description="Visibility of the symbol: public or private.")

    # Enriched hierarchical metadata fields
    symbol_name: str = Field(..., description="Simple name of the symbol.")
    qualified_name: str = Field(..., description="Fully qualified name of the symbol.")
    package: Optional[str] = Field(None, description="Package or folder containing this symbol.")
    module: Optional[str] = Field(None, description="Dotted module name containing this symbol.")
    file_path: str = Field(..., description="Relative filesystem path where this node is located.")
    node_type: str = Field(..., description="Hierarchical node type.")
    parent: Optional[str] = Field(None, description="FQN or ID of the parent node.")
    children: List[str] = Field(default_factory=list, description="List of child node FQNs or IDs.")
    signature: Optional[str] = Field(None, description="Function parameter layout or class superclass listing.")
    docstring: Optional[str] = Field(None, description="Docstring extracted from the symbol block.")
    start_line: Optional[int] = Field(None, description="Start line number of the definition.")
    end_line: Optional[int] = Field(None, description="End line number of the definition.")
    hierarchy_depth: int = Field(0, description="Nesting level inside the repository tree hierarchy.")


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


class UnresolvedReference(BaseModel):
    """
    Strongly typed model representing an unresolved code symbol reference during indexing.
    """
    symbol_name: str = Field(..., description="Simple or dotted name of the unresolved symbol.")
    resolved_name: Optional[str] = Field(None, description="The FQN name resolution attempt, if any.")
    file: str = Field(..., description="Source file containing the unresolved reference.")
    line: Optional[int] = Field(None, description="Line number of the reference occurrence.")
    reason: Optional[str] = Field(None, description="Reason why resolution failed.")
    resolution_attempt: Optional[str] = Field(None, description="Description of the resolution strategy attempted.")
    context: Optional[str] = Field(None, description="Context code snippet around reference.")

