from abc import ABC, abstractmethod
import csv
import os
from pathlib import Path
import logging

from core.models.graph import Graph
from core.graph.difference import DIFFERENCE_STATUS_FIELD

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
        Exports the graph to CSV files in the specified directory.

        Args:
            graph: Graph instance to export
            directory_path: Path to the directory where files will be saved
                (will be created if it doesn't exist). Files will be:
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
        Exports the graph with difference information to CSV files in the specified directory.

        Args:
            graph: Graph instance to export
            directory_path: Path to the directory where files will be saved
                (will be created if it doesn't exist). Files will be:
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

                for node in graph.get_all_nodes():
                    writer.writerow({
                        'id': node.id,
                        'name': node.name,
                        'type': node.type,
                        'hash': node.hash,
                        'source': node.source
                    })

            logger.info(f"Successfully saved {len(graph.nodes)} nodes to {file_path}")

        except (IOError, PermissionError) as e:
            text_error = f"Error writing nodes file: {str(e)}"
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
                for edge in graph.get_all_edges():
                    writer.writerow({'src': edge.src, 'dest': edge.dest, 'type': edge.type, 'source': edge.source})
                    edge_count += 1

            logger.info(f"Successfully saved {edge_count} edges to {file_path}")

        except (IOError, PermissionError) as e:
            text_error = f"Error writing edges file: {str(e)}"
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

                for node in graph.get_all_nodes():
                    if DIFFERENCE_STATUS_FIELD not in node.meta:
                        logger.warning(f"Node {node.id} does not contain {DIFFERENCE_STATUS_FIELD} field in meta data")
                        continue
                    writer.writerow({
                        'id': node.id,
                        'name': node.name,
                        'type': node.type,
                        'diff_status': node.meta[DIFFERENCE_STATUS_FIELD],
                        'source': node.source
                    })

            logger.info(f"Successfully saved {len(graph.nodes)} nodes to {file_path}")

        except (IOError, PermissionError) as e:
            text_error = f"Error writing nodes file: {str(e)}"
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
                for edge in graph.get_all_edges():
                    if DIFFERENCE_STATUS_FIELD not in edge.meta:
                        logger.warning(
                            f"Edge {edge.src} -> {edge.dest} does not contain {DIFFERENCE_STATUS_FIELD} field in meta data"
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

            logger.info(f"Successfully saved {edge_count} edges to {file_path}")

        except (IOError, PermissionError) as e:
            text_error = f"Error writing edges file: {str(e)}"
            logger.critical(text_error)
            raise Exception(text_error)
