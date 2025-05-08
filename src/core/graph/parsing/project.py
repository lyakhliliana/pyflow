from abc import ABC, abstractmethod
import hashlib
import logging
from pathlib import Path
from typing import List, Set
import os

from src.core.graph.parsing.file import FileCodeParser
from core.models.edge import Edge, TypeEdge, TypeSourceEdge
from core.models.node import ROOT_NODE_NAME, Node, TypeNode, TypeSourceNode
from core.models.graph import Graph
from src.core.utils.hash import stable_hash_from_hashes

logger = logging.getLogger(__name__)

IGNORED_DIRS = ["venv", "tmp"]


class IProjectParser(ABC):

    @abstractmethod
    def __init__(self, project_path: str | Path, ignored_directories: List = IGNORED_DIRS):
        pass

    @abstractmethod
    def parse(self) -> Graph:
        pass


class ProjectParser(IProjectParser):
    __slots__ = ('project_path', 'ignored_directories', '_graph', '_possible_edges')

    def __init__(self, project_path: str | Path, ignored_directories: List = IGNORED_DIRS):
        self.project_path = Path(project_path).resolve()
        self.ignored_directories = ignored_directories

        self._graph = Graph()
        self._possible_edges: List[Edge] = []

    def parse(self) -> Graph:
        self._graph = Graph()
        self._possible_edges = []

        self._build_project_structure()
        self._analyze_edges()
        self._graph.calculate_all_hashes()

        return self._graph

    def _build_project_structure(self):
        py_files = self._get_python_files()

        root_node = Node(id=ROOT_NODE_NAME,
                         name=ROOT_NODE_NAME,
                         type=TypeNode.DIRECTORY,
                         hash="",
                         source=TypeSourceNode.CODE)
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
                current_path = current_path / part
                str_current_path = str(current_path)

                if str_current_path not in self._graph:
                    dir_node = Node(id=str_current_path,
                                    name=part,
                                    type=TypeNode.DIRECTORY,
                                    hash="",
                                    source=TypeSourceNode.CODE)
                    self._graph.add_node(dir_node)

                    dir_edge = Edge(src=parent_node_name,
                                    dest=dir_node.id,
                                    type=TypeEdge.CONTAIN,
                                    source=TypeSourceEdge.CODE)

                    self._graph.add_edge(dir_edge)

                    parent_node_name = dir_node.id
                else:
                    parent_node_name = str_current_path

            file_node = Node(id=rel_path.as_posix(),
                             name=path_parts[-1],
                             type=TypeNode.FILE,
                             hash="",
                             source=TypeSourceNode.CODE)

            if self._graph.add_node(file_node):
                file_edge = Edge(src=parent_node_name,
                                 dest=file_node.id,
                                 type=TypeEdge.CONTAIN,
                                 source=TypeSourceEdge.CODE)
                self._graph.add_edge(file_edge)

        def _build_code_nodes_from_file(path: Path):
            file_node_id = path.relative_to(self.project_path).as_posix()
            parser = FileCodeParser(path, self.project_path)
            file_graph = parser.parse()

            for node in file_graph.nodes.values():
                if self._graph.add_node(node):
                    edge = Edge(
                        src=file_node_id,
                        dest=node.id,
                        type=TypeEdge.CONTAIN,
                        source=TypeSourceEdge.CODE,
                    )
                    self._graph.add_edge(edge)

            for edges in file_graph.edges.values():
                for edge in edges:
                    self._possible_edges.append(edge)

        _build_path_nodes_from_file(path)
        _build_code_nodes_from_file(path)

    def _analyze_edges(self):
        for edge in self._possible_edges:
            if edge.src in self._graph and edge.dest in self._graph:
                self._graph.add_edge(edge)
