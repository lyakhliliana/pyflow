from dataclasses import dataclass, field
from typing import List

from core.models.edge import Edge


class TypeNode:
    DIRECTORY = 'directory'
    FILE = 'file'

    CLASS = 'class'
    FUNC = 'func'
    BODY = 'body'

    ARC_ELEMENT = 'arc_elem'


class TypeSourceNode(str):
    CODE = 'code'
    HAND = 'hand'


@dataclass
class Node:
    id: str
    type: TypeNode
    source_type: TypeSourceNode
    edges: List[Edge] = field(default_factory=list)
