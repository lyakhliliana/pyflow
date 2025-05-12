from argparse import Namespace
import logging
import os
from pathlib import Path

from core.graph.dependency import DepenendencyExtensions
from core.graph.filters import CommonFilter
from core.models.graph import Graph
from core.utils.validatie import is_git_url
from core.utils.git_handler import GitHandler
from core.graph.parsing.project import ProjectParser
from core.graph.difference import GraphComparator
from core.graph.builder import ADDITIONAL_SECTION_NAME, CODE_SECTION_NAME, UNION_SECTION_NAME, CSVGraphBuilder
from core.graph.exporter import CSVGraphExporter
from core.graph.visualise import HtmlGraphVisualizer
from core.graph.contractor import GraphContractor

logger = logging.getLogger(__name__)

VIS_NAME = "graph.html"
DIFF_NAME = "diff.html"


def handle_extract(args: Namespace):

    def _prepare_source(args) -> Path:
        if is_git_url(args.link):
            git_dir = GitHandler.clone_repo(args.link, destination=args.output_dir, force_clone=True)
            if git_dir is None:
                print(f"error while cloning directory: {args.link}")
                return
            src_dir = os.path.join(git_dir, args.source)
            return src_dir

        source_path = Path(args.source)
        if not source_path.exists():
            print(f"source path is not exist: {args.source}")
            return None

        return source_path

    if args.output_dir is None:
        args.output_dir = os.getcwd()
    graph_data_dir = os.path.join(args.output_dir, CODE_SECTION_NAME)

    source = _prepare_source(args)
    if source is None:
        return

    try:
        parser = ProjectParser(source)
        graph = parser.parse()
    except Exception as e:
        print(f"error parsing project: {args.source}: {str(e)}")
        return

    try:
        CSVGraphExporter.save(graph, graph_data_dir)
    except Exception as e:
        print(f"error saving project graph {args.source}: {str(e)}")
        return

    try:
        CSVGraphBuilder.init_additional_files(args.output_dir)
    except Exception as e:
        print(f"error create union files in {args.output_dir}: {str(e)}")
        return


def handle_visualise(args: Namespace):
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"source path is not exist: {args.source}")
        return

    graph: Graph
    if args.mode == "basic":
        try:
            graph = CSVGraphBuilder.build(source_path)
        except Exception as e:
            print(f"error extract graph {source_path}: {str(e)}")
            return
        vis_path = os.path.join(source_path, VIS_NAME)

        try:
            HtmlGraphVisualizer.create(graph, vis_path)
        except Exception as e:
            print(f"error visualize graph {source_path}: {str(e)}")
            return

    if args.mode == "diff":
        try:
            graph = CSVGraphBuilder.build_diff(source_path)
        except Exception as e:
            print(f"error extract graph {source_path}: {str(e)}")
            return
        vis_path = os.path.join(source_path, VIS_NAME)

        try:
            HtmlGraphVisualizer.create_difference(graph, vis_path)
        except Exception as e:
            print(f"error visualize difference graph {source_path}: {str(e)}")
            return


def handle_union(args: Namespace):
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"source path is not exist: {args.source}")
        return

    try:
        graph_path = os.path.join(source_path, args.graph)
        additional_path = os.path.join(source_path, ADDITIONAL_SECTION_NAME)
        graph = CSVGraphBuilder.union(graph_path, additional_path)
    except Exception as e:
        print(f"error build union graph: {str(e)}")
        return

    union_dir = os.path.join(args.source, UNION_SECTION_NAME)
    try:
        CSVGraphExporter.save(graph, union_dir)
    except Exception as e:
        print(f"error saving union graph {union_dir}: {str(e)}")
        return


def handle_diff(args: Namespace):
    first_path = Path(args.first_path)
    second_path = Path(args.second_path)
    output_dir = Path(args.output_dir)
    if not first_path.exists():
        print(f"first graph path is not exist: {args.first_path}")
        return
    if not second_path.exists():
        print(f"second graph path is not exist: {args.second_path}")
        return

    first_graph: Graph
    second_graph: Graph
    try:
        first_graph = CSVGraphBuilder.build(first_path)
    except Exception as e:
        print(f"error extract first graph {first_path}: {str(e)}")
        return

    try:
        second_graph = CSVGraphBuilder.build(second_path)
    except Exception as e:
        print(f"error extract first graph {second_path}: {str(e)}")
        return

    try:
        difference_graph = GraphComparator.get_difference(first_graph, second_graph)
    except Exception as e:
        print(f"error get difference between {args.first} and {args.second}: {str(e)}")
        return

    try:
        CSVGraphExporter.save_diff(difference_graph, output_dir)
    except Exception as e:
        print(f"error saving difference graph {args.output_dir}: {str(e)}")
        return


def handle_contract(args: Namespace):
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"source path is not exist: {args.source}")
        return

    output_path = Path(args.output)

    try:
        graph = CSVGraphBuilder.build(source_path)
    except Exception as e:
        print(f"error extract graph {source_path}: {str(e)}")
        return

    try:
        contractor = GraphContractor(graph)
        contracted_graph = contractor.contract_graph(args.elements)
    except Exception as e:
        print(f"error contract graph: {str(e)}")
        return

    try:
        CSVGraphExporter.save(contracted_graph, output_path)
    except Exception as e:
        print(f"error saving contracted graph {output_path}: {str(e)}")
        return


def handle_filter(args: Namespace):
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"source path is not exist: {args.source}")
        return

    output_path = Path(args.output)

    try:
        graph = CSVGraphBuilder.build(source_path)
    except Exception as e:
        print(f"error extract graph {source_path}: {str(e)}")
        return

    try:
        filtered_graph = CommonFilter.apply(graph, args.node_types, args.edge_types)
    except Exception as e:
        print(f"error filter graph: {str(e)}")
        return

    try:
        CSVGraphExporter.save(filtered_graph, output_path)
    except Exception as e:
        print(f"error saving filtered graph {output_path}: {str(e)}")
        return


def handle_get_used(args: Namespace):
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"source path is not exist: {args.source}")
        return

    output_path = Path(args.output)

    try:
        graph = CSVGraphBuilder.build(source_path)
    except Exception as e:
        print(f"error extract graph {source_path}: {str(e)}")
        return

    try:
        used_graph = DepenendencyExtensions.get_used_nodes(graph, args.elements, args.depth)
    except Exception as e:
        print(f"error get used elements: {str(e)}")
        return

    try:
        CSVGraphExporter.save(used_graph, output_path)
    except Exception as e:
        print(f"error saving used elements graph {output_path}: {str(e)}")
        return


def handle_get_dependent(args: Namespace):
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"source path is not exist: {args.source}")
        return

    output_path = Path(args.output)

    try:
        graph = CSVGraphBuilder.build(source_path)
    except Exception as e:
        print(f"error extract graph {source_path}: {str(e)}")
        return

    try:
        dependent_graph = DepenendencyExtensions.get_dependent_nodes(graph, args.elements, args.depth)
    except Exception as e:
        print(f"error get dependent elements: {str(e)}")
        return

    try:
        CSVGraphExporter.save(dependent_graph, output_path)
    except Exception as e:
        print(f"error saving dependent elements graph {output_path}: {str(e)}")
        return
