from typing import Callable, List
import logging

from core.models.graph import Graph
from core.models.node import Node, TYPE_NODES
from core.models.edge import Edge, TYPE_EDGES

logger = logging.getLogger(__name__)


class FilterFunc:

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

        return result_graph

    @staticmethod
    def apply_edges_filter(graph: Graph, edges_filter: Callable[[Edge], bool]) -> Graph:
        result_graph = Graph()

        for node in graph.get_all_nodes():
            result_graph.add_node(node)

        for edge in graph.get_all_edges():
            if edges_filter(edge):
                result_graph.add_edge(edge)

        return result_graph


class CommonFilter:

    @staticmethod
    def apply(graph: Graph, nodes_types: List[str] = [], edges_types: List[str] = []) -> Graph:
        """Filter a graph based on specified node and edge types.

        This method applies filtering to the input graph by keeping only nodes and edges
        of the specified types. If no types are specified for either nodes or edges,
        all nodes or edges of that category are kept.

        Args:
            graph (Graph): The input graph to be filtered
            nodes_types (List[str], optional): List of node types to keep. Defaults to empty list.
            edges_types (List[str], optional): List of edge types to keep. Defaults to empty list.

        Returns:
            Graph: A new filtered graph containing only the specified node and edge types
        """
        invalid_node_types = [t for t in nodes_types if t not in TYPE_NODES]
        if len(invalid_node_types) > 0:
            logger.warning(f"Invalid node types found: {invalid_node_types}. Valid types are: {TYPE_NODES}")
            nodes_types = [t for t in nodes_types if t in TYPE_NODES]

        invalid_edge_types = [t for t in edges_types if t not in TYPE_EDGES]
        if len(invalid_edge_types) > 0:
            logger.warning(f"Invalid edge types found: {invalid_edge_types}. Valid types are: {TYPE_EDGES}")
            edges_types = [t for t in edges_types if t in TYPE_EDGES]

        if len(nodes_types) > 0:
            graph = FilterFunc.apply_nodes_filter(graph, lambda node: node.type in nodes_types)

        if len(edges_types) > 0:
            graph = FilterFunc.apply_edges_filter(graph, lambda edge: edge.type in edges_types)
        return graph
