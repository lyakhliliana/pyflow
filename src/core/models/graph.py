from collections import defaultdict
import logging
from typing import Dict, Set, List

from core.models.edge import Edge, TypeEdge
from core.models.node import ADDITIONAL_NODE_TYPES, CODE_NODE_TYPES, ROOT_NODE_NAME, Node
from src.core.utils.hash import stable_hash_from_hashes

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
            return True

        self.edges[edge.src].append(edge)
        self.inv_edges[edge.dest].add(edge.src)

        return True
    
    def calculate_all_hashes(self):

        def recursive_structure_hash(cur_id: str = ROOT_NODE_NAME) -> str:
            cur_node = self.nodes[cur_id]

            if cur_node.type in CODE_NODE_TYPES:
                return cur_node.hash

            hashes = []
            contain_edges = self.edges.get(cur_id, [])
            for edge in contain_edges:
                if edge.type != TypeEdge.CONTAIN:
                    continue
                hash_node_id = recursive_structure_hash(edge.dest)
                hashes.append(hash_node_id)

            cur_node.hash = stable_hash_from_hashes(hashes)
            return cur_node.hash
        
        def recursive_additional_hash(cur_id: str = ROOT_NODE_NAME) -> str:
            cur_node = self.nodes[cur_id]

            if cur_node.type not in ADDITIONAL_NODE_TYPES or cur_node.hash != "":
                return cur_node.hash

            hashes = []
            contain_edges = self.edges.get(cur_id, [])
            for edge in contain_edges:
                if edge.type != TypeEdge.CONTAIN:
                    continue
                hash_node_id = recursive_additional_hash(edge.dest)
                hashes.append(hash_node_id)

            cur_node.hash = stable_hash_from_hashes(hashes)
            return cur_node.hash
        
        recursive_structure_hash()

        for node in self.nodes.values():
            if node.type in ADDITIONAL_NODE_TYPES:
                recursive_additional_hash(node.id)
