from __future__ import annotations
from abc import ABC, abstractmethod
import copy
import csv
import logging
from typing import Dict, List, Tuple

from src.core.models.edge import TypeEdge
from src.core.models.node import MetaInfo, Node
from src.core.models.graph import Graph

logger = logging.getLogger(__name__)


class IGraphData(ABC):

    @staticmethod
    @abstractmethod
    def build(nodes_file: str, edges_file: str) -> Graph:
        pass

    @staticmethod
    @abstractmethod
    def add_elements(cur_graph: Graph, nodes_file: str, edges_file: str) -> Graph:
        pass

    @staticmethod
    @abstractmethod
    def add_labels(graph: Graph, labels_file: str, overwrite: bool = False) -> Dict[str, List[str]]:
        pass


class ValidationError(Exception):
    pass


class CSVGraphData(IGraphData):

    @staticmethod
    def build(nodes_file: str, edges_file: str) -> Graph:
        """
        Args:
            nodes_file: CSV с колонками [id, type, labels]
                        Пример: "id.py,file,'admin;manager'"
                        id - уникальный идентификатор узла
                        type - тип узла (класс)
                        labels - метки через точку с запятой

            edges_file: CSV с колонками [source_id, target_id, type]
                        Пример: "id.1,id.2,use"
                        source_id - идентификатор исходного узла
                        target_id - идентификатор целевого узла
                        type - тип связи

        Raises:
            ValidationError: при критических ошибках формата файлов
        """
        graph = Graph()

        try:
            GraphDataCSV._process_nodes(nodes_file, graph)
            GraphDataCSV._process_edges(edges_file, graph)
        except FileNotFoundError as e:
            logger.critical(f"Файл не найден: {str(e)}")
            raise
        except csv.Error as e:
            logger.critical(f"Ошибка CSV: {str(e)}")
            raise ValidationError from e

        return graph

    @staticmethod
    def add_elements(cur_graph: Graph, nodes_file: str, edges_file: str) -> Graph:
        """
        Добавляет узлы и связи из CSV-файлов в существующий граф с валидацией.

        Особенности:
        - Не перезаписывает существующие узлы с одинаковыми ID

        Args:
            cur_graph: Существующий граф для обновления
            nodes_file: CSV с колонками [id, type, labels]
            edges_file: CSV с колонками [source_id, target_id, type]

        Returns:
            Graph: Обновленный граф (новый объект)

        Raises:
            ValidationError: при критических ошибках формата файлов
        """
        answer = copy.deepcopy(cur_graph)
        try:
            GraphDataCSV._process_nodes(
                file_path=nodes_file,
                graph=answer,
                update_mode=True
            )

            GraphDataCSV._process_edges(
                file_path=edges_file,
                graph=answer
            )

        except FileNotFoundError as e:
            logger.critical(f"Файл не найден: {str(e)}")
            raise
        except csv.Error as e:
            logger.critical(f"Ошибка CSV: {str(e)}")
            raise ValidationError from e

        return answer

    @staticmethod
    def add_labels(graph: Graph, labels_file: str, overwrite: bool = False) -> Dict[str, List[str]]:
        """
        Добавляет метки к узлам графа из CSV-файла, избегая дубликатов.

        Формат файла: CSV с колонками [id, labels]

        Args:
            graph: Граф для обновления
            labels_file: Путь к CSV-файлу с метками

        Raises:
            FileNotFoundError: если файл не существует
            ValueError: при некорректном формате данных
        """
        added_labels = {}

        try:
            with open(labels_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                if not {'id', 'labels'}.issubset(reader.fieldnames):
                    raise ValueError("CSV должен содержать колонки: id, labels")

                for row_num, row in enumerate(reader, 1):
                    node_id = row['id'].strip()
                    labels_str = row.get('labels', '').strip()

                    if not node_id:
                        logger.warning(f"Строка {row_num}: Пропущено - отсутствует id")
                        continue

                    # Парсинг меток
                    labels = [l.strip() for l in labels_str.split(";") if l.strip()]

                    if not labels:
                        logger.debug(f"Строка {row_num}: Нет меток для {node_id}")
                        continue

                    # Поиск узла
                    if node_id not in graph.nodes:
                        logger.warning(f"Строка {row_num}: Узел {node_id} не найден")
                        continue

                    node = graph.nodes[node_id]
                    existing = set(node.meta.labels)
                    new_labels = [l for l in labels if l not in existing]

                    # Обновление меток
                    if overwrite:
                        node.meta.labels = labels
                        added = list(set(labels) - existing)
                    else:
                        node.meta.labels.extend(new_labels)
                        added = new_labels

                    if added:
                        added_labels[node_id] = added

        except csv.Error as e:
            logger.error(f"Ошибка CSV: {str(e)}")
            raise

        return added_labels

    @staticmethod
    def _process_nodes(file_path: str, graph: Graph, update_mode: bool = False) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                try:
                    node = GraphDataCSV._parse_node_row(row)

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
                    source_id, target_id, edge_type = GraphDataCSV._parse_edge_row(row)

                    if source_id in graph and target_id in graph:
                        success = graph.add_edge(source_id, target_id, edge_type)
                    else:
                        success = False

                    if not success:
                        logger.error(
                            f"Строка {row_num}: Невозможно добавить связь {source_id}->{target_id} (узлы отсутствуют)")

                except (KeyError, ValueError) as e:
                    logger.error(f"Строка {row_num}: Ошибка парсинга связи - {str(e)}")

    @staticmethod
    def _parse_node_row(row: Dict[str, str]) -> Node:
        return Node(
            id=row['id'].strip(),
            type=row['type'].strip(),
            meta=MetaInfo(
                labels=[l.strip() for l in row.get('labels', '').split(';') if l.strip()]
            )
        )

    @staticmethod
    def _parse_edge_row(row: Dict[str, str]) -> Tuple[str, str, TypeEdge]:
        return (
            row['source_id'].strip(),
            row['target_id'].strip(),
            row['type'].strip()
        )
