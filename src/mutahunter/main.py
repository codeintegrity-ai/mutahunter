import argparse
import sys

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.controller import MutationTestController
from mutahunter.core.entities.config import (
    MutationTestControllerConfig,
)
from mutahunter.core.io import FileOperationHandler
from mutahunter.core.llm_mutation_engine import LLMMutationEngine
from mutahunter.core.prompt_factory import (
    MutationTestingPromptFactory,
)
from mutahunter.core.report import MutantReport
from mutahunter.core.router import LLMRouter
from mutahunter.core.runner import MutantTestRunner


def add_mutation_testing_subparser(subparsers):
    parser = subparsers.add_parser("run", help="Run the mutation testing process.")
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="The LLM model to use for mutation generation. Default is 'gpt-4o-mini'.",
    )
    parser.add_argument(
        "--source-path",
        type=str,
        default="",
        help="The path to the source code to mutate.",
    )
    parser.add_argument(
        "--test-path",
        type=str,
        default="",
        help="The path to the test code to run.",
    )
    parser.add_argument(
        "--api-base",
        type=str,
        default="",
        help="The base URL for the API if using a self-hosted LLM model.",
    )
    parser.add_argument(
        "--test-command",
        type=str,
        default=None,
        required=True,
        help="The command to run the tests (e.g., 'pytest'). This argument is required.",
    )
    parser.add_argument(
        "--exclude-files",
        type=str,
        nargs="+",
        default=[],
        required=False,
        help="A list of files to exclude from mutation testing. Optional.",
    )


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
    add_mutation_testing_subparser(subparsers)

    return parser.parse_args()


def create_run_mutation_testing_controller(
    args: argparse.Namespace,
) -> MutationTestController:
    config = MutationTestControllerConfig(
        model=args.model,
        api_base=args.api_base,
        test_command=args.test_command,
        exclude_files=args.exclude_files,
        source_path=args.source_path,
        test_path=args.test_path,
    )

    analyzer = Analyzer()
    test_runner = MutantTestRunner(test_command=config.test_command)
    prompt = MutationTestingPromptFactory.get_prompt()
    router = LLMRouter(model=config.model, api_base=config.api_base)
    engine = LLMMutationEngine(model=config.model, router=router, prompt=prompt)
    mutant_report = MutantReport()
    file_handler = FileOperationHandler()

    return MutationTestController(
        config=config,
        analyzer=analyzer,
        test_runner=test_runner,
        router=router,
        engine=engine,
        mutant_report=mutant_report,
        file_handler=file_handler,
        prompt=prompt,
    )


def run():
    args = parse_arguments()
    if args.command == "run":
        controller = create_run_mutation_testing_controller(args)
        controller.run()
        pass
    else:
        print("Invalid command.")
        sys.exit(1)


if __name__ == "__main__":
    run()
