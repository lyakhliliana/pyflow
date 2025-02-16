from dataclasses import dataclass
from enum import Enum


class TypeEdge(Enum):
    USE = "use"
    CONTAIN = 'contain'


@dataclass
class Edge:
    id: str
    type: TypeEdge
