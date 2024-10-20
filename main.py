from fastapi import FastAPI
from gremlin_python.process.graph_traversal import __
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver.serializer import GraphSONSerializersV3d0
from gremlin_python.process.anonymous_traversal import traversal
from starlette.responses import HTMLResponse

from graph_utils import plot_graph

app = FastAPI()


connection = DriverRemoteConnection(
    "ws://localhost:8182/gremlin", "g", message_serializer=GraphSONSerializersV3d0()
)

g = traversal().withRemote(connection)


# load database


@app.get("/")
async def root():
    return {"message": "Welcome to Wishnet!"}


@app.get("/network/viz/")
def visualise_network():
    fig = plot_graph(g)
    return HTMLResponse(fig.to_html(full_html=False))


@app.get("/network/summary/")
def get_network_summary():
    vertex_count = g.V().count().next()
    edge_count = g.E().count().next()
    return {"vertices": vertex_count, "edges": edge_count}


@app.get("/entity/{entity_id}")
def get_entity_by_id(entity_id: int):
    ...
    return ...
