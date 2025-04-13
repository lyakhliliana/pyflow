from collections import defaultdict
import logging
from pathlib import Path
from typing import List
import os

from src.core.code_parsing.file import FileCodeParser
from src.core.models.edge import TypeEdge
from src.core.models.node import Node, TypeNode
from src.core.models.graph import Graph

logger = logging.getLogger(__name__)

ROOT_NODE_NAME = "root"


class ProjectCodeParser:
    def __init__(self, project_path: str, ignored_directories: list = ["venv", "tmp"]):
        self.project_path = Path(project_path).resolve()
        self.graph = Graph()
        self.ignored_directories = ignored_directories
        self.usages = {}

    def parse_project(self) -> Graph:
        self._build_project_structure()
        self._analyze_usages()
        return self.graph

    def save_graph(self, path):
        self.graph.save(path)

    def _build_project_structure(self):
        py_files = self._find_python_files()

        root_node = Node(id=ROOT_NODE_NAME, type=TypeNode.DIRECTORY)
        self.graph.add_node(root_node)

        for file_path in py_files:
            self._add_path_to_graph(file_path)

    def _find_python_files(self) -> List[Path]:
        py_files = []
        for root, dirs, files in os.walk(self.project_path):
            for dir in self.ignored_directories:
                if dir in dirs:
                    dirs.remove(dir)
            for file in files:
                if file.endswith('.py'):
                    py_files.append(Path(root) / file)
        return py_files

    def _add_path_to_graph(self, path: Path):
        rel_path = path.relative_to(self.project_path)
        path_parts = list(rel_path.parts)

        parent_node_name = ROOT_NODE_NAME
        current_path = Path('')

        for part in path_parts[:-1]:
            str_current_path = str(current_path / part)

            if str_current_path not in self.graph:
                dir_node = Node(
                    id=str_current_path,
                    type=TypeNode.DIRECTORY
                )

                self.graph.add_node(dir_node)
                self.graph.add_edge(parent_node_name, dir_node.id, TypeEdge.CONTAIN)

                parent_node_name = dir_node.id
            else:
                parent_node_name = str_current_path

        file_node = Node(
            id=rel_path.as_posix(),
            type=TypeNode.FILE
        )

        if self.graph.add_node(file_node):
            self.graph.add_edge(parent_node_name, file_node.id, TypeEdge.CONTAIN)

        usages = self._parse_file(path)
        for key, value in usages.items():
            if key in self.usages:
                self.usages[key].update(value)
            else:
                self.usages[key] = value.copy()

    def _parse_file(self, file_path: Path) -> defaultdict:
        rel_path = file_path.relative_to(self.project_path)
        file_node_name = str(rel_path)

        visitor = FileCodeParser(file_node_name, file_path, self.project_path, self.graph)
        return visitor.parse()

    def _analyze_usages(self):
        for source, usages in self.usages.items():
            for target in usages:
                if source in self.graph and target in self.graph:
                    self.graph.add_edge(source, target, TypeEdge.USE)
