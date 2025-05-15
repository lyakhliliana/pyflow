from argparse import Namespace
import logging
import os
from pathlib import Path

from core.models.graph import Graph
from utils.validatie import is_git_url
from utils.git_handler import GitHandler

from core.graph.parsing.project import ProjectParser
from core.graph.difference import GraphComparator
from core.graph.builder import CSVGraphBuilder
from core.graph.exporter import CSVGraphExporter
from core.graph.visualise import HtmlGraphVisualizer
from core.graph.contractor import GraphContractor
from core.graph.dependency import DependencyExtensions
from core.graph.filters import CommonFilter

logger = logging.getLogger(__name__)

VIS_NAME = "graph.html"
DIFF_NAME = "diff.html"


def handle_extract(args: Namespace):

    if args.link != "":
        if not is_git_url(args.link):
            print(f"error validate git link: {args.link}")
            return

        git_dir = GitHandler.clone_repo(args.link, destination=args.output, force_clone=True)
        if git_dir is None:
            print(f"error while cloning directory: {args.link}")
            return

        args.source = os.path.join(git_dir, args.source)

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"source path is not exist: {args.source}")
        return None

    if args.output is None:
        args.output = os.getcwd()

    try:
        parser = ProjectParser(source_path)
        graph = parser.parse()
    except Exception as e:
        print(f"error parsing project: {args.source}: {str(e)}")
        return

    try:
        CSVGraphExporter.save(graph, args.output)
    except Exception as e:
        print(f"error saving project graph {args.source}: {str(e)}")
        return
    
    vis_path = os.path.join(args.output, VIS_NAME)
    try:
        HtmlGraphVisualizer.create(graph, vis_path)
    except Exception as e:
        print(f"error visualize graph {source_path}: {str(e)}")
        return


def handle_init_additional(args: Namespace):
    directory = Path(args.directory)

    try:
        CSVGraphBuilder.init_additional_files(directory)
    except Exception as e:
        print(f"error initializing additional files in {directory}: {str(e)}")
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
    additional_path = Path(args.additional)

    if not source_path.exists():
        print(f"source path is not exist: {args.source}")
        return
    if not additional_path.exists():
        print(f"additional path is not exist: {args.additional}")
        return

    try:
        graph = CSVGraphBuilder.union(source_path, additional_path)
    except Exception as e:
        print(f"error build union graph: {str(e)}")
        return

    try:
        CSVGraphExporter.save(graph, args.output)
    except Exception as e:
        print(f"error saving union graph in {args.output}: {str(e)}")
        return
    
    vis_path = os.path.join(args.output, VIS_NAME)
    try:
        HtmlGraphVisualizer.create(graph, vis_path)
    except Exception as e:
        print(f"error visualize graph {source_path}: {str(e)}")
        return


def handle_diff(args: Namespace):
    first_path = Path(args.first_path)
    second_path = Path(args.second_path)
    output_dir = Path(args.output)

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
        print(f"error saving difference graph {args.output}: {str(e)}")
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
    
    vis_path = os.path.join(args.output, VIS_NAME)
    try:
        HtmlGraphVisualizer.create(contracted_graph, vis_path)
    except Exception as e:
        print(f"error visualize graph {source_path}: {str(e)}")
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
        filtered_graph = CommonFilter.apply(graph,
                                            nodes_types=args.node_types if hasattr(args, 'node_types') else [],
                                            edges_types=args.edge_types if hasattr(args, 'edge_types') else [],
                                            node_reg=args.node_id_mask if hasattr(args, 'node_id_mask') else "",
                                            inv_flag=args.inv if hasattr(args, 'inv') else False)
    except Exception as e:
        print(f"error filter graph: {str(e)}")
        return

    try:
        CSVGraphExporter.save(filtered_graph, output_path)
    except Exception as e:
        print(f"error saving filtered graph {output_path}: {str(e)}")
        return
    
    vis_path = os.path.join(args.output, VIS_NAME)
    try:
        HtmlGraphVisualizer.create(filtered_graph, vis_path)
    except Exception as e:
        print(f"error visualize graph {source_path}: {str(e)}")
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
        used_graph = DependencyExtensions.get_used_nodes(graph, args.elements, args.depth)
    except Exception as e:
        print(f"error get used elements: {str(e)}")
        return

    try:
        CSVGraphExporter.save(used_graph, output_path)
    except Exception as e:
        print(f"error saving used elements graph {output_path}: {str(e)}")
        return
    
    vis_path = os.path.join(args.output, VIS_NAME)
    try:
        HtmlGraphVisualizer.create(used_graph, vis_path)
    except Exception as e:
        print(f"error visualize graph {source_path}: {str(e)}")
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
        dependent_graph = DependencyExtensions.get_dependent_nodes(graph, args.elements, args.depth)
    except Exception as e:
        print(f"error get dependent elements: {str(e)}")
        return

    try:
        CSVGraphExporter.save(dependent_graph, output_path)
    except Exception as e:
        print(f"error saving dependent elements graph {output_path}: {str(e)}")
        return
    
    vis_path = os.path.join(args.output, VIS_NAME)
    try:
        HtmlGraphVisualizer.create(dependent_graph, vis_path)
    except Exception as e:
        print(f"error visualize graph {source_path}: {str(e)}")
        return
