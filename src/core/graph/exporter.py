from abc import ABC, abstractmethod
import csv
import os
from pathlib import Path
import logging

from core.models.node import Node
from core.models.graph import Graph

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
                - nodes.csv: [id,type,source_type]
                - edges.csv: [source_id,target_id,type,source_type]
        """
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        nodes_path = os.path.join(directory_path, "nodes.csv")
        edges_path = os.path.join(directory_path, "edges.csv")
        CSVGraphExporter._save_nodes(graph, nodes_path)
        CSVGraphExporter._save_edges(graph, edges_path)

    @staticmethod
    def _save_nodes(graph: Graph, file_path: str) -> None:
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'type', 'source_type'], quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()

                for node in graph.nodes.values():
                    writer.writerow({'id': node.id, 'type': node.type, 'source_type': node.source_type})

            logger.info(f"Успешно сохранено {len(graph.nodes)} узлов в {file_path}")

        except (IOError, PermissionError) as e:
            logger.critical(f"Ошибка записи файла узлов: {str(e)}")
            raise

    @staticmethod
    def _save_edges(graph: Graph, file_path: str) -> None:
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f,
                                        fieldnames=['source_id', 'target_id', 'type', 'source_type'],
                                        quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()

                edge_count = 0
                for node in graph.nodes.values():
                    for edge in node.edges:
                        writer.writerow({
                            'source_id': node.id,
                            'target_id': edge.id,
                            'type': edge.type,
                            'source_type': edge.source_type
                        })
                        edge_count += 1

            logger.info(f"Успешно сохранено {edge_count} связей в {file_path}")

        except (IOError, PermissionError) as e:
            logger.critical(f"Ошибка записи файла связей: {str(e)}")
            raise
