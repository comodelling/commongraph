from fastapi import FastAPI, HTTPException, status, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import Order
from gremlin_python.structure.graph import Edge as GremlinEdge
from gremlin_python.structure.graph import Vertex as GremlinVertex
from janusgraph_python.driver.serializer import JanusGraphSONSerializersV3d0
from janusgraph_python.process.traversal import Text

# from gremlin_python.process.traversal import T
# from gremlin_python.process.traversal import Cardinality

from models import *

# TODO: optimise gremlin python for fastapi

app = FastAPI(
    title="ObjectiveNet API",
)
origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://127.0.0.1:5173",
    "https://localhost:5173",
    "https://localhost",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    connection = DriverRemoteConnection(
        "ws://localhost:8182/gremlin",  # TODO: abstract in config
        "g",
        message_serializer=JanusGraphSONSerializersV3d0(),
    )
    g = traversal().with_remote(connection)
    try:
        yield g
    finally:
        connection.close()


def convert_gremlin_vertex(vertex: GremlinVertex) -> NodeBase:
    d = dict()
    d["node_id"] = vertex.id
    d["node_type"] = vertex.label
    if vertex.properties is not None:
        for p in vertex.properties:
            if p.key == "proponent":
                if "proponents" not in d:
                    d["proponents"] = [p.value]
                else:
                    d["proponents"].append(p.value)
            elif p.key == "reference":
                if "references" not in d:
                    d["references"] = [p.value]
                else:
                    d["references"].append(p.value)
            elif p.key in NodeBase.model_fields:
                d[p.key] = p.value
            else:
                print("property not in model_fields", p.key)
    # print("vertex properties from gremlin", vertex.properties)
    # print("converted vertex", d)
    return NodeBase(**d)


def convert_gremlin_edge(edge) -> EdgeBase:
    d = dict()
    d["source"] = edge.outV.id
    d["target"] = edge.inV.id
    d["edge_type"] = edge.label
    if edge.properties is not None:
        for p in edge.properties:
            if p.key == "reference":
                if "references" not in d:
                    d["references"] = [p.value]
                else:
                    d["references"].append(p.value)
            elif p.key in EdgeBase.model_fields:
                d[p.key] = p.value
            else:
                print("property not in model_fields", p.key)
    # print("edge properties from gremlin", edge.properties)
    return EdgeBase(**d)


# TODO: is contrast vertex / node helpful? What equivalent for edge?


### root ###


@app.get("/")
async def root():
    return {"message": "Welcome to ObjectiveNet!"}


# /network/* ###  TODO: reorganise code in submodules


@app.get("/network")
def get_network(
    db=Depends(get_db_connection),
) -> Network:
    """Return total number of nodes and edges."""
    nodes = [
        convert_gremlin_vertex(vertex)
        for vertex in db.V().to_list()
        if vertex is not None
    ]
    edges = [
        convert_gremlin_edge(edge) for edge in db.E().to_list() if edge is not None
    ]
    return {"nodes": nodes, "edges": edges}


@app.delete("/network", status_code=status.HTTP_205_RESET_CONTENT)
def reset_whole_network(db=Depends(get_db_connection)) -> None:
    """Reset the whole network."""
    # TODO: add warning or confirmation
    vertex_count = db.V().count().next()

    if vertex_count:
        db.V().drop().iterate()


@app.put("/network")
def update_network(
    network: Network, delete=False, db=Depends(get_db_connection)
) -> Network:
    """Add missing nodes and edges, update existing ones, and delete the rest only if requested."""
    print("network:", network)
    if delete:
        raise NotImplementedError
    mapping = {}
    nodes_out = []
    edges_out = []
    for node in network.nodes:
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
    for edge in network.edges:
        try:
            if (
                db.V(edge.source)
                .outE(edge.edge_type)
                .where(__.inV().hasId(edge.target))
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
                    print("edge.source", edge.source)
                    print("mapping[edge.source]", update_edge_source_from)
                if edge.target in mapping:
                    update_edge_target_from = edge.target
                    edge.target = mapping[edge.target]
                    print("edge.target", edge.target)
                    print("mapping[edge.target]", update_edge_target_from)
                edge_out = convert_gremlin_edge(create_gremlin_edge(edge, db))
                edge_out.source_from_ui = (
                    update_edge_source_from  # TODO: add to history log
                )
                edge_out.target_from_ui = update_edge_target_from
            edges_out.append(edge_out)
        except StopIteration:
            ...

    return {"nodes": nodes_out, "edges": edges_out}


@app.get("/network/summary")
def get_network_summary(db=Depends(get_db_connection)) -> dict[str, int]:
    """Return total number of nodes and edges."""
    vertex_count = db.V().count().next()
    edge_count = db.E().count().next()
    return {"nodes": vertex_count, "edges": edge_count}


@app.get("/subgraph/{node_id}")
def get_subgraph_from_node(
    node_id: NodeId,
    levels: Annotated[int, Query(get=0)] = 2,
    db=Depends(get_db_connection),
) -> Network:
    """Return the subgraph containing a particular element with an optional limit number of connections.
    If no neighbour is found, a singleton subgraph with a single node is returned from the provided ID.
    """
    print("get_subgraph_from_node", node_id, levels)
    try:
        # # Start traversal from the given node
        # trav = db.V(node_id).repeat(__.bothE().subgraph('subGraph').bothV()).times(levels).cap('subGraph')
        # subgraph = trav.next()
        # # Extract vertices and edges from the subgraph
        # vertices = subgraph.V().toList()
        # edges = subgraph.E().toList()

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

        print("nodes", nodes)
        print("edges", edges)

        return {"nodes": nodes, "edges": edges}
    except StopIteration:
        raise HTTPException(status_code=404, detail="Node not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


### /nodes/* ###


# @app.get("/nodes")
# def get_node_list(
#     node_type: NodeType | None = None, db=Depends(get_db_connection)
# ) -> list[NodeBase]:
#     """Return all vertices, optionally of a certain node type."""
#     if node_type is not None:
#         return db.V().has_label(node_type).to_list()
#     return [
#         convert_gremlin_vertex(vertex)
#         for vertex in db.V().to_list()
#         if vertex is not None
#     ]


@app.get("/nodes")
def search_nodes(
    node_type: str | None = None,
    title: str | None = None,
    scope: str | None = None,
    description: str | None = None,
    db=Depends(get_db_connection),
) -> list[NodeBase]:
    """Search in nodes."""
    print("search_nodes", node_type, title, scope, description)
    traversal = db.V()
    if node_type is not None:
        traversal = traversal.has_label(node_type)
    if title:
        traversal = traversal.has("title", Text.text_contains_fuzzy(title))
    if scope:
        traversal = traversal.has("scope", Text.text_contains_fuzzy(scope))
    if description:
        traversal = traversal.has("description", Text.text_contains_fuzzy(description))
    return [convert_gremlin_vertex(node) for node in traversal.to_list()]


@app.get("/nodes/random")
def get_random_node(
    node_type: str | None = None, db=Depends(get_db_connection)
) -> NodeBase:
    """Return a random node."""
    print("\nget_random_node")
    try:
        # vertex = db.V().sample(1).next()
        # vertex = db.V().order().to_list()[0]
        trav = db.V()
        if node_type is not None:
            trav = trav.has_label(node_type)
        vertex = trav.order().by(Order.shuffle).limit(1).next()
        print("vertex", vertex)
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
        print("vertex", vertex)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Node not found")
    return convert_gremlin_vertex(vertex)


@app.post("/nodes", status_code=status.HTTP_201_CREATED)
def create_node(node: NodeBase, db=Depends(get_db_connection)) -> NodeBase:
    """Create a node."""
    # TODO: Check for possible duplicates
    created_node = create_gremlin_node(node, db)
    print("created_node", created_node)
    return convert_gremlin_vertex(created_node)


@app.delete("/nodes/{node_id}", status_code=status.HTTP_205_RESET_CONTENT)
def delete_node(node_id: NodeId, db=Depends(get_db_connection)):
    """Delete the node with provided ID."""
    if not db.V(node_id).has_next():
        raise HTTPException(status_code=404, detail="Node not found")

    db.V(node_id).both_e().drop().iterate()
    db.V(node_id).drop().iterate()
    return {"message": "Node deleted successfully"}


@app.put("/nodes")
def update_node(node: NodeBase, db=Depends(get_db_connection)) -> NodeBase:
    """Update the node with provided ID."""
    if not db.V(node.node_id).has_next():
        raise HTTPException(status_code=404, detail="Node not found")
    gremlin_vertex = update_gremlin_node(node, db)
    return convert_gremlin_vertex(gremlin_vertex)


### /edges/* ###


@app.get("/edges")
def get_edge_list(db=Depends(get_db_connection)) -> list[EdgeBase]:
    """Return all edges."""
    return [convert_gremlin_edge(edge) for edge in db.E().to_list() if edge is not None]


@app.get("/edges/{source_id}/{target_id}")
def get_edge(
    source_id: NodeId, target_id: NodeId, db=Depends(get_db_connection)
) -> EdgeBase:
    """Return the edge associated with the provided ID."""
    try:
        traversal = db.V(source_id).outE().where(__.inV().hasId(target_id))
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
        traversal = db.E()

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
def create_edge(edge: EdgeBase, db=Depends(get_db_connection)) -> EdgeBase:
    """Create an edge."""
    # TODO: Check for possible duplicates
    try:
        created_edge = create_gremlin_edge(edge, db)
        return convert_gremlin_edge(created_edge)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Node or edge not found")


@app.delete("/edges")
def delete_edges(edge: EdgeBase, db=Depends(get_db_connection)):
    """Delete the edge associated with provided ID."""
    try:
        traversal = (
            db.V(edge.source).outE(edge.edge_type).where(__.inV().hasId(edge.target))
        )
        traversal.drop().next()
        return {"message": "Edges deleted successfully"}
    except StopIteration:
        raise HTTPException(status_code=404, detail="Edge not found")


@app.put("/edges")
def update_edge(edge: EdgeBase, db=Depends(get_db_connection)) -> EdgeBase:
    """Update the edge with provided ID."""
    try:
        if not exists_edge_in_db(edge, db):
            raise HTTPException(status_code=404, detail="Edge not found")
        print("updating edge", edge)
        gremlin_edge = update_gremlin_edge(edge, db)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Error updating edge")

    return convert_gremlin_edge(gremlin_edge)


# Utils


def create_gremlin_node(node: NodeBase, db=Depends(get_db_connection)) -> GremlinVertex:
    created_node = db.add_v(node.node_type)
    # if node.node_id is not None:
    #    created_node = created_node.property(T.id, UUID(long=node.node_id))
    created_node = created_node.property("title", node.title)
    created_node = created_node.property("scope", node.scope)
    created_node = created_node.property("gradable", node.gradable)
    created_node = created_node.property("grade", node.grade)
    created_node = created_node.property("description", node.description)
    for proponent in node.proponents:
        created_node = created_node.property("proponent", proponent)
    for reference in node.references:
        created_node = created_node.property("reference", reference)
    return created_node.next()


def create_gremlin_edge(edge: EdgeBase, db=Depends(get_db_connection)) -> GremlinEdge:
    created_edge = db.V(edge.source).add_e(edge.edge_type)
    created_edge = created_edge.property("cprob", edge.cprob)
    for reference in edge.references:
        created_edge = created_edge.property("reference", reference)
    created_edge = created_edge.to(__.V(edge.target))
    return created_edge.next()


def exists_edge_in_db(edge: EdgeBase, db=Depends(get_db_connection)) -> bool:
    return (
        db.V(edge.source)
        .outE(edge.edge_type)
        .where(__.inV().hasId(edge.target))
        .has_next()
    )


def update_gremlin_node(
    node: NodeBase, db=Depends(get_db_connection)
) -> GremlinVertex | None:
    updated_node = None
    if node.title is not None:
        updated_node = db.V(node.node_id).property("title", node.title).next()
    if node.scope is not None:
        updated_node = db.V(node.node_id).property("scope", node.scope).next()
    if node.description is not None:
        updated_node = (
            db.V(node.node_id).property("description", node.description).next()
        )
    if node.gradable is not None:
        updated_node = db.V(node.node_id).property("gradable", node.gradable).next()
    if node.grade is not None:
        updated_node = db.V(node.node_id).property("grade", node.grade).next()
    if node.proponents is not None:
        for proponent in node.proponents:
            updated_node = db.V(node.node_id).property("proponent", proponent).next()
    if node.references is not None:
        for reference in node.references:
            updated_node = db.V(node.node_id).property("reference", reference).next()
    return updated_node


def update_gremlin_edge(edge: EdgeBase, db=Depends(get_db_connection)) -> GremlinEdge:
    traversal = (
        db.V(edge.source).outE(edge.edge_type).where(__.inV().hasId(edge.target))
    )
    # TODO: test if any change is made and deal with mere additions
    updated_edge = traversal.property("cprob", edge.cprob)
    for reference in edge.references:
        updated_edge = updated_edge.property("reference", reference)
    return updated_edge.next()
