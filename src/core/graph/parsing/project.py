from abc import ABC, abstractmethod
from ast import Set
import logging
from pathlib import Path
from typing import Dict, List
import os

from core.graph.parsing.file import FileCodeParser
from core.models.edge import TypeEdge, TypeSourceEdge
from core.models.node import Node, TypeNode, TypeSourceNode
from core.models.graph import Graph

logger = logging.getLogger(__name__)

ROOT_NODE_NAME = "root"
IGNORED_DIRS =  ["venv", "tmp"]


class IProjectCodeParser(ABC):

    @abstractmethod
    def __init__(self, project_path: str | Path, ignored_directories: List = IGNORED_DIRS):
        pass

    @abstractmethod
    def parse(self) -> Graph:
        pass


class ProjectCodeParser(IProjectCodeParser):

    __slots__ = ('project_path', 'ignored_directories', '_graph', '_usages')

    def __init__(self, project_path: str | Path, ignored_directories: List = IGNORED_DIRS):
        self.project_path = Path(project_path).resolve()
        self.ignored_directories = ignored_directories

    def parse(self) -> Graph:
        self._graph = Graph()
        self._usages = {}

        self._build_project_structure()
        self._analyze_usages()

        return self._graph

    def _build_project_structure(self):
        py_files = self._get_python_files()

        root_node = Node(id=ROOT_NODE_NAME, type=TypeNode.DIRECTORY, source_type=TypeSourceNode.CODE)
        self._graph.add_node(root_node)

        for file_path in py_files:
            self._build_file_structure(file_path)

    def _get_python_files(self) -> List[Path]:
        py_files = []
        for root, dirs, files in os.walk(self.project_path):
            for dir in self.ignored_directories:
                if dir in dirs:
                    dirs.remove(dir)
            for file in files:
                if file.endswith('.py'):
                    py_files.append(Path(root) / file)
        return py_files

    def _build_file_structure(self, path: Path):

        def _build_path_nodes_from_file(path: Path):
            rel_path = path.relative_to(self.project_path)
            path_parts = list(rel_path.parts)

            parent_node_name = ROOT_NODE_NAME
            current_path = Path('')

            for part in path_parts[:-1]:
                str_current_path = str(current_path / part)

                if str_current_path not in self._graph:
                    dir_node = Node(id=str_current_path, type=TypeNode.DIRECTORY, source_type=TypeSourceNode.CODE)
                    self._graph.add_node(dir_node)
                    self._graph.add_edge(parent_node_name, dir_node.id, TypeEdge.CONTAIN, source_type=TypeSourceEdge.CODE)

                    parent_node_name = dir_node.id
                else:
                    parent_node_name = str_current_path

            file_node = Node(id=rel_path.as_posix(), type=TypeNode.FILE, source_type=TypeSourceNode.CODE)

            if self._graph.add_node(file_node):
                self._graph.add_edge(parent_node_name, file_node.id, TypeEdge.CONTAIN, source_type=TypeSourceEdge.CODE)

        def _build_code_nodes_from_file(path: Path):
            visitor = FileCodeParser(path, self._graph, self.project_path)
            visitor.parse()
            usages: Dict[str, Set] = visitor.get_usages()

            for key, value in usages.items():
                if key in self._usages:
                    self._usages[key].update(value)
                else:
                    self._usages[key] = value.copy()

        _build_path_nodes_from_file(path)
        _build_code_nodes_from_file(path)

    def _analyze_usages(self):
        for source, usages in self._usages.items():
            for target in usages:
                if source in self._graph and target in self._graph:
                    self._graph.add_edge(source, target, TypeEdge.USE, TypeSourceEdge.CODE)
