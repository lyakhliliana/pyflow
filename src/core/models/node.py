from dataclasses import dataclass, field
from typing import Dict

ROOT_NODE_NAME = "root"


class TypeNode(str):
    DIRECTORY = 'directory'
    FILE = 'file'

    CLASS = 'class'
    FUNC = 'func'
    BODY = 'body'

    ARC_ELEMENT = 'arc_elem'
    USE_CASE = 'use_case'


STRUCTURE_NODE_TYPES = [TypeNode.DIRECTORY, TypeNode.FILE]
CODE_NODE_TYPES = [TypeNode.CLASS, TypeNode.FUNC, TypeNode.BODY]
ADDITIONAL_NODE_TYPES = [TypeNode.ARC_ELEMENT, TypeNode.USE_CASE]


class TypeSourceNode(str):
    CODE = 'code'
    HAND = 'hand'


@dataclass
class Node:
    id: str
    name: str
    type: TypeNode
    hash: str = field(default="")
    source: TypeSourceNode = field(default=TypeSourceNode.CODE)
    meta: Dict = field(default_factory=dict)
