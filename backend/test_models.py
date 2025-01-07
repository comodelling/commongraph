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


def test_node_required_fields():
    with pytest.raises(ValidationError):
        NodeBase(node_type="objective", scope="test scope")  # Missing 'title'


def test_node_field_types():
    with pytest.raises(ValidationError):
        NodeBase(
            node_type="objective", title=123, scope="test scope"
        )  # 'title' should be str

    with pytest.raises(ValidationError):
        NodeBase(
            node_type="objective", title="test", scope=456
        )  # 'scope' should be str


def test_edge_required_fields():
    with pytest.raises(ValidationError):
        EdgeBase(edge_type="imply", target=1)  # Missing 'source'

    with pytest.raises(ValidationError):
        EdgeBase(source=1, target=2)  # Missing 'edge_type'


def test_edge_field_types():
    with pytest.raises(ValidationError):
        EdgeBase(edge_type="imply", source="one", target=2)  # 'source' should be int

    with pytest.raises(ValidationError):
        # 'target' should be int
        EdgeBase(edge_type="imply", source=1, target="two")


def test_node_optional_fields():
    node = NodeBase(title="test", scope="test scope")
    assert node.description is None
    assert node.tags == []
    assert node.references == []
    assert node.status == "unspecified"
    assert node.node_type == "potentiality"
    assert node.support is None

    node = NodeBase(
        node_type="objective",
        title="test",
        scope="test scope",
        status="live",
        description="A test node",
        tags=["tag1", "tag2"],
        references=["ref1", "ref2"],
        support="A",
    )
    assert node.description == "A test node"
    assert node.tags == ["tag1", "tag2"]
    assert node.references == ["ref1", "ref2"]
    assert node.status == "live"
    assert node.node_type == "objective"
    assert node.support == "A"


def test_edge_optional_fields():
    edge = EdgeBase(edge_type="imply", source=1, target=2)
    assert edge.cprob is None
    assert edge.references == []
    assert edge.description is None

    edge = EdgeBase(
        edge_type="imply",
        source=1,
        target=2,
        cprob=0.75,
        references=["ref1"],
        description="A test edge",
    )
    assert edge.cprob == 0.75
    assert edge.references == ["ref1"]
    assert edge.description == "A test edge"
