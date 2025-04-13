from collections import deque
from copy import deepcopy
import logging
from typing import Set

from src.core.models.node import Node
from src.core.models.graph import Graph

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
        new_graph.add_node(Node(
            id=start_node_data.id,
            type=start_node_data.type,
            edges=[],
            meta=start_node_data.meta
        ))
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
                    new_graph.add_node(Node(
                        id=target_node.id,
                        type=target_node.type,
                        edges=[],
                        meta=target_node.meta
                    ))
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
            
            new_graph.add_node(Node(
                id=original_node.id,
                type=original_node.type,
                edges=[],
                meta=deepcopy(original_node.meta)
            ))

        for node_id in visited:
            original_node = graph.nodes[node_id]
            
            for edge in original_node.edges:
                if edge.id in visited:
                    new_graph.add_edge(node_id, edge.id, edge.type)
        
        return new_graph