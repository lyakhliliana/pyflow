import argparse
from interfaces.cli.handlers import handle_diff, handle_extract, handle_union, handle_visualise, handle_contract


def main():
    parser = argparse.ArgumentParser(description="Pyflow - Python Dependency Analysis Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Парсер для команды extract
    extract_parser = subparsers.add_parser(
        "extract", help="Extract dependency information from a Python project directory or Git repository")
    extract_parser.add_argument("source", help="Path to the source directory containing Python files to analyze")
    extract_parser.add_argument("-l", "--link", default="", help="Git repository URL to clone and analyze (optional)")
    extract_parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Directory where the extracted dependency graph will be saved (default: current directory)")

    # Парсер для команды union
    union_parser = subparsers.add_parser("union", help="Union graph and additional elements")
    union_parser.add_argument("source", help="Path to source directory with project graphs")
    union_parser.add_argument("graph", help="Graph name from a directory with project graphs")

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
    diff_parser.add_argument("output_dir", help="Directory where the difference graph will be saved")

    # Парсер для команды contract
    contract_parser = subparsers.add_parser("contract", help="Contract architectural elements in a graph")
    contract_parser.add_argument("source", help="Path to the graph directory")
    contract_parser.add_argument("output", help="Path to the graph directory where the contracted graph will be saved")
    contract_parser.add_argument("elements", nargs="+", help="List of architectural elements to contract")

    args = parser.parse_args()

    try:
        if args.command == "extract":
            handle_extract(args)
        if args.command == "visualize":
            handle_visualise(args)
        if args.command == "union":
            handle_union(args)
        if args.command == "diff":
            handle_diff(args)
        if args.command == "contract":
            handle_contract(args)
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
