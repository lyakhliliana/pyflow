from dataclasses import dataclass, field
from typing import Dict

from src.entities.common.node import BaseNode
from src.entities.imports import Import


@dataclass
class FileNode(BaseNode):
    imports: Dict[str, Import] = field(default_factory=dict, repr=False)

    def add_import(self, import_obj: Import):
        self.imports[import_obj.name] = import_obj
