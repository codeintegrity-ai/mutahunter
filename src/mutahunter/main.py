import argparse

from mutahunter.core.hunter import MutantHunter


def parse_arguments():
    """
    Parses command-line arguments.
    """
    parser = argparse.ArgumentParser(description="MutantHunter CLI.")
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # Main command arguments
    main_parser = subparsers.add_parser("run", help="Main functionality")

    main_parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="",
    )
    main_parser.add_argument(
        "--test-command",
        type=str,
        default=None,
        required=True,
        help="The command to run the tests. Default is pytest.",
    )
    main_parser.add_argument(
        "--code-coverage-report-path",
        type=str,
        required=False,
        help="The path to the code coverage report file.",
    )
    main_parser.add_argument(
        "--test-file-path",
        type=str,
        required=True,
        help="The test file path to run the tests on.",
    )
    main_parser.add_argument(
        "--exclude-files",
        type=str,
        nargs="+",
        default=[],
        required=False,
        help="Files to exclude from analysis.",
    )
    main_parser.add_argument(
        "--only-mutate-file-paths",
        type=str,
        nargs="+",
        default=[],
        required=False,
        help="Files to ",
    )
    return parser.parse_args()


def determine_language(filename):
    ext = filename.split(".")[-1]
    language_mappings = {
        "py": "python",
        "java": "java",
        "js": "javascript",
        "ts": "typescript",
        "c": "c",
        "cpp": "cpp",
        "rs": "rust",
        "go": "go",
        "php": "php",
        "rb": "ruby",
        "swift": "swift",
        "kt": "kotlin",
    }
    if ext not in language_mappings:
        raise ValueError(f"Unsupported file extension: {ext}")
    return language_mappings[ext]


def run():
    args = parse_arguments()
    config = {
        "model": args.model,
        "code_coverage_report_path": args.code_coverage_report_path,
        "test_command": args.test_command,
        "test_file_path": args.test_file_path,
        "exclude_files": args.exclude_files,
        "only_mutate_file_paths": args.only_mutate_file_paths,
        "language": determine_language(args.test_file_path),
    }
    runner = MutantHunter(config=config)
    runner.run()


if __name__ == "__main__":
    run()
