from fastapi import FastAPI, HTTPException
from starlette.responses import HTMLResponse
from gremlin_python.process.graph_traversal import __
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver.serializer import GraphSONSerializersV3d0
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.traversal import T
from gremlin_python.process.traversal import Cardinality

from data_models import Node, Edge, NodeSearch
from graph_utils import plot_graph


id = T.id
single = Cardinality.single

app = FastAPI()

connection = DriverRemoteConnection(
    "ws://localhost:8182/gremlin",
    "g",
    message_serializer=GraphSONSerializersV3d0(),
    # transport_factory=lambda:AiohttpTransport(call_from_event_loop=True)
)

g = traversal().withRemote(connection)


@app.get("/")
async def root():
    return {"message": "Welcome to Wishnet!"}


@app.post("/network/reset/")
def resetting_network():
    print("resetting network")
    vertex_count = g.V().count().next()

    if vertex_count:
        g.V().drop().iterate()

    # Create vertices
    # v1 = g.addV("wish").property("summary", "Wish 1").next()
    # v2 = g.addV("wish").property("summary", "Wish 2").next()
    # v3 = g.addV("wish").property("summary", "Wish 3").next()
    # v4 = g.addV("wish").property("summary", "Wish 4").next()
    # v5 = g.addV().property("summary", "Wish 5").next()
    # v6 = g.addV("proposal").property("summary", "Proposal 1").next()

    # # Create edges
    # g.V(v1.id).addE("requirement").to(v2).next()
    # g.V(v1.id).addE("requirement").to(v3).next()
    # g.V(v1.id).addE("implication").to(v4).next()
    # g.V(v1.id).addE("implication").to(v5).next()
    #####


@app.get("/network/viz/")
def visualise_network():
    fig = plot_graph(g)
    return HTMLResponse(fig.to_html(full_html=False))


@app.get("/network/summary/")
def get_network_summary():
    vertex_count = g.V().count().next()
    edge_count = g.E().count().next()
    return {"vertices": vertex_count, "edges": edge_count}


@app.get("/nodes/")
def get_node_list(node_type: str = None):
    if node_type is not None:
        return g.V().has_label(node_type).toList()
    return g.V().toList()


@app.get("/edges/")
def get_edge_list():
    return g.E().toList()


@app.get("/nodes/{node_id}")
def get_node(node_id: int):
    return g.V(node_id).next()


@app.get("/edge/{edge_id}")
def get_edge(edge_id: int):
    return g.E(edge_id).next()


@app.post("/nodes/add/")
def add_node(node: Node):
    # TODO: Check for possible duplicates
    g.addV(node.node_type).property("summary", node.summary).property(
        "description", node.description
    ).next()
    return node


@app.post("/edges/add/")
def add_edge(edge: Edge):
    # TODO: Check for possible duplicates
    g.V(edge.source_node).addE(edge.edge_type).to(__.V(edge.target_node)).next()
    return edge


@app.delete("/nodes/{node_id}")
def delete_node(node_id: int):
    node = g.V(node_id).next()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    g.V(node_id).bothE().drop().iterate()
    g.V(node_id).drop().iterate()
    return {"message": "Node deleted successfully"}


@app.delete("/edges/{edge_id}")
def delete_edge(edge_id: str):
    edge = g.E(edge_id).next()
    if edge is None:
        raise HTTPException(status_code=404, detail="Edge not found")
    g.E(edge_id).drop().iterate()
    return {"message": "Edge deleted successfully"}


@app.put("/nodes/{node_id}")
def update_node(node_id: str, node: Node):
    node = g.V(node_id).nest()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.summary is not None:
        g.V(node_id).property("summary", node.summary).iterate()
    if node.description is not None:
        g.V(node_id).property("description", node.description).iterate()
    return {"message": "Node updated successfully"}


@app.get("/nodes/search")
def search_nodes(node_search: NodeSearch):
    traversal = g.V()
    if node_search.node_type is not None:
        traversal = traversal.has_label(node_search.node_type)
    if node_search.summary is not None:
        traversal = traversal.has("summary", node_search.summary)
    if node_search.description is not None:
        traversal = traversal.has("description", node_search.description)
    return traversal.toList()


# TODO: update the viz API
