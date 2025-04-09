from dataclasses import dataclass, field
from typing import List

from src.core.models.edge import Edge


class TypeNode:
    DIRECTORY = 'directory'
    FILE = 'file'

    CLASS = 'class'
    FUNC = 'func'
    BODY = 'body'


@dataclass
class MetaInfo:
    labels: List[str] = field(default_factory=list)


@dataclass
class Node:
    name: str
    type: str
    edges: List[Edge] = field(default_factory=list)
    meta: MetaInfo = field(default_factory=MetaInfo)


@dataclass
class FileMetaInfo(MetaInfo):
    imports: List[str] = field(default_factory=list)
