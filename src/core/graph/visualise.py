from abc import ABC, abstractmethod
from dataclasses import asdict
import networkx as nx
from pyvis.network import Network

from src.core.models.graph import Graph
from src.core.models.node import Node, TypeNode, TypeSourceNode


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
            node_color = HtmlGraphVisualizer._get_node_color(data)
            G.add_node(node, color=node_color, **asdict(data))
            for edge in data.edges:
                G.add_edge(node, edge.id, label=edge.type)

        net = Network(notebook=True, cdn_resources="remote", directed=True)
        net.from_nx(G)

        net.show_buttons(filter_=['physics'])
        net.show(vis_path)

    @staticmethod
    def _get_node_color(node: Node) -> str:
        if node.type in [TypeNode.DIRECTORY, TypeNode.FILE]:
            # Зеленый
            if node.source_type == TypeSourceNode.CODE:
                return '#b3d9a5'
            return '#75db4f'
        elif node.type in [TypeNode.CLASS, TypeNode.FUNC, TypeNode.BODY]:
            # Голубой
            if node.source_type == TypeSourceNode.CODE:
                return '#8cc6db'
            return '#14a9de'
        else:
            return '#aa86cf'  # Сиреневый