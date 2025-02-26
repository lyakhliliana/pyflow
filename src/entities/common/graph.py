from dataclasses import asdict, fields
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

    def __contains__(self, name: str) -> bool:
        return name in self.nodes

    def __getitem__(self, name: str):
        if name in self.nodes:
            return self.nodes[name]
        return None

    def __setitem__(self, name: str, node: BaseNode):
        self.nodes[name] = node

    def get_node(self, name: str) -> BaseNode:
        if name in self.nodes:
            return self.nodes[name]
        return None

    def add_node(self, node: BaseNode) -> bool:
        if node.name in self.nodes:
            return False
        self.nodes[node.name] = node
        return True

    def update_node(self, node: BaseNode):
        self.nodes[node.name] = node

    def update_nodes(self, nodes: List[BaseNode]):
        for node in nodes:
            self.update_node(node)

    def add_edge(self, source: BaseNode, target_name: str, edge_type: TypeEdge):
        edge = Edge(id=target_name, type=edge_type)
        source.add_link(edge)

    def save_to_json(self, output_file=f'{TMP_RES_DIR}/output.json'):
        def serialize(obj):
            if isinstance(obj, BaseNode):
                base_fields = {field.name for field in fields(BaseNode)}
                return {key: getattr(obj, key) for key in base_fields}
            if isinstance(obj, Enum):
                return obj.value
            elif hasattr(obj, "__dict__"):
                return asdict(obj)

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(self.nodes, file, default=serialize, indent=4, ensure_ascii=False)
