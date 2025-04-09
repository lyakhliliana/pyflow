from collections import defaultdict
from dataclasses import asdict
import json
from typing import Dict, List

from src.core.models.edge import Edge, TypeEdge
from src.core.models.node import Node


class Graph:
    __slots__ = ('nodes')

    def __init__(self):
        self.nodes: Dict[str, Node] = {}

    def __contains__(self, name: str) -> bool:
        return name in self.nodes

    def add_node(self, node: Node) -> bool:
        if node.name in self.nodes:
            return False
        self.nodes[node.name] = node
        return True

    def add_edge(self, source_name: str, dest_name: str, edge_type: TypeEdge):
        edge = Edge(id=dest_name, type=edge_type)
        self.nodes[source_name].edges.append(edge)

    def save(self, path: str) -> None:
        data = {node_id: asdict(node) for node_id, node in self.nodes.items()}
    
        # Сохранение в файл
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


