from collections import deque
from copy import deepcopy
import logging
from typing import Set

from core.models.edge import TypeEdge
from core.models.node import Node
from core.models.graph import Graph

logger = logging.getLogger(__name__)


class GraphExtensions:

    @staticmethod
    def get_used_nodes(graph: Graph, start_node: str) -> Graph:
        """
        Строит подграф из всех узлов, достижимых из start_node через исходящие ребра.

        Args:
            graph: Исходный граф
            start_node: ID стартового узла

        Returns:
            Graph: Новый граф с достижимыми узлами и ребрами
        """

        new_graph = Graph()

        if start_node not in graph.nodes:
            logger.warning(f"Стартовый узел {start_node} не найден")
            return new_graph

        visited: Set[str] = set()
        queue = deque([start_node])

        start_node_data = graph.nodes[start_node]
        new_graph.add_node(Node(id=start_node_data.id, type=start_node_data.type, edges=[], meta=start_node_data.meta))
        visited.add(start_node)

        while queue:
            current_id = queue.popleft()
            current_node = graph.nodes[current_id]

            for edge in current_node.edges:
                target_id = edge.id

                if target_id not in graph.nodes:
                    logger.warning(f"Ребро {current_id}->{target_id} ведет к несуществующему узлу")
                    continue

                if target_id not in visited:
                    target_node = graph.nodes[target_id]
                    new_graph.add_node(Node(id=target_node.id, type=target_node.type, edges=[], meta=target_node.meta))
                    visited.add(target_id)
                    queue.append(target_id)

                new_graph.add_edge(current_id, target_id, edge.type)

        return new_graph

    @staticmethod
    def get_dependent_nodes(graph: Graph, start_node: str) -> Graph:
        """
        Возвращает подграф всех узлов, зависящих от start_node (включая его самого).

        Алгоритм:
        1. Найти все узлы, которые прямо или косвенно ссылаются на start_node через inv_edges.
        2. Скопировать эти узлы и связи между ними в новый граф.

        Args:
            graph: Исходный граф
            start_node: ID узла, для которого анализируются зависимости

        Returns:
            Graph: Подграф зависимых узлов
        """
        new_graph = Graph()

        if start_node not in graph.nodes:
            logger.warning(f"Узел {start_node} не найден")
            return new_graph

        visited: Set[str] = set()
        queue = deque([start_node])
        visited.add(start_node)

        while queue:
            current_id = queue.popleft()

            for source_id in graph.inv_edges.get(current_id, set()):
                if source_id not in visited:
                    visited.add(source_id)
                    queue.append(source_id)

        for node_id in visited:
            original_node = graph.nodes[node_id]

            new_graph.add_node(
                Node(id=original_node.id, type=original_node.type, edges=[], meta=deepcopy(original_node.meta)))

        for node_id in visited:
            original_node = graph.nodes[node_id]

            for edge in original_node.edges:
                if edge.id in visited:
                    new_graph.add_edge(node_id, edge.id, edge.type)

        return new_graph

    # @staticmethod
    # def get_elements(graph: Graph) -> Graph:
    #     """
    #     Создает граф лейблов, где:
    #     - Узлы: лейблы из исходного графа
    #     - Ребра: USE-связи между лейблами
    #     - Элементы: все узлы, помеченные лейблом или содержащиеся через CONTAIN

    #     Returns:
    #         Graph: Новый граф с лейблами как узлами
    #     """
    #     new_graph = Graph()
    #     label_map: Dict[str, Set[str]] = defaultdict(set)

    #     for node in graph.nodes.values():
    #         for label in node.meta.labels:
    #             contained = GraphExtensions._get_contained_elements(graph, node.id)
    #             label_map[label].update(contained)

    #     for label, elements in label_map.items():
    #         new_node = Node(id=label, type="Label"))
    #         new_graph.add_node(new_node)

    #     edges_added: Set[Tuple[str, str]] = set()
    #     for node in graph.nodes.values():
    #         for edge in node.edges:
    #             if edge.type == TypeEdge.USE and edge.id in graph.nodes:
    #                 target_node = graph.nodes[edge.id]
    #                 source_labels = set(node.meta.labels)
    #                 target_labels = set(target_node.meta.labels)

    #                 for src_label in source_labels:
    #                     for tgt_label in target_labels:
    #                         if src_label != tgt_label and (src_label, tgt_label) not in edges_added:
    #                             new_graph.add_edge(src_label, tgt_label, TypeEdge.USE)
    #                             edges_added.add((src_label, tgt_label))
    #     return new_graph

    @staticmethod
    def _get_contained_elements(graph: Graph, start_id: str) -> Set[str]:
        visited = set()
        queue = deque([start_id])

        while queue:
            current_id = queue.popleft()
            if current_id in visited:
                continue
            visited.add(current_id)

            for edge in graph.nodes[current_id].edges:
                if edge.type == TypeEdge.CONTAIN and edge.id in graph.nodes:
                    queue.append(edge.id)

        return visited
