from typing import List

from src.filter import FILTER_BY_MODE, FilterMode
from src.parser import Parser
from src.utils.repo_manager.git_manager import GitManager


class ProjectAnalyzerSettings:
    ignored_directories: List[str] = ['venv', '.git', 'tmp', 'view', 'exp']
    filter_mode: str = FilterMode.OBJECT_LINKS
    link_from_git: bool = False


class ProjectAnalyzer:
    __slots__ = ('settings', 'parser')

    def __init__(self, link_from_git=False, filter_mode=FilterMode.OBJECT_LINKS):
        self.settings = ProjectAnalyzerSettings()
        self.settings.link_from_git = link_from_git
        self.settings.filter_mode = filter_mode

    def process_project(self, path: str = "", link=""):
        if self.settings.link_from_git:
            project = GitManager(link)
            path = project.path

        parser = Parser(path, self.settings.ignored_directories)
        parser.analyze()
        project_graph = parser.get_graph()
        filter_graph = FILTER_BY_MODE[self.settings.filter_mode](project_graph)
        filter_graph.save_to_json()

        if self.settings.link_from_git:
            project.delete()

        # Сохраняем граф в HTML-файл
        import json
        import networkx as nx
        from pyvis.network import Network
        file_path = "tmp/results/output.json"
        with open(file_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)

        G = nx.DiGraph()

        for node, data in graph_data.items():
            G.add_node(node, **data)
            for link in data["links"]:
                G.add_edge(node, link['id'], label=link['type'])

        net = Network(notebook=True, cdn_resources="remote", directed=True)
        net.from_nx(G)

        # Настройка визуализации
        net.show_buttons(filter_=['physics'])
        net.show("tmp/results/graph.html")
