from dataclasses import dataclass, field
from enum import Enum
from typing import List

from src.entities.common.edge import Edge


class TypeNode(Enum):
    DIRECTORY = 'directory'
    FILE = 'file'


@dataclass
class BaseNode:
    name: str
    type: TypeNode
    links: List[Edge] = field(default_factory=list)

    def add_link(self, edge: Edge):
        self.links.append(edge)