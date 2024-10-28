from fastapi import FastAPI, HTTPException, status
from contextlib import asynccontextmanager
from gremlin_python.process.graph_traversal import __
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver.serializer import GraphSONSerializersV3d0
from gremlin_python.process.anonymous_traversal import traversal

# from gremlin_python.process.traversal import T
# from gremlin_python.process.traversal import Cardinality

from models import *

# TODO: optimise gremlin python for fastapi

g = None


def convert_vertex_to_node(vertex):
    d = {p.key: p.value for p in vertex.properties if p.key in Node.model_fields}
    if "node_id" not in d:
        d["node_id"] = vertex.id
    return Node(**d)


# TODO: is contrast vertex / node helpful? What equivalent for edge?


def setup_db_connection():
    connection = DriverRemoteConnection(
        "ws://localhost:8182/gremlin",  # TODO: abstract in config
        "g",
        message_serializer=GraphSONSerializersV3d0(),
    )
    global g
    g = traversal().with_remote(connection)
    return connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = setup_db_connection()
    yield
    connection.close()


app = FastAPI(
    lifespan=lifespan,
    title="Wishnet",
    description="API for Wishnet's backend",
    contact={"name": "Mario", "email": "mario.morvan@ucl.ac.uk"},
)

### root ###


@app.get("/")
async def root():
    return {"message": "Welcome to Wishnet!"}


# /network/* ###  TODO: reorganise code in submodules


@app.get("/network/summary")
def get_network_summary() -> dict[str, int]:
    """Return total number of nodes and edges."""
    vertex_count = g.V().count().next()
    edge_count = g.E().count().next()
    return {"vertices": vertex_count, "edges": edge_count}


@app.post("/network/reset", status_code=status.HTTP_205_RESET_CONTENT)
def resetting_network() -> None:
    """Reset the whole network."""
    vertex_count = g.V().count().next()

    if vertex_count:
        g.V().drop().iterate()


# @app.get("/network/{node_id}/connected", status_code=status.HTTP_205_RESET_CONTENT)
# def get_network_from_node(node_id: NodeIdAnnotation, max_connections: Annotated[int, Query(get=0)] = None):
#     """Return the network containing a particular element with an optional limit number of connections."""
#     raise NotImplementedError


### /nodes/* ###


@app.get("/nodes")
def get_node_list(node_type: NodeType | None = None) -> list[Node]:
    """Return all vertices, optionally of a certain node type."""
    if node_type is not None:
        return g.V().has_label(node_type).to_list()
    return [convert_vertex_to_node(vertex) for vertex in g.V().to_list()]


@app.get("/nodes/{node_id}")
def get_node(node_id: NodeId) -> Node:
    """Return the node associated with the provided ID."""
    try:
        vertex = g.V(node_id).next()
    except StopIteration:
        raise HTTPException(status_code=404, detail="Node not found")
    return convert_vertex_to_node(vertex)


@app.post("/nodes", status_code=status.HTTP_201_CREATED)
def create_node(node: Node) -> Node:
    """Create a node."""
    # TODO: Check for possible duplicates
    created_node = (
        g.add_v(node.node_type)
        .property("summary", node.summary)
        .property("description", node.description)
        .next()
    )
    return convert_vertex_to_node(created_node)


@app.delete("/nodes/{node_id}")
def delete_node(node_id: NodeId):
    """Delete the node with provided ID."""
    try:
        g.V(node_id).both_e().drop().next()
        g.V(node_id).drop().next()
        return {"message": "Node deleted successfully"}
    except StopIteration:
        raise HTTPException(status_code=404, detail="Node not found")


@app.put("/nodes/{node_id}")
def update_node(node_id: NodeId, node: Node):
    """Update the node with provided ID."""
    try:
        g.V(node_id).next()
    except StopIteration:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.summary is not None:
        g.V(node_id).property("summary", node.summary).iterate()
    if node.description is not None:
        g.V(node_id).property("description", node.description).iterate()
    return {"message": "Node updated successfully"}


@app.post("/nodes/search")
def search_nodes(node_search: NodeSearch):
    """Search in nodes."""
    traversal = g.V()
    if node_search.node_type is not None:
        traversal = traversal.has_label(node_search.node_type)
    if node_search.summary is not None:
        traversal = traversal.has("summary", node_search.summary)
    if node_search.description is not None:
        traversal = traversal.has("description", node_search.description)
    return traversal.to_list()


### /edges/* ###


@app.get("/edges")
def get_edge_list():
    """Return all edges."""
    return g.E().to_list()


@app.get("/edges/{edge_id}")
def get_edge(edge_id: EdgeId):
    """Return the edge associated with the provided ID."""
    try:
        return g.E(edge_id).next()
    except StopIteration:
        raise HTTPException(status_code=404, detail="Edge not found")


@app.post("/edges", status_code=201)
def create_edge(edge: Edge):
    """Create an edge."""
    # TODO: Check for possible duplicates
    try:
        created_edge = (
            g.V(edge.source).add_e(edge.edge_type).to(__.V(edge.target)).next()
        )
        return created_edge
    except StopIteration:
        raise HTTPException(status_code=404, detail="Node or edge not found")


@app.delete("/edges/{edge_id}")
def delete_edge(edge_id: EdgeId):
    """Delete the edge associated with provided ID."""
    try:
        g.E(edge_id).drop().next()
        return {"message": "Edge deleted successfully"}
    except StopIteration:
        raise HTTPException(status_code=404, detail="Edge not found")


@app.put("/edges/{edge_id}")
def update_node(edge_id: NodeId, edge: Edge):
    """Update the edge with provided ID."""
    raise NotImplementedError
    try:
        g.E(edge_id).next()
    except StopIteration:
        raise HTTPException(status_code=404, detail="Edge not found")

    return {"message": "Edge updated successfully"}
