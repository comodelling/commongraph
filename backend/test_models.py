"""
Unit tests for base models and dynamic model creation.

Tests the current architecture:
- Base models (NodeBase, EdgeBase) with minimal required fields
- Dynamic model generation based on configuration
- Type validation from config
"""
import pytest
from pydantic_core import ValidationError

from backend.models.base import NodeBase, EdgeBase, SubgraphBase
from backend.models.dynamic import NodeTypeModels, EdgeTypeModels
from backend.config import valid_node_types, valid_edge_types


# Test Base Models - Minimal Required Fields
# ============================================

def test_node_base_requires_node_type():
    """NodeBase requires node_type field"""
    with pytest.raises(ValidationError) as exc_info:
        NodeBase()
    
    errors = exc_info.value.errors()
    assert any(e['loc'] == ('node_type',) and e['type'] == 'missing' for e in errors)


def test_node_base_validates_node_type():
    """NodeBase validates node_type against config"""
    # Valid node type should work
    valid_types = valid_node_types()
    if valid_types:
        node = NodeBase(node_type=list(valid_types)[0])
        assert node.node_type in valid_types
    
    # Invalid node type should raise ValueError
    with pytest.raises(ValueError, match="not in configured node_types"):
        NodeBase(node_type="invalid_type_xyz")


def test_node_base_accepts_optional_node_id():
    """NodeBase accepts optional node_id"""
    node = NodeBase(node_type="objective")
    assert node.node_id is None
    
    node_with_id = NodeBase(node_type="objective", node_id=42)
    assert node_with_id.node_id == 42


def test_edge_base_requires_all_fields():
    """EdgeBase requires edge_type, source, and target"""
    # Missing edge_type
    with pytest.raises(ValidationError) as exc_info:
        EdgeBase(source=1, target=2)
    errors = exc_info.value.errors()
    assert any(e['loc'] == ('edge_type',) and e['type'] == 'missing' for e in errors)
    
    # Missing source
    with pytest.raises(ValidationError) as exc_info:
        EdgeBase(edge_type="imply", target=2)
    errors = exc_info.value.errors()
    assert any(e['loc'] == ('source',) and e['type'] == 'missing' for e in errors)
    
    # Missing target
    with pytest.raises(ValidationError) as exc_info:
        EdgeBase(edge_type="imply", source=1)
    errors = exc_info.value.errors()
    assert any(e['loc'] == ('target',) and e['type'] == 'missing' for e in errors)


def test_edge_base_validates_edge_type():
    """EdgeBase validates edge_type against config"""
    # Valid edge type should work
    valid_types = valid_edge_types()
    if valid_types:
        edge = EdgeBase(edge_type=list(valid_types)[0], source=1, target=2)
        assert edge.edge_type in valid_types
    
    # Invalid edge type should raise ValueError
    with pytest.raises(ValueError, match="not in configured edge_types"):
        EdgeBase(edge_type="invalid_type_xyz", source=1, target=2)


def test_edge_base_validates_field_types():
    """EdgeBase validates source and target are integers"""
    # source must be int
    with pytest.raises(ValidationError):
        EdgeBase(edge_type="imply", source="not_an_int", target=2)
    
    # target must be int
    with pytest.raises(ValidationError):
        EdgeBase(edge_type="imply", source=1, target="not_an_int")


def test_edge_base_creates_valid_edge():
    """EdgeBase creates valid edge with all required fields"""
    edge = EdgeBase(edge_type="imply", source=1, target=2)
    assert edge.edge_type == "imply"
    assert edge.source == 1
    assert edge.target == 2


# Test Dynamic Models
# ===================

def test_dynamic_node_models_created():
    """Dynamic node models are created for each configured node type"""
    configured_types = valid_node_types()
    
    assert len(NodeTypeModels) == len(configured_types)
    for node_type in configured_types:
        assert node_type in NodeTypeModels
        assert NodeTypeModels[node_type].__name__ == f"{node_type.title()}NodeBase"


def test_dynamic_edge_models_created():
    """Dynamic edge models are created for each configured edge type"""
    configured_types = valid_edge_types()
    
    assert len(EdgeTypeModels) == len(configured_types)
    for edge_type in configured_types:
        assert edge_type in EdgeTypeModels
        assert EdgeTypeModels[edge_type].__name__ == f"{edge_type.title()}EdgeBase"


def test_dynamic_node_model_has_properties():
    """Dynamic node models include properties from config"""
    # Pick first available node type
    node_type = list(valid_node_types())[0]
    DynamicNode = NodeTypeModels[node_type]
    
    # Should have base fields
    assert 'node_type' in DynamicNode.model_fields
    assert 'node_id' in DynamicNode.model_fields
    
    # node_type should be fixed to the type
    node = DynamicNode()
    assert node.node_type == node_type


def test_dynamic_edge_model_has_properties():
    """Dynamic edge models include properties from config"""
    # Pick first available edge type
    edge_type = list(valid_edge_types())[0]
    DynamicEdge = EdgeTypeModels[edge_type]
    
    # Should have base fields
    assert 'edge_type' in DynamicEdge.model_fields
    assert 'source' in DynamicEdge.model_fields
    assert 'target' in DynamicEdge.model_fields
    
    # edge_type should be fixed to the type
    edge = DynamicEdge(source=1, target=2)
    assert edge.edge_type == edge_type


# Test Subgraph Model
# ===================

def test_subgraph_requires_nodes_and_edges():
    """SubgraphBase requires nodes and edges lists"""
    with pytest.raises(ValidationError):
        SubgraphBase()
    
    subgraph = SubgraphBase(nodes=[], edges=[])
    assert subgraph.nodes == []
    assert subgraph.edges == []


def test_subgraph_accepts_node_and_edge_objects():
    """SubgraphBase accepts lists of nodes and edges"""
    node = NodeBase(node_type="objective", node_id=1)
    edge = EdgeBase(edge_type="imply", source=1, target=2)
    
    subgraph = SubgraphBase(nodes=[node], edges=[edge])
    assert len(subgraph.nodes) == 1
    assert len(subgraph.edges) == 1
    assert subgraph.nodes[0].node_type == "objective"
    assert subgraph.edges[0].edge_type == "imply"
