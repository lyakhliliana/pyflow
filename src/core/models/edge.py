from dataclasses import dataclass


class TypeEdge(str):
    USE = 'use'
    CONTAIN = 'contain'


@dataclass
class Edge:
    id: str
    type: str
