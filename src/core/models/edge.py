from dataclasses import dataclass, field
from typing import Dict


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
    meta: Dict = field(default_factory=dict)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Edge):
            return NotImplemented
        self_tuple = (self.src, self.dest, self.type, self.source)
        other_tuple = (other.src, other.dest, other.type, other.source)
        return self_tuple == other_tuple

    def __hash__(self) -> int:
        return hash((self.src, self.dest, self.type, self.source))
