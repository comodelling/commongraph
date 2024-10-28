import pytest
import json
from fastapi.testclient import TestClient

from main import app, setup_db_connection


# TODO: ensure we're handling a test database, e.g. https://jointhegraph.github.io/articles/hosting-multiple-graphs-on-janusgraph/
# see.g. https://www.answeroverflow.com/m/1258024441737117716 or https://gist.github.com/pluradj/7879df851c45269cd0cf8042955169f5

client = TestClient(app)


@pytest.fixture(scope="session")
def fixtures():
    connection = setup_db_connection()

    result = client.post(
        "/nodes",
        json={"summary": "test", "description": "test"},
    ).content
    node_dict = json.loads(result.decode("utf-8"))

    yield node_dict
    try:
        client.delete(f"/nodes/{node_dict['node_id']}")
    except Exception as e:
        print(e)
    connection.close()


# @pytest.fixture(scope="session")
# def fixture_edge():
#     result = client.post(
#         "/edge",
#         json={"summary": "test", "description": "test"},
#     ).content
#     node_dict = json.loads(result.decode('utf-8'))
#     yield node_dict
#     client.delete(f"/nodes/{node_dict['node_id']}")


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200


def test_fixtures(fixtures):
    ...


### /network/*


def test_network_summary():
    response = client.get("/network/summary")
    assert response.status_code == 200


### /nodes/*


def test_get_nodes_list():
    response = client.get("/nodes")
    assert response.status_code == 200


def test_create_and_delete_node():
    n_nodes = json.loads(client.get("/network/summary").content.decode("utf-8"))[
        "nodes"
    ]
    response = client.post(
        "/nodes",
        json={"summary": "test", "description": "test"},
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
    print(f"Created node ID: {node_id}")

    # Verify node creation
    response = client.get(f"/nodes/{node_id}")
    assert (
        response.status_code == 200
    ), f"Node not found after creation with status code {response.status_code}"

    # Delete node
    response = client.delete(f"/nodes/{node_id}")
    assert (
        response.status_code == 205
    ), f"Node deletion failed with status code {response.status_code}"
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["nodes"]
        == n_nodes
    ), "Node count did not come back to initial value"


def test_get_node_wrong_id(fixtures):
    response = client.get(f"/nodes/{fixtures['node_id']}")
    assert response.status_code == 200

    # inexistant ID
    response = client.get("/nodes/999999999")
    assert response.status_code == 404


def test_update_node(fixtures):
    response = client.put(
        f"/nodes/{fixtures['node_id']}",
        json={"summary": "test modified", "description": "test modified"},
    )
    assert response.status_code == 200

    # inexistant ID
    response = client.put(
        "/nodes/999999999", json={"summary": "test", "description": "test"}
    )
    assert response.status_code == 404


def test_search_nodes():
    response = client.post(
        "/nodes/search",
        json={"summary": "test", "description": "test"},
    )
    assert response.status_code == 200


### /edges/* ###


def test_get_edge_list():
    response = client.get("/edges")
    assert response.status_code == 200


def test_create_and_delete_edge(fixtures):
    n_edges = json.loads(client.get("/network/summary").content.decode("utf-8"))[
        "edges"
    ]
    response = client.post(
        "/edges",
        json={
            "edge_type": "implication",
            "source": fixtures["node_id"],
            "target": fixtures["node_id"],
        },
    )
    assert response.status_code == 201
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["edges"]
        == n_edges + 1
    ), "Edge count did not increase by 1"


def test_delete_node_wrong_id():
    response = client.delete("/nodes/999999999")
    assert response.status_code == 404


def test_reset_network():
    response = client.post("/network/reset")
    assert response.status_code == 205
