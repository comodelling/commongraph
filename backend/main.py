import os
import warnings
import logging
from pathlib import Path as PathlibPath

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import Order, P
from gremlin_python.structure.graph import Edge as GremlinEdge
from gremlin_python.structure.graph import Vertex as Gremlin_vertex
from janusgraph_python.driver.serializer import JanusGraphSONSerializersV3d0
from janusgraph_python.process.traversal import Text

from models import *


app = FastAPI(title="ObjectiveNet API", version="v0.1.0")

env_path = PathlibPath("/app/.env") if os.getenv("DOCKER_ENV") else PathlibPath(".env")

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    warnings.warn(
        f".env file not found at {env_path}, using default environment variables"
    )

origins = (
    [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")]
    if os.getenv("ALLOWED_ORIGINS")
    else []
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    janusgraph_host = os.getenv("JANUSGRAPH_HOST", "localhost")
    traversal_source = os.getenv("TRAVERSAL_SOURCE", "g")
    print("opening connection... with traversal_source:", traversal_source)
    connection = DriverRemoteConnection(
        f"ws://{janusgraph_host}:8182/gremlin",  # TODO: abstract in config
        traversal_source,
        message_serializer=JanusGraphSONSerializersV3d0(),
    )
    g = traversal().with_remote(connection)
    try:
        yield g
    finally:
        connection.close()


### root ###


@app.get("/")
async def root():
    return {"message": "Welcome to ObjectiveNet!"}


### /network/ ###


@app.get("/network")
def get_whole_network(
    db=Depends(get_db_connection),
) -> Subnet:
    """Return full network of nodes and edges from the database."""
    nodes = [
        convert_gremlin_vertex(vertex)
        for vertex in db.V().to_list()
        if vertex is not None
    ]
    edges = [
        convert_gremlin_edge(edge) for edge in db.E().to_list() if edge is not None
    ]
    return {"nodes": nodes, "edges": edges}


@app.get("/network/summary")
def get_network_summary(db=Depends(get_db_connection)) -> dict[str, int]:
    """Count nodes and edges."""
    vertex_count = db.V().count().next()
    edge_count = db.E().count().next()
    return {"nodes": vertex_count, "edges": edge_count}


@app.delete("/network", status_code=status.HTTP_205_RESET_CONTENT)
def reset_whole_network(db=Depends(get_db_connection)) -> None:
    """Delete all nodes and edges. Be careful!"""
    warnings.warn("Deleting all nodes and edges in the database!")
    vertex_count = db.V().count().next()

    if vertex_count:
        db.V().drop().iterate()


### /subnet/ ###


@app.put("/subnet")
def update_subnet(subnet: Subnet, db=Depends(get_db_connection)) -> Subnet:
    """Add missing nodes and edges and update existing ones (given IDs)."""
    mapping = {}
    nodes_out = []
    edges_out = []
    for node in subnet.nodes:
        try:
            if (
                node.node_id is not None and db.V(node.node_id).has_next()
            ):  # TODO: node_id shouldn't be none!
                # update node
                node_out = convert_gremlin_vertex(update_gremlin_node(node, db))
            else:
                # create node
                node_out = convert_gremlin_vertex(create_gremlin_node(node, db))
                node_out.id_from_ui = node.node_id  # TODO: add to history log instead
                mapping[node.node_id] = node_out.node_id
            nodes_out.append(node_out)
        except StopIteration:
            ...
    for edge in subnet.edges:
        try:
            if (
                db.V(edge.source)
                .out_e(edge.edge_type)
                .where(__.inV().has_id(edge.target))
                .has_next()
            ):
                # update edge
                edge_out = convert_gremlin_edge(update_gremlin_edge(edge, db))
            else:
                # create edge
                update_edge_source_from = None
                update_edge_target_from = None
                if edge.source in mapping:
                    update_edge_source_from = edge.source
                    edge.source = mapping[edge.source]
                if edge.target in mapping:
                    update_edge_target_from = edge.target
                    edge.target = mapping[edge.target]
                edge_out = convert_gremlin_edge(create_gremlin_edge(edge, db))
                edge_out.source_from_ui = update_edge_source_from
                edge_out.target_from_ui = update_edge_target_from
            edges_out.append(edge_out)
        except StopIteration:
            ...

    return {"nodes": nodes_out, "edges": edges_out}


@app.get("/subnet/{node_id}")
def get_induced_subnet(
    node_id: NodeId,
    levels: Annotated[int, Query(get=0)] = 2,
    db=Depends(get_db_connection),
) -> Subnet:
    """Return the subnet induced from a particular element with an optional limit number of connections.
    If no neighbour is found, a singleton subnet with a single node is returned from the provided ID.
    """
    try:
        # Start traversal from the given node
        trav = db.V(node_id).repeat(__.bothE().bothV()).times(levels).dedup()
        vertices = trav.toList()

        if not vertices:
            vertex = db.V(node_id).next()
            return {"nodes": [convert_gremlin_vertex(vertex)], "edges": []}

        # Collect edges separately
        edge_trav = (
            db.V(node_id)
            .repeat(__.bothE().bothV())
            .times(levels)
            .dedup()
            .bothE()
            .dedup()
        )
        edges = edge_trav.toList()

        # Convert vertices and edges to the appropriate data models
        nodes = [convert_gremlin_vertex(vertex) for vertex in vertices]
        edges = [convert_gremlin_edge(edge) for edge in edges]
        return {"nodes": nodes, "edges": edges}
    except StopIteration:
        raise HTTPException(status_code=404, detail="Node not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


### /nodes/ ###


@app.get("/nodes")
def search_nodes(
    node_type: list[NodeType] | NodeType = Query(None),
    title: str | None = None,
    scope: str | None = None,
    status: list[NodeStatus] | NodeStatus = Query(None),
    tags: list[str] | None = Query(None),
    description: str | None = None,
    db=Depends(get_db_connection),
) -> list[NodeBase]:
    """Search in nodes on a field by field level."""
    trav = db.V()
    if node_type is not None:
        if isinstance(node_type, list):
            trav = trav.has_label(P.within(node_type))
        elif isinstance(node_type, NodeType):
            trav = trav.has_label(node_type)
    if title:
        for word in title.split(" "):
            trav = trav.has("title", Text.text_contains_fuzzy(word))
        # trav = trav.has("title", Text.text_fuzzy(title))           # in-memory which can be costly
    if scope:
        for word in scope.split(" "):
            trav = trav.has("scope", Text.text_contains_fuzzy(scope))
    if status is not None:
        if isinstance(status, list):
            trav = trav.has("status", P.within(status))
        elif isinstance(status, NodeStatus):
            trav = trav.has("status", status)
    if tags:
        for tag in tags:
            trav = trav.has(
                "tags", Text.text_contains_fuzzy(tag)
            )  # Ok for now because tags is parsed as string
    if description:
        for word in description.split(" "):
            trav = trav.has("description", Text.text_contains_fuzzy(word))
    return [convert_gremlin_vertex(node) for node in trav.to_list()]


@app.get("/nodes/random")
def get_random_node(
    node_type: NodeType | None = None, db=Depends(get_db_connection)
) -> NodeBase:
    """Return a random node with optional node_type."""
    try:
        trav = db.V()
        if node_type is not None:
            trav = trav.has_label(node_type)
        vertex = trav.order().by(Order.shuffle).limit(1).next()
    except StopIteration:
        if node_type is not None:
            raise HTTPException(
                status_code=404,
                detail=f"Error fetching a random node of type {node_type}, there may be no node in the database",
            )
        raise HTTPException(
            status_code=404,
            detail="Error fetching a random node, there may be no node in the database",
        )
    return convert_gremlin_vertex(vertex)


@app.get("/nodes/{node_id}")
def get_node(node_id: NodeId, db=Depends(get_db_connection)) -> NodeBase:
    """Return the node associated with the provided ID."""
    try:
        vertex = db.V(node_id).next()
    except StopIteration:
        raise HTTPException(status_code=404, detail="Node not found")
    return convert_gremlin_vertex(vertex)


@app.post("/nodes", status_code=status.HTTP_201_CREATED)
def create_node(node: NodeBase, db=Depends(get_db_connection)) -> NodeBase:
    """Create a node."""
    # TODO: Check for possible duplicates
    created_node = create_gremlin_node(node, db)
    return convert_gremlin_vertex(created_node)


@app.delete("/nodes/{node_id}")  # , status_code=status.HTTP_205_RESET_CONTENT)
def delete_node(node_id: NodeId, db=Depends(get_db_connection)):
    """Delete the node with provided ID."""
    if not db.V(node_id).has_next():
        raise HTTPException(status_code=404, detail="Node not found")

    db.V(node_id).both_e().drop().iterate()
    db.V(node_id).drop().iterate()
    return {"message": "Node deleted"}


@app.put("/nodes")
def update_node(node: PartialNodeBase, db=Depends(get_db_connection)) -> NodeBase:
    """Update the properties of an existing node."""
    if not db.V(node.node_id).has_next():
        raise HTTPException(status_code=404, detail="Node not found")
    gremlin_vertex = update_gremlin_node(node, db)
    return convert_gremlin_vertex(gremlin_vertex)


### /edges/ ###


@app.get("/edges")
def get_edge_list(db=Depends(get_db_connection)) -> list[EdgeBase]:
    """Return all edges in the database."""
    return [convert_gremlin_edge(edge) for edge in db.E().to_list() if edge is not None]


@app.get("/edges/{source_id}/{target_id}")
def get_edge(
    source_id: NodeId, target_id: NodeId, db=Depends(get_db_connection)
) -> EdgeBase:
    """Return the edge associated with the provided ID."""
    try:
        traversal = db.V(source_id).out_e().where(__.in_v().has_id(target_id))
        edge = traversal.next()
        return convert_gremlin_edge(edge)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Edge not found")


@app.post("/edges/find")
def find_edges(
    source_id: NodeId = None,
    target_id: NodeId = None,
    edge_type: EdgeType = None,
    db=Depends(get_db_connection),
) -> list[EdgeBase]:
    """Return the edge associated with the provided ID."""
    try:
        # Start with a base traversal
        trav = db.E()

        # Add source condition if provided
        if source_id:
            trav = trav.where(__.out_v().has_id(source_id))

        # Add target condition if provided
        if target_id:
            trav = trav.where(__.in_v().has_id(target_id))

        # Add edge type condition if provided
        if edge_type:
            trav = trav.has_label(edge_type)

        # Execute the traversal and convert to list
        edges = trav.to_list()

        # Check if edges are found
        if not edges:
            return []

        return [convert_gremlin_edge(edge) for edge in edges]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/edges", status_code=201)
def create_edge(edge: EdgeBase, db=Depends(get_db_connection)) -> EdgeBase:
    """Create an edge."""
    # TODO: Check for possible duplicates
    try:
        created_edge = create_gremlin_edge(edge, db)
        return convert_gremlin_edge(created_edge)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Node or edge not found")


@app.delete(
    "/edges/{source_id}/{target_id}"
)  # , status_code=status.HTTP_205_RESET_CONTENT)
def delete_edge(
    source_id: NodeId,
    target_id: NodeId,
    edge_type: EdgeType | None = None,
    db=Depends(get_db_connection),
):
    """Delete the edge between two nodes and for an optional edge_type."""
    # logging.info(f"Attempting to delete edge from {source_id} to {target_id} with edge_type {edge_type}")
    trav = db.V(source_id)
    try:
        if edge_type is not None:
            trav = trav.out_e(edge_type).where(__.in_v().has_id(target_id))
        else:
            warnings.warn(
                "No edge type provided, deleting all edges from source to target"
            )
            trav = trav.out_e().where(__.in_v().has_id(target_id))
        # logging.info(f"Traversal query: {trav}")
        trav.drop().iterate()
        return {"message": "Edge deleted"}
    except StopIteration:
        logging.error(f"Edge from {source_id} to {target_id} not found")
        raise HTTPException(status_code=404, detail="Edge not found")


@app.put("/edges")
def update_edge(edge: EdgeBase, db=Depends(get_db_connection)) -> EdgeBase:
    """Update the properties of an edge."""
    try:
        if not exists_edge_in_db(edge, db):
            raise HTTPException(status_code=404, detail="Edge not found")
        gremlin_edge = update_gremlin_edge(edge, db)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Error updating edge")

    return convert_gremlin_edge(gremlin_edge)


# Utils


def create_gremlin_node(
    node: NodeBase, db=Depends(get_db_connection)
) -> Gremlin_vertex:
    """Create a gremlin vertex in the database."""
    created_node = db.add_v(node.node_type)
    # if node.node_id is not None:
    #    created_node = created_node.property(T.id, UUID(long=node.node_id))
    created_node = created_node.property("title", node.title)
    created_node = created_node.property("scope", node.scope)
    created_node = created_node.property("status", node.status)
    created_node = created_node.property("gradable", node.gradable)
    created_node = created_node.property("grade", node.grade)
    created_node = created_node.property("description", node.description)
    created_node = created_node.property("proponents", parse_list(node.proponents))
    created_node = created_node.property("references", parse_list(node.references))
    created_node = created_node.property("tags", parse_list(node.tags))
    return created_node.next()


def create_gremlin_edge(edge: EdgeBase, db=Depends(get_db_connection)) -> GremlinEdge:
    """Create a gremlin edge in the database."""
    created_edge = db.V(edge.source).add_e(edge.edge_type)
    created_edge = created_edge.property("cprob", edge.cprob)
    created_edge = created_edge.property("references", parse_list(edge.references))
    created_edge = created_edge.to(__.V(edge.target))
    return created_edge.next()


def exists_edge_in_db(edge: EdgeBase, db=Depends(get_db_connection)) -> bool:
    """Check if an edge exists in the database."""
    return (
        db.V(edge.source)
        .out_e(edge.edge_type)
        .where(__.in_v().has_id(edge.target))
        .has_next()
    )


def update_gremlin_node(
    node: NodeBase, db=Depends(get_db_connection)
) -> Gremlin_vertex | None:
    """Update the properties of a node defined by its ID."""
    updated_node = db.V(node.node_id)
    if node.node_type is not None:
        warnings.warn("node_type is not updatable because encoded as label")
    if node.title is not None:
        updated_node = updated_node.property("title", node.title)
    if node.scope is not None:
        updated_node = updated_node.property("scope", node.scope)
    if node.status is not None:
        updated_node = updated_node.property("status", node.status)
    if node.description is not None:
        updated_node = updated_node.property("description", node.description)
    if node.gradable is not None:
        updated_node = updated_node.property("gradable", node.gradable)
    if node.grade is not None:
        updated_node = updated_node.property("grade", node.grade)
    if node.references is not None:
        updated_node = updated_node.property("references", parse_list(node.references))
    if node.proponents is not None:
        updated_node = updated_node.property("proponents", parse_list(node.proponents))
    if node.tags is not None:
        updated_node = updated_node.property("tags", parse_list(node.tags))
    return updated_node.next()


def update_gremlin_edge(edge: EdgeBase, db=Depends(get_db_connection)) -> GremlinEdge:
    """Update the properties of an edge defined by its source and target nodes."""
    updated_edge = db.V(edge.source).out_e().where(__.in_v().has_id(edge.target))
    # TODO: test if any change is made and deal with mere additions
    if edge.edge_type is not None:
        warnings.warn("edge_type is not updatable because encoded as label")
    if edge.cprob is not None:
        updated_edge = updated_edge.property("cprob", edge.cprob)
    if edge.references is not None:
        updated_edge = updated_edge.property("references", parse_list(edge.references))
    return updated_edge.next()


def parse_list(l: list[str]) -> str | None:
    if len(l) == 0:
        return None
    if len(l) > 1:
        warnings.warn(
            "list properties are experimental and currently only supported with separator ;"
        )
    return ";".join(l)


def unparse_stringlist(s: str) -> list[str]:
    return s.split(";")


def convert_gremlin_vertex(vertex: Gremlin_vertex) -> NodeBase:
    """Convert a gremlin vertex to a NodeBase object."""
    d = dict()
    d["node_id"] = vertex.id
    d["node_type"] = vertex.label
    if vertex.properties is not None:
        for p in vertex.properties:
            if p.key in ["proponents", "references", "tags"]:
                d[p.key] = unparse_stringlist(p.value)
            elif (
                p.key in NodeBase.model_fields
                and p.key != "node_id"
                and p.key != "node_type"
            ):
                d[p.key] = p.value
            else:
                warnings.warn(f"invalid node property: {p.key}")
    return NodeBase(**d)


def convert_gremlin_edge(edge) -> EdgeBase:
    """Convert a gremlin edge to an EdgeBase object."""
    d = dict()
    d["source"] = edge.outV.id
    d["target"] = edge.inV.id
    d["edge_type"] = edge.label
    if edge.properties is not None:
        for p in edge.properties:
            if p.key == "references":
                d["references"] = unparse_stringlist(p.value)
            elif (
                p.key in EdgeBase.model_fields
                and p.key != "source"
                and p.key != "target"
                and p.key != "edge_type"
            ):
                d[p.key] = p.value
            else:
                warnings.warn(f"invalid edge property: {p.key}")
    return EdgeBase(**d)
