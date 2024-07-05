import os
import subprocess
import time
from typing import Any, Dict, List

from tqdm import tqdm

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.entities.mutant import Mutant
from mutahunter.core.logger import logger
from mutahunter.core.mutator import MutantGenerator
from mutahunter.core.report import MutantReport
from mutahunter.core.router import LLMRouter
from mutahunter.core.runner import TestRunner


class MutantHunter:
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initializes the MutantHunter class with the given configuration.
        """
        self.config: Dict[str, Any] = config
        self.mutants: List[Mutant] = []
        self.mutant_report = MutantReport(config=self.config)
        self.analyzer = Analyzer(self.config)
        self.test_runner = TestRunner()
        self.router = LLMRouter(
            model=self.config["model"], api_base=self.config["api_base"]
        )

    def run(self) -> None:
        """
        Executes the mutation testing process from start to finish.
        """
        try:
            start = time.time()
            logger.info("Starting Coverage Analysis...")
            self.analyzer.dry_run()
            logger.info("🦠 Generating Mutations... 🦠")
            if self.config.get("modified_files_only", False):
                logger.info("🦠 Running mutation testing on modified files... 🦠")
                self.run_mutation_testing_on_modified_files()
            else:
                logger.info("🦠 Running mutation testing on entire codebase... 🦠")
                self.run_mutation_testing()
            logger.info("🎯 Generating Mutation Report... 🎯")
            self.mutant_report.generate_report(self.mutants, self.router.total_cost)
            logger.info(f"Mutation Testing Ended. Took {round(time.time() - start)}s")
        except Exception as e:
            logger.error(
                "Error during mutation testing. Please report this issue.",
                exc_info=True,
            )

    def should_skip_file(self, filename: str) -> bool:
        """
        Determines if a file should be skipped based on various conditions.
        """
        logger.debug(f"Checking if file should be skipped: {filename}")
        if self.config["only_mutate_file_paths"]:
            for file_path in self.config["only_mutate_file_paths"]:
                if not os.path.exists(file_path):
                    logger.error(f"File {file_path} does not exist.")
                    raise FileNotFoundError(f"File {file_path} does not exist.")
            return all(
                file_path != filename
                for file_path in self.config["only_mutate_file_paths"]
            )
        if filename in self.config["exclude_files"]:
            return True

        TEST_FILE_PATTERNS = [
            "test_",
            "_test",
            ".test",
            ".spec",
            ".tests",
            ".Test",
            "Test",
        ]
        should_skip = any(keyword in filename for keyword in TEST_FILE_PATTERNS)
        logger.debug(
            f"File {filename} {'is' if should_skip else 'is not'} identified as a test file."
        )
        return should_skip

    def run_mutation_testing(self) -> None:
        """
        Runs mutation testing on the entire codebase.
        """
        logger.info("Running mutation testing on the entire codebase.")
        all_covered_files = self.analyzer.file_lines_executed.keys()
        logger.info(f"Generating mutations for {len(all_covered_files)} covered files.")

        for covered_file_path in tqdm(all_covered_files):
            if self.should_skip_file(covered_file_path):
                continue
            self.generate_mutations(
                covered_file_path, self.analyzer.file_lines_executed[covered_file_path]
            )

    def run_mutation_testing_on_modified_files(self) -> None:
        """
        Runs mutation testing on modified files.
        """
        logger.info("Running mutation testing on modified files.")
        modified_files = self.get_modified_files()
        logger.info(
            f"Generating mutations for {len(modified_files)} modified files - {','.join(modified_files)}"
        )

        for file_path in tqdm(modified_files):
            if self.should_skip_file(file_path):
                logger.debug(f"Skipping file: {file_path}")
                continue

            modified_lines = self.get_modified_lines(file_path)
            if not modified_lines:
                logger.debug(f"No modified lines found in file: {file_path}")
                continue

            self.generate_mutations(file_path, modified_lines)

    def generate_mutations(self, file_path: str, executed_lines: List[int]) -> None:
        """
        Generates mutations for a single file based on the executed lines.
        """
        logger.info(f"Generating mutations for file: {file_path}.")
        covered_function_blocks, covered_function_block_executed_lines = (
            self.analyzer.get_covered_function_blocks(
                executed_lines=executed_lines,
                source_file_path=file_path,
            )
        )

        logger.info(
            f"Total function blocks to mutate for {file_path}: {len(covered_function_blocks)}"
        )
        if not covered_function_blocks:
            return

        for function_block, executed_lines in zip(
            covered_function_blocks, covered_function_block_executed_lines
        ):
            start_byte = function_block.start_byte
            end_byte = function_block.end_byte
            function_name = function_block.child_by_field_name("name").text.decode(
                "utf8"
            )
            mutant_generator = MutantGenerator(
                config=self.config,
                executed_lines=executed_lines,
                cov_files=list(self.analyzer.file_lines_executed.keys()),
                source_file_path=file_path,
                function_name=function_name,
                start_byte=start_byte,
                end_byte=end_byte,
                router=self.router,
            )
            for mutant_data in mutant_generator.generate():
                self.process_mutant(mutant_data, file_path, start_byte, end_byte)

    def process_mutant(
        self,
        mutant_data: Dict[str, Any],
        source_file_path: str,
        start_byte: int,
        end_byte: int,
    ) -> None:
        """
        Processes a single mutant data dictionary.
        """
        mutant = Mutant(
            id=str(len(self.mutants) + 1),
            source_path=source_file_path,
            mutant_code=mutant_data["mutant_code"],
            type=mutant_data["type"],
            description=mutant_data["description"],
        )
        mutant_path = self.prepare_mutant_file(mutant, start_byte, end_byte)

        if mutant_path:  # Only run tests if the mutant file is prepared successfully
            mutant.mutant_path = mutant_path
            result = self.run_test(
                {
                    "module_path": source_file_path,
                    "replacement_module_path": mutant_path,
                    "test_command": self.config["test_command"],
                }
            )
            self.process_test_result(result, mutant)
        else:
            mutant.status = "COMPILE_ERROR"

        self.mutants.append(mutant)

    def prepare_mutant_file(
        self, mutant: Mutant, start_byte: int, end_byte: int
    ) -> str:
        """
        Prepares the mutant file for testing.
        """
        mutant_file_name = f"{mutant.id}_{os.path.basename(mutant.source_path)}"
        mutant_path = os.path.join(
            os.getcwd(), f"logs/_latest/mutants/{mutant_file_name}"
        )
        logger.debug(f"Preparing mutant file: {mutant_path}")

        with open(mutant.source_path, "rb") as f:
            source_code = f.read()

        modified_byte_code = (
            source_code[:start_byte]
            + bytes(mutant.mutant_code, "utf-8")
            + source_code[end_byte:]
        )

        if self.analyzer.check_syntax(
            source_file_path=mutant.source_path,
            source_code=modified_byte_code.decode("utf-8"),
        ):
            with open(mutant_path, "wb") as f:
                f.write(modified_byte_code)
            logger.info(f"Mutant file prepared: {mutant_path}")
            return mutant_path
        else:
            logger.error(f"Syntax error in mutant code for file: {mutant.source_path}")
            return ""

    def run_test(self, params: Dict[str, str]) -> Any:
        """
        Runs the test command on the given parameters.
        """
        logger.info(
            f"Running test command: {params['test_command']} for mutant file: {params['replacement_module_path']}"
        )
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
            error_output = result.stderr + result.stdout.lower()
            mutant.error_msg = error_output
            mutant.status = "KILLED"
        elif result.returncode == 2:
            logger.info(f"⏱️ Mutant {mutant.id} timed out ⏱️\n")
            mutant.error_msg = result.stderr
            mutant.status = "TIMEOUT"
        else:
            error_output = result.stderr + result.stdout
            logger.info(f"🔧 Mutant {mutant.id} caused a compile error 🔧\n")
            mutant.error_msg = error_output
            mutant.status = "COMPILE_ERROR"

    def get_modified_files(self) -> List[str]:
        """
        Identifies the files that were modified based on the current context (PR stage or local development).

        Returns:
            List[str]: A list of modified file paths.
        """
        try:
            # Detect if there are any unstaged changes
            unstaged_changes = (
                subprocess.check_output(["git", "diff", "--name-only"])
                .decode("utf-8")
                .splitlines()
            )

            if unstaged_changes:
                # Local development: Compare unstaged changes to the current commit
                modified_files = (
                    subprocess.check_output(["git", "diff", "--name-only", "HEAD"])
                    .decode("utf-8")
                    .splitlines()
                )
            else:
                try:
                    # PR stage: Compare the latest commit to the previous head
                    modified_files = (
                        subprocess.check_output(
                            ["git", "diff", "--name-only", "HEAD^..HEAD"]
                        )
                        .decode("utf-8")
                        .splitlines()
                    )
                except subprocess.CalledProcessError as e:
                    if "ambiguous argument 'HEAD^'" in e.stderr.decode("utf-8"):
                        logger.warning(
                            "No previous commit found. Using initial commit for diff."
                        )
                        modified_files = (
                            subprocess.check_output(
                                ["git", "diff", "--name-only", "HEAD"]
                            )
                            .decode("utf-8")
                            .splitlines()
                        )
                    else:
                        raise
            # Get the list of covered files
            covered_files = list(self.analyzer.file_lines_executed.keys())
            # Filter out files not in the line coverage report
            modified_files = [
                file_path for file_path in modified_files if file_path in covered_files
            ]
            logger.info(f"Modified files: {modified_files}")
            return modified_files
        except subprocess.CalledProcessError as e:
            logger.error(f"Error identifying modified files: {e}")
            return []

    def get_modified_lines(self, file_path: str) -> List[int]:
        """
        Identifies the lines that were modified in the latest commit for a given file.

        Args:
            file_path (str): The path to the file.

            Returns:
                List[int]: A list of modified line numbers.
        """
        try:
            # Detect if there are any unstaged changes
            unstaged_changes = (
                subprocess.check_output(["git", "diff", "--name-only"])
                .decode("utf-8")
                .splitlines()
            )

            if unstaged_changes:
                # Local development: Compare unstaged changes to the current commit
                diff_output = (
                    subprocess.check_output(["git", "diff", "-U0", file_path])
                    .decode("utf-8")
                    .splitlines()
                )
            else:
                try:
                    # PR stage: Compare the latest commit to the previous head
                    diff_output = (
                        subprocess.check_output(
                            ["git", "diff", "-U0", "HEAD^..HEAD", file_path]
                        )
                        .decode("utf-8")
                        .splitlines()
                    )
                except subprocess.CalledProcessError as e:
                    if "ambiguous argument 'HEAD^'" in e.stderr.decode("utf-8"):
                        logger.warning(
                            "No previous commit found. Using initial commit for diff."
                        )
                        diff_output = (
                            subprocess.check_output(
                                ["git", "diff", "-U0", "HEAD", file_path]
                            )
                            .decode("utf-8")
                            .splitlines()
                        )
                    else:
                        raise

            modified_lines = []
            for line in diff_output:
                if line.startswith("@@"):
                    # Extract line numbers from the diff header
                    parts = line.split()
                    line_info = parts[2]  # e.g., "+5,7"
                    start_line = int(line_info.split(",")[0][1:])
                    line_count = int(line_info.split(",")[1]) if "," in line_info else 1
                    modified_lines.extend(range(start_line, start_line + line_count))
            logger.info(f"Modified lines in file {file_path}: {modified_lines}")
            return modified_lines

        except subprocess.CalledProcessError as e:
            logger.error(f"Error identifying modified lines in {file_path}: {e}")
            return []
