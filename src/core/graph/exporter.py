from abc import ABC, abstractmethod
import csv
from typing import Dict
from pathlib import Path
import logging

from src.core.models.node import Node
from src.core.models.graph import Graph

logger = logging.getLogger(__name__)


class IGraphExporter(ABC):

    @staticmethod
    @abstractmethod
    def save(graph: Graph, nodes_path: str, edges_path: str) -> None:
        pass


class CSVGraphExporter(IGraphExporter):

    @staticmethod
    def save(graph: Graph, nodes_path: str, edges_path: str) -> None:
        """
        Сохраняет граф в два CSV-файла: узлы и связи.

        Args:
            graph: Экземпляр графа для экспорта
            nodes_path: Путь для файла узлов (формат: id,type,labels)
            edges_path: Путь для файла связей (формат: source_id,target_id,type)
        """
        CSVGraphExporter._save_nodes(graph.nodes, nodes_path)
        CSVGraphExporter._save_edges(graph.nodes, edges_path)

    @staticmethod
    def _save_nodes(nodes: Dict[str, Node], file_path: str) -> None:
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=['id', 'type', 'labels'],
                    quoting=csv.QUOTE_MINIMAL
                )
                writer.writeheader()

                for node in nodes.values():
                    writer.writerow({
                        'id': node.id,
                        'type': node.type,
                        'labels': ";".join(node.meta.labels)
                    })

            logger.info(f"Успешно сохранено {len(nodes)} узлов в {file_path}")

        except (IOError, PermissionError) as e:
            logger.critical(f"Ошибка записи файла узлов: {str(e)}")
            raise

    @staticmethod
    def _save_edges(nodes: Dict[str, Node], file_path: str) -> None:
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=['source_id', 'target_id', 'type'],
                    quoting=csv.QUOTE_MINIMAL
                )
                writer.writeheader()

                edge_count = 0
                for node in nodes.values():
                    for edge in node.edges:
                        writer.writerow({
                            'source_id': node.id,
                            'target_id': edge.id,
                            'type': edge.type
                        })
                        edge_count += 1

            logger.info(f"Успешно сохранено {edge_count} связей в {file_path}")

        except (IOError, PermissionError) as e:
            logger.critical(f"Ошибка записи файла связей: {str(e)}")
            raise
