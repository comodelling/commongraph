import os

import pytest
import json
from fastapi.testclient import TestClient
import tempfile

from main import app, get_db_connection
from database.janusgraph import JanusGraphDB
from database.sqlite import SQLiteDB


@pytest.fixture(scope="module", params=["janusgraph", "sqlite"])
def db(request):
    db_type = request.param
    if db_type == "janusgraph":
        # os.environ["TRAVERSAL_SOURCE"] = "g_test"
        janusgraph_host = os.getenv("JANUSGRAPH_HOST", "localhost")
        try:
            db = JanusGraphDB(janusgraph_host, "g_test")
            with db.connection():
                db.get_network_summary()
        except Exception:
            pytest.skip("JanusGraph server not running.")
    elif db_type == "sqlite":
        fd, path = tempfile.mkstemp()
        os.close(fd)
        db = SQLiteDB(path)
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")

    yield db
    db.reset_whole_network()
    if db_type == "sqlite":
        os.remove(path)


@pytest.fixture(autouse=True, scope="module")
def override_get_db_connection(db):
    app.dependency_overrides[get_db_connection] = lambda: db
    yield
    app.dependency_overrides.pop(get_db_connection, None)


@pytest.fixture(scope="module")
def client(override_get_db_connection):
    return TestClient(app)


@pytest.fixture(scope="module")
def initial_node(db, client):
    client.delete("/network")

    result = client.post(
        "/nodes",
        json={
            "title": "test",
            "node_type": "objective",
            "scope": "test scope",
            "description": "test",
        },
    ).content
    node_dict = json.loads(result.decode("utf-8"))

    yield node_dict

    client.delete("/network")


def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200


def test_get_whole_network(db, client):
    response = client.get("/network")
    assert response.status_code == 200


def test_update_subnet(db, client):
    n_nodes = json.loads(client.get("/network/summary").content.decode("utf-8"))[
        "nodes"
    ]
    response = client.put(
        "/subnet",
        json={"nodes": [{"title": "test", "scope": "test scope"}], "edges": []},
    )
    assert response.status_code == 200
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["nodes"]
        == n_nodes + 1
    )


def test_get_subnet(initial_node, client):
    node_id = initial_node["node_id"]
    response = client.get(f"/subnet/{node_id}")
    assert response.status_code == 200
    assert node_id in [
        node["node_id"]
        for node in json.loads(response.content.decode("utf-8"))["nodes"]
    ]


def test_network_summary(db, client):
    response = client.get("/network/summary")
    assert response.status_code == 200


def test_get_nodes_list(db, client):
    response = client.get("/nodes")
    assert response.status_code == 200


def test_create_and_delete_node(db, client):
    n_nodes = json.loads(client.get("/network/summary").content.decode("utf-8"))[
        "nodes"
    ]
    response = client.post(
        "/nodes",
        json={"title": "test", "scope": "unscoped", "description": "test"},
    )
    assert response.status_code == 201
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["nodes"]
        == n_nodes + 1
    )

    node_id = json.loads(response.content.decode("utf-8"))["node_id"]

    response = client.get(f"/nodes/{node_id}")
    assert response.status_code == 200

    response = client.delete(f"/nodes/{node_id}")
    assert response.status_code == 200
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["nodes"]
        == n_nodes
    )


@pytest.mark.skip
def test_create_node_specific_id(db, client):
    response = client.post(
        "/nodes",
        json={
            "title": "test",
            "scope": "unscoped",
            "description": "test",
            "node_id": 777777,
        },
    )
    assert response.status_code == 201
    response = client.get(f"/nodes/777777")
    assert response.status_code == 200


def test_get_random_node(db, client):
    response = client.get("/nodes/random")
    assert response.status_code == 200


def test_get_node_wrong_id(initial_node, client):
    response = client.get(f"/nodes/{initial_node['node_id']}")
    assert response.status_code == 200

    response = client.get("/nodes/999999999")
    assert response.status_code == 404


def test_search_nodes(db, client):
    response = client.get("/nodes?title=test")
    assert response.status_code == 200
    assert len(json.loads(response.content.decode("utf-8"))) == 1


def test_search_nodes_with_node_type(db, client):
    client.post(
        "/nodes",
        json={
            "title": "Objective Node",
            "node_type": "objective",
            "scope": "test scope",
        },
    )
    client.post(
        "/nodes",
        json={"title": "Action Node", "node_type": "action", "scope": "test scope"},
    )
    client.post(
        "/nodes",
        json={
            "title": "Potentiality Node",
            "node_type": "potentiality",
            "scope": "test scope",
        },
    )

    response = client.get("/nodes?node_type=objective")
    assert response.status_code == 200
    nodes = json.loads(response.content.decode("utf-8"))
    assert all(node["node_type"] == "objective" for node in nodes)

    response = client.get("/nodes?node_type=action")
    assert response.status_code == 200
    nodes = json.loads(response.content.decode("utf-8"))
    assert all(node["node_type"] == "action" for node in nodes)

    response = client.get("/nodes?node_type=potentiality")
    assert response.status_code == 200
    nodes = json.loads(response.content.decode("utf-8"))
    assert all(node["node_type"] == "potentiality" for node in nodes)


def test_update_node(initial_node, client):
    response = client.put(
        "/nodes",
        json={
            "node_id": initial_node["node_id"],
            "title": "test modified",
            "description": "test modified",
        },
    )
    assert response.status_code == 200
    assert json.loads(response.content.decode("utf-8"))["title"] == "test modified"

    response = client.put("/nodes", json={"title": "test", "description": "test"})
    assert response.status_code == 422


def test_delete_node_wrong_id(db, client):
    response = client.delete("/nodes/999999999")
    assert response.status_code == 404


def test_get_edge_list(db, client):
    response = client.get("/edges")
    assert response.status_code == 200


def test_create_update_and_delete_edge(initial_node, client):
    n_edges = json.loads(client.get("/network/summary").content.decode("utf-8"))[
        "edges"
    ]
    response = client.post(
        "/edges",
        json={
            "edge_type": "imply",
            "source": initial_node["node_id"],
            "target": initial_node["node_id"],
        },
    )
    assert response.status_code == 201
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["edges"]
        == n_edges + 1
    )

    response = client.put(
        "/edges",
        json={
            "edge_type": "imply",
            "source": initial_node["node_id"],
            "target": initial_node["node_id"],
            "cprob": 0.5,
        },
    )
    assert response.status_code == 200
    assert json.loads(response.content.decode("utf-8"))["cprob"] == 0.5

    response = client.delete(
        f"/edges/{initial_node['node_id']}/{initial_node['node_id']}",
        params={"edge_type": "imply"},
    )
    assert response.status_code == 200

    response = client.get(f"/edges/{initial_node['node_id']}/{initial_node['node_id']}")
    assert response.status_code == 404


def test_find_edges(db, client):
    response = client.post(
        "/edges/find",
        json={"edge_type": "imply"},
    )
    assert response.status_code == 200


def test_create_node_with_references(db, client):
    response = client.post(
        "/nodes",
        json={
            "title": "test node with references",
            "description": "test description",
            "scope": "test scope",
            "references": ["ref1", "ref2", "ref3"],
        },
    )
    assert response.status_code == 201
    node = json.loads(response.content.decode("utf-8"))
    assert "references" in node
    assert len(node["references"]) == 3
    assert set(node["references"]) == {"ref1", "ref2", "ref3"}


def test_update_node_with_references(db, client):
    response = client.post(
        "/nodes",
        json={
            "title": "test node for update",
            "node_type": "potentiality",
            "scope": "test scope",
            "description": "test description",
            "references": ["ref1", "ref2"],
        },
    )
    assert response.status_code == 201
    node = json.loads(response.content.decode("utf-8"))
    node_id = node["node_id"]

    response = client.put(
        "/nodes",
        json={
            "node_id": node_id,
            "title": "updated title",
            "description": "updated description",
            "references": ["ref3", "ref4"],
        },
    )
    assert response.status_code == 200
    updated_node = json.loads(response.content.decode("utf-8"))
    assert "references" in updated_node
    assert len(updated_node["references"]) == 2
    assert set(updated_node["references"]) == {"ref3", "ref4"}


def test_create_edge_with_references(initial_node, client):
    response = client.post(
        "/edges",
        json={
            "edge_type": "imply",
            "source": initial_node["node_id"],
            "target": initial_node["node_id"],
            "references": ["ref1", "ref2", "ref3"],
        },
    )
    assert response.status_code == 201
    edge = json.loads(response.content.decode("utf-8"))
    assert "references" in edge
    assert len(edge["references"]) == 3
    assert set(edge["references"]) == {"ref1", "ref2", "ref3"}


def test_update_edge_with_references(initial_node, client):
    response = client.post(
        "/edges",
        json={
            "edge_type": "imply",
            "source": initial_node["node_id"],
            "target": initial_node["node_id"],
            "references": ["ref1", "ref2"],
        },
    )
    assert response.status_code == 201
    edge = json.loads(response.content.decode("utf-8"))

    response = client.put(
        "/edges",
        json={
            "edge_type": "imply",
            "source": initial_node["node_id"],
            "target": initial_node["node_id"],
            "references": ["ref3", "ref4"],
        },
    )
    assert response.status_code == 200
    updated_edge = json.loads(response.content.decode("utf-8"))
    assert "references" in updated_edge
    assert len(updated_edge["references"]) == 2
    assert set(updated_edge["references"]) == {"ref3", "ref4"}
