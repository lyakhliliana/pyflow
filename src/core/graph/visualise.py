from abc import ABC, abstractmethod
from dataclasses import asdict
import networkx as nx
from pyvis.network import Network

from src.core.models.graph import Graph
from src.core.models.node import TypeNode


class IGraphVisualizer(ABC):

    @staticmethod
    @abstractmethod
    def create(graph: Graph, vis_path: str):
        pass


class HtmlGraphVisualizer(IGraphVisualizer):

    @staticmethod
    def create(graph: Graph, vis_path: str):
        G = nx.DiGraph()

        for node, data in graph.nodes.items():
            node_color = HtmlGraphVisualizer._get_node_color(data.type)
            G.add_node(node, color=node_color, **asdict(data))
            for edge in data.edges:
                G.add_edge(node, edge.id, label=edge.type)

        net = Network(notebook=True, cdn_resources="remote", directed=True)
        net.from_nx(G)

        net.show_buttons(filter_=['physics'])
        net.show(vis_path)

    @staticmethod
    def _get_node_color(node_type: str) -> str:
        if node_type in [TypeNode.DIRECTORY, TypeNode.FILE]:
            return '#86cf90'  # Зеленый
        elif node_type in [TypeNode.CLASS, TypeNode.FUNC, TypeNode.BODY]:
            return '##8698cf'  # Голубой
        else:
            return '#aa86cf'  # Сиреневый