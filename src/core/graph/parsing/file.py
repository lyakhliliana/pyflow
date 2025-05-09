from abc import ABC, abstractmethod
import ast
import hashlib
import keyword
import logging
from pathlib import Path
from typing import List, Optional, Set

from core.models.dependency import Import, ImportObject
from core.models.edge import Edge, TypeEdge, TypeSourceEdge
from core.models.node import Node, TypeNode, TypeSourceNode
from core.models.graph import Graph

NAME_BODY_NODE = "body"

logger = logging.getLogger(__name__)


class IFileCodeParser(ABC):

    @abstractmethod
    def __init__(self, file_path: Path | str, project_path: Path | str):
        pass

    @abstractmethod
    def parse(self) -> Graph:
        pass


class FileCodeParser(IFileCodeParser):

    def __init__(self, file_path: Path | str, project_path: Path | str):
        self.file_path = Path(file_path).resolve()
        self.project_path = Path(project_path).resolve()
        self.rel_path_to_project_root = str(self.file_path.relative_to(self.project_path))

        self._imports: List[Import] = []
        self._graph = Graph()
        self._tree = None

    def parse(self):
        self._imports: List[Import] = []
        self._graph = Graph()

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self._tree = ast.parse(f.read())
        except Exception as e:
            error_text = f"Ошибка при отркытии файла {self.file_path}: {str(e)}"
            raise Exception(error_text)

        try:
            self._find_nodes()
            self._find_edges()

        except Exception as e:
            error_text = f"Ошибка при анализе файла {self.file_path}: {str(e)}"
            raise Exception(error_text)

        return self._graph

    def _find_nodes(self):
        body_nodes = []

        for node in self._tree.body:
            if isinstance(node, ast.Import):
                self._process_import(node)
            elif isinstance(node, ast.ImportFrom):
                self._process_import_from(node)
            elif isinstance(node, ast.ClassDef):
                self._add_class_node(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._add_function_node(node)
            else:
                body_nodes.append(node)

        self._add_body_node(body_nodes)

    def _process_import(self, node: ast.Import):
        for alias in node.names:
            self._imports.append(Import(fullname=alias.name, alias=alias.asname))

    def _process_import_from(self, node: ast.ImportFrom):
        import_objects = [ImportObject(alias.name, alias.asname) for alias in node.names]
        self._imports.append(Import(fullname=node.module, alias=None, objects=import_objects))

    def _add_class_node(self, node: ast.ClassDef):
        class_hash = self._calculate_node_hash(node)
        class_id = f"{self.rel_path_to_project_root}#{node.name}"
        class_node = Node(id=class_id, name=node.name, type=TypeNode.CLASS, hash=class_hash, source=TypeSourceNode.CODE)
        self._graph.add_node(class_node)

    def _add_function_node(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        func_hash = self._calculate_node_hash(node)
        func_id = f"{self.rel_path_to_project_root}#{node.name}"
        func_node = Node(id=func_id, name=node.name, type=TypeNode.FUNC, hash=func_hash, source=TypeSourceNode.CODE)
        self._graph.add_node(func_node)

    def _add_body_node(self, body_nodes: List[ast.AST]):
        if len(body_nodes) == 0:
            return

        body_hash = self._calculate_nodes_hash(body_nodes)
        body_id = f"{self.rel_path_to_project_root}#{NAME_BODY_NODE}"
        body_node = Node(id=body_id,
                         name=NAME_BODY_NODE,
                         type=TypeNode.BODY,
                         hash=body_hash,
                         source=TypeSourceNode.CODE)
        self._graph.add_node(body_node)

    def _calculate_node_hash(self, node: ast.AST) -> str:
        dumped = ast.dump(node, annotate_fields=True, include_attributes=False)
        data = dumped.encode('utf-8')
        return hashlib.sha256(data).hexdigest()[0:8]

    def _calculate_nodes_hash(self, nodes: List[ast.AST]) -> str:
        hasher = hashlib.sha256()
        for node in nodes:
            dumped = ast.dump(node, annotate_fields=True, include_attributes=False)
            segment = (dumped + '\n').encode('utf-8')
            hasher.update(segment)
        return hasher.hexdigest()[0:8]

    def _find_edges(self):

        for ast_node in self._tree.body:
            current_entity: str
            used: Set[str]

            if isinstance(ast_node, (ast.Import, ast.ImportFrom)):
                continue

            elif isinstance(ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                current_entity = f"{self.rel_path_to_project_root}#{ast_node.name}"
                used = UsagesCollector.get_function_usages(ast_node)

            elif isinstance(ast_node, (ast.ClassDef)):
                current_entity = f"{self.rel_path_to_project_root}#{ast_node.name}"
                used = UsagesCollector.get_class_usages(ast_node)

            else:
                current_entity = f"{self.rel_path_to_project_root}#{NAME_BODY_NODE}"
                used = UsagesCollector.get_body_usages(ast_node)

            self._form_edges(used, current_entity)

    def _form_edges(self, used: Set[str], current_entity: str):

        for name in used:
            if name in __builtins__ or keyword.iskeyword(name):
                continue

            parts = list(name.split('.'))
            base_name = parts[0]

            local_candidate = f"{self.rel_path_to_project_root}#{base_name}"
            if local_candidate in self._graph.get_all_nodes():
                use_edge = Edge(src=current_entity, dest=local_candidate, type=TypeEdge.USE, source=TypeSourceEdge.CODE)
                added = self._graph.add_edge(use_edge)
                if not added:
                    logger.warning(f"failed add edge from {current_entity} to {local_candidate}")
                continue

            # Поиск в импортах
            for imp in self._imports:

                target = ""
                # Обработка обычного импорта: import module [as alias]
                if not imp.objects:
                    imported_name = imp.alias or imp.fullname.split('.')[-1]
                    if imported_name == base_name:
                        target_path = self._resolve_module_path(imp.fullname, self.file_path)
                        if len(parts) > 1 and target_path:
                            target = f"{target_path}#{parts[1]}"

                # Обработка from-импорта: from module import obj [as alias]
                else:
                    for obj in imp.objects:
                        obj_name = obj.alias or obj.fullname
                        if obj_name == base_name:
                            target_path = self._resolve_module_path(imp.fullname, self.file_path)
                            if target_path:
                                target = f"{target_path}#{obj.fullname}"
                            break

                if target:
                    use_edge = Edge(src=current_entity, dest=target, type=TypeEdge.USE, source=TypeSourceEdge.CODE)
                    added = self._graph.add_edge(use_edge, with_check=False)
                    if not added:
                        logger.warning(f"failed add edge from {current_entity} to {target}")
                    break

    def _resolve_module_path(self, import_name: str, current_file_path: Optional[Path] = None) -> Optional[str]:
        try:
            if not import_name:
                return None

            parts = import_name.split('.')
            normalized_path = Path(*parts)

            if import_name.startswith('.'):
                if not current_file_path:
                    logger.warning("Relative import without file context")
                    return None

                level = 0
                while parts[level] == '':
                    level += 1
                parts = parts[level:]

                try:
                    base_dir = current_file_path.parent.resolve().parents[level - 1]
                except IndexError:
                    logger.warning("Relative import beyond project root")
                    return None

                full_path = base_dir.joinpath(*parts)
            else:
                full_path = Path(self.project_path).joinpath(normalized_path)

            candidate = full_path.with_suffix('.py')

            try:
                if candidate.exists():
                    rel_path = candidate.relative_to(self.project_path)
                    return rel_path
            except ValueError:
                logger.debug(f"Module not found: {import_name}")
            return None

        except Exception as e:
            logger.error(f"Error resolving {import_name}: {str(e)}")
            return None


class UsageVisitor(ast.NodeVisitor):

    def __init__(self, ignore_self: bool = False):
        self.used: Set[str] = set()
        self.ignore_self = ignore_self

    def _get_full_name(self, node: ast.AST) -> Optional[str]:
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return '.'.join(reversed(parts)) if parts else None

    def visit_Call(self, node: ast.Call) -> None:
        if self.ignore_self:
            if isinstance(node.func, ast.Attribute):
                value = node.func.value
                if isinstance(value, ast.Name) and value.id == 'self':
                    return

        if name := self._get_full_name(node.func):
            self.used.add(name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if self.ignore_self and node.id == 'self':
            return
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if self.ignore_self:
            value = node.value
            if isinstance(value, ast.Name) and value.id == 'self':
                return
        if isinstance(node.ctx, ast.Load) and (name := self._get_full_name(node)):
            self.used.add(name)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.annotation:
            self.visit(node.annotation)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.returns:
            self.visit(node.returns)
        for arg in node.args.args + node.args.kwonlyargs:
            if arg.annotation:
                self.visit(arg.annotation)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for base in node.bases:
            self.visit(base)
        self.generic_visit(node)


class UsagesCollector:

    @staticmethod
    def get_class_usages(class_node: ast.ClassDef) -> Set[str]:
        visitor = UsageVisitor(ignore_self=True)
        visitor.visit(class_node)
        return visitor.used

    @staticmethod
    def get_function_usages(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> Set[str]:
        visitor = UsageVisitor(ignore_self=True)
        visitor.visit(func_node)
        return visitor.used

    @staticmethod
    def get_body_usages(node: ast.AST) -> Set[str]:
        visitor = UsageVisitor(ignore_self=False)
        visitor.visit(node)
        return visitor.used
