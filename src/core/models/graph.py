from collections import defaultdict
from dataclasses import asdict
import json
import logging
from typing import Dict, Set

from src.core.models.edge import Edge, TypeEdge
from src.core.models.node import Node

logger = logging.getLogger(__name__)


class Graph:
    __slots__ = ('nodes', 'inv_edges')

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.inv_edges: Dict[str, Set[str]] = defaultdict(set)

    def __contains__(self, id: str) -> bool:
        return id in self.nodes

    def add_node(self, node: Node) -> bool:
        if node.id in self.nodes:
            return False
        
        for edge in node.edges:
            self.inv_edges[edge.id].add(node.id)

        return True

    def add_edge(self, source_id: str, target_id: str, edge_type: TypeEdge) -> bool:
        if source_id not in self.nodes:
            logger.error(
                f"Не удалось добавить ребро {source_id}->{target_id}: исходный узел '{source_id}' не существует")
            return False

        if target_id not in self.nodes:
            logger.error(
                f"Не удалось добавить ребро {source_id}->{target_id}: целевой узел '{target_id}' не существует")
            return False

        edge = Edge(id=target_id, type=edge_type)
        self.nodes[source_id].edges.append(edge)
        self.inv_edges[target_id].add(source_id)

        return True

    def save(self, path: str) -> None:
        data = {node_id: asdict(node) for node_id, node in self.nodes.items()}

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
