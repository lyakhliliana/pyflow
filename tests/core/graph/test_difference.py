from copy import deepcopy
import pytest

from core.graph.difference import GraphComparator, TypeDiff, DIFFERENCE_STATUS_FIELD

from core.models.graph import Graph
from core.models.node import Node, TypeNode
from core.models.edge import Edge, TypeEdge
from core.models.common import TypeSource

@pytest.fixture
def sample_graph():
    """Creates a sample graph with the following structure:
    directory1/
        file1.py/
            code1
            code2
        file2.py/
            code3
    arch_element1 (contains code1, code2)
    arch_element2 (contains code3)
    code3 use code2
    """
    graph = Graph()
    
    directory1 = Node("dir1", "directory1", TypeNode.DIRECTORY)
    file1 = Node("file1", "file1.py", TypeNode.FILE)
    file2 = Node("file2", "file2.py", TypeNode.FILE)
    code1 = Node("code1", "code1", TypeNode.CLASS)
    code2 = Node("code2", "code2", TypeNode.CLASS)
    code3 = Node("code3", "code3", TypeNode.CLASS)
    arch1 = Node("arch1", "arch_element1", TypeNode.ARC_ELEMENT)
    arch2 = Node("arch2", "arch_element2", TypeNode.ARC_ELEMENT)
    
    for node in [directory1, file1, file2, code1, code2, code3, arch1, arch2]:
        graph.add_node(node)
    
    edges = [
        Edge("code3", "code2", TypeEdge.USE, TypeSource.HAND),
        Edge("dir1", "file1", TypeEdge.CONTAIN, TypeSource.HAND),
        Edge("dir1", "file2", TypeEdge.CONTAIN, TypeSource.HAND),
        Edge("file1", "code1", TypeEdge.CONTAIN, TypeSource.HAND),
        Edge("file1", "code2", TypeEdge.CONTAIN, TypeSource.HAND),
        Edge("file2", "code3", TypeEdge.CONTAIN, TypeSource.HAND),
        Edge("arch1", "code1", TypeEdge.CONTAIN, TypeSource.HAND),
        Edge("arch1", "code2", TypeEdge.CONTAIN, TypeSource.HAND),
        Edge("arch2", "code3", TypeEdge.CONTAIN, TypeSource.HAND),
    ]
    
    for edge in edges:
        graph.add_edge(edge)
    
    return graph

def test_get_difference_no_changes(sample_graph: Graph):
    """Test getting difference between identical graphs"""
    diff_graph = GraphComparator.get_difference(sample_graph, sample_graph)
    
    for node in diff_graph.get_all_nodes():
        assert node.meta[DIFFERENCE_STATUS_FIELD] == TypeDiff.UNCHACHGED
    
    for edge in diff_graph.get_all_edges():
        assert edge.meta[DIFFERENCE_STATUS_FIELD] == TypeDiff.UNCHACHGED

def test_get_difference_added_node_and_edge(sample_graph: Graph):
    """Test getting difference when adding a new node and edge"""
    new_graph = deepcopy(sample_graph)
    
    new_code = Node("code4", "code4", TypeNode.CLASS)
    new_graph.add_node(new_code)
    new_edge = Edge("code4", "code1", TypeEdge.USE, TypeSource.HAND)
    new_graph.add_edge(new_edge)
    
    diff_graph = GraphComparator.get_difference(sample_graph, new_graph)
    
    new_node = diff_graph.get_node("code4")
    assert new_node is not None
    assert new_node.meta[DIFFERENCE_STATUS_FIELD] == TypeDiff.NEW
    
    new_edges = list(diff_graph.get_edges_out("code4"))
    assert len(new_edges) == 1
    assert new_edges[0].meta[DIFFERENCE_STATUS_FIELD] == TypeDiff.NEW
    
    for node in sample_graph.get_all_nodes():
        if node.id != "code4":
            node = diff_graph.get_node(node.id)
            assert node is not None
            assert node.meta[DIFFERENCE_STATUS_FIELD] == TypeDiff.UNCHACHGED

def test_get_difference_deleted_node_and_edge(sample_graph: Graph):
    """Test getting difference when deleting a node and its edges"""
    new_graph = Graph()
    
    for node in sample_graph.get_all_nodes():
        if node.id != "code3":
            new_graph.add_node(node)
    
    for edge in sample_graph.get_all_edges():
        if edge.src != "code3" and edge.dest != "code3":
            new_graph.add_edge(edge)
    
    diff_graph = GraphComparator.get_difference(sample_graph, new_graph)
    
    deleted_node = diff_graph.get_node("code3")
    assert deleted_node is not None
    assert deleted_node.meta[DIFFERENCE_STATUS_FIELD] == TypeDiff.DELETED
    
    deleted_edges = [e for e in diff_graph.get_all_edges() if e.src == "code3" or e.dest == "code3"]
    assert len(deleted_edges) == 3
    for edge in deleted_edges:
        assert edge.meta[DIFFERENCE_STATUS_FIELD] == TypeDiff.DELETED
    
    for node in new_graph.get_all_nodes():
        node = diff_graph.get_node(node.id)
        assert node is not None
        assert node.meta[DIFFERENCE_STATUS_FIELD] == TypeDiff.UNCHACHGED

def test_get_difference_changed_node(sample_graph: Graph):
    """Test getting difference when a node's content changes"""
    new_graph = Graph()
    
    for node in sample_graph.get_all_nodes():
        new_node = Node(node.id, node.name, node.type)
        if node.id == "code1":
            new_node.hash = "code1_modified"
        new_graph.add_node(new_node)
    
    for edge in sample_graph.get_all_edges():
        new_graph.add_edge(edge)
    
    diff_graph = GraphComparator.get_difference(sample_graph, new_graph)
    
    changed_node = diff_graph.get_node("code1")
    assert changed_node is not None
    assert changed_node.meta[DIFFERENCE_STATUS_FIELD] == TypeDiff.CHANGED
    
    for node in sample_graph.get_all_nodes():
        if node.id != "code1":
            node = diff_graph.get_node(node.id)
            assert node is not None
            assert node.meta[DIFFERENCE_STATUS_FIELD] == TypeDiff.UNCHACHGED 