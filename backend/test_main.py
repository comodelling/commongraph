import os
import warnings
import logging
import pytest
import json
from fastapi.testclient import TestClient
import threading

from main import app, get_graph_db_connection, get_graph_history_db_connection
from db.janusgraph import JanusGraphDB
from db.postgresql import GraphHistoryPostgreSQLDB


POSTGRES_TEST_DB_URL = "postgresql://postgres:postgres@localhost/testdb"
os.environ["POSTGRES_DB_URL"] = POSTGRES_TEST_DB_URL
os.environ["SECRET_KEY"] = "testsecret"


logger = logging.getLogger(__name__)


@pytest.fixture(scope="module", params=[None, "janusgraph"])
def graph_db(request):
    db_type = request.param
    if db_type == "janusgraph":
        try:
            graph_db = JanusGraphDB("localhost", "g_test")
            with graph_db.connection():
                graph_db.reset_whole_network()
        except Exception:
            pytest.skip("JanusGraph server not running.")
    elif db_type is None:
        graph_db = None
    else:
        raise ValueError(f"Unsupported GRAPH_DB_TYPE: {db_type}")

    yield graph_db


@pytest.fixture(autouse=True, scope="module")
def override_db_connections(graph_db):

    graph_history_db = GraphHistoryPostgreSQLDB(POSTGRES_TEST_DB_URL)
    graph_history_db.reset_whole_network()

    app.dependency_overrides[get_graph_history_db_connection] = lambda: graph_history_db

    # Only override the graph DB dependency if ENABLE_GRAPH_DB is true.
    if graph_db is not None:
        app.dependency_overrides[get_graph_db_connection] = lambda: graph_db
    else:
        app.dependency_overrides[get_graph_db_connection] = lambda: None

    yield

    app.dependency_overrides.pop(get_graph_db_connection, None)
    app.dependency_overrides.pop(get_graph_history_db_connection, None)


@pytest.fixture(scope="module")
def client(override_db_connections):
    return TestClient(app)


@pytest.fixture(scope="module")
def initial_node(graph_db, client):
    warnings.filterwarnings("ignore", category=UserWarning)
    client.delete("/network")

    result = client.post(
        "/node",
        json={
            "title": "test",
            "node_type": "objective",
            "scope": "test scope",
            "description": "test",
        },
    ).content
    node_dict = json.loads(result.decode("utf-8"))
    logger.info(f"Initial node: {node_dict}")

    yield node_dict
    warnings.filterwarnings("ignore", category=UserWarning)
    client.delete("/network")


def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200, print(response.json())


def test_get_whole_network(graph_db, client):
    response = client.get("/network")
    assert response.status_code == 200, print(response.json())
    assert "nodes" in response.json()
    assert "edges" in response.json()
    # assert len(response.json()["nodes"])


def test_reset_whole_network(graph_db, client):
    # Ensure there are nodes and edges before reset
    # client.post(
    #     "/node",
    #     json={
    #         "title": "test",
    #         "node_type": "objective",
    #         "scope": "test scope",
    #         "description": "test",
    #     },
    # )
    warnings.filterwarnings("ignore", category=UserWarning)
    response = client.delete("/network")
    assert response.status_code == 205

    summary_response = client.get("/network/summary")
    summary = json.loads(summary_response.content.decode("utf-8"))
    assert summary["nodes"] == 0
    assert summary["edges"] == 0


def test_update_subnet(graph_db, client):
    n_nodes = json.loads(client.get("/network/summary").content.decode("utf-8"))[
        "nodes"
    ]
    response = client.put(
        "/subnet",
        json={"nodes": [{"title": "test", "scope": "test scope"}], "edges": []},
    )
    assert response.status_code == 200, print(response.json())
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["nodes"]
        == n_nodes + 1
    )


def test_get_subnet(initial_node, client):
    node_id = initial_node["node_id"]
    response = client.get(f"/subnet/{node_id}")
    assert response.status_code == 200, print(response.json())
    assert node_id in [
        node["node_id"]
        for node in json.loads(response.content.decode("utf-8"))["nodes"]
    ]


def test_network_summary(graph_db, client):
    response = client.get("/network/summary")
    assert response.status_code == 200, print(response.json())


def test_get_nodes_list(graph_db, client):
    response = client.get("/nodes")
    assert response.status_code == 200, print(response.json())
    # assert len(json.loads(response.content.decode("utf-8")))


def test_create_and_delete_node(graph_db, client):
    n_nodes = json.loads(client.get("/network/summary").content.decode("utf-8"))[
        "nodes"
    ]
    response = client.post(
        "/node",
        json={"title": "test", "scope": "unscoped", "description": "test"},
    )
    assert response.status_code == 201, print(response.json())
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["nodes"]
        == n_nodes + 1
    )

    node_id = json.loads(response.content.decode("utf-8"))["node_id"]

    response = client.get(f"/node/{node_id}")
    assert response.status_code == 200, print(response.json())

    warnings.filterwarnings("ignore", category=UserWarning)
    response = client.delete(f"/node/{node_id}")
    assert response.status_code == 200, print(response.json())
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["nodes"]
        == n_nodes
    )


@pytest.mark.skip
def test_create_node_specific_id(graph_db, client):
    response = client.post(
        "/node",
        json={
            "title": "test",
            "node_type": "objective",
            "scope": "unscoped",
            "description": "test",
            "node_id": 777777,
        },
    )
    assert response.status_code == 201, print(response.json())
    response = client.get(f"/node/777777")
    assert response.status_code == 200, print(response.json())


def test_create_node_with_missing_fields(client):
    response = client.post(
        "/node",
        json={
            "node_type": "objective",
            "scope": "test scope",
            # "title" is missing
            "description": "test description",
        },
    )
    assert response.status_code == 422, print(response.json())


def create_node_concurrently(client, title, results, index):
    response = client.post(
        "/node",
        json={
            "title": title,
            "node_type": "objective",
            "scope": "test scope",
            "description": "test",
        },
    )
    results[index] = response.status_code


def test_concurrent_node_creations(client):
    threads = []
    results = [None] * 5
    for i in range(5):
        thread = threading.Thread(
            target=create_node_concurrently, args=(client, f"node{i}", results, i)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    assert all(status == 201 for status in results)


def test_get_random_node(graph_db, client):
    response = client.get("/node/random")
    assert response.status_code == 200, print(response.json())


def test_get_node_wrong_id(initial_node, client):
    response = client.get(f"/node/{initial_node['node_id']}")
    assert response.status_code == 200, print(response.json())

    response = client.get("/node/999999999")
    assert response.status_code == 404, print(response.json())


def test_search_nodes(graph_db, client):
    # Ensure the node with title "test" exists
    response = client.post(
        "/node",
        json={
            "title": "testtesttest",
            "node_type": "objective",
            "scope": "test scope",
            "description": "test",
        },
    )
    assert response.status_code == 201, print(response.json())

    # Log the entire node list before searching
    all_nodes_response = client.get("/nodes")
    print("DEBUG: All nodes after creation:", all_nodes_response.json())

    # Perform the search
    response = client.get("/nodes?title=testtesttest")
    print("DEBUG: Search response:", response.json())
    assert response.status_code == 200, print(response.json())
    assert len(response.json()) == 1, print(response.json())


def test_search_nodes_with_node_type(graph_db, client):
    client.post(
        "/node",
        json={
            "title": "Objective Node",
            "node_type": "objective",
            "scope": "test scope",
        },
    )
    client.post(
        "/node",
        json={"title": "Action Node", "node_type": "action", "scope": "test scope"},
    )
    client.post(
        "/node",
        json={
            "title": "Potentiality Node",
            "node_type": "potentiality",
            "scope": "test scope",
        },
    )

    response = client.get("/nodes?node_type=objective")
    assert response.status_code == 200, print(response.json())
    nodes = json.loads(response.content.decode("utf-8"))
    assert len(nodes) >= 1
    assert all(node["node_type"] == "objective" for node in nodes)

    response = client.get("/nodes?node_type=action")
    assert response.status_code == 200, print(response.json())
    nodes = json.loads(response.content.decode("utf-8"))
    assert len(nodes) == 1
    assert all(node["node_type"] == "action" for node in nodes)

    response = client.get("/nodes?node_type=potentiality")
    assert response.status_code == 200, print(response.json())
    nodes = json.loads(response.content.decode("utf-8"))
    assert len(nodes) == 1
    assert all(node["node_type"] == "potentiality" for node in nodes)


def test_update_node(initial_node, client):
    response = client.put(
        "/node",
        json={
            "node_id": initial_node["node_id"],
            "title": "test modified",
            "description": "test modified",
        },
    )
    assert response.status_code == 200, print(response.json())
    assert json.loads(response.content.decode("utf-8"))["title"] == "test modified"

    response = client.put("/node", json={"title": "test", "description": "test"})
    assert response.status_code == 422, print(response.json())


def test_delete_node_wrong_id(graph_db, client):
    response = client.delete("/node/999999999")
    assert response.status_code == 404, print(response.json())


def test_get_edge_list(graph_db, client):
    response = client.get("/edges")
    assert response.status_code == 200, print(response.json())


def test_create_update_and_delete_edge(initial_node, client):
    n_edges = json.loads(client.get("/network/summary").content.decode("utf-8"))[
        "edges"
    ]
    response = client.post(
        "/edge",
        json={
            "edge_type": "imply",
            "source": initial_node["node_id"],
            "target": initial_node["node_id"],
        },
    )
    assert response.status_code == 201, print(response.json())
    assert (
        json.loads(client.get("/network/summary").content.decode("utf-8"))["edges"]
        == n_edges + 1
    )

    response = client.put(
        "/edge",
        json={
            "edge_type": "imply",
            "source": initial_node["node_id"],
            "target": initial_node["node_id"],
            "sufficiency": 0.5,
        },
    )
    assert response.status_code == 200, print(response.json())

    response = client.delete(
        f"/edge/{initial_node['node_id']}/{initial_node['node_id']}",
        params={"edge_type": "imply"},
    )
    assert response.status_code == 200, print(response.json())

    response = client.get(f"/edge/{initial_node['node_id']}/{initial_node['node_id']}")
    assert response.status_code == 404, print(response.json())


def test_create_edge_with_nonexistent_nodes(graph_db, client):
    response = client.post(
        "/edge",
        json={
            "edge_type": "imply",
            "source": 999999,  # Nonexistent source
            "target": 999998,  # Nonexistent target
        },
    )
    assert response.status_code == 404, print(response.json())


def test_find_edges(graph_db, client):
    response = client.post(
        "/edges/find",
        json={"edge_type": "imply"},
    )
    assert response.status_code == 200, print(response.json())


def test_create_node_with_references(graph_db, client):
    response = client.post(
        "/node",
        json={
            "title": "test node with references",
            "description": "test description",
            "scope": "test scope",
            "references": ["ref1", "ref2", "ref3"],
        },
    )
    assert response.status_code == 201, print(response.json())
    node = json.loads(response.content.decode("utf-8"))
    assert "references" in node
    assert len(node["references"]) == 3
    assert set(node["references"]) == {"ref1", "ref2", "ref3"}

    response = client.get("/network")


def test_update_node_with_references(graph_db, client):
    response = client.post(
        "/node",
        json={
            "title": "test node for update",
            "node_type": "potentiality",
            "scope": "test scope",
            "description": "test description",
            "references": ["ref1", "ref2"],
        },
    )
    assert response.status_code == 201, print(response.json())
    node = json.loads(response.content.decode("utf-8"))
    node_id = node["node_id"]

    response = client.put(
        "/node",
        json={
            "node_id": node_id,
            "title": "updated title",
            "description": "updated description",
            "references": ["ref3", "ref4"],
        },
    )
    assert response.status_code == 200, print(response.json())
    updated_node = json.loads(response.content.decode("utf-8"))
    assert "references" in updated_node
    assert len(updated_node["references"]) == 2
    assert set(updated_node["references"]) == {"ref3", "ref4"}


def test_create_edge_with_references(initial_node, client):
    response = client.post(
        "/edge",
        json={
            "edge_type": "imply",
            "source": initial_node["node_id"],
            "target": initial_node["node_id"],
            "references": ["ref1", "ref2", "ref3"],
        },
    )
    assert response.status_code == 201, print(response.json())
    edge = json.loads(response.content.decode("utf-8"))
    assert "references" in edge
    assert len(edge["references"]) == 3, f"references = {edge['references']}"
    assert set(edge["references"]) == {"ref1", "ref2", "ref3"}


def test_update_edge_with_references(initial_node, client):

    response = client.post(
        "/edge",
        json={
            "edge_type": "require",
            "source": initial_node["node_id"],
            "target": initial_node["node_id"],
            "references": ["ref1", "ref2"],
        },
    )
    assert response.status_code == 201, print(response.json())
    edge = json.loads(response.content.decode("utf-8"))

    response = client.put(
        "/edge",
        json={
            "edge_type": "imply",
            "source": initial_node["node_id"],
            "target": initial_node["node_id"],
            "references": ["ref3", "ref4"],
        },
    )
    assert response.status_code == 200, print(response.json())
    updated_edge = json.loads(response.content.decode("utf-8"))
    assert "references" in updated_edge
    assert len(updated_edge["references"]) == 2
    assert set(updated_edge["references"]) == {"ref3", "ref4"}


def test_migrate_label_to_property(graph_db, client):
    from gremlin_python.process.graph_traversal import __
    from gremlin_python.process.traversal import T

    if not isinstance(graph_db, JanusGraphDB):
        pytest.skip("This test is only for JanusGraph DB")

    # Define a node with a label directly in the test graph using Gremlin Python
    with graph_db.connection() as g:
        g.add_v("label_value").property("name", "test_migration").next()

    # Call the migrate_label_to_property endpoint
    response = client.post(
        "/migrate_label_to_property", json={"property_name": "new_property"}
    )
    assert response.status_code == 200, print(response.json())

    # Verify that the label has been migrated to the property
    with graph_db.connection() as g:
        node = g.V().has("name", "test_migration").next()
        assert node.label == "label_value"  # just checking presence of former index
        # assert 'new_property' in [p.key for p in node.properties]
        assert "label_value" in [
            p.value for p in node.properties if p.key == "new_property"
        ]
