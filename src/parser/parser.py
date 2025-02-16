import ast

import os
from pathlib import Path
from typing import Optional

from src.entities.common.edge import TypeEdge
from src.entities.common.graph import Graph
from src.entities.common.node import BaseNode, TypeNode

DO_NOT_VISIT = ['venv', '.git', 'tmp', 'exp']

class ProjectAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.graph = Graph()

    def analyze(self):
        self._walk_directory()
        self._analyze_project()

    def _walk_directory(self):
        for root, dirs , files in os.walk(self.project_path):
            rel_root = self._get_rel_path(root)
            for dir in DO_NOT_VISIT:
                if dir in dirs:
                    dirs.remove(dir)

            dir_node = BaseNode(name=rel_root, type=TypeNode.DIRECTORY)
            self.graph.add_node(dir_node)

            for dir in dirs:
                child_dir_path = os.path.join(rel_root, dir)
                self.graph.add_edge(dir_node, child_dir_path, TypeEdge.CONTAIN)
        
            for file in files:
                if file.endswith('.py'):
                    child_file_path = os.path.join(rel_root, file)
                    file_node = BaseNode(name=child_file_path, type=TypeNode.FILE)
                    self.graph.add_node(file_node)
                    self.graph.add_edge(dir_node, child_file_path, TypeEdge.CONTAIN)


    def _analyze_project(self):
        for node in self.graph.nodes.values():
            if node.type == TypeNode.FILE:
                self._process_file(node)


    def _process_file(self, file_node: BaseNode):
        file_path = self._get_full_path(file_node.name)
        with open(file_path, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read(), filename=file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._add_import_edge(file_node, alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                if module:
                    self._add_import_edge(file_node, module)


    def _add_import_edge(self, source_node: BaseNode, import_name: str):
        target_path = self._resolve_import_to_path(import_name)
        if target_path and target_path in self.graph.nodes:
            self.graph.add_edge(source_node, target_path, TypeEdge.USE)


    def _resolve_import_to_path(self, import_name: str) -> Optional[str]:
        module_path = import_name.replace('.', '/') + '.py'
        full_path = os.path.join(self.project_path, module_path)
        rel_path = self._get_rel_path(full_path)

        if os.path.exists(full_path):
            return rel_path

        return None
    
    def _get_rel_path(self, full_path: str) -> str:
        project_name = os.path.basename(self.project_path)
        rel_path = os.path.relpath(full_path, self.project_path)
        rel_path_with_project = os.path.join(project_name, rel_path)
        return os.path.normpath(rel_path_with_project)


    def _get_full_path(self, relative_path: str) -> str:
        base_path = Path(self.project_path)
        relative_parts = Path(relative_path).parts
        
        if relative_parts[0] == base_path.name:
            relative_parts = relative_parts[1:]

        full_path = base_path / Path(*relative_parts)
        return os.path.normpath(full_path)
