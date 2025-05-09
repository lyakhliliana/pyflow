from typing import Callable
from core.graph.hasher import Hasher
from core.models.edge import Edge
from core.models.graph import Graph
from core.models.node import CODE_NODE_TYPES, Node


class Filter:

    @staticmethod
    def apply_nodes_filter(graph: Graph, nodes_filter: Callable[[Node], bool]) -> Graph:
        result_graph = Graph()

        for node in graph.get_all_nodes():
            if nodes_filter(node):
                result_graph.add_node(node)

        for node in result_graph.get_all_nodes():

            for edge in graph.get_edges_out(node.id):
                if edge.src in result_graph.nodes and edge.dest in result_graph.nodes:
                    result_graph.add_edge(edge)

        Hasher.recalculate(graph)
        return result_graph

    @staticmethod
    def apply_edges_filter(graph: Graph, edges_filter: Callable[[Edge], bool]) -> Graph:
        result_graph = Graph()

        for node in graph.get_all_nodes():
            result_graph.add_node(node)

        for node in graph.get_all_nodes():

            for edge in graph.get_edges_out(node.id):
                if edges_filter(edge):
                    result_graph.add_edge(edge)

        Hasher.recalculate(graph)
        return result_graph


class CommonCasesFilter:

    @staticmethod
    def get_code_elements(graph: Graph) -> Graph:
        return Filter.apply_nodes_filter(graph, lambda node: node.type in CODE_NODE_TYPES)
