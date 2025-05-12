from typing import List
import pytest
from core.models.graph import Graph
from core.models.node import Node
from core.models.edge import Edge


@pytest.fixture
def graph():
    return Graph()


@pytest.fixture
def sample_nodes():
    return [
        Node(id="node1", name="node1", type="type1"),
        Node(id="node2", name="node2", type="type2"),
        Node(id="node3", name="node3", type="type3")
    ]


@pytest.fixture
def sample_edges():
    return [
        Edge(src="node1", dest="node2", type="use"),
        Edge(src="node2", dest="node3", type="contain"),
        Edge(src="node1", dest="node3", type="coupling")
    ]


class TestGraph:
    def test_add_node(self, graph: Graph, sample_nodes: List[Node]):
        assert graph.add_node(sample_nodes[0]) is True
        assert graph.get_node("node1") == sample_nodes[0]
        
        assert graph.add_node(sample_nodes[0]) is False
        
        assert graph.add_node(None) is False

    def test_remove_node(self, graph: Graph, sample_nodes: List[Node]):
        for node in sample_nodes:
            graph.add_node(node)
        
        assert graph.remove_node("node1") is True
        assert graph.get_node("node1") is None
        
        assert graph.remove_node("non_existent") is False

    def test_update_node(self, graph: Graph, sample_nodes: List[Node]):
        graph.add_node(sample_nodes[0])
        
        updated_node = Node(id="node1",name="node1", type="updated_type")
        graph.update_node(updated_node)
        
        assert graph.get_node("node1").type == "updated_type"

    def test_add_edge(self, graph: Graph, sample_nodes: List[Node], sample_edges: List[Edge]):
        for node in sample_nodes:
            graph.add_node(node)
        
        assert graph.add_edge(sample_edges[0]) is True
        assert sample_edges[0] in graph.get_edges_out("node1")
        assert sample_edges[0] in graph.get_edges_in("node2")
        
        invalid_edge = Edge(src="non_existent", dest="node1", type="invalid")
        assert graph.add_edge(invalid_edge) is False
        
        self_loop = Edge(src="node1", dest="node1", type="self_loop")
        assert graph.add_edge(self_loop) is True

    def test_remove_edge(self, graph: Graph, sample_nodes: List[Node], sample_edges: List[Edge]):
        for node in sample_nodes:
            graph.add_node(node)
        for edge in sample_edges:
            graph.add_edge(edge)
        
        assert graph.remove_edge(sample_edges[0]) is True
        assert sample_edges[0] not in graph.get_edges_out("node1")
        assert sample_edges[0] not in graph.get_edges_in("node2")
        
        non_existent_edge = Edge(src="node1", dest="node2", type="non_existent")
        assert graph.remove_edge(non_existent_edge) is False

    def test_get_edges(self, graph: Graph, sample_nodes: List[Node], sample_edges: List[Edge]):
        for node in sample_nodes:
            graph.add_node(node)
        for edge in sample_edges:
            graph.add_edge(edge)
        
        assert len(graph.get_edges_out("node1")) == 2
        assert len(graph.get_edges_out("node2")) == 1
        
        assert len(graph.get_edges_in("node2")) == 1
        assert len(graph.get_edges_in("node3")) == 2
        
        assert len(graph.get_edges_out("non_existent")) == 0
        assert len(graph.get_edges_in("non_existent")) == 0

    def test_get_all_nodes(self, graph: Graph, sample_nodes: List[Node]):
        for node in sample_nodes:
            graph.add_node(node)
        
        all_nodes = graph.get_all_nodes()
        assert len(all_nodes) == 3
        assert all(node in all_nodes for node in sample_nodes)

    def test_get_all_edges(self, graph: Graph, sample_nodes: List[Node], sample_edges: List[Edge]):
        for node in sample_nodes:
            graph.add_node(node)
        for edge in sample_edges:
            graph.add_edge(edge)
        
        all_edges = graph.get_all_edges()
        assert len(all_edges) == 3
        assert all(edge in all_edges for edge in sample_edges) 