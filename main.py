from fastapi import FastAPI
from gremlin_python.process.graph_traversal import __
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver.serializer import GraphSONSerializersV3d0
from gremlin_python.process.anonymous_traversal import traversal
from starlette.responses import HTMLResponse
from gremlin_python.process.traversal import T
from gremlin_python.process.traversal import Cardinality
from gremlin_python.driver.aiohttp.transport import AiohttpTransport

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


@app.get("/network/initialise/")
def initialise_network():
    print("initialising network")
    vertex_count = g.V().count().next()

    if vertex_count:
        g.V().drop().iterate()

    # Create vertices
    v1 = g.addV("wish").property("summary", "Wish 1").next()
    v2 = g.addV("wish").property("summary", "Wish 2").next()
    v3 = g.addV("wish").property("summary", "Wish 3").next()
    v4 = g.addV("wish").property("summary", "Wish 4").next()
    v5 = g.addV("wish").property("summary", "Wish 5").next()

    # Create edges
    g.V(v1.id).addE("requirement").to(v2).next()
    g.V(v1.id).addE("requirement").to(v3).next()
    g.V(v1.id).addE("implication").to(v4).next()
    g.V(v1.id).addE("implication").to(v5).next()
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
def get_node_list():
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


@app.post("/nodes/{node_id}")
def add_node(node_id: int, node_type: str = "node"):
    g.addV(node_type).property(id, node_id).next()
