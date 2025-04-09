from dataclasses import dataclass


class TypeEdge:
    USE = 'use'
    CONTAIN = 'contain'


@dataclass
class Edge:
    id: str
    type: str
