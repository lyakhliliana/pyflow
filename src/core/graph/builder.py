from __future__ import annotations
from abc import ABC, abstractmethod
import csv
import logging
import os
from collections import deque

from core.models.edge import Edge
from core.models.node import Node, TypeNode, CODE_NODE_TYPES, STRUCTURE_NODE_TYPES, ADDITIONAL_NODE_TYPES
from core.models.graph import Graph
from core.models.common import TypeSource
from core.models.edge import TypeEdge

from core.graph.difference import DIFFERENCE_STATUS_FIELD
from core.graph.hasher import Hasher

logger = logging.getLogger(__name__)

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
            text_error = f"File not found: {str(e)}"
            logger.critical(text_error)
            raise Exception(text_error)
        except csv.Error as e:
            text_error = f"CSV error: {str(e)}"
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
            Hasher.recalculate(graph)

        except FileNotFoundError as e:
            logger.critical(f"File not found: {str(e)}")
            raise
        except csv.Error as e:
            logger.critical(f"CSV error: {str(e)}")
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
            text_error = f"File not found: {str(e)}"
            logger.critical(text_error)
            raise Exception(text_error)
        except csv.Error as e:
            text_error = f"CSV error: {str(e)}"
            logger.critical(text_error)
            raise Exception(text_error)

        return graph

    @staticmethod
    def init_additional_files(directory_path: str):
        f"""
        Initializes the directory structure and empty CSV files for storing additional graph elements.

        Creates the following structure in the specified directory:
        - {NODES_FILE_NAME}: (CSV file with 'id,name,type' header)
        - {EDGES_FILE_NAME}: (CSV file with 'src,dest,type' header)

        If the files already exist, they will not be overwritten. The directory will be created
        if it doesn't exist (including all necessary parent directories).

        Args:
            directory_path: Path to the directory where additional files should be created.

        Returns:
            None
        """
        nodes_path = os.path.join(directory_path, NODES_FILE_NAME)
        edges_path = os.path.join(directory_path, EDGES_FILE_NAME)

        os.makedirs(directory_path, exist_ok=True)

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

                    if node.id in graph.nodes:
                        logger.info(f"Line {row_num}: Node {node.id} already exists - skipping")
                        continue

                    if not graph.add_node(node):
                        logger.warning(f"Line {row_num}: Node ID conflict {node.id}")

                except (KeyError, ValueError) as e:
                    logger.error(f"Line {row_num}: Node parsing error - {str(e)}")

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
                                source=TypeSource.HAND)

                    if node.id in graph.nodes:
                        logger.info(f"Line {row_num}: Node {node.id} already exists - skipping")
                        continue

                    if not graph.add_node(node):
                        logger.warning(f"Line {row_num}: Node ID conflict {node.id}")

                except (KeyError, ValueError) as e:
                    logger.error(f"Line {row_num}: Node parsing error - {str(e)}")

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

                    if node.id in graph.nodes:
                        logger.info(f"Line {row_num}: Node {node.id} already exists - skipping")
                        continue

                    if not graph.add_node(node):
                        logger.warning(f"Line {row_num}: Node ID conflict {node.id}")

                except (KeyError, ValueError) as e:
                    logger.error(f"Line {row_num}: Node parsing error - {str(e)}")

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

                    if edge.src in graph.nodes and edge.dest in graph.nodes:
                        success = graph.add_edge(edge)
                    else:
                        success = False

                    if not success:
                        logger.error(
                            f"Line {row_num}: Cannot add edge {edge.src}->{edge.dest} (nodes missing)")

                except (KeyError, ValueError) as e:
                    logger.error(f"Line {row_num}: Edge parsing error - {str(e)}")

    @staticmethod
    def _process_additional_edges(file_path: str, graph: Graph) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    edge = Edge(src=row['src'].strip(),
                                dest=row['dest'].strip(),
                                type=row['type'].strip(),
                                source=TypeSource.HAND)

                    if edge.src in graph.nodes and edge.dest in graph.nodes:
                        if graph.get_node(edge.src).type == TypeNode.ARC_ELEMENT:
                            success = CSVGraphBuilder._add_arc_edge(edge, graph)
                        else:
                            success = graph.add_edge(edge)
                    else:
                        success = False

                    if not success:
                        logger.error(
                            f"Line {row_num}: Cannot add edge {edge.src}->{edge.dest} (nodes missing)")

                except (KeyError, ValueError) as e:
                    logger.error(f"Line {row_num}: Edge parsing error - {str(e)}")

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

                    if edge.src in graph.nodes and edge.dest in graph.nodes:
                        success = graph.add_edge(edge)
                    else:
                        success = False

                    if not success:
                        logger.error(
                            f"Line {row_num}: Cannot add edge {edge.src}->{edge.dest} (nodes missing)")

                except (KeyError, ValueError) as e:
                    logger.error(f"Line {row_num}: Edge parsing error - {str(e)}")

    @staticmethod
    def _add_arc_edge(edge: Edge, graph: Graph) -> bool:
        dest_node = graph.get_node(edge.dest)
        if dest_node is None:
            logger.warning(f"Destination node {edge.dest} not found in the graph")
            return False

        if dest_node.type in CODE_NODE_TYPES:
            return graph.add_edge(edge)
        
        elif dest_node.type in STRUCTURE_NODE_TYPES:
            is_success = True
            visited = set()
            queue = deque([dest_node.id])
            while queue:
                current_id = queue.popleft()
                if current_id in visited:
                    continue
                visited.add(current_id)
                current_node = graph.get_node(current_id)
                if current_node is None:
                    continue
                if current_node.type in CODE_NODE_TYPES:
                    new_edge = Edge(src=edge.src, dest=current_id, type=edge.type, source=edge.source)
                    if not graph.add_edge(new_edge):
                        is_success = False
                elif current_node.type in STRUCTURE_NODE_TYPES:
                    for out_edge in graph.get_edges_out(current_id):
                        if out_edge.type == TypeEdge.CONTAIN:
                            queue.append(out_edge.dest)
            return is_success
        
        elif dest_node.type in ADDITIONAL_NODE_TYPES:
            logger.warning(f"Architectural element can only be linked to code and structure elements, not to {dest_node.type}")
            return False
        else:
            logger.warning(f"Unknown destination node type: {dest_node.type}")
            return False
