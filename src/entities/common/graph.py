from dataclasses import asdict
from enum import Enum
import json
from typing import Dict, List

from src.entities.common.edge import Edge, TypeEdge
from src.entities.common.node import BaseNode
from src.settings import TMP_RES_DIR


class Graph:
    __slots__ = ('nodes')

    def __init__(self):
        self.nodes: Dict[str, BaseNode] = {}

    def add_node(self, node: BaseNode) -> bool:
        if node.name in self.nodes:
            return False
        self.nodes[node.name] = node
        return True

    def update_node(self, node: BaseNode):
        self.nodes[node.name] = node

    def add_nodes(self, nodes: List[BaseNode]):
        for node in nodes:
            self.add_node(node)

    def add_edge(self, source: BaseNode, target_name: str, edge_type: TypeEdge):
        edge = Edge(id=target_name, type=edge_type)
        source.add_link(edge)

    def save_to_json(self, output_file=f'{TMP_RES_DIR}/output.json'):
        def serialize(obj):
            if isinstance(obj, Enum):
                return obj.value
            elif hasattr(obj, "__dict__"):
                return asdict(obj)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.nodes, f, default=serialize, indent=4, ensure_ascii=False)