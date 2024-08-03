import argparse
import sys

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.controller import MutationTestController
from mutahunter.core.coverage_processor import CoverageProcessor
from mutahunter.core.db import MutationDatabase
from mutahunter.core.entities.config import (MutationTestControllerConfig,
                                             UnittestGeneratorConfig)
from mutahunter.core.error_parser import extract_error_message
from mutahunter.core.git_handler import GitHandler
from mutahunter.core.io import FileOperationHandler
from mutahunter.core.llm_mutation_engine import LLMMutationEngine
from mutahunter.core.logger import logger
from mutahunter.core.report import MutantReport
from mutahunter.core.router import LLMRouter
from mutahunter.core.runner import MutantTestRunner
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
        "--diff",
        default=False,
        action="store_true",
        help="Run mutation testing only on modified files in the latest commit.",
    )
    return parser.parse_args()


def create_controller(config: MutationTestControllerConfig) -> MutationTestController:
    coverage_processor = CoverageProcessor(
        code_coverage_report_path=config.code_coverage_report_path,
        coverage_type=config.coverage_type,
    )
    analyzer = Analyzer()
    test_runner = MutantTestRunner(test_command=config.test_command)
    router = LLMRouter(model=config.model, api_base=config.api_base)
    engine = LLMMutationEngine(
        model=config.model,
        router=router,
    )
    db = MutationDatabase()
    mutant_report = MutantReport(db=db)
    file_handler = FileOperationHandler()

    return MutationTestController(
        config=config,
        coverage_processor=coverage_processor,
        analyzer=analyzer,
        test_runner=test_runner,
        router=router,
        engine=engine,
        db=db,
        mutant_report=mutant_report,
        file_handler=file_handler,
    )


def create_unittest_controller(config: UnittestGeneratorConfig) -> UnittestGenerator:
    coverage_processor = CoverageProcessor(
        code_coverage_report_path=config.code_coverage_report_path,
        coverage_type=config.coverage_type,
    )
    analyzer = Analyzer()
    test_runner = MutantTestRunner(test_command=config.test_command)
    router = LLMRouter(model=config.model, api_base=config.api_base)

    db = MutationDatabase()

    mutation_config = MutationTestControllerConfig(
        model=config.model,
        api_base=config.api_base,
        test_command=config.test_command,
        code_coverage_report_path=config.code_coverage_report_path,
        coverage_type=config.coverage_type,
        exclude_files=[],
        only_mutate_file_paths=[config.source_file_path],
        diff=False,
    )
    mutator = create_controller(mutation_config)

    return UnittestGenerator(
        config=config,
        coverage_processor=coverage_processor,
        analyzer=analyzer,
        test_runner=test_runner,
        router=router,
        db=db,
        mutator=mutator,
    )


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
        controller = create_unittest_controller(config)
        controller.run()
    else:
        config = MutationTestControllerConfig(
            model=args.model,
            api_base=args.api_base,
            test_command=args.test_command,
            code_coverage_report_path=args.code_coverage_report_path,
            coverage_type=args.coverage_type,
            exclude_files=args.exclude_files,
            only_mutate_file_paths=args.only_mutate_file_paths,
            diff=args.diff,
        )
        controller = create_controller(config)
        controller.run()


if __name__ == "__main__":
    run()
