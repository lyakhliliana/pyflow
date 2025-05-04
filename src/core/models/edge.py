from dataclasses import dataclass, field


class TypeEdge(str):
    USE = 'use'
    CONTAIN = 'contain'
    COUPLING = "coupling"


class TypeSourceEdge(str):
    CODE = 'code'
    HAND = 'hand'


@dataclass
class Edge:
    src: str
    dest: str
    type: TypeEdge
    source: TypeSourceEdge = field(default=TypeSourceEdge.CODE)
