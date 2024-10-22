from pydantic import BaseModel


class Node(BaseModel):
    node_type: str = "node"
    summary: str
    description: str | None = None


class Edge(BaseModel):
    edge_type: str
    source_node: int
    target_node: int


class NodeSearch(BaseModel):
    node_type: str | None = None
    summary: str | None = None
    description: str | None = None
