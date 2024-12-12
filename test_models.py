import pytest
from pydantic import ValidationError

from models import NodeBase, EdgeBase


correct_node_types = [
    "change",
    "wish",
    "proposal",
    "action",
    "objective",
    "potentiality",
]
correct_edge_types = ["require", "imply"]


def test_node_types():
    for node_type in correct_node_types:
        node = NodeBase(node_type=node_type, title="test")
        assert node.node_type == node_type

    with pytest.raises(ValidationError):
        NodeBase(node_type="wrong_node_type", title="")


def test_edge_types():
    for edge_type in correct_edge_types:
        edge = EdgeBase(edge_type=edge_type, source=0, target=0)
        assert edge.edge_type == edge_type

    with pytest.raises(ValidationError):
        EdgeBase(edge_type="wrong_edge_type", source=0, target=0)
