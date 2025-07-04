from dataclasses import dataclass, field
from typing import Dict

from core.models.common import TypeSource

ROOT_NODE_NAME = "root"


class TypeNode(str):
    DIRECTORY = 'directory'
    FILE = 'file'

    CLASS = 'class'
    FUNC = 'func'
    BODY = 'body'

    ARC_ELEMENT = 'arc_elem'
    USE_CASE = 'use_case'


TYPE_NODES = [
    TypeNode.DIRECTORY,
    TypeNode.FILE,
    TypeNode.CLASS,
    TypeNode.FUNC,
    TypeNode.BODY,
    TypeNode.ARC_ELEMENT,
    TypeNode.USE_CASE,
]

STRUCTURE_NODE_TYPES = [
    TypeNode.DIRECTORY,
    TypeNode.FILE,
]

CODE_NODE_TYPES = [TypeNode.CLASS, TypeNode.FUNC, TypeNode.BODY]

ADDITIONAL_NODE_TYPES = [TypeNode.ARC_ELEMENT, TypeNode.USE_CASE]


@dataclass
class Node:
    id: str
    name: str
    type: TypeNode
    hash: str = field(default="")
    source: TypeSource = field(default=TypeSource.CODE)
    meta: Dict = field(default_factory=dict)
