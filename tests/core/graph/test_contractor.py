import pytest
from core.graph.contractor import GraphContractor
from core.models.graph import Graph
from core.models.node import Node, TypeNode
from core.models.edge import Edge, TypeEdge, TypeSourceEdge

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
        Edge("code3", "code2", TypeEdge.USE, TypeSourceEdge.HAND),
        Edge("dir1", "file1", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("dir1", "file2", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file1", "code1", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file1", "code2", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file2", "code3", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch1", "code1", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch1", "code2", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch2", "code3", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
    ]
    
    for edge in edges:
        graph.add_edge(edge)
    
    return graph

@pytest.fixture
def complex_graph():
    """Creates a more complex graph with nested structure and multiple types of relationships:
    root_dir/
        src/
            module1/
                file1.py/
                    code1
                    code2
                file2.py/
                    code3
            module2/
                file3.py/
                    code4
                    code5
                file4.py/
                    code6
    arch_element1 (contains code1, code2, code4)
    arch_element2 (contains code3, code5)
    arch_element3 (contains code6)
    """
    graph = Graph()
    
    root_dir = Node("root", "root_dir", TypeNode.DIRECTORY)
    src_dir = Node("src", "src", TypeNode.DIRECTORY)
    module1 = Node("mod1", "module1", TypeNode.DIRECTORY)
    module2 = Node("mod2", "module2", TypeNode.DIRECTORY)
    
    file1 = Node("file1", "file1.py", TypeNode.FILE)
    file2 = Node("file2", "file2.py", TypeNode.FILE)
    file3 = Node("file3", "file3.py", TypeNode.FILE)
    file4 = Node("file4", "file4.py", TypeNode.FILE)
    
    code_nodes = {
        f"code{i}": Node(f"code{i}", f"code{i}", TypeNode.CLASS)
        for i in range(1, 7)
    }
    
    arch1 = Node("arch1", "arch_element1", TypeNode.ARC_ELEMENT)
    arch2 = Node("arch2", "arch_element2", TypeNode.ARC_ELEMENT)
    arch3 = Node("arch3", "arch_element3", TypeNode.ARC_ELEMENT)
    
    all_nodes = [root_dir, src_dir, module1, module2, file1, file2, file3, file4,
                *code_nodes.values(), arch1, arch2, arch3]
    for node in all_nodes:
        graph.add_node(node)
    
    dir_edges = [
        Edge("root", "src", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("src", "mod1", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("src", "mod2", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("mod1", "file1", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("mod1", "file2", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("mod2", "file3", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("mod2", "file4", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
    ]
    
    file_code_edges = [
        Edge("file1", "code1", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file1", "code2", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file2", "code3", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file3", "code4", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file3", "code5", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("file4", "code6", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
    ]
    
    arch_edges = [
        Edge("arch1", "code1", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch1", "code2", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch1", "code4", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch2", "code3", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch2", "code5", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch3", "code6", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
    ]
    
    for edge in dir_edges + file_code_edges + arch_edges:
        graph.add_edge(edge)
    
    return graph

def test_contract_arch_element(sample_graph: Graph):
    """Test contracting an architectural element with its contained code nodes"""
    contractor = GraphContractor(sample_graph)
    con_graph = contractor.contract_graph(["arch1"])
    
    assert con_graph.get_node("arch1") is not None
    
    assert con_graph.get_node("code1") is None
    assert con_graph.get_node("code2") is None
    
    assert con_graph.get_node("code3") is not None
    
    assert len(con_graph.get_edges_out("arch1")) == 0

    assert len(con_graph.get_edges_in("arch1")) == 2

    assert set([edge.src for edge in con_graph.get_edges_in("arch1")]) == set(["code3", "file1"])
    
    assert con_graph.get_node("file1") is not None
    assert con_graph.get_node("file2") is not None

def test_contract_multiple_arch_elements(sample_graph: Graph):
    """Test contracting multiple architectural elements"""
    contractor = GraphContractor(sample_graph)
    con_graph = contractor.contract_graph(["arch1", "arch2"])
    
    assert con_graph.get_node("arch1") is not None
    assert con_graph.get_node("arch2") is not None
    
    assert con_graph.get_node("code1") is None
    assert con_graph.get_node("code2") is None
    assert con_graph.get_node("code3") is None
    
    assert len(con_graph.get_edges_out("arch1")) == 0
    assert len(con_graph.get_edges_out("arch2")) == 1
    assert list(con_graph.get_edges_out("arch2"))[0].dest == "arch1"

def test_contract_invalid_node(sample_graph: Graph):
    """Test contracting an invalid node (not an architectural element)"""
    contractor = GraphContractor(sample_graph)
    con_graph = contractor.contract_graph(["file1"])
    
    assert len(con_graph.nodes) == len(sample_graph.nodes)
    assert len(con_graph.edges) == len(sample_graph.edges)

def test_contract_nonexistent_node(sample_graph: Graph):
    """Test contracting a nonexistent node"""
    contractor = GraphContractor(sample_graph)
    con_graph = contractor.contract_graph(["nonexistent"])
    
    assert len(con_graph.nodes) == len(sample_graph.nodes)
    assert len(con_graph.edges) == len(sample_graph.edges)

def test_contract_with_coupling_edges(sample_graph: Graph):
    """Test contracting nodes with coupling edges between them"""
    # Add coupling edge between code1 and code2
    edge = Edge("arch2", "code2", TypeEdge.CONTAIN, TypeSourceEdge.HAND)
    sample_graph.add_edge(edge)
    
    contractor = GraphContractor(sample_graph)
    con_graph = contractor.contract_graph(["arch1", "arch2"])
    
    coupling_edges = [e for e in con_graph.get_edges_out("arch2") if e.type == TypeEdge.COUPLING]
    assert len(coupling_edges) == 1
    assert coupling_edges[0].dest == "arch1"

def test_complex_graph_contracting(complex_graph: Graph):
    """Test contracting in a complex graph with nested structure"""
    contractor = GraphContractor(complex_graph)
    con_graph = contractor.contract_graph(["arch1", "arch2"])
    
    assert con_graph.get_node("arch1") is not None
    assert con_graph.get_node("arch2") is not None
    assert con_graph.get_node("arch3") is not None
    
    for code_id in ["code1", "code2", "code3", "code4", "code5"]:
        assert con_graph.get_node(code_id) is None
    
    assert con_graph.get_node("code6") is not None
    
    assert con_graph.get_node("root") is not None
    assert con_graph.get_node("src") is not None
    assert con_graph.get_node("mod1") is not None
    assert con_graph.get_node("mod2") is not None
    
    for file_id in ["file1", "file2", "file3", "file4"]:
        assert con_graph.get_node(file_id) is not None

def test_complex_graph_with_use_edges(complex_graph: Graph):
    """Test contracting with multiple types of edges between nodes"""
    edges = [
        Edge("code1", "code2", TypeEdge.USE, TypeSourceEdge.HAND),
        Edge("code2", "code3", TypeEdge.USE, TypeSourceEdge.HAND),
        Edge("code4", "code5", TypeEdge.USE, TypeSourceEdge.HAND),
        Edge("code5", "code6", TypeEdge.USE, TypeSourceEdge.HAND),
    ]
    
    for edge in edges:
        complex_graph.add_edge(edge)
    
    contractor = GraphContractor(complex_graph)
    con_graph = contractor.contract_graph(["arch1", "arch2"])
    
    arch1_edges = con_graph.get_edges_out("arch1")
    arch2_edges = con_graph.get_edges_out("arch2")

    assert len(arch1_edges) == 1
    assert len(arch2_edges) == 1
    
    assert list(arch1_edges)[0].dest == "arch2"
    assert list(arch2_edges)[0].dest == "code6"


def test_circular_dependencies(complex_graph: Graph):
    """Test contracting with circular dependencies between nodes"""
    edges = [
        Edge("code1", "code2", TypeEdge.USE, TypeSourceEdge.HAND),
        Edge("code2", "code3", TypeEdge.USE, TypeSourceEdge.HAND),
        Edge("code3", "code1", TypeEdge.USE, TypeSourceEdge.HAND),
    ]
    
    for edge in edges:
        complex_graph.add_edge(edge)
    
    contractor = GraphContractor(complex_graph)
    con_graph = contractor.contract_graph(["arch1", "arch2"])
    
    arch1_edges = con_graph.get_edges_out("arch1")
    arch2_edges = con_graph.get_edges_out("arch2")
    
    assert any(e.dest == "arch2" and e.type == TypeEdge.USE for e in arch1_edges)
    assert any(e.dest == "arch1" and e.type == TypeEdge.USE for e in arch2_edges)

def test_complex_coupling(complex_graph: Graph):
    """Test complex coupling dependencies between nodes"""
    edges = [
        Edge("arch1", "code5", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("arch1", "code6", TypeEdge.CONTAIN, TypeSourceEdge.HAND),
        Edge("code2", "code3", TypeEdge.USE, TypeSourceEdge.HAND),
    ]
    
    for edge in edges:
        complex_graph.add_edge(edge)
    
    contractor = GraphContractor(complex_graph)
    con_graph = contractor.contract_graph(["arch1", "arch2", "arch3"])
    
    arch1_edges = con_graph.get_edges_out("arch1")
    arch2_edges = con_graph.get_edges_out("arch2")
    arch3_edges = con_graph.get_edges_out("arch3")

    assert len(arch1_edges) == 3
    assert len(arch2_edges) == 1
    assert len(arch3_edges) == 1

    arch1_edges_coupling = [e for e in arch1_edges if e.type == TypeEdge.COUPLING]
    assert len(arch1_edges_coupling) == 2
    
    assert any(e.dest == "arch2" and e.type == TypeEdge.USE for e in arch1_edges)