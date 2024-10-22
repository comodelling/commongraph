from pydantic import BaseModel


class Node(BaseModel):
    node_type: str = "node"
    summary: str
    description: str | None = None
    node_id: int | None = None  # only if retrieved from database


class Edge(BaseModel):
    edge_type: str
    source_node: int
    target_node: int
