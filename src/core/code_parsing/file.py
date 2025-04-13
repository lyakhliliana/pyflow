import ast
from collections import defaultdict
import keyword
import logging
from pathlib import Path
from typing import Dict, Optional, Set

from src.core.models.dependency import Import, Object
from src.core.models.edge import TypeEdge
from src.core.models.node import Node, TypeNode
from src.core.models.graph import Graph

logger = logging.getLogger(__name__)


class FileParser:
    def __init__(self, file_node_name: str, file_path: Path, project_path: Path, graph: Graph):
        self.file_node_name = file_node_name
        self.file_path = file_path
        self.project_path = project_path
        self.graph = graph

        self.has_body = False
        self.imports = []
        self.usages: Dict[str, Set[str]] = defaultdict(set)

    def parse(self):
        tree = None
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except Exception as e:
            logger.error(f"Error parsing {self.file_path}: {str(e)}")
            return {}

        try:
            self._create_structure(tree)
            return self._analyze_dependencies(tree)

        except Exception as e:
            logger.error(f"Error parsing {self.file_path}: {str(e)}")
            raise e

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
                self.has_body = True

    def _process_import(self, node):
        for alias in node.names:
            self.imports.append(
                Import(
                    fullname=alias.name,
                    alias=alias.asname
                )
            )

    def _process_import_from(self, node):
        import_objects = [Object(alias.name, alias.asname) for alias in node.names]
        self.imports.append(
            Import(
                fullname=node.module,
                alias=None,
                objects=import_objects
            )
        )

    def _process_class_node(self, node):
        class_name = f"{self.file_node_name}#{node.id}"
        class_node = Node(
            id=class_name,
            type=TypeNode.CLASS
        )
        if self.graph.add_node(class_node):
            self.graph.add_edge(self.file_node_name, class_name, TypeEdge.CONTAIN)

    def _process_function_node(self, node):
        func_name = f"{self.file_node_name}#{node.id}"
        func_node = Node(
            id=func_name,
            type=TypeNode.FUNC
        )
        if self.graph.add_node(func_node):
            self.graph.add_edge(self.file_node_name, func_name, TypeEdge.CONTAIN)

    def _analyze_dependencies(self, tree) -> Dict[str, Set]:
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self._analyze_entity(node, f"{self.file_node_name}#{node.name}")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._analyze_entity(node, f"{self.file_node_name}#{node.name}")
            elif self.has_body:
                self._analyze_body(node)

        return self.usages

    def _analyze_entity(self, node: ast.AST, entity_name: str):
        self.current_entity = entity_name
        used = self._get_usage(node)
        self._process_usages(used)
        self.current_entity = None

    def _analyze_body(self, node: ast.AST):
        body_name = f"{self.file_node_name}#body"
        self.current_entity = body_name
        used = self._get_usage(node)
        self._process_usages(used)
        self.current_entity = None

    def _get_usage(self, node: ast.AST) -> Set[str]:
        if isinstance(node, ast.ClassDef):
            return self._get_class_usage(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return self._get_function_usage(node)
        return self._get_body_usage(node)

    def _get_class_usage(self, class_node: ast.ClassDef) -> Set[str]:
        used = set()

        class CallVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Attribute) and \
                        isinstance(node.func.value, ast.Name) and \
                        node.func.value.id == 'self':
                    return

                name = self._get_full_name(node.func)
                if name:
                    used.add(name)
                self.generic_visit(node)

            def _get_full_name(self, node):
                parts = []
                current = node
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                return '.'.join(reversed(parts)) if parts else None

        CallVisitor().visit(class_node)
        return used

    def _get_function_usage(self, func_node: ast.FunctionDef) -> Set[str]:
        used = set()

        class CallVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Attribute) and \
                        isinstance(node.func.value, ast.Name) and \
                        node.func.value.id == 'self':
                    return

                name = self._get_full_name(node.func)
                if name:
                    used.add(name)
                self.generic_visit(node)

            def _get_full_name(self, node):
                parts = []
                current = node
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                return '.'.join(reversed(parts)) if parts else None

        CallVisitor().visit(func_node)
        return used

    def _get_body_usage(self, node: ast.AST) -> Set[str]:
        used = set()

        class TopLevelVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                name = self._get_full_name(node.func)
                if name:
                    used.add(name)
                self.generic_visit(node)

            def _get_full_name(self, node):
                parts = []
                current = node
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                return '.'.join(reversed(parts)) if parts else None

        TopLevelVisitor().visit(node)
        return used

    def _process_usages(self, used: Set[str]):
        usage_info = self.usages[self.current_entity]

        for name in used:
            if name in __builtins__ or keyword.iskeyword(name):
                continue

            parts = list(name.split('.'))
            base_name = parts[0]

            local_candidate = f"{self.file_node_name}#{base_name}"
            if local_candidate in self.graph.nodes:
                usage_info.add(local_candidate)
                continue

            # Поиск в импортах
            for imp in self.imports:

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

    def _resolve_module_path(
        self,
        import_name: str,
        current_file_path: Optional[Path] = None
    ) -> Optional[str]:
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
