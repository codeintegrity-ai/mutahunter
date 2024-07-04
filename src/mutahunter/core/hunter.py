import os
import time
from typing import Any, Dict, Generator, List

from tqdm import tqdm

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.entities.mutant import Mutant
from mutahunter.core.logger import logger
from mutahunter.core.mutator import MutantGenerator
from mutahunter.core.report import MutantReport
from mutahunter.core.runner import TestRunner


class MutantHunter:
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initializes the MutantHunter class with the given configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing various settings.
                - model (str): LLM model to use for mutation testing.
                - api_base (str): Base URL for self-hosted LLM models.
                - test_command (str): Command to run the tests.
                - code_coverage_report_path (Optional[str]): Path to the code coverage report file.
                - exclude_files (List[str]): List of files to exclude from analysis.
                - only_mutate_file_paths (List[str]): List of specific files to mutate.
        """
        self.config: Dict[str, Any] = config
        self.mutants: List[Mutant] = []
        self.mutant_report = MutantReport(config=self.config)
        self.analyzer = Analyzer(self.config)
        self.test_runner = TestRunner()

    def run(self) -> None:
        """
        Executes the mutation testing process from start to finish.
        """
        try:
            start = time.time()
            logger.info("Starting Coverage Analysis...")
            self.analyzer.dry_run()
            logger.info("🦠 Generating Mutations... 🦠")
            self.run_mutation_testing()
            logger.info("🎯 Generating Mutation Report... 🎯")
            self.mutant_report.generate_report(self.mutants)
            logger.info(f"Mutation Testing Ended. Took {round(time.time() - start)}s")
        except Exception as e:
            import traceback

            print(traceback.format_exc())
            logger.error(
                f"Error during mutation testing. Please report this issue. {e}"
            )

    def should_skip_file(self, filename: str) -> bool:
        """
        Determines if a file should be skipped based on various conditions.

        Args:
            filename (str): The filename to check.

        Returns:
            bool: True if the file should be skipped, False otherwise.
        """
        if self.config["only_mutate_file_paths"]:
            # NOTE: Check if the file exists before proceeding.
            for file_path in self.config["only_mutate_file_paths"]:
                if not os.path.exists(file_path):
                    logger.error(f"File {file_path} does not exist.")
                    raise FileNotFoundError(f"File {file_path} does not exist.")
            # NOTE: Only mutate the files specified in the config.
            return all(
                file_path != filename
                for file_path in self.config["only_mutate_file_paths"]
            )
        if filename in self.config["exclude_files"]:
            return True
        test_keywords = ["test/", "tests/", "test_", "_test", ".test"]
        return any(keyword in filename for keyword in test_keywords)

    def generate_mutations(self) -> Generator[Dict[str, Any], None, None]:
        """
        Generates mutations for all covered files.

        Yields:
            Generator[Dict[str, Any], None, None]: Dictionary containing mutation details.
        """
        all_covered_files = self.analyzer.file_lines_executed.keys()
        for covered_file_path in tqdm(all_covered_files):
            if self.should_skip_file(covered_file_path):
                continue
            covered_function_blocks, covered_function_block_executed_lines = (
                self.analyzer.get_covered_function_blocks(
                    executed_lines=self.analyzer.file_lines_executed[covered_file_path],
                    source_file_path=covered_file_path,
                )
            )
            logger.info(
                f"Total function blocks to mutate for {covered_file_path}: {len(covered_function_blocks)}"
            )
            if not covered_function_blocks:
                continue

            for function_block, executed_lines in zip(
                covered_function_blocks,
                covered_function_block_executed_lines,
            ):
                start_byte = function_block.start_byte
                end_byte = function_block.end_byte

                mutant_generator = MutantGenerator(
                    config=self.config,
                    executed_lines=executed_lines,
                    cov_files=list(all_covered_files),
                    source_file_path=covered_file_path,
                    start_byte=start_byte,
                    end_byte=end_byte,
                )

                for _, hunk, content in mutant_generator.generate():
                    yield {
                        "source_path": covered_file_path,
                        "start_byte": start_byte,
                        "end_byte": end_byte,
                        "hunk": hunk,
                        "mutant_code_snippet": content,
                    }

    def run_mutation_testing(self) -> None:
        """
        Runs mutation testing on generated mutants.
        """
        for mutant_data in self.generate_mutations():
            try:
                mutant_id = str(len(self.mutants) + 1)
                mutant_path = self.prepare_mutant_file(
                    mutant_id=mutant_id,
                    source_file_path=mutant_data["source_path"],
                    start_byte=mutant_data["start_byte"],
                    end_byte=mutant_data["end_byte"],
                    mutant_code=mutant_data["mutant_code_snippet"],
                )
                unified_diff = "".join(mutant_data["hunk"])
                mutant = Mutant(
                    id=mutant_id,
                    diff=unified_diff,
                    source_path=mutant_data["source_path"],
                    mutant_path=mutant_path,
                )
                result = self.run_test(
                    {
                        "module_path": mutant_data["source_path"],
                        "replacement_module_path": mutant_path,
                        "test_command": self.config["test_command"],
                    }
                )
                self.process_test_result(result, mutant)
            except Exception as e:
                logger.error(f"Error generating mutant: {e}")

    def prepare_mutant_file(
        self,
        mutant_id: str,
        source_file_path: str,
        start_byte: int,
        end_byte: int,
        mutant_code: str,
    ) -> str:
        """
        Prepares the mutant file for testing.

        Args:
            mutant_id (str): The ID of the mutant.
            source_path (str): The path to the original source file.
            start_byte (int): The start byte position of the mutation.
            end_byte (int): The end byte position of the mutation.
            mutant_code (str): The mutated code snippet.

        Returns:
            str: The path to the mutant file.

        Raises:
            Exception: If the mutant code has syntax errors.
        """
        mutant_file_name = f"{mutant_id}_{os.path.basename(source_file_path)}"
        mutant_path = os.path.join(
            os.getcwd(), f"logs/_latest/mutants/{mutant_file_name}"
        )

        with open(source_file_path, "rb") as f:
            source_code = f.read()

        modified_byte_code = (
            source_code[:start_byte]
            + bytes(mutant_code, "utf-8")
            + source_code[end_byte:]
        )

        if self.analyzer.check_syntax(
            source_file_path=source_file_path,
            source_code=modified_byte_code.decode("utf-8"),
        ):
            with open(mutant_path, "wb") as f:
                f.write(modified_byte_code)
            return mutant_path
        else:
            raise SyntaxError("Mutant code has syntax errors.")

    def run_test(self, params: Dict[str, str]) -> Any:
        """
        Runs the test command on the given parameters.

        Args:
            params (Dict[str, str]): Dictionary containing test command parameters.

        Returns:
            Any: The result of the test command execution.
        """
        return self.test_runner.run_test(params)

    def process_test_result(self, result: Any, mutant: Mutant) -> None:
        """
        Processes the result of a test run.

        Args:
            result (Any): The result of the test command execution.
            mutant (Mutant): The mutant being tested.
        """
        if result.returncode == 0:
            logger.info(f"🛡️ Mutant {mutant.id} survived 🛡️\n")
            mutant.status = "SURVIVED"
        elif result.returncode == 1:
            logger.info(f"🗡️ Mutant {mutant.id} killed 🗡️\n")
            mutant.error_msg = result.stderr + result.stdout
            mutant.status = "KILLED"
        else:
            logger.error(f"Mutant {mutant.id} failed to run tests.")
            return
        self.mutants.append(mutant)

    # def _parse_stderr(self, log: str) -> None:
    #     """
    #     Parses the stderr output to extract the error message.

    #     Args:
    #         stderr (str): The stderr output.
    #     """
    #     import re

    #     # Define keywords for different programming languages
    #     keywords = [
    #         # Java JUnit
    #         "[ERROR] Tests run:",
    #         # Python pytest
    #         "FAILURES",
    #         # Go testing
    #         "--- FAIL:",
    #         # Rust testing
    #         "---- stdout ----",
    #     ]
    #     matches = []

    #     lines = log.split("\n")
    #     for i, line in enumerate(lines):
    #         for keyword in keywords:
    #             if keyword in line:
    #                 matches.extend(lines[i:])
    #                 return " ".join(matches)
    #     return log
