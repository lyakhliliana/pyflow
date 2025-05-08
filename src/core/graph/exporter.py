from abc import ABC, abstractmethod
import csv
import os
from pathlib import Path
import logging

from core.models.graph import Graph
from src.core.graph.difference import DIFFERENCE_STATUS_FIELD

logger = logging.getLogger(__name__)


class IGraphExporter(ABC):

    @staticmethod
    @abstractmethod
    def save(graph: Graph, directory_path: str) -> None:
        pass


class CSVGraphExporter(IGraphExporter):

    @staticmethod
    def save(graph: Graph, directory_path: str) -> None:
        """
        Сохраняет граф в CSV-файлы в указанной директории.

        Args:
            graph: Экземпляр графа для экспорта
            directory_path: Путь к директории для сохранения файлов
                (создастся при отсутствии). Файлы будут:
                - nodes.csv: [id, name, type, hash, source]
                - edges.csv: [src, dest, type, source]
        """
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        nodes_path = os.path.join(directory_path, "nodes.csv")
        edges_path = os.path.join(directory_path, "edges.csv")
        CSVGraphExporter._save_nodes(graph, nodes_path)
        CSVGraphExporter._save_edges(graph, edges_path)

    @staticmethod
    def save_diff(graph: Graph, directory_path: str) -> None:
        """
        Сохраняет граф в CSV-файлы в указанной директории.

        Args:
            graph: Экземпляр графа для экспорта
            directory_path: Путь к директории для сохранения файлов
                (создастся при отсутствии). Файлы будут:
                - nodes.csv: [id, name, type, diff_status, source]
                - edges.csv: [src, dest, type, diff_status, source]
        """
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        nodes_path = os.path.join(directory_path, "nodes.csv")
        edges_path = os.path.join(directory_path, "edges.csv")
        CSVGraphExporter._save_diff_nodes(graph, nodes_path)
        CSVGraphExporter._save_diff_edges(graph, edges_path)

    @staticmethod
    def _save_nodes(graph: Graph, file_path: str) -> None:
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f,
                                        fieldnames=['id', 'name', 'type', 'hash', 'source'],
                                        quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()

                for node in graph.nodes.values():
                    writer.writerow({
                        'id': node.id,
                        'name': node.name,
                        'type': node.type,
                        'hash': node.hash,
                        'source': node.source
                    })

            logger.info(f"Успешно сохранено {len(graph.nodes)} узлов в {file_path}")

        except (IOError, PermissionError) as e:
            text_error = f"Ошибка записи файла узлов: {str(e)}"
            logger.critical(text_error)
            raise Exception(text_error)

    @staticmethod
    def _save_edges(graph: Graph, file_path: str) -> None:
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['src', 'dest', 'type', 'source'], quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()

                edge_count = 0
                for edges in graph.edges.values():
                    for edge in edges:
                        writer.writerow({'src': edge.src, 'dest': edge.dest, 'type': edge.type, 'source': edge.source})
                        edge_count += 1

            logger.info(f"Успешно сохранено {edge_count} связей в {file_path}")

        except (IOError, PermissionError) as e:
            text_error = f"Ошибка записи файла связей: {str(e)}"
            logger.critical(text_error)
            raise Exception(text_error)

    @staticmethod
    def _save_diff_nodes(graph: Graph, file_path: str) -> None:
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f,
                                        fieldnames=['id', 'name', 'type', 'diff_status', 'source'],
                                        quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()

                for node in graph.nodes.values():
                    if DIFFERENCE_STATUS_FIELD not in node.meta:
                        logger.warning(f"Node {node.id} do not contain {DIFFERENCE_STATUS_FIELD} filed in meta data")
                        continue
                    writer.writerow({
                        'id': node.id,
                        'name': node.name,
                        'type': node.type,
                        'diff_status': node.meta[DIFFERENCE_STATUS_FIELD],
                        'source': node.source
                    })

            logger.info(f"Успешно сохранено {len(graph.nodes)} узлов в {file_path}")

        except (IOError, PermissionError) as e:
            text_error = f"Ошибка записи файла узлов: {str(e)}"
            logger.critical(text_error)
            raise Exception(text_error)

    @staticmethod
    def _save_diff_edges(graph: Graph, file_path: str) -> None:
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f,
                                        fieldnames=['src', 'dest', 'type', 'diff_status', 'source'],
                                        quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()

                edge_count = 0
                for edges in graph.edges.values():
                    for edge in edges:
                        if DIFFERENCE_STATUS_FIELD not in edge.meta:
                            logger.warning(
                                f"Edge {edge.src} -> {edge.dest} do not contain {DIFFERENCE_STATUS_FIELD} filed in meta data"
                            )
                            continue
                        writer.writerow({
                            'src': edge.src,
                            'dest': edge.dest,
                            'type': edge.type,
                            'diff_status': edge.meta[DIFFERENCE_STATUS_FIELD],
                            'source': edge.source
                        })
                        edge_count += 1

            logger.info(f"Успешно сохранено {edge_count} связей в {file_path}")

        except (IOError, PermissionError) as e:
            text_error = f"Ошибка записи файла связей: {str(e)}"
            logger.critical(text_error)
            raise Exception(text_error)
