from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Object:
    fullname: str
    alias: Optional[str]


@dataclass
class Import:
    fullname: str  # название модуля, откуда происходит импорт
    alias: Optional[str]
    objects: List[Object] = field(default_factory=list)  # объекты, которые импортируются(для import from)

