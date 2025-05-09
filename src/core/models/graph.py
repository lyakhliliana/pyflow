import logging
from collections import defaultdict
from typing import Dict, Optional, Set, List

from core.models.edge import Edge
from core.models.node import Node

logger = logging.getLogger(__name__)


class Graph:
    __slots__ = ('nodes', 'edges', 'inv_edges')

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Set[Edge]] = defaultdict(set)
        self.inv_edges: Dict[str, Set[Edge]] = defaultdict(set)

    def add_node(self, node: Node) -> bool:
        if node.id in self.nodes:
            return False
        self.nodes[node.id] = node
        return True

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def update_node(self, node: Node):
        self.nodes[node.id] = node

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self.nodes:
            return False

        for edge in list(self.edges[node_id]):
            self.remove_edge(edge)

        for edge in list(self.inv_edges[node_id]):
            self.remove_edge(edge)

        del self.nodes[node_id]
        return True

    def add_edge(self, edge: Edge, with_check: bool = True) -> bool:
        if with_check and edge.src not in self.nodes:
            return False

        if with_check and edge.dest not in self.nodes:
            return False

        if edge.dest == edge.src:
            return True

        if edge not in self.edges[edge.src]:
            self.edges[edge.src].add(edge)
            self.inv_edges[edge.dest].add(edge)
            return True

        return True

    def remove_edge(self, edge: Edge) -> bool:
        if edge in self.edges[edge.src]:
            self.edges[edge.src].remove(edge)
            self.inv_edges[edge.dest].remove(edge)
            return True
        return False

    def get_edges_out(self, node_id: str) -> Set[Edge]:
        return self.edges.get(node_id, [])

    def get_edges_in(self, node_id: str) -> Set[Edge]:
        return self.inv_edges.get(node_id, set())

    def get_all_nodes(self) -> List[Node]:
        return list(self.nodes.values())

    def get_all_edges(self):
        return [edge for edges in self.edges.values() for edge in edges]
