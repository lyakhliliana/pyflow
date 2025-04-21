from abc import ABC, abstractmethod
import ast
from collections import defaultdict
import keyword
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

from core.models.dependency import Import, Object
from core.models.edge import TypeEdge, TypeSourceEdge
from core.models.node import Node, TypeNode, TypeSourceNode
from core.models.graph import Graph

logger = logging.getLogger(__name__)


class IFileCodeParser(ABC):

    @abstractmethod
    def __init__(self, file_path: Path, graph: Graph, project_path: Path):
        pass

    @abstractmethod
    def parse(self):
        pass


class FileCodeParser(IFileCodeParser):

    def __init__(self, file_path: Path, graph: Graph, project_path: Path):
        self.file_path: Path = file_path
        self.project_path: Path = project_path
        self.parent_node_id: str = str(file_path.relative_to(project_path))
        self.graph: Graph = graph

        self._has_body = False
        self._imports: List[Import] = []
        self._usages: Dict[str, Set[str]] = defaultdict(set)

    def parse(self):
        tree = None
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except Exception as e:
            logger.error(f"Error parsing {self.file_path}: {str(e)}")
            raise e

        try:
            self._create_structure(tree)
            self._form_usages(tree)

        except Exception as e:
            logger.error(f"Error parsing {self.file_path}: {str(e)}")
            raise e

    def get_usages(self) -> Dict[str, Set]:
        return self._usages

    def _create_structure(self, tree):
        for node in tree.body:
            if isinstance(node, ast.Import):
                self._process_import(node)
            elif isinstance(node, ast.ImportFrom):
                self._process_import_from(node)
            elif isinstance(node, ast.ClassDef):
                self._process_class_node(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._process_function_node(node)
            else:
                self._has_body = True

    def _process_import(self, node):
        for alias in node.names:
            self._imports.append(Import(fullname=alias.name, alias=alias.asname))

    def _process_import_from(self, node):
        import_objects = [Object(alias.name, alias.asname) for alias in node.names]
        self._imports.append(Import(fullname=node.module, alias=None, objects=import_objects))

    def _process_class_node(self, node):
        class_node_id = f"{self.parent_node_id}#{node.name}"
        class_node = Node(id=class_node_id, type=TypeNode.CLASS, source_type=TypeSourceNode.CODE)
        if self.graph.add_node(class_node):
            self.graph.add_edge(self.parent_node_id, class_node_id, TypeEdge.CONTAIN, source_type=TypeSourceEdge.CODE)

    def _process_function_node(self, node):
        func_node_id = f"{self.parent_node_id}#{node.name}"
        func_node = Node(id=func_node_id, type=TypeNode.FUNC, source_type=TypeSourceNode.CODE)
        if self.graph.add_node(func_node):
            self.graph.add_edge(self.parent_node_id, func_node_id, TypeEdge.CONTAIN, source_type=TypeSourceEdge.CODE)

    def _form_usages(self, tree):
        for ast_node in tree.body:
            current_entity: str
            used: Set[str]

            if isinstance(ast_node, (ast.Import, ast.ImportFrom)):
                continue

            elif isinstance(ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                current_entity = f"{self.parent_node_id}#{ast_node.name}"
                used = UsagesCollector.get_function_usages(ast_node)

            elif isinstance(ast_node, (ast.ClassDef)):
                current_entity = f"{self.parent_node_id}#{ast_node.name}"
                used = UsagesCollector.get_class_usages(ast_node)

            elif self._has_body:
                current_entity = f"{self.parent_node_id}#body"
                used = UsagesCollector.get_body_usages(ast_node)

            else:
                continue

            self._process_usages(used, current_entity)

    def _process_usages(self, used: Set[str], current_entity: str):
        usage_info = self._usages[current_entity]

        for name in used:
            if name in __builtins__ or keyword.iskeyword(name):
                continue

            parts = list(name.split('.'))
            base_name = parts[0]

            local_candidate = f"{self.parent_node_id}#{base_name}"
            if local_candidate in self.graph.nodes:
                usage_info.add(local_candidate)
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
                    usage_info.add(target)
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
