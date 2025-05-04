from collections import defaultdict
import logging
from typing import Dict, Set, List

from core.models.edge import Edge
from core.models.node import Node

logger = logging.getLogger(__name__)


class Graph:
    __slots__ = ('nodes', 'edges', 'inv_edges')

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, List[Edge]] = defaultdict(list)
        self.inv_edges: Dict[str, Set[str]] = defaultdict(set)

    def __contains__(self, id: str) -> bool:
        return id in self.nodes

    def add_node(self, node: Node) -> bool:
        if node.id in self.nodes:
            return False

        self.nodes[node.id] = node

        return True

    def add_edge(self, edge: Edge, with_check: bool = True) -> bool:
        if with_check and edge.src not in self.nodes:
            return False

        if with_check and edge.dest not in self.nodes:
            return False
        
        if edge.dest in self.inv_edges and edge.src in self.inv_edges[edge.dest]:
            return False

        self.edges[edge.src].append(edge)
        self.inv_edges[edge.dest].add(edge.src)

        return True
