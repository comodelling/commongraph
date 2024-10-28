import pytest
from pydantic import ValidationError

from models import Node, Edge


correct_node_types = ["undefined", "wish", "proposal", "citw"]
correct_edge_types = ["condition", "implication"]


def test_node_types():
    for node_type in correct_node_types:
        node = Node(node_type=node_type, summary="test")
        assert node.node_type == node_type

    with pytest.raises(ValidationError):
        Node(node_type="wrong_node_type", summary="")


def test_edge_types():
    for edge_type in correct_edge_types:
        edge = Edge(edge_type=edge_type, source=0, target=0)
        assert edge.edge_type == edge_type

    with pytest.raises(ValidationError):
        Edge(edge_type="wrong_edge_type", source=0, target=0)
