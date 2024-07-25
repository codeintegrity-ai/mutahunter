import argparse
import sys

from mutahunter.core.entities.config import (MutatorConfig,
                                             UnittestGeneratorConfig)
from mutahunter.core.logger import logger
from mutahunter.core.mutator import Mutator
from mutahunter.core.unittest_generator import UnittestGenerator


def parse_arguments():
    """
    Parses command-line arguments for the Mutahunter CLI.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Mutahunter CLI for performing mutation testing."
    )
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # add subparser for test gen
    test_gen_parser = subparsers.add_parser(
        "gen", help="Generate test cases for a given code snippet."
    )
    test_gen_parser.add_argument(
        "--test-file-path",
    )
    test_gen_parser.add_argument(
        "--source-file-path",
    )
    test_gen_parser.add_argument(
        "--code-coverage-report-path",
        type=str,
        required=False,
        help="The path to the code coverage report file. Optional.",
    )
    test_gen_parser.add_argument(
        "--coverage-type",
        type=str,
        default="cobertura",
        required=False,
        choices=["cobertura", "jacoco", "lcov"],
        help="The type of code coverage report to parse. Default is 'cobertura'.",
    )
    test_gen_parser.add_argument(
        "--test-command",
        type=str,
        default=None,
        required=True,
        help="The command to run the tests (e.g., 'pytest'). This argument is required.",
    )
    test_gen_parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="The LLM model to use for mutation generation. Default is 'gpt-4o-mini'.",
    )
    test_gen_parser.add_argument(
        "--api-base",
        type=str,
        default="",
        help="The base URL for the API if using a self-hosted LLM model.",
    )
    test_gen_parser.add_argument(
        "--target-line-coverage-rate",
        type=float,
        default=0.9,
        help="The target line coverage rate. Default is 0.9.",
    )

    test_gen_parser.add_argument(
        "--target-mutation-coverage-rate",
        type=float,
        default=0.9,
        help="The target mutation coverage rate. Default is 0.9.",
    )
    test_gen_parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="The maximum number of attempts to generate a test case. Default is 3.",
    )

    # Main command arguments
    main_parser = subparsers.add_parser("run", help="Run the mutation testing process.")
    main_parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="The LLM model to use for mutation generation. Default is 'gpt-4o-mini'.",
    )
    main_parser.add_argument(
        "--api-base",
        type=str,
        default="",
        help="The base URL for the API if using a self-hosted LLM model.",
    )
    main_parser.add_argument(
        "--test-command",
        type=str,
        default=None,
        required=True,
        help="The command to run the tests (e.g., 'pytest'). This argument is required.",
    )
    main_parser.add_argument(
        "--code-coverage-report-path",
        type=str,
        required=False,
        help="The path to the code coverage report file. Optional.",
    )
    main_parser.add_argument(
        "--coverage-type",
        type=str,
        default="cobertura",
        required=False,
        choices=["cobertura", "jacoco", "lcov"],
        help="The type of code coverage report to parse. Default is 'cobertura'.",
    )
    main_parser.add_argument(
        "--exclude-files",
        type=str,
        nargs="+",
        default=[],
        required=False,
        help="A list of files to exclude from mutation testing. Optional.",
    )
    main_parser.add_argument(
        "--only-mutate-file-paths",
        type=str,
        nargs="+",
        default=[],
        required=False,
        help="A list of specific files to mutate. Optional.",
    )
    main_parser.add_argument(
        "--modified-files-only",
        default=False,
        action="store_true",
        help="Run mutation testing only on modified files in the latest commit.",
    )
    main_parser.add_argument(
        "--extreme",
        default=False,
        action="store_true",
        help="Enable extreme mutation testing mode.",
    )
    return parser.parse_args()


def run():
    """
    Main function to parse arguments and initiate the Mutahunter run process.
    """
    args = parse_arguments()
    command_line_input = " ".join(sys.argv)
    logger.info(f"Command line input: {command_line_input}")
    # distinguish between gen and run commands
    if args.command == "gen":
        config = UnittestGeneratorConfig(
            model=args.model,
            api_base=args.api_base,
            test_file_path=args.test_file_path,
            source_file_path=args.source_file_path,
            test_command=args.test_command,
            code_coverage_report_path=args.code_coverage_report_path,
            coverage_type=args.coverage_type,
            target_line_coverage_rate=args.target_line_coverage_rate,
            target_mutation_coverage_rate=args.target_mutation_coverage_rate,
            max_attempts=args.max_attempts,
        )
        runner = UnittestGenerator(config=config)
        runner.run()
    else:
        config = MutatorConfig(
            model=args.model,
            api_base=args.api_base,
            test_command=args.test_command,
            code_coverage_report_path=args.code_coverage_report_path,
            coverage_type=args.coverage_type,
            exclude_files=args.exclude_files,
            only_mutate_file_paths=args.only_mutate_file_paths,
            modified_files_only=args.modified_files_only,
            extreme=args.extreme,
        )
        runner = Mutator(config=config)
        runner.run()


if __name__ == "__main__":
    run()
