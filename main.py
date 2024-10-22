from fastapi import FastAPI
from gremlin_python.process.graph_traversal import __
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver.serializer import GraphSONSerializersV3d0
from gremlin_python.process.anonymous_traversal import traversal
from starlette.responses import HTMLResponse
from gremlin_python.process.traversal import T
from gremlin_python.process.traversal import Cardinality
from gremlin_python.driver.aiohttp.transport import AiohttpTransport

from data_models import Node, Edge
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
def get_node(node_id: str):
    return g.V(node_id).next()


@app.get("/edge/{edge_id}")
def get_edge(edge_id: str):
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


# TODO: delete and update APIs for network elements
# TODO: update the viz API
