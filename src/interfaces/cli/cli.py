import argparse
from interfaces.cli.handlers import handle_extract, handle_union, handle_visualise


def main():
    parser = argparse.ArgumentParser(description="Pyflow CLI Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Парсер для команды extract
    extract_parser = subparsers.add_parser("extract", help="Extract data from a directory or Git repository")
    extract_parser.add_argument("source", help="Path to source directory or Git repository URL")
    extract_parser.add_argument("-o",
                                "--output-dir",
                                default=None,
                                help="Output directory (default: current directory)")
    
    # Парсер для команды union
    union_parser = subparsers.add_parser("union", help="Union graph and additional elements")
    union_parser.add_argument("source", help="Path to source directory with project graphs")
    union_parser.add_argument("graph", help="Graph name from a directory with project graphs")

    # Парсер для команды visualize
    visualise_parser = subparsers.add_parser("visualize", help="Мisualize saved dependency graph")
    visualise_parser.add_argument("source", help="Path to saved graph file (.json/.graphml)")
    visualise_parser.add_argument("-m",
                                  "--mode",
                                  choices=["basic", "union"],
                                  default="basic",
                                  help="Visualization mode(basic, union)")

    args = parser.parse_args()

    try:
        if args.command == "extract":
            handle_extract(args)
        if args.command == "visualize":
            handle_visualise(args)
        if args.command == "union":
            handle_union(args)
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
