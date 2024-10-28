from fastapi import FastAPI, HTTPException, status, Query
from contextlib import asynccontextmanager
from gremlin_python.process.graph_traversal import __
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver.serializer import GraphSONSerializersV3d0
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.structure.graph import Edge as GremlinEdge
from gremlin_python.structure.graph import Vertex as GremlinVertex

# from gremlin_python.process.traversal import T
# from gremlin_python.process.traversal import Cardinality

from models import *

# TODO: optimise gremlin python for fastapi

g = None


def convert_gremlin_vertex(vertex: GremlinVertex) -> NodeBase:
    d = dict()
    if vertex.properties is not None:
        d = {
            p.key: p.value for p in vertex.properties if p.key in NodeBase.model_fields
        }
    d["node_id"] = vertex.id
    d["node_type"] = vertex.label
    return NodeBase(**d)


def convert_gremlin_edge(edge: GremlinEdge) -> EdgeBase:
    d = dict()
    if edge.properties is not None:
        d = {p.key: p.value for p in edge.properties if p.key in EdgeBase.model_fields}
    print("edge ID from gremlin", edge.id)
    d["source"] = edge.inV.id
    d["target"] = edge.outV.id
    d["edge_type"] = edge.label
    return EdgeBase(**d)


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
    return {"nodes": vertex_count, "edges": edge_count}


@app.post("/network/reset", status_code=status.HTTP_205_RESET_CONTENT)
def reset_network() -> None:
    """Reset the whole network."""
    vertex_count = g.V().count().next()

    if vertex_count:
        g.V().drop().iterate()


@app.get("/network/connected/{node_id}", status_code=status.HTTP_205_RESET_CONTENT)
def get_network_from_node(
    node_id: NodeId, max_connections: Annotated[int, Query(get=0)] = None
):
    """Return the network containing a particular element with an optional limit number of connections."""
    raise NotImplementedError


### /nodes/* ###


@app.get("/nodes")
def get_node_list(node_type: NodeType | None = None) -> list[NodeBase]:
    """Return all vertices, optionally of a certain node type."""
    if node_type is not None:
        return g.V().has_label(node_type).to_list()
    return [
        convert_gremlin_vertex(vertex)
        for vertex in g.V().to_list()
        if vertex is not None
    ]


@app.get("/nodes/{node_id}")
def get_node(node_id: NodeId) -> NodeBase:
    """Return the node associated with the provided ID."""
    try:
        vertex = g.V(node_id).next()
    except StopIteration:
        raise HTTPException(status_code=404, detail="Node not found")
    return convert_gremlin_vertex(vertex)


@app.post("/nodes", status_code=status.HTTP_201_CREATED)
def create_node(node: NodeBase) -> NodeBase:
    """Create a node."""
    # TODO: Check for possible duplicates
    created_node = (
        g.add_v(node.node_type)
        .property("summary", node.summary)
        .property("description", node.description)
        .next()
    )
    return convert_gremlin_vertex(created_node)


@app.delete("/nodes/{node_id}", status_code=status.HTTP_205_RESET_CONTENT)
def delete_node(node_id: NodeId):
    """Delete the node with provided ID."""
    if not g.V(node_id).has_next():
        raise HTTPException(status_code=404, detail="Node not found")

    g.V(node_id).both_e().drop().iterate()
    g.V(node_id).drop().iterate()
    return {"message": "Node deleted successfully"}


@app.put("/nodes/{node_id}")
def update_node(node_id: NodeId, node: NodeBase):
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
def search_nodes(
    node_search: NodeSearch,
) -> list[NodeBase]:  # TODO: pros and cons of using a model here
    """Search in nodes."""
    traversal = g.V()
    if node_search.node_type is not None:
        traversal = traversal.has_label(node_search.node_type)
    if node_search.summary is not None:
        traversal = traversal.has("summary", node_search.summary)
    if node_search.description is not None:
        traversal = traversal.has("description", node_search.description)
    return [convert_gremlin_vertex(node) for node in traversal.to_list()]


### /edges/* ###


@app.get("/edges")
def get_edge_list() -> list[EdgeBase]:
    """Return all edges."""
    return [convert_gremlin_edge(edge) for edge in g.E().to_list() if edge is not None]


@app.get("/edges/find")
def find_edges(
    source_id: NodeId = None, target_id: NodeId = None, edge_type: EdgeType = None
) -> list[EdgeBase]:
    """Return the edge associated with the provided ID."""
    try:
        # Start with a base traversal
        traversal = g.E()

        # Add source condition if provided
        if source_id:
            traversal = traversal.where(__.out_v().hasId(source_id))

        # Add target condition if provided
        if target_id:
            traversal = traversal.where(__.in_v().hasId(target_id))

        # Add edge type condition if provided
        if edge_type:
            traversal = traversal.has_label(edge_type)

        # Execute the traversal and convert to list
        edges = traversal.to_list()

        # Check if edges are found
        if not edges:
            raise HTTPException(status_code=404, detail="No such edge found")

        return [convert_gremlin_edge(edge) for edge in edges]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/edges", status_code=201)
def create_edge(edge: EdgeBase) -> EdgeBase:
    """Create an edge."""
    # TODO: Check for possible duplicates
    try:
        created_edge = (
            g.V(edge.source).add_e(edge.edge_type).to(__.V(edge.target)).next()
        )
        return convert_gremlin_edge(created_edge)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Node or edge not found")


@app.delete("/edges/delete")
def delete_edges(edge: EdgeBase):
    """Delete the edge associated with provided ID."""
    try:
        traversal = (
            g.V(edge.source).outE(edge.edge_type).where(__.inV().hasId(edge.target))
        )
        traversal.drop().next()
        return {"message": "Edges deleted successfully"}
    except StopIteration:
        raise HTTPException(status_code=404, detail="Edge not found")


@app.put("/edges/update_property")
def update_edge_property(current_edge: EdgeBase, edge_property: EdgeBase):
    """Update the edge with provided ID."""
    try:
        traversal = (
            g.V(current_edge.source)
            .outE(current_edge.edge_type)
            .where(__.inV().hasId(current_edge.target))
        )
        traversal.property("edge_type", edge_property).iterate()
    except StopIteration:
        raise HTTPException(status_code=404, detail="Edge not found")

    return {"message": "Edge updated successfully"}
