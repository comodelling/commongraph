import os

import pytest
import json
from fastapi.testclient import TestClient

from main import app


os.environ["TRAVERSAL_SOURCE"] = "g_test"

client = TestClient(app)


@pytest.fixture(scope="module")
def fixtures():
    client.delete("/network")

    result = client.post(
        "/nodes",
        json={"title": "test", "description": "test"},
    ).content
    node_dict = json.loads(result.decode("utf-8"))

    yield node_dict

    client.delete("/network")


### / ###


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200


### /network/ ###


def test_get_whole_network():
    response = client.get("/network")
    assert response.status_code == 200


### /subnet/ ###


def test_update_subnet():
    n_nodes = json.loads(client.get("/network/summary").content.decode("utf-8"))[
        "nodes"
    ]
    response = client.put(
        "/subnet",
        json={"nodes": [{"title": "test", "description": "test"}], "edges": []},
    )
    assert response.status_code == 200
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["nodes"]
        == n_nodes + 1
    )


def test_get_subnet(fixtures):
    node_id = fixtures["node_id"]
    response = client.get(f"/subnet/{node_id}")
    assert response.status_code == 200
    assert node_id in [
        node["node_id"]
        for node in json.loads(response.content.decode("utf-8"))["nodes"]
    ]


def test_network_summary():
    response = client.get("/network/summary")
    assert response.status_code == 200


### /nodes/ ###


def test_get_nodes_list():
    response = client.get("/nodes")
    assert response.status_code == 200


def test_create_and_delete_node():
    n_nodes = json.loads(client.get("/network/summary").content.decode("utf-8"))[
        "nodes"
    ]
    response = client.post(
        "/nodes",
        json={"title": "test", "description": "test"},
    )
    assert (
        response.status_code == 201
    ), f"Node creation failed with status code {response.status_code}"
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["nodes"]
        == n_nodes + 1
    ), "Node count did not increase by 1"

    # Retrieve node ID
    node_id = json.loads(response.content.decode("utf-8"))["node_id"]

    # Verify node creation
    response = client.get(f"/nodes/{node_id}")
    assert (
        response.status_code == 200
    ), f"Node not found after creation with status code {response.status_code}"

    # Delete node
    response = client.delete(f"/nodes/{node_id}")
    assert (
        response.status_code == 200
    ), f"Node deletion failed with status code {response.status_code}"
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["nodes"]
        == n_nodes
    ), "Node count did not come back to initial value"


@pytest.mark.skip
def test_create_node_specific_id():
    response = client.post(
        "/nodes",
        json={"title": "test", "description": "test", "node_id": 777777},
    )
    assert response.status_code == 201
    response = client.get(f"/nodes/777777")
    assert response.status_code == 200


def test_get_random_node():
    response = client.get("/nodes/random")
    assert response.status_code == 200


def test_get_node_wrong_id(fixtures):
    response = client.get(f"/nodes/{fixtures['node_id']}")
    assert response.status_code == 200

    # inexistant ID
    response = client.get("/nodes/999999999")
    assert response.status_code == 404


def test_search_nodes():
    response = client.get("/nodes?title=test")
    assert (
        response.status_code == 200
    ), f"Unexpected status code: {response.status_code}, response: {response.json()}"
    assert len(json.loads(response.content.decode("utf-8"))) == 1


def test_search_nodes_with_node_type():
    # Create nodes with different types
    client.post("/nodes", json={"title": "Objective Node", "node_type": "objective"})
    client.post("/nodes", json={"title": "Action Node", "node_type": "action"})
    client.post(
        "/nodes", json={"title": "Potentiality Node", "node_type": "potentiality"}
    )

    # Search for nodes with type 'objective'
    response = client.get("/nodes?node_type=objective")
    assert response.status_code == 200
    nodes = json.loads(response.content.decode("utf-8"))
    assert all(
        node["node_type"] == "objective" for node in nodes
    ), "Non-objective nodes found"

    # Search for nodes with type 'action'
    response = client.get("/nodes?node_type=action")
    assert response.status_code == 200
    nodes = json.loads(response.content.decode("utf-8"))
    assert all(
        node["node_type"] == "action" for node in nodes
    ), "Non-action nodes found"

    # Search for nodes with type 'potentiality'
    response = client.get("/nodes?node_type=potentiality")
    assert response.status_code == 200
    nodes = json.loads(response.content.decode("utf-8"))
    assert all(
        node["node_type"] == "potentiality" for node in nodes
    ), "Non-potentiality nodes found"


def test_update_node(fixtures):
    response = client.put(
        "/nodes",
        json={
            "node_id": fixtures["node_id"],
            "title": "test modified",
            "description": "test modified",
        },
    )
    assert response.status_code == 200
    assert json.loads(response.content.decode("utf-8"))["title"] == "test modified"

    # inexistant ID
    response = client.put("/nodes", json={"title": "test", "description": "test"})
    assert (
        response.status_code == 422
    )  # Unprocessable Entity #TODO: maybe something more informative?


def test_delete_node_wrong_id():
    response = client.delete("/nodes/999999999")
    assert response.status_code == 404


### /edges/ ###


def test_get_edge_list():
    response = client.get("/edges")
    assert response.status_code == 200


def test_create_update_and_delete_edge(fixtures):
    n_edges = json.loads(client.get("/network/summary").content.decode("utf-8"))[
        "edges"
    ]
    # POST
    response = client.post(
        "/edges",
        json={
            "edge_type": "imply",
            "source": fixtures["node_id"],
            "target": fixtures["node_id"],
        },
    )
    assert response.status_code == 201
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["edges"]
        == n_edges + 1
    ), "Edge count did not increase by 1"

    # PUT
    response = client.put(
        "/edges",
        json={
            "edge_type": "imply",
            "source": fixtures["node_id"],
            "target": fixtures["node_id"],
            "cprob": 0.5,
        },
    )
    assert response.status_code == 200
    assert json.loads(response.content.decode("utf-8"))["cprob"] == 0.5

    # DELETE
    response = client.delete(f"/edges/{fixtures['node_id']}/{fixtures['node_id']}")
    assert response.status_code == 200

    # Verify edge deletion
    response = client.get(f"/edges/{fixtures['node_id']}/{fixtures['node_id']}")
    assert response.status_code == 404


def test_find_edges():
    response = client.post(
        "/edges/find",
        json={"edge_type": "imply"},
    )
    assert response.status_code == 200


def test_create_node_with_references():
    response = client.post(
        "/nodes",
        json={
            "title": "test node with references",
            "description": "test description",
            "references": ["ref1", "ref2", "ref3"],
        },
    )
    assert response.status_code == 201
    node = json.loads(response.content.decode("utf-8"))
    assert "references" in node
    assert len(node["references"]) == 3
    assert set(node["references"]) == {"ref1", "ref2", "ref3"}


def test_update_node_with_references():
    response = client.post(
        "/nodes",
        json={
            "title": "test node for update",
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


def test_create_edge_with_references(fixtures):
    response = client.post(
        "/edges",
        json={
            "edge_type": "imply",
            "source": fixtures["node_id"],
            "target": fixtures["node_id"],
            "references": ["ref1", "ref2", "ref3"],
        },
    )
    assert response.status_code == 201
    edge = json.loads(response.content.decode("utf-8"))
    assert "references" in edge
    assert len(edge["references"]) == 3
    assert set(edge["references"]) == {"ref1", "ref2", "ref3"}


def test_update_edge_with_references(fixtures):
    response = client.post(
        "/edges",
        json={
            "edge_type": "imply",
            "source": fixtures["node_id"],
            "target": fixtures["node_id"],
            "references": ["ref1", "ref2"],
        },
    )
    assert response.status_code == 201
    edge = json.loads(response.content.decode("utf-8"))

    response = client.put(
        "/edges",
        json={
            "edge_type": "imply",
            "source": fixtures["node_id"],
            "target": fixtures["node_id"],
            "references": ["ref3", "ref4"],
        },
    )
    assert response.status_code == 200
    updated_edge = json.loads(response.content.decode("utf-8"))
    assert "references" in updated_edge
    assert len(updated_edge["references"]) == 2
    assert set(updated_edge["references"]) == {"ref3", "ref4"}
