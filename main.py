from src.core.graph.filters import FilterMode
from src.core.code_parsing.project import ProjectCodeParser
from src.interfaces.html.html import HtmlGraphBuilder

if __name__ == "__main__":
    directory = ""
    parser = ProjectCodeParser(directory)
    graph = parser.parse_project()
    parser.save_graph("tmp/results/output.json")
    HtmlGraphBuilder().apply_filter_and_save(graph, FilterMode.FULL)