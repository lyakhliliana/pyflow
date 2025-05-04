from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ImportObject:
    fullname: str
    alias: Optional[str]


@dataclass
class Import:
    fullname: str
    alias: Optional[str]
    objects: List[ImportObject] = field(default_factory=list)
