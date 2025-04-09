from src.core.graph.filters import FilterMode
from src.core.parsing.project_parser import ProjectParser
from src.interfaces.html.html import HtmlGraphBuilder

if __name__ == "__main__":
    directory = "src/core/models/edge.py"
    # directory = "venv/lib/python3.10/site-packages/matplotlib"
    parser = ProjectParser(directory)
    graph = parser.parse_project()
    parser.save_graph("tmp/results/output.json")
    HtmlGraphBuilder().apply_filter_and_save(graph, FilterMode.FILE_LINKS)


# from src.interfaces.tkinter.interface import ParserApp

# if __name__ == "__main__":
    # app = ParserApp()
    # app.start()