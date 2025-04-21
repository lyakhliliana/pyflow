from dataclasses import dataclass


class TypeEdge(str):
    USE = 'use'
    CONTAIN = 'contain'

class TypeSourceEdge(str):
    CODE = 'code'
    HAND = 'hand'

@dataclass
class Edge:
    id: str
    type: TypeEdge
    source_type: TypeSourceEdge
