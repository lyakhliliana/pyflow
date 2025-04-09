from dataclasses import asdict
from src.core.models.node import TypeNode
from src.core.graph.filters import FILTER_BY_MODE


class HtmlGraphBuilder:

    def apply_filter_and_save(self, graph, filter_mode: str):

        filter_graph = FILTER_BY_MODE[filter_mode](graph)
        filter_graph.save("tmp/results/filtered.json")

        import networkx as nx
        from pyvis.network import Network

        G = nx.DiGraph()

        for node, data in filter_graph.nodes.items():
            node_color = self._get_node_color(data.type)
            G.add_node(node, color=node_color, **asdict(data))
            for edge in data.edges:
                G.add_edge(node, edge.id, label=edge.type)

        net = Network(notebook=True, cdn_resources="remote", directed=True)
        net.from_nx(G)

        # Настройка визуализации
        net.show_buttons(filter_=['physics'])
        net.show("tmp/results/graph.html")

    def _get_node_color(self, node_type: str) -> str:
        if node_type in [TypeNode.DIRECTORY, TypeNode.FILE]:
            return '#00ff00'  # Зеленый
        else:
            return '#0066ff'   # Синий
