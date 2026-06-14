from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any]


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    type: str
    properties: Dict[str, Any]


class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class ShortestPathRequest(BaseModel):
    source_id: str
    target_id: str
    max_depth: int = 5


class PathNode(BaseModel):
    id: str
    label: str
    type: str


class PathEdge(BaseModel):
    source: str
    target: str
    label: str


class ShortestPathResponse(BaseModel):
    path: List[PathNode]
    edges: List[PathEdge]
    length: int


class RelatedNodesRequest(BaseModel):
    node_id: str
    max_depth: int = 2
    node_types: Optional[List[str]] = None