import pytest
from core.models.graph import Graph
from core.models.node import Node, TypeNode, TypeSourceNode
from core.models.edge import Edge, TypeEdge, TypeSourceEdge
from core.graph.filters import CommonFilter

@pytest.fixture
def complex_graph():
    """Creates a complex graph with multiple types of nodes and edges:
    root_dir/
        src/
            module1/
                file1.py/
                    class1
                    func1
                file2.py/
                    class2
            module2/
                file3.py/
                    class3
                    func2
    arch_element1 (contains class1, func1)
    arch_element2 (contains class2)
    arch_element3 (contains class3, func2)
    class2 uses class1
    func2 uses func1
    """
    graph = Graph()
    
    root_dir = Node("root", "root_dir", TypeNode.DIRECTORY)
    src_dir = Node("src", "src", TypeNode.DIRECTORY)
    module1 = Node("mod1", "module1", TypeNode.DIRECTORY)
    module2 = Node("mod2", "module2", TypeNode.DIRECTORY)
    
    file1 = Node("file1", "file1.py", TypeNode.FILE)
    file2 = Node("file2", "file2.py", TypeNode.FILE)
    file3 = Node("file3", "file3.py", TypeNode.FILE)
    
    class1 = Node("class1", "class1", TypeNode.CLASS)
    func1 = Node("func1", "func1", TypeNode.FUNC)
    class2 = Node("class2", "class2", TypeNode.CLASS)
    class3 = Node("class3", "class3", TypeNode.CLASS)
    func2 = Node("func2", "func2", TypeNode.FUNC)
    
    arch1 = Node("arch1", "arch_element1", TypeNode.ARC_ELEMENT)
    arch2 = Node("arch2", "arch_element2", TypeNode.ARC_ELEMENT)
    arch3 = Node("arch3", "arch_element3", TypeNode.ARC_ELEMENT)
    
    all_nodes = [root_dir, src_dir, module1, module2, file1, file2, file3,
                class1, func1, class2, class3, func2, arch1, arch2, arch3]
    for node in all_nodes:
        graph.add_node(node)
    
    containment_edges = [
        Edge("root", "src", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("src", "mod1", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("src", "mod2", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("mod1", "file1", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("mod1", "file2", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("mod2", "file3", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("file1", "class1", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("file1", "func1", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("file2", "class2", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("file3", "class3", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("file3", "func2", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("arch1", "class1", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("arch1", "func1", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("arch2", "class2", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("arch3", "class3", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
        Edge("arch3", "func2", TypeEdge.CONTAIN, TypeSourceEdge.CODE),
    ]
    
    usage_edges = [
        Edge("class2", "class1", TypeEdge.USE, TypeSourceEdge.CODE),
        Edge("func2", "func1", TypeEdge.USE, TypeSourceEdge.CODE),
    ]
    
    for edge in containment_edges + usage_edges:
        graph.add_edge(edge)
    
    return graph

def test_filter_code_nodes_only(complex_graph: Graph):
    """Test filtering to show only code nodes (class, func, body) and their relationships"""
    filtered_graph = CommonFilter.apply(complex_graph, 
                                           nodes_types=[TypeNode.CLASS, TypeNode.FUNC, TypeNode.BODY])
    
    for node in filtered_graph.get_all_nodes():
        assert node.type in [TypeNode.CLASS, TypeNode.FUNC, TypeNode.BODY]
    
    code_nodes = ["class1", "func1", "class2", "class3", "func2"]
    for node_id in code_nodes:
        assert filtered_graph.get_node(node_id) is not None
    
    assert len(list(filtered_graph.get_edges_out("class2"))) == 1
    assert len(list(filtered_graph.get_edges_out("func2"))) == 1
    assert list(filtered_graph.get_edges_out("class2"))[0].dest == "class1"
    assert list(filtered_graph.get_edges_out("func2"))[0].dest == "func1"

def test_filter_structure_nodes_only(complex_graph: Graph):
    """Test filtering to show only structure nodes (directory, file) and their relationships"""
    filtered_graph = CommonFilter.apply(complex_graph, 
                                           nodes_types=[TypeNode.DIRECTORY, TypeNode.FILE])
    
    for node in filtered_graph.get_all_nodes():
        assert node.type in [TypeNode.DIRECTORY, TypeNode.FILE]
    
    structure_nodes = ["root", "src", "mod1", "mod2", "file1", "file2", "file3"]
    for node_id in structure_nodes:
        assert filtered_graph.get_node(node_id) is not None
    
    assert len(list(filtered_graph.get_edges_out("root"))) == 1
    assert len(list(filtered_graph.get_edges_out("src"))) == 2
    assert len(list(filtered_graph.get_edges_out("mod1"))) == 2
    assert len(list(filtered_graph.get_edges_out("mod2"))) == 1

def test_filter_arch_elements_only(complex_graph: Graph):
    """Test filtering to show only architectural elements and their relationships"""
    filtered_graph = CommonFilter.apply(complex_graph, 
                                           nodes_types=[TypeNode.ARC_ELEMENT])
    
    for node in filtered_graph.get_all_nodes():
        assert node.type == TypeNode.ARC_ELEMENT
    
    arch_nodes = ["arch1", "arch2", "arch3"]
    for node_id in arch_nodes:
        assert filtered_graph.get_node(node_id) is not None

def test_filter_use_edges_only(complex_graph: Graph):
    """Test filtering to show only use edges"""
    filtered_graph = CommonFilter.apply(complex_graph, 
                                           edges_types=[TypeEdge.USE])
    
    assert len(filtered_graph.nodes) == len(complex_graph.nodes)
    
    for edge in filtered_graph.get_all_edges():
        assert edge.type == TypeEdge.USE
    
    use_edges = [
        ("class2", "class1"),
        ("func2", "func1")
    ]
    for src, dest in use_edges:
        edges = list(filtered_graph.get_edges_out(src))
        assert len(edges) == 1
        assert edges[0].dest == dest

def test_filter_containment_edges_only(complex_graph: Graph):
    """Test filtering to show only containment edges"""
    filtered_graph = CommonFilter.apply(complex_graph, 
                                           edges_types=[TypeEdge.CONTAIN])
    
    assert len(filtered_graph.nodes) == len(complex_graph.nodes)
    
    for edge in filtered_graph.get_all_edges():
        assert edge.type == TypeEdge.CONTAIN
    
    containment_edges = [
        ("root", "src"),
        ("src", "mod1"),
        ("src", "mod2"),
        ("mod1", "file1"),
        ("mod1", "file2"),
        ("mod2", "file3"),
        ("file1", "class1"),
        ("file1", "func1"),
        ("file2", "class2"),
        ("file3", "class3"),
        ("file3", "func2"),
        ("arch1", "class1"),
        ("arch1", "func1"),
        ("arch2", "class2"),
        ("arch3", "class3"),
        ("arch3", "func2")
    ]
    for src, dest in containment_edges:
        edges = list(filtered_graph.get_edges_out(src))
        assert any(edge.dest == dest for edge in edges)

def test_filter_code_nodes_and_use_edges(complex_graph: Graph):
    """Test filtering to show only code nodes and use edges between them"""
    filtered_graph = CommonFilter.apply(complex_graph,
                                           nodes_types=[TypeNode.CLASS, TypeNode.FUNC, TypeNode.BODY],
                                           edges_types=[TypeEdge.USE])
    
    for node in filtered_graph.get_all_nodes():
        assert node.type in [TypeNode.CLASS, TypeNode.FUNC, TypeNode.BODY]
    
    code_nodes = ["class1", "func1", "class2", "class3", "func2"]
    for node_id in code_nodes:
        assert filtered_graph.get_node(node_id) is not None
    
    for edge in filtered_graph.get_all_edges():
        assert edge.type == TypeEdge.USE
    
    use_edges = [
        ("class2", "class1"),
        ("func2", "func1")
    ]
    for src, dest in use_edges:
        edges = list(filtered_graph.get_edges_out(src))
        assert len(edges) == 1
        assert edges[0].dest == dest

def test_get_arch_elements_containing(complex_graph: Graph):
    """Test getting architectural elements and their contained code nodes"""
    filtered_graph = CommonFilter.apply(complex_graph,
                                          nodes_types=[TypeNode.ARC_ELEMENT, TypeNode.CLASS, TypeNode.FUNC, TypeNode.BODY],
                                          edges_types=[TypeEdge.CONTAIN])
    
    assert filtered_graph.get_node("arch1") is not None
    assert filtered_graph.get_node("arch2") is not None
    assert filtered_graph.get_node("arch3") is not None
    
    assert filtered_graph.get_node("class1") is not None
    assert filtered_graph.get_node("func1") is not None
    assert filtered_graph.get_node("class2") is not None
    assert filtered_graph.get_node("class3") is not None
    assert filtered_graph.get_node("func2") is not None
    
    arch1_edges = list(filtered_graph.get_edges_out("arch1"))
    assert len(arch1_edges) == 2
    assert any(e.dest == "class1" for e in arch1_edges)
    assert any(e.dest == "func1" for e in arch1_edges)
    
    arch2_edges = list(filtered_graph.get_edges_out("arch2"))
    assert len(arch2_edges) == 1
    assert any(e.dest == "class2" for e in arch2_edges)
    
    arch3_edges = list(filtered_graph.get_edges_out("arch3"))
    assert len(arch3_edges) == 2
    assert any(e.dest == "class3" for e in arch3_edges)
    assert any(e.dest == "func2" for e in arch3_edges)

def test_filter_by_node_pattern(complex_graph: Graph):
    """Test filtering nodes by ID pattern using wildcards"""
    # Test with * wildcard
    filtered_graph = CommonFilter.apply(complex_graph, node_reg="class*")
    class_nodes = ["class1", "class2", "class3"]
    for node_id in class_nodes:
        assert filtered_graph.get_node(node_id) is not None
    assert filtered_graph.get_node("func1") is None
    
    # Test with . wildcard
    filtered_graph = CommonFilter.apply(complex_graph, node_reg="class.")
    assert filtered_graph.get_node("class1") is not None
    assert filtered_graph.get_node("class2") is not None
    assert filtered_graph.get_node("class3") is not None
    assert filtered_graph.get_node("class10") is None

def test_inverted_filtering(complex_graph: Graph):
    """Test inverted filtering logic"""
    filtered_graph = CommonFilter.apply(complex_graph, 
                                      nodes_types=[TypeNode.CLASS, TypeNode.FUNC],
                                      inv_flag=True)
    
    for node in filtered_graph.get_all_nodes():
        assert node.type not in [TypeNode.CLASS, TypeNode.FUNC]
    
    filtered_graph = CommonFilter.apply(complex_graph,
                                      edges_types=[TypeEdge.USE],
                                      inv_flag=True)
    
    for edge in filtered_graph.get_all_edges():
        assert edge.type != TypeEdge.USE
    
    filtered_graph = CommonFilter.apply(complex_graph,
                                      node_reg="class*",
                                      inv_flag=True)
    
    for node in filtered_graph.get_all_nodes():
        assert not node.id.startswith("class")

def test_combined_filtering(complex_graph: Graph):
    """Test combining multiple filter criteria"""
    filtered_graph = CommonFilter.apply(complex_graph,
                                      nodes_types=[TypeNode.CLASS],
                                      edges_types=[TypeEdge.USE],
                                      node_reg="class[12]")

    assert filtered_graph.get_node("class1") is not None
    assert filtered_graph.get_node("class2") is not None
    assert filtered_graph.get_node("class3") is None
    assert filtered_graph.get_node("func1") is None
    
    edges = list(filtered_graph.get_all_edges())
    assert len(edges) == 1
    assert edges[0].src == "class2"
    assert edges[0].dest == "class1"
    assert edges[0].type == TypeEdge.USE

def test_invalid_type_handling(complex_graph: Graph):
    """Test handling of invalid node and edge types"""
    filtered_graph = CommonFilter.apply(complex_graph,
                                      nodes_types=["INVALID_TYPE", TypeNode.CLASS])
    
    for node in filtered_graph.get_all_nodes():
        assert node.type == TypeNode.CLASS
    
    filtered_graph = CommonFilter.apply(complex_graph,
                                      edges_types=["INVALID_TYPE", TypeEdge.USE])
    
    for edge in filtered_graph.get_all_edges():
        assert edge.type == TypeEdge.USE 