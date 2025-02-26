from dataclasses import dataclass, field
from typing import List

from src.entities.common.edge import Edge


class TypeNode:
    DIRECTORY = 'directory'
    FILE = 'file'

    CLASS = 'class'
    FUNC = 'func'
    BODY = 'body'


@dataclass
class BaseNode:
    name: str
    type: str
    links: List[Edge] = field(default_factory=list)

    def add_link(self, edge: Edge):
        self.links.append(edge)
