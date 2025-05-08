from abc import ABC, abstractmethod
from dataclasses import asdict
from core.graph.difference import DIFFERENCE_STATUS_FIELD, TypeDiff
import networkx as nx
from pyvis.network import Network

from src.core.models.graph import Graph
from src.core.models.node import CODE_NODE_TYPES, STRUCTURE_NODE_TYPES, Node, TypeNode, TypeSourceNode

PINK = "#f57676"
GREEN = '#76f594'
BLUE = "#8ff2e7"
YELLOW = "#f0f28f"
GREY = "#757574"
PURPLE = '#aa86cf'


class IGraphVisualizer(ABC):

    @staticmethod
    @abstractmethod
    def create(graph: Graph, vis_path: str):
        pass

    @staticmethod
    @abstractmethod
    def create_difference(dif_graph: Graph, vis_path: str):
        pass


class HtmlGraphVisualizer(IGraphVisualizer):

    @staticmethod
    def create(graph: Graph, vis_path: str):

        def _get_node_color(node: Node) -> str:
            if node.type in STRUCTURE_NODE_TYPES:
                return GREEN
            elif node.type in CODE_NODE_TYPES:
                return BLUE
            else:
                return PURPLE

        G = nx.DiGraph()

        for node, data in graph.nodes.items():
            node_color = _get_node_color(data)
            G.add_node(node, color=node_color, **asdict(data))
            for edge in graph.edges.get(node, []):
                G.add_edge(edge.src, edge.dest, label=edge.type)

        net = Network(notebook=True, cdn_resources="remote", directed=True)
        net.from_nx(G)

        net.show_buttons(filter_=['physics'])
        net.show(vis_path)

    @staticmethod
    def create_difference(dif_graph: Graph, vis_path: str):
        G = nx.DiGraph()

        UNKNOWN = 'unknown'

        diff_colors = {
            TypeDiff.NEW: GREEN,
            TypeDiff.DELETED: PINK,
            TypeDiff.CHANGED: YELLOW,
            TypeDiff.UNCHACHGED: GREY,
            UNKNOWN: BLUE
        }
        for node_id, node in dif_graph.nodes.items():
            diff_status = UNKNOWN
            if DIFFERENCE_STATUS_FIELD in node.meta:
                diff_status = node.meta[DIFFERENCE_STATUS_FIELD]
            G.add_node(node_id, color=diff_colors[diff_status])

            for edge in dif_graph.edges.get(node_id, []):
                diff_status = UNKNOWN
                if DIFFERENCE_STATUS_FIELD in edge.meta:
                    diff_status = edge.meta[DIFFERENCE_STATUS_FIELD]
                G.add_edge(edge.src, edge.dest, label=edge.type, color=diff_colors[diff_status])

        net = Network(notebook=True, cdn_resources="remote", directed=True)
        net.from_nx(G)

        net.show_buttons(filter_=['physics'])
        net.show(vis_path)
