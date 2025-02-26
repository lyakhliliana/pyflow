import ast

import os
from pathlib import Path
from typing import List, Optional, Union

from src.settings import SPLITTER, TMP_RES_DIR
from src.entities.file import FileNode
from src.entities.imports import Import, TypeImport
from src.entities.common.edge import TypeEdge
from src.entities.common.graph import Graph
from src.entities.common.node import BaseNode, TypeNode


class Parser:
    __slots__ = ('project_path', 'graph', 'ignored_directories')

    def __init__(self, project_path: str, ignored_directories: list = []):
        self.project_path = project_path
        self.graph = Graph()
        self.ignored_directories = ignored_directories

    def analyze(self):
        # составляет дерево объектов, файлов, директорий
        self._walk_directory()
        # анализ зависимостей и дополнение ребер в графе
        self._analyze_project()

    def get_graph(self) -> Graph:
        return self.graph

    def save_graph_to_json(self, output_file=f'{TMP_RES_DIR}/output.json'):
        return self.graph.save_to_json(output_file)

    def _walk_directory(self):
        for root_path, dirs, files in os.walk(self.project_path):
            rel_root_path = self._get_rel_path(root_path)
            for dir in self.ignored_directories:
                if dir in dirs:
                    dirs.remove(dir)

            dir_node = BaseNode(name=rel_root_path, type=TypeNode.DIRECTORY)
            self.graph.add_node(dir_node)

            for dir in dirs:
                child_dir_path = os.path.join(rel_root_path, dir)
                self.graph.add_edge(dir_node, child_dir_path, TypeEdge.CONTAIN)

            for file in files:
                if file.endswith('.py'):
                    child_file_path = os.path.join(rel_root_path, file)
                    file_node = FileNode(name=child_file_path, type=TypeNode.FILE)
                    self.graph.add_node(file_node)
                    self.graph.add_edge(dir_node, child_file_path, TypeEdge.CONTAIN)
                    self._process_file(file_node)

    def _process_file(self, file_node: FileNode):
        file_path = self._get_full_path(file_node.name)
        with open(file_path, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read(), filename=file_path)

        has_body = False
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target_path = self._resolve_import_to_path(alias.name)
                    if target_path:
                        import_obj = Import(type=TypeImport.MODULE,
                                            link_id=target_path,
                                            name=alias.name.split('.')[-1])
                        file_node.add_import(import_obj)

            elif isinstance(node, ast.ImportFrom):
                target_path = self._resolve_import_to_path(node.module)
                if target_path:
                    for node_name in node.names:
                        object_id = _get_object_name(target_path, node_name.name)
                        import_obj = Import(type=TypeImport.OBJECT,
                                            link_id=object_id,
                                            name=node_name.name)
                        file_node.add_import(import_obj)

            elif isinstance(node, ast.ClassDef):
                class_name = _get_object_name(file_node.name, node.name)
                class_node = BaseNode(name=class_name,
                                      type=TypeNode.CLASS)
                self.graph.add_node(class_node)
                self.graph.add_edge(file_node, class_name, TypeEdge.CONTAIN)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = _get_object_name(file_node.name, node.name)
                func_node = BaseNode(name=func_name,
                                     type=TypeNode.FUNC)
                self.graph.add_node(func_node)
                self.graph.add_edge(file_node, func_name, TypeEdge.CONTAIN)

            else:
                has_body = True

        if has_body:
            body_name = _get_object_name(file_node.name, TypeNode.BODY)
            body_node = BaseNode(name=body_name,
                                 type=TypeNode.BODY)
            self.graph.add_node(body_node)
            self.graph.add_edge(file_node, body_name, TypeEdge.CONTAIN)

    def _analyze_project(self):
        for node in self.graph.nodes.values():
            if node.type == TypeNode.FILE:
                self._analyze_file(node)

    def _analyze_file(self, file_node: FileNode):
        file_path = self._get_full_path(file_node.name)
        with open(file_path, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read(), filename=file_path)

        for node in tree.body:
            if isinstance(node, (ast.ImportFrom, ast.Import)):
                continue

            if isinstance(node, ast.ClassDef):
                cur_name = _get_object_name(file_node.name, node.name)
                cur_object = self.graph.nodes[cur_name]
                used = _get_class_usage(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cur_name = _get_object_name(file_node.name, node.name)
                cur_object = self.graph.nodes[cur_name]
                used = _get_function_usage(node)
            else:
                used = _get_body_usage(node)
                cur_name = _get_object_name(file_node.name, TypeNode.BODY)
                cur_object = self.graph.nodes[cur_name]

            for use in used:
                # ищем в файле
                name_to_find_in_graph = file_node.name + "#" + use.split('.')[0]
                if name_to_find_in_graph in self.graph.nodes:
                    self.graph.add_edge(
                        source=cur_object,
                        target_name=self.graph.nodes[name_to_find_in_graph].name,
                        edge_type=TypeEdge.USE)
                    continue
                # ищем в импортах файла
                name_to_find_in_imports = use.split('.')[0]
                if name_to_find_in_imports in file_node.imports:
                    cur_import = file_node.imports[name_to_find_in_imports]
                    # рассматриваем случай объектного импорта
                    if cur_import.type == TypeImport.OBJECT:
                        self.graph.add_edge(
                            source=cur_object,
                            target_name=cur_import.link_id,
                            edge_type=TypeEdge.USE)
                        continue
                    # рассматриваем случай модульного импорта
                    if cur_import.type == TypeImport.MODULE:
                        import_object = use.split('.')[1]
                        import_object_id = _get_object_name(cur_import.link_id, import_object)
                        if import_object_id in self.graph.nodes:
                            self.graph.add_edge(
                                source=cur_object,
                                target_name=import_object_id,
                                edge_type=TypeEdge.USE)
                        continue

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


def _get_object_name(file_path: str, object_name: str):
    return file_path + SPLITTER + object_name


def _get_class_usage(class_node: ast.ClassDef) -> List[str]:
    used = set()

    class CallAnalyzer(ast.NodeVisitor):
        def _get_full_name(self, node):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts)) if parts else None

        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and \
               isinstance(node.func.value, ast.Name) and \
               node.func.value.id == 'self':
                return

            full_name = self._get_full_name(node.func)
            if full_name:
                used.add(full_name)
            self.generic_visit(node)

    for item in class_node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            CallAnalyzer().visit(item)

    return sorted(used)


def _get_function_usage(func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[str]:
    used = set()

    class CallAnalyzer(ast.NodeVisitor):
        def _get_full_name(self, node):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts)) if parts else None

        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute):
                if (isinstance(node.func.value, ast.Name) and
                        node.func.value.id == 'self'):
                    return
            if isinstance(node, ast.Await):
                node = node.value

            full_name = self._get_full_name(node.func)
            if full_name:
                used.add(full_name)
            self.generic_visit(node)

    CallAnalyzer().visit(func_node)

    return sorted(used)


def _get_body_usage(tree: ast.Module) -> List[str]:
    used = set()

    class TopLevelAnalyzer(ast.NodeVisitor):
        def _get_full_name(self, node):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts)) if parts else None

        def visit_Call(self, node):
            full_name = self._get_full_name(node.func)
            if full_name:
                used.add(full_name)
            self.generic_visit(node)

        def visit_Import(self, node):
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            self.generic_visit(node)
    if not hasattr(tree, "body"):
        return []
    for node in tree.body:
        if not isinstance(
                node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            TopLevelAnalyzer().visit(node)

    return sorted(used)
