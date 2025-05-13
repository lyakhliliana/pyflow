import argparse
from interfaces.cli.handlers import handle_diff, handle_extract, handle_union, handle_visualise, handle_contract, handle_filter, handle_get_used, handle_get_dependent, handle_init_additional


def main():
    parser = argparse.ArgumentParser(description="Pyflow - Python Dependency Analysis Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Парсер для команды extract
    extract_parser = subparsers.add_parser(
        "extract", help="Extract dependency information from a Python project directory or Git repository")
    extract_parser.add_argument("source", help="Path to the source directory containing Python files to analyze")
    extract_parser.add_argument("output",
                                default="",
                                help="Directory where the extracted dependency graph will be saved")
    extract_parser.add_argument("-l", "--link", default="", help="Git repository URL to clone and analyze (optional)")

    # Парсер для команды init_additional
    init_additional_parser = subparsers.add_parser(
        "init_additional",
        help="Initialize files for writing additional elements (nodes, edges, architectural elements, use cases)")
    init_additional_parser.add_argument(
        "directory", help="Path to the directory where files for additional elements will be created")

    # Парсер для команды union
    union_parser = subparsers.add_parser("union", help="Union graph directory with additional elements")
    union_parser.add_argument("source", help="Path to the main graph directory to be extended")
    union_parser.add_argument(
        "additional",
        help="Path to directory containing files with additional nodes and edges, architectural elements and use cases")
    union_parser.add_argument("output", help="Directory where the resulting union graph will be saved")

    # Парсер для команды visualize
    visualise_parser = subparsers.add_parser("visualize", help="Generate a visual representation of a dependency graph")
    visualise_parser.add_argument("source", help="Path to the graph file")
    visualise_parser.add_argument(
        "-m",
        "--mode",
        choices=["basic", "diff"],
        default="basic",
        help="Visualization mode: 'basic' for standard view, 'diff' for difference highlighting")

    # Парсер для команды diff
    diff_parser = subparsers.add_parser("diff", help="Compare two dependency graphs and visualize their differences")
    diff_parser.add_argument("first_path", help="Path to the first dependency graph file for comparison")
    diff_parser.add_argument("second_path", help="Path to the second dependency graph file for comparison")
    diff_parser.add_argument("output", help="Directory where the difference graph will be saved")

    # Парсер для команды contract
    contract_parser = subparsers.add_parser("contract", help="Contract architectural elements in a graph")
    contract_parser.add_argument("source", help="Path to the graph directory")
    contract_parser.add_argument("output", help="Path to the graph directory where the contracted graph will be saved")
    contract_parser.add_argument("elements", nargs="+", help="List of architectural elements to contract")

    # Парсер для команды filter
    filter_parser = subparsers.add_parser("filter", help="Filter graph based on node and edge types")
    filter_parser.add_argument("source", help="Path to the source directory containing the graph")
    filter_parser.add_argument("output", help="Path to the directory where the filtered graph will be saved")
    filter_parser.add_argument("--node-types",
                               nargs="+",
                               default=[],
                               help="List of node types to keep in the filtered graph")
    filter_parser.add_argument("--edge-types",
                               nargs="+",
                               default=[],
                               help="List of edge types to keep in the filtered graph")
    filter_parser.add_argument("--inv",
                               action="store_true",
                               help="Inverse filtering - keep nodes/edges that do NOT match the specified types")
    filter_parser.add_argument("--node-id-mask", help="Regular expression pattern to match node IDs")

    # Парсер для команды get_used
    get_used_parser = subparsers.add_parser("get_used", help="Get elements that are used by specified elements")
    get_used_parser.add_argument("source", help="Path to the source graph file")
    get_used_parser.add_argument("output", help="Path where the result will be saved")
    get_used_parser.add_argument("elements", nargs="+", help="List of elements to find usages for")
    get_used_parser.add_argument("-d",
                                 "--depth",
                                 type=int,
                                 default=0,
                                 help="Maximum depth of dependency search (0 for unlimited)")

    # Парсер для команды get_dependent
    get_dependent_parser = subparsers.add_parser("get_dependent", help="Get elements that depend on specified elements")
    get_dependent_parser.add_argument("source", help="Path to the source graph file")
    get_dependent_parser.add_argument("output", help="Path where the result will be saved")
    get_dependent_parser.add_argument("elements", nargs="+", help="List of elements to find dependencies for")
    get_dependent_parser.add_argument("-d",
                                      "--depth",
                                      type=int,
                                      default=0,
                                      help="Maximum depth of dependency search (0 for unlimited)")

    args = parser.parse_args()

    try:
        if args.command == "extract":
            handle_extract(args)
        if args.command == "init_additional":
            handle_init_additional(args)
        if args.command == "visualize":
            handle_visualise(args)
        if args.command == "union":
            handle_union(args)
        if args.command == "diff":
            handle_diff(args)
        if args.command == "contract":
            handle_contract(args)
        if args.command == "filter":
            handle_filter(args)
        if args.command == "get_used":
            handle_get_used(args)
        if args.command == "get_dependent":
            handle_get_dependent(args)

    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
