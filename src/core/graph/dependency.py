from collections import deque
from copy import deepcopy
import logging
from typing import Set

from core.models.graph import Graph

logger = logging.getLogger(__name__)


class DepenendencyExtensions:

    @staticmethod
    def get_used_nodes(graph: Graph, code_nodes: Set[str], depth: int = 0) -> Graph:
        """
        Creates a new graph containing nodes that are used by the specified code nodes and their dependencies.

        This method performs a breadth-first search starting from the given code nodes and follows outgoing edges
        to find all nodes that are used by the specified nodes. The search can be limited by depth.

        Args:
            graph (Graph): The source graph to analyze
            code_nodes (Set[str]): Set of node IDs to start the search from
            depth (int, optional): Maximum depth to search. If 0, searches without depth limit. Defaults to 0.

        Returns:
            Graph: A new graph containing the used nodes and their edges
        """
        new_graph = Graph()
        visited: Set[str] = set()

        for start_node_id in code_nodes:
            if start_node_id not in graph.nodes:
                logger.warning(f"{start_node_id} not found")
                continue

            if start_node_id in visited:
                continue

            start_node = graph.get_node(start_node_id)
            new_graph.add_node(deepcopy(start_node))
            visited.add(start_node_id)

            queue = deque([(0, start_node_id)])

            while queue:
                cur_depth, current_id = queue.popleft()

                for edge in graph.get_edges_out(current_id):
                    if edge.dest not in graph.nodes:
                        continue

                    if edge.dest not in visited:
                        dest_node = graph.get_node(edge.dest)
                        new_graph.add_node(deepcopy(dest_node))
                        visited.add(dest_node.id)
                        if depth == 0 or cur_depth + 1 < depth:
                            queue.append((cur_depth + 1, dest_node.id))

                    new_graph.add_edge(deepcopy(edge))

        return new_graph

    @staticmethod
    def get_dependent_nodes(graph: Graph, code_nodes: Set[str], depth: int = 0) -> Graph:
        """
        Creates a new graph containing nodes that depend on the specified code nodes.

        This method performs a breadth-first search starting from the given code nodes and follows incoming edges
        to find all nodes that depend on the specified nodes. The search can be limited by depth.

        Args:
            graph (Graph): The source graph to analyze
            code_nodes (Set[str]): Set of node IDs to start the search from
            depth (int, optional): Maximum depth to search. If 0, searches without depth limit. Defaults to 0.

        Returns:
            Graph: A new graph containing the dependent nodes and their connections
        """
        new_graph = Graph()
        visited: Set[str] = set()

        for start_node_id in code_nodes:
            if start_node_id not in graph.nodes:
                logger.warning(f"{start_node_id} not found")
                continue

            if start_node_id in visited:
                continue

            start_node = graph.get_node(start_node_id)
            new_graph.add_node(deepcopy(start_node))
            visited.add(start_node_id)

            queue = deque([(0, start_node_id)])

            while queue:
                cur_depth, current_id = queue.popleft()

                for edge in graph.get_edges_in(current_id):
                    if edge.src not in graph.nodes:
                        continue

                    if edge.src not in visited:
                        src_node = graph.get_node(edge.src)
                        new_graph.add_node(deepcopy(src_node))
                        visited.add(src_node.id)
                        if depth == 0 or cur_depth + 1 < depth:
                            queue.append((cur_depth + 1, src_node.id))

                    new_graph.add_edge(deepcopy(edge))

        return new_graph