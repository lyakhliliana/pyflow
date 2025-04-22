from __future__ import annotations
from abc import ABC, abstractmethod
import csv
import logging
import os

from core.models.edge import TypeEdge, TypeSourceEdge
from core.models.node import Node, TypeSourceNode
from core.models.graph import Graph

logger = logging.getLogger(__name__)

CODE_SECTION_NAME = "code"
UNION_SECTION_NAME = "union"
ADDITIONAL_SECTION_NAME = "additional"
NODES_FILE_NAME = "nodes.csv"
EDGES_FILE_NAME = "edges.csv"


class IGraphBuilder(ABC):

    @staticmethod
    @abstractmethod
    def build(graph_path: str) -> Graph:
        pass

    @staticmethod
    @abstractmethod
    def union(directory_path: str) -> Graph:
        pass

    @staticmethod
    @abstractmethod
    def init_additional_files(directory_path: str):
        pass


class CSVGraphBuilder(IGraphBuilder):

    @staticmethod
    def build(graph_path: str) -> Graph:
        f"""
        Собирает граф зависимостей из CSV-файлов в указанной директории.

        Ожидает в целевой директории два обязательных файла: 
        - {NODES_FILE_NAME}: перечень узлов графа [id, type, source_type]
        - {EDGES_FILE_NAME}: перечень связей между узлами [source_id, target_id, type, source_type]

        Args:
            graph_path: Путь к директории графа

        Returns:
            Graph: Построенный объект графа зависимостей
        """
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
    def union(graph_path: str, additional_path: str) -> Graph:
        f"""
        Создает объединеный граф из исходного и дополнительных, написанных вручную, элементов.

        Ожидает в целевой директории два обязательных файла: 
        - {graph_path}/{NODES_FILE_NAME}: перечень узлов графа [id, type, source_type]
        - {graph_path}/{EDGES_FILE_NAME}: перечень связей между узлами [source_id, target_id, type, source_type]
        - {additional_path}/{NODES_FILE_NAME}: перечень узлов графа [id, type]
        - {additional_path}/{EDGES_FILE_NAME}: перечень связей между узлами [source_id, target_id, type]

        Args:
            graph_path: Путь к директории графа
            additional_path: Путь к директории дополнительных элементов

        Returns:
            Graph: Объект графа, который содержит элменеты из кода и ручные элементы  
        """
        graph = CSVGraphBuilder.build(graph_path)

        nodes_path = os.path.join(additional_path, NODES_FILE_NAME)
        edges_path = os.path.join(additional_path, EDGES_FILE_NAME)

        try:
            CSVGraphBuilder._process_nodes(file_path=nodes_path, graph=graph, additional=True)

            CSVGraphBuilder._process_edges(file_path=edges_path, graph=graph, additional=True)

        except FileNotFoundError as e:
            logger.critical(f"Файл не найден: {str(e)}")
            raise
        except csv.Error as e:
            logger.critical(f"Ошибка CSV: {str(e)}")
            raise

        return graph

    @staticmethod
    def init_additional_files(directory_path: str):
        additional_dir = os.path.join(directory_path, ADDITIONAL_SECTION_NAME)
        nodes_path = os.path.join(additional_dir, NODES_FILE_NAME)
        edges_path = os.path.join(additional_dir, EDGES_FILE_NAME)

        os.makedirs(additional_dir, exist_ok=True)

        if not os.path.exists(nodes_path):
            with open(nodes_path, "w", newline="", encoding="utf-8") as nodes_file:
                nodes_file.write("id,type\n")

        if not os.path.exists(edges_path):
            with open(edges_path, "w", newline="", encoding="utf-8") as edges_file:
                edges_file.write("source_id,target_id,type\n")

    @staticmethod
    def _process_nodes(file_path: str, graph: Graph, additional: bool = False) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    node = Node(id=row['id'].strip(), type=row['type'].strip(), source_type="")
                    node.source_type = TypeSourceNode.HAND if additional else row['source_type'].strip()

                    if node.id in graph:
                        logger.info(f"Строка {row_num}: Узел {node.id} уже существует - пропуск")
                        continue

                    if not graph.add_node(node):
                        logger.warning(f"Строка {row_num}: Конфликт ID узла {node.id}")

                except (KeyError, ValueError) as e:
                    logger.error(f"Строка {row_num}: Ошибка парсинга узла - {str(e)}")

    @staticmethod
    def _process_edges(file_path: str, graph: Graph, additional: bool = False) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    source_id, target_id, edge_type = row['source_id'].strip(), row['target_id'].strip(
                    ), row['type'].strip()
                    source_type = TypeSourceEdge.HAND if additional else row['source_type'].strip()

                    if source_id in graph and target_id in graph:
                        success = graph.add_edge(source_id, target_id, edge_type, source_type)
                    else:
                        success = False

                    if not success:
                        logger.error(
                            f"Строка {row_num}: Невозможно добавить связь {source_id}->{target_id} (узлы отсутствуют)")

                except (KeyError, ValueError) as e:
                    logger.error(f"Строка {row_num}: Ошибка парсинга связи - {str(e)}")
