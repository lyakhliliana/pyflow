import pytest
from core.graph.dependency import DepenendencyExtensions
from core.models.graph import Graph
from core.models.node import Node, TypeNode
from core.models.edge import Edge, TypeEdge, TypeSourceEdge

@pytest.fixture
def complex_graph():
    """Creates a complex graph with multiple layers of dependencies:
    root/
        src/
            module1/
                file1.py/
                    class1
                    class2
                file2.py/
                    class3
            module2/
                file3.py/
                    class4
                    class5
                file4.py/
                    class6
    arch1 (contains class1, class2, class4)
    arch2 (contains class3, class5)
    arch3 (contains class6)
    
    Dependencies:
    - class3 uses class2
    - class4 uses class1
    - class5 uses class3
    - class6 uses class5
    - class1 uses class6 (circular dependency)
    """
    graph = Graph()

    root = Node("root", "root", TypeNode.DIRECTORY)
    src = Node("src", "src", TypeNode.DIRECTORY)
    module1 = Node("mod1", "module1", TypeNode.DIRECTORY)
    module2 = Node("mod2", "module2", TypeNode.DIRECTORY)

    file1 = Node("file1", "file1.py", TypeNode.FILE)
    file2 = Node("file2", "file2.py", TypeNode.FILE)
    file3 = Node("file3", "file3.py", TypeNode.FILE)
    file4 = Node("file4", "file4.py", TypeNode.FILE)
    
    classes = {
        f"class{i}": Node(f"class{i}", f"class{i}", TypeNode.CLASS)
        for i in range(1, 7)
    }
    
    arch1 = Node("arch1", "arch_element1", TypeNode.ARC_ELEMENT)
    arch2 = Node("arch2", "arch_element2", TypeNode.ARC_ELEMENT)
    arch3 = Node("arch3", "arch_element3", TypeNode.ARC_ELEMENT)
    
    all_nodes = [root, src, module1, module2, file1, file2, file3, file4,
                *classes.values(), arch1, arch2, arch3]
    for node in all_nodes:
        graph.add_node(node)
    
    containment_edges = [
        Edge("root", "src", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("src", "mod1", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("src", "mod2", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("mod1", "file1", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("mod1", "file2", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("mod2", "file3", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("mod2", "file4", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file1", "class1", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file1", "class2", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file2", "class3", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file3", "class4", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file3", "class5", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file4", "class6", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
    ]
    
    arch_edges = [
        Edge("arch1", "class1", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch1", "class2", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch1", "class4", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch2", "class3", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch2", "class5", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch3", "class6", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
    ]
    
    usage_edges = [
        Edge("class3", "class2", TypeEdge.USE, TypeSourceEdge.HAND),
        Edge("class4", "class1", TypeEdge.USE, TypeSourceEdge.HAND),
        Edge("class5", "class3", TypeEdge.USE, TypeSourceEdge.HAND),
        Edge("class6", "class5", TypeEdge.USE, TypeSourceEdge.HAND),
        Edge("class1", "class6", TypeEdge.USE, TypeSourceEdge.HAND), 
    ]
    
    for edge in containment_edges + arch_edges + usage_edges:
        graph.add_edge(edge)
    
    return graph

def test_get_used_nodes_basic(complex_graph: Graph):
    """Test getting used nodes from a single starting point"""
    result = DepenendencyExtensions.get_used_nodes(complex_graph, {"class3"})
    
    assert result.get_node("class3") is not None
    assert result.get_node("class2") is not None
    assert result.get_node("class1") is None
    
    edges = list(result.get_edges_out("class3"))
    assert len(edges) == 1
    assert edges[0].dest == "class2"

def test_get_used_nodes_with_depth(complex_graph: Graph):
    """Test getting used nodes with depth limit"""
    result = DepenendencyExtensions.get_used_nodes(complex_graph, {"class5"}, depth=1)
    
    assert result.get_node("class5") is not None
    assert result.get_node("class3") is not None
    assert result.get_node("class2") is None  # Beyond depth limit
    
    edges = list(result.get_edges_out("class5"))
    assert len(edges) == 1
    assert edges[0].dest == "class3"

def test_get_used_nodes_multiple_starting_points(complex_graph: Graph):
    """Test getting used nodes from multiple starting points"""
    result = DepenendencyExtensions.get_used_nodes(complex_graph, {"class4", "class6"})
    
    assert result.get_node("class4") is not None
    assert result.get_node("class1") is not None
    assert result.get_node("class6") is not None
    assert result.get_node("class5") is not None
    assert result.get_node("class3") is not None
    assert result.get_node("class2") is not None

def test_get_dependent_nodes_basic(complex_graph: Graph):
    """Test getting dependent nodes from a single starting point"""
    result = DepenendencyExtensions.get_dependent_nodes(complex_graph, {"class1"})
    
    assert result.get_node("class1") is not None
    assert result.get_node("class4") is not None
    assert result.get_node("arch1") is not None
    
    edges = list(result.get_edges_in("class1"))
    assert len(edges) == 3
    assert set([edge.src for edge in edges]) == set(["class4", "file1", "arch1"])

def test_get_dependent_nodes_with_depth(complex_graph: Graph):
    """Test getting dependent nodes with depth limit"""
    result = DepenendencyExtensions.get_dependent_nodes(complex_graph, {"class3"}, depth=1)
    
    # Should include class3 and class5 (direct dependency)
    assert result.get_node("class3") is not None
    assert result.get_node("class5") is not None
    assert result.get_node("class6") is None  # Beyond depth limit
    
    edges = list(result.get_edges_in("class3"))
    assert len(edges) == 3
    assert set([edge.src for edge in edges]) == set(["class5", "file2", "arch2"])

def test_get_dependent_nodes_multiple_starting_points(complex_graph: Graph):
    """Test getting dependent nodes from multiple starting points"""
    result = DepenendencyExtensions.get_dependent_nodes(complex_graph, {"class1", "class5"})
    
    assert result.get_node("class1") is not None
    assert result.get_node("class4") is not None
    assert result.get_node("class5") is not None
    assert result.get_node("class6") is not None

def test_get_used_nodes_circular_dependency(complex_graph: Graph):
    """Test getting used nodes with circular dependencies"""
    result = DepenendencyExtensions.get_used_nodes(complex_graph, {"class1"})
    
    assert result.get_node("class1") is not None
    assert result.get_node("class6") is not None
    assert result.get_node("class5") is not None
    assert result.get_node("class3") is not None
    assert result.get_node("class2") is not None
    
    edges = list(result.get_edges_out("class1"))
    assert len(edges) == 1
    assert edges[0].dest == "class6"
    
    edges = list(result.get_edges_out("class6"))
    assert len(edges) == 1
    assert edges[0].dest == "class5"
