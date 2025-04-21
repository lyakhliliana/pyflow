from __future__ import annotations
from abc import ABC, abstractmethod
import copy
import csv
import logging
import os
from typing import Dict, List, Tuple

from core.models.edge import TypeEdge, TypeSourceEdge
from core.models.node import Node
from core.models.graph import Graph

logger = logging.getLogger(__name__)

GRAPH_SECTION_NAME = "graph"
ADDITIONAL_SECTION_NAME = "additional"
NODES_FILE_NAME = "nodes.csv"
EDGES_FILE_NAME = "edges.csv"


class IGraphBuilder(ABC):

    @staticmethod
    @abstractmethod
    def build(directory_path: str) -> Graph:
        pass

    @staticmethod
    @abstractmethod
    def add_elements(cur_graph: Graph, nodes_file: str, edges_file: str) -> Graph:
        pass


class CSVGraphBuilder(IGraphBuilder):

    @staticmethod
    def build(directory_path: str) -> Graph:
        f"""
        Собирает граф зависимостей из CSV-файлов в указанной директории.

        Ожидает в целевой директории два обязательных файла:
        - {GRAPH_SECTION_NAME}/{NODES_FILE_NAME}: перечень узлов графа
        - {GRAPH_SECTION_NAME}/{EDGES_FILE_NAME}: перечень связей между узлами

        Требования к файлам:
        nodes: CSV с колонками [id, type, source]
        edge: CSV с колонками [source_id, target_id, type, source]

        Args:
            directory_path: Путь к директории графа

        Returns:
            Graph: Построенный объект графа зависимостей
        """

        graph_path = os.path.join(directory_path, GRAPH_SECTION_NAME)
        nodes_path = os.path.join(graph_path, NODES_FILE_NAME)
        edges_path = os.path.join(graph_path, EDGES_FILE_NAME)

        graph = Graph()

        try:
            CSVGraphBuilder._process_nodes(nodes_path, graph)
            CSVGraphBuilder._process_edges(edges_path, graph)
        except FileNotFoundError as e:
            logger.critical(f"Файл не найден: {str(e)}")
            raise
        except csv.Error as e:
            logger.critical(f"Ошибка CSV: {str(e)}")
            raise

        return graph

    @staticmethod
    def add_elements(cur_graph: Graph, nodes_file: str, edges_file: str) -> Graph:
        """
        Добавляет узлы и связи из CSV-файлов в существующий граф с валидацией.

        Особенности:
        - Не перезаписывает существующие узлы с одинаковыми ID

        Args:
            cur_graph: Существующий граф для обновления
            nodes_file: CSV с колонками [id, type]
            edges_file: CSV с колонками [source_id, target_id, type]

        Returns:
            Graph: Обновленный граф (новый объект)

        Raises:
            ValidationError: при критических ошибках формата файлов
        """
        answer = copy.deepcopy(cur_graph)
        try:
            CSVGraphBuilder._process_nodes(file_path=nodes_file, graph=answer, update_mode=True)

            CSVGraphBuilder._process_edges(file_path=edges_file, graph=answer)

        except FileNotFoundError as e:
            logger.critical(f"Файл не найден: {str(e)}")
            raise
        except csv.Error as e:
            logger.critical(f"Ошибка CSV: {str(e)}")
            raise ValidationError from e

        return answer

    @staticmethod
    def _process_nodes(file_path: str, graph: Graph, update_mode: bool = False) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    node = CSVGraphBuilder._parse_node_row(row)

                    if update_mode and node.id in graph:
                        logger.info(f"Строка {row_num}: Узел {node.id} уже существует - пропуск")
                        continue

                    if not graph.add_node(node):
                        logger.warning(f"Строка {row_num}: Конфликт ID узла {node.id}")

                except (KeyError, ValueError) as e:
                    logger.error(f"Строка {row_num}: Ошибка парсинга узла - {str(e)}")

    @staticmethod
    def _process_edges(file_path: str, graph: Graph) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    source_id, target_id, edge_type, source_type = CSVGraphBuilder._parse_edge_row(row)

                    if source_id in graph and target_id in graph:
                        success = graph.add_edge(source_id, target_id, edge_type, source_type)
                    else:
                        success = False

                    if not success:
                        logger.error(
                            f"Строка {row_num}: Невозможно добавить связь {source_id}->{target_id} (узлы отсутствуют)")

                except (KeyError, ValueError) as e:
                    logger.error(f"Строка {row_num}: Ошибка парсинга связи - {str(e)}")

    @staticmethod
    def _parse_node_row(row: Dict[str, str]) -> Node:
        return Node(id=row['id'].strip(), type=row['type'].strip(), source_type=row['source_type'].strip())

    @staticmethod
    def _parse_edge_row(row: Dict[str, str]) -> Tuple[str, str, TypeEdge, TypeSourceEdge]:
        return (row['source_id'].strip(), row['target_id'].strip(), row['type'].strip(), row['source_type'].strip())
