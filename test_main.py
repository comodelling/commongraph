import pytest
import json
from fastapi.testclient import TestClient

from main import app, setup_db_connection


setup_db_connection()  # TODO: ensure we're handling a test database, e.g. https://jointhegraph.github.io/articles/hosting-multiple-graphs-on-janusgraph/
# see.g. https://www.answeroverflow.com/m/1258024441737117716 or https://gist.github.com/pluradj/7879df851c45269cd0cf8042955169f5

client = TestClient(app)

# TODO: add fixtures to properly create and delete (if needed) nodes


@pytest.fixture(scope="session")
def fixture_node():
    result = client.post(
        "/nodes",
        json={"summary": "test", "description": "test"},
    ).content
    node_dict = json.loads(result.decode("utf-8"))
    yield node_dict
    client.delete(f"/nodes/{node_dict['node_id']}")


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


# /network/*


def test_network_summary():
    response = client.get("/network/summary")
    assert response.status_code == 200


def test_reset_network():
    response = client.post("/network/reset")
    assert response.status_code == 205


### /nodes/* ###
def test_get_nodes_list():
    response = client.get("/nodes")
    assert response.status_code == 200


def test_get_node(fixture_node):
    response = client.get(f"/nodes/{fixture_node['node_id']}")
    assert response.status_code == 200

    # inexistant ID
    response = client.get("/nodes/999999999")
    assert response.status_code == 404


def test_create_node():
    response = client.post(
        "/nodes",
        json={"summary": "test", "description": "test"},
    )
    assert response.status_code == 201


def test_update_node(fixture_node):
    response = client.put(
        f"/nodes/{fixture_node['node_id']}",
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


def test_get_edge():
    # inexistant ID
    response = client.get("/edges/999999999")
    assert response.status_code == 404


def test_create_edge():
    ...
    # response = client.post("/edges",
    #                        json={"source_node": ...,
    #                              "target_node": ...},
    #                        )
    # assert response.status_code == 201

    # inexistant ID
    response = client.post(
        "/edges",
        json={"edge_type": "implication", "source": 9999999, "target": 9999999},
    )
    assert response.status_code == 404


def test_update_edge():
    # inexistant ID
    response = client.put(
        "/nodes/999999999", json={"summary": "test", "description": "test"}
    )
    assert response.status_code == 404


def test_delete_edge():

    # inexistant ID
    response = client.delete("/edges/999999999")
    assert response.status_code == 404


def test_delete_node():
    ...
    # response = client.delete("/nodes")
    # assert response.status_code == 205

    # inexistant ID
    response = client.delete("/nodes/999999999")
    assert response.status_code == 404
