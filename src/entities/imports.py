from dataclasses import dataclass


class TypeImport:
    MODULE = 'module'
    OBJECT = 'object'


@dataclass
class Import:
    type: str
    link_id: str
    name: str
