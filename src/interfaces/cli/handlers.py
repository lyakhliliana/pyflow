from argparse import Namespace
import logging
import os
from pathlib import Path
from core.utils.validatie import is_git_url
from core.graph.parsing.project import ProjectCodeParser
from core.graph.builder import CSVGraphBuilder
from core.graph.exporter import CSVGraphExporter
from core.utils.git_handler import GitHandler
from src.core.graph.visualise import HtmlGraphVisualizer

logger = logging.getLogger(__name__)

GRAPH_DIR_NAME = "graph"
VIS_NAME = "graph.html"


def handle_extract(args: Namespace):

    def _prepare_source(args) -> Path:
        if is_git_url(args.source):
            git_dir = GitHandler.clone_repo(args.source, destination=args.output_dir)
            if git_dir is None:
                print(f"error while cloning directory: {args.source}")
            return git_dir

        source_path = Path(args.source)
        if not source_path.exists():
            print(f"source path is not exist: {args.source}")
            return None

        return source_path

    if args.output_dir is None:
        args.output_dir = os.getcwd()
    graph_data_dir = os.path.join(args.output_dir, GRAPH_DIR_NAME)

    source = _prepare_source(args)
    if source is None:
        return

    try:
        parser = ProjectCodeParser(source)
        graph = parser.parse()
    except Exception as e:
        print(f"error parsing project: {args.source}: {str(e)}")
        return

    try:
        CSVGraphExporter.save(graph, graph_data_dir)
    except Exception as e:
        print(f"error saving project graph {args.source}: {str(e)}")
        return


def handle_visualise(args: Namespace):
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"source path is not exist: {args.source}")
        return None

    if args.mode == "basic":
        graph = CSVGraphBuilder.build(source_path)
        vis_path = os.path.join(source_path, VIS_NAME)
        HtmlGraphVisualizer.create(graph, vis_path)
