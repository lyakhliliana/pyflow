from __future__ import annotations
from abc import ABC, abstractmethod
import csv
import logging
import os

from core.models.edge import Edge, TypeEdge, TypeSourceEdge
from core.models.node import Node, TypeSourceNode
from core.models.graph import Graph
from src.core.graph.difference import DIFFERENCE_STATUS_FIELD

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
    def build_diff(graph_path: str) -> Graph:
        pass

    @staticmethod
    @abstractmethod
    def init_additional_files(directory_path: str):
        pass


class CSVGraphBuilder(IGraphBuilder):

    @staticmethod
    def build(graph_path: str) -> Graph:
        f"""
        Builds a graph from CSV files in the specified directory.

        Expects the following two required files in the target directory:
        - {NODES_FILE_NAME}: List of graph nodes [id, name, type, hash, source]
        - {EDGES_FILE_NAME}: List of edges [src, dest, type, source]

        Args:
            graph_path: Path to the graph directory

        Returns:
            Graph: Constructed dependency graph object
        """
        nodes_path = os.path.join(graph_path, NODES_FILE_NAME)
        edges_path = os.path.join(graph_path, EDGES_FILE_NAME)

        graph = Graph()

        try:
            CSVGraphBuilder._process_nodes(nodes_path, graph)
            CSVGraphBuilder._process_edges(edges_path, graph)
        except FileNotFoundError as e:
            text_error = f"Файл не найден: {str(e)}"
            logger.critical(text_error)
            raise Exception(text_error)
        except csv.Error as e:
            text_error = f"Ошибка CSV: {str(e)}"
            logger.critical(text_error)
            raise Exception(text_error)

        return graph

    @staticmethod
    def union(graph_path: str, additional_path: str) -> Graph:
        f"""
        Creates a merged graph from the original and additional manually written elements.

        Expects the following required files in the target directories:
        - {graph_path}/{NODES_FILE_NAME}: List of graph nodes [id, name, type, hash, source]
        - {graph_path}/{EDGES_FILE_NAME}: List of edges between nodes [src, dest, type, source]
        - {additional_path}/{NODES_FILE_NAME}: List of graph nodes [id, name, type]
        - {additional_path}/{EDGES_FILE_NAME}: List of edges between nodes [src, dest, type]

        Args:
            graph_path: Path to the main graph directory
            additional_path: Path to the directory with additional elements

        Returns:
            Graph: Graph object containing both code elements and manually added elements
        """
        graph = CSVGraphBuilder.build(graph_path)

        nodes_path = os.path.join(additional_path, NODES_FILE_NAME)
        edges_path = os.path.join(additional_path, EDGES_FILE_NAME)

        try:
            CSVGraphBuilder._process_additional_nodes(nodes_path, graph)
            CSVGraphBuilder._process_additional_edges(file_path=edges_path, graph=graph)
            graph.calculate_all_hashes()

        except FileNotFoundError as e:
            logger.critical(f"Файл не найден: {str(e)}")
            raise
        except csv.Error as e:
            logger.critical(f"Ошибка CSV: {str(e)}")
            raise

        return graph

    @staticmethod
    def build_diff(graph_path: str) -> Graph:
        f"""
        Builds a difference graph between two project versions from CSV files in the specified directory.

        Expects the following two required files in the target directory:
        - {NODES_FILE_NAME}: List of graph nodes [id, name, type, diff_status, source]
        - {EDGES_FILE_NAME}: List of edges between nodes [src, dest, type, diff_status, source]

        Args:
            graph_path: Path to the graph directory

        Returns:
            Graph: Constructed dependency graph object
        """
        nodes_path = os.path.join(graph_path, NODES_FILE_NAME)
        edges_path = os.path.join(graph_path, EDGES_FILE_NAME)

        graph = Graph()

        try:
            CSVGraphBuilder._process_diff_nodes(nodes_path, graph)
            CSVGraphBuilder._process_diff_edges(edges_path, graph)
        except FileNotFoundError as e:
            text_error = f"Файл не найден: {str(e)}"
            logger.critical(text_error)
            raise Exception(text_error)
        except csv.Error as e:
            text_error = f"Ошибка CSV: {str(e)}"
            logger.critical(text_error)
            raise Exception(text_error)

        return graph

    @staticmethod
    def init_additional_files(directory_path: str):
        f"""
        Initializes the directory structure and empty CSV files for storing additional graph elements.

        Creates the following structure in the specified directory:
        - {directory_path}/{ADDITIONAL_SECTION_NAME}/ (directory)
        - {NODES_FILE_NAME}: (CSV file with 'id,name,type' header)
        - {EDGES_FILE_NAME}: (CSV file with 'src,dest,type' header)

        If the files already exist, they will not be overwritten. The directory will be created
        if it doesn't exist (including all necessary parent directories).

        Args:
            directory_path: Path to the base directory where additional files should be created.
                        The actual files will be created in a subdirectory named {ADDITIONAL_SECTION_NAME}.

        Returns:
            None
        """
        additional_dir = os.path.join(directory_path, ADDITIONAL_SECTION_NAME)
        nodes_path = os.path.join(additional_dir, NODES_FILE_NAME)
        edges_path = os.path.join(additional_dir, EDGES_FILE_NAME)

        os.makedirs(additional_dir, exist_ok=True)

        if not os.path.exists(nodes_path):
            with open(nodes_path, "w", newline="", encoding="utf-8") as nodes_file:
                nodes_file.write("id,name,type\n")

        if not os.path.exists(edges_path):
            with open(edges_path, "w", newline="", encoding="utf-8") as edges_file:
                edges_file.write("src,dest,type\n")

    @staticmethod
    def _process_nodes(file_path: str, graph: Graph) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    node = Node(id=row['id'].strip(),
                                name=row['name'].strip(),
                                type=row['type'].strip(),
                                hash=row['hash'].strip(),
                                source=row['source'].strip())

                    if node.id in graph:
                        logger.info(f"Строка {row_num}: Узел {node.id} уже существует - пропуск")
                        continue

                    if not graph.add_node(node):
                        logger.warning(f"Строка {row_num}: Конфликт ID узла {node.id}")

                except (KeyError, ValueError) as e:
                    logger.error(f"Строка {row_num}: Ошибка парсинга узла - {str(e)}")

    @staticmethod
    def _process_additional_nodes(file_path: str, graph: Graph) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    node = Node(id=row['id'].strip(),
                                name=row['name'].strip(),
                                type=row['type'].strip(),
                                hash="",
                                source=TypeSourceNode.HAND)

                    if node.id in graph:
                        logger.info(f"Строка {row_num}: Узел {node.id} уже существует - пропуск")
                        continue

                    if not graph.add_node(node):
                        logger.warning(f"Строка {row_num}: Конфликт ID узла {node.id}")

                except (KeyError, ValueError) as e:
                    logger.error(f"Строка {row_num}: Ошибка парсинга узла - {str(e)}")

    @staticmethod
    def _process_diff_nodes(file_path: str, graph: Graph) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    node = Node(id=row['id'].strip(),
                                name=row['name'].strip(),
                                type=row['type'].strip(),
                                source=row['source'].strip())
                    node.meta[DIFFERENCE_STATUS_FIELD] = row['diff_status'].strip()

                    if node.id in graph:
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
                    edge = Edge(src=row['src'].strip(),
                                dest=row['dest'].strip(),
                                type=row['type'].strip(),
                                source=row['source'].strip())

                    if edge.src in graph and edge.dest in graph:
                        success = graph.add_edge(edge)
                    else:
                        success = False

                    if not success:
                        logger.error(
                            f"Строка {row_num}: Невозможно добавить связь {edge.src}->{edge.dest} (узлы отсутствуют)")

                except (KeyError, ValueError) as e:
                    logger.error(f"Строка {row_num}: Ошибка парсинга связи - {str(e)}")

    @staticmethod
    def _process_additional_edges(file_path: str, graph: Graph) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    edge = Edge(src=row['src'].strip(),
                                dest=row['dest'].strip(),
                                type=row['type'].strip(),
                                source=TypeSourceEdge.HAND)

                    if edge.src in graph and edge.dest in graph:
                        success = graph.add_edge(edge)
                    else:
                        success = False

                    if not success:
                        logger.error(
                            f"Строка {row_num}: Невозможно добавить связь {edge.src}->{edge.dest} (узлы отсутствуют)")

                except (KeyError, ValueError) as e:
                    logger.error(f"Строка {row_num}: Ошибка парсинга связи - {str(e)}")

    @staticmethod
    def _process_diff_edges(file_path: str, graph: Graph) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    edge = Edge(src=row['src'].strip(),
                                dest=row['dest'].strip(),
                                type=row['type'].strip(),
                                source=row['source'].strip())
                    edge.meta[DIFFERENCE_STATUS_FIELD] = row['diff_status'].strip()

                    if edge.src in graph and edge.dest in graph:
                        success = graph.add_edge(edge)
                    else:
                        success = False

                    if not success:
                        logger.error(
                            f"Строка {row_num}: Невозможно добавить связь {edge.src}->{edge.dest} (узлы отсутствуют)")

                except (KeyError, ValueError) as e:
                    logger.error(f"Строка {row_num}: Ошибка парсинга связи - {str(e)}")
