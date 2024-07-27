import difflib
import os
import subprocess
import time
from typing import Any, Dict, List, Optional

from grep_ast import filename_to_lang
from jinja2 import Template
from tqdm import tqdm
import random

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.coverage_processor import CoverageProcessor
from mutahunter.core.entities.config import MutatorConfig
from mutahunter.core.entities.mutant import Mutant
from mutahunter.core.error_parser import extract_error_message
from mutahunter.core.llm_mutation_engine import LLMMutationEngine
from mutahunter.core.logger import logger
from mutahunter.core.prompts.mutant_generator import MUTANT_ANALYSIS
from mutahunter.core.report import MutantReport
from mutahunter.core.router import LLMRouter
from mutahunter.core.runner import TestRunner

TEST_FILE_PATTERNS = [
    "test_",
    "_test",
    ".test",
    ".spec",
    ".tests",
    ".Test",
    "tests/",
    "test/",
]

from typing import List


class LLMBasedMutation:
    def generate_mutations(
        self, hunter: "Mutator", file_path: str, executed_lines: List[int]
    ):
        """
        Generates mutations for a single file based on the executed lines.
        """
        engine = LLMMutationEngine(
            model=hunter.config.model,
            executed_lines=hunter.coverage_processor.file_lines_executed[file_path],
            cov_files=list(hunter.coverage_processor.file_lines_executed.keys()),
            source_file_path=file_path,
            router=hunter.router,
        )
        mutations = engine.generate()["mutants"]
        return mutations


class Mutator:
    def __init__(self, config: MutatorConfig) -> None:
        self.config = config
        self.logger = logger
        self.mutants = []
        self.coverage_processor = CoverageProcessor(
            code_coverage_report_path=self.config.code_coverage_report_path,
            coverage_type=self.config.coverage_type,
        )
        self.analyzer = Analyzer()
        self.mutant_report = MutantReport(extreme=self.config.extreme)
        self.test_runner = TestRunner(test_command=self.config.test_command)
        self.router = LLMRouter(model=self.config.model, api_base=self.config.api_base)
        self.mutation_strategy = LLMBasedMutation()

    def run(self) -> None:
        """
        Executes the mutation testing process from start to finish.
        """
        try:
            start = time.time()
            self.logger.info("Starting Coverage Analysis...")
            self.test_runner.dry_run()
            self.coverage_processor.parse_coverage_report()
            if self.config.modified_files_only:
                self.logger.info("Running mutation testing on modified files...")
                self.run_mutation_testing_on_modified_files()
            else:
                self.logger.info("Running mutation testing on entire codebase...")
                self.run_mutation_testing()

            self.mutant_report.generate_report(
                mutants=self.mutants,
                total_cost=self.router.total_cost,
                line_rate=self.coverage_processor.line_coverage_rate,
            )
            if not self.config.extreme:
                self.run_mutant_analysis()

            self.logger.info(
                f"Mutation Testing Ended. Took {round(time.time() - start)}s"
            )
        except Exception as e:
            self.logger.error(
                "Error during mutation testing. Please report this issue.",
                exc_info=True,
            )

    def should_skip_file(self, filename: str) -> bool:
        """
        Determines if a file should be skipped based on various conditions.
        """
        self.logger.debug(f"Checking if file should be skipped: {filename}")
        if self.config.only_mutate_file_paths:
            for file_path in self.config.only_mutate_file_paths:
                if not os.path.exists(file_path):
                    self.logger.error(f"File {file_path} does not exist.")
                    raise FileNotFoundError(f"File {file_path} does not exist.")
            return all(
                file_path != filename
                for file_path in self.config.only_mutate_file_paths
            )
        if filename in self.config.exclude_files:
            return True

        should_skip = any(keyword in filename for keyword in TEST_FILE_PATTERNS)
        self.logger.info(
            f"File {filename} {'is' if should_skip else 'is not'} identified as a test file."
        )
        return should_skip

    def run_mutation_testing(self) -> None:
        self.logger.info("Running mutation testing on the entire codebase.")
        all_covered_files = self.coverage_processor.file_lines_executed.keys()

        for covered_file_path in tqdm(all_covered_files):
            if self.should_skip_file(covered_file_path):
                continue

            executed_lines = self.coverage_processor.file_lines_executed[
                covered_file_path
            ]
            if not executed_lines:
                continue

            mutations = self.mutation_strategy.generate_mutations(
                self, file_path=covered_file_path, executed_lines=executed_lines
            )
            self.process_mutations(mutations, covered_file_path)

    def run_mutation_testing_on_modified_files(self) -> None:
        """
        Runs mutation testing on modified files.
        """
        self.logger.info("Running mutation testing on modified files.")
        modified_files = self.get_modified_files()
        self.logger.info(
            f"Generating mutations for {len(modified_files)} modified files - {','.join(modified_files)}"
        )

        for file_path in tqdm(modified_files):
            if self.should_skip_file(file_path):
                self.logger.debug(f"Skipping file: {file_path}")
                continue

            modified_lines = self.get_modified_lines(file_path)
            if not modified_lines:
                self.logger.debug(f"No modified lines found in file: {file_path}")
                continue

            self.mutation_strategy.generate_mutations(
                self, file_path=file_path, executed_lines=modified_lines
            )

    def process_mutations(
        self, mutations: List[Dict[str, Any]], source_file_path: str
    ) -> None:
        for mutant_data in mutations:
            mutant = self.create_mutant(mutant_data, source_file_path)
            mutant_path = self.prepare_mutant_file(
                mutant.id, mutant_data, source_file_path
            )

            if mutant_path:
                self.test_mutant(mutant, mutant_path, source_file_path)
            else:
                mutant.status = "COMPILE_ERROR"

            self.mutants.append(mutant)

    def create_mutant(
        self, mutant_data: Dict[str, Any], source_file_path: str
    ) -> Mutant:
        return Mutant(
            id=len(self.mutants) + 1,
            source_path=source_file_path,
            function_name=mutant_data["function_name"],
            line_number=[mutant_data["line_number"]],
            type=mutant_data["type"],
            description=mutant_data["description"],
            original_line=[mutant_data["original_line"]],
            mutated_line=[mutant_data["mutated_line"]],
        )

    def prepare_mutant_file(
        self, mutant_id, mutant_data: Dict[str, Any], source_file_path: str
    ) -> Optional[str]:
        mutant_file_name = f"{mutant_id}_{os.path.basename(source_file_path)}"
        mutant_path = os.path.join(
            os.getcwd(), f"logs/_latest/mutants/{mutant_file_name}"
        )

        with open(source_file_path, "r") as f:
            source_code = f.read()

        applied_mutant = self.apply_mutation(source_code, mutant_data)

        if self.analyzer.check_syntax(
            source_file_path=source_file_path, source_code=applied_mutant
        ):
            with open(mutant_path, "w") as f:
                f.write(applied_mutant)
            self.logger.debug(f"Mutant file prepared: {mutant_path}")
            return mutant_path
        else:
            self.logger.error(
                f"Syntax error in mutant code for file: {source_file_path}"
            )
            return None

    def apply_mutation(self, source_code: str, mutant_data: Dict[str, Any]) -> str:
        src_code_lines = source_code.splitlines(keepends=True)
        original_line = mutant_data["original_line"].strip()
        mutated_line = mutant_data["mutated_line"].strip()
        line_number = mutant_data["line_number"]

        indentation = len(src_code_lines[line_number - 1]) - len(
            src_code_lines[line_number - 1].lstrip()
        )
        src_code_lines[line_number - 1] = " " * indentation + mutated_line + "\n"

        return "".join(src_code_lines)

    def run_test(self, params: Dict[str, str]) -> Any:
        """
        Runs the test command on the given parameters.
        """
        self.logger.info(
            f"'{params['test_command']}' - '{params['replacement_module_path']}'"
        )
        return self.test_runner.run_test(params)

    def test_mutant(
        self, mutant: Mutant, mutant_path: str, source_file_path: str
    ) -> None:
        result = self.run_test(
            {
                "module_path": source_file_path,
                "replacement_module_path": mutant_path,
                "test_command": self.config.test_command,
            }
        )
        self.process_test_result(result, mutant)
        udiff_list = self.get_unified_diff(source_file_path, mutant_path)
        mutant.udiff = "\n".join(udiff_list)

    def get_unified_diff(self, source_file_path: str, mutant_path: str) -> List[str]:
        with open(source_file_path, "r") as file:
            original = file.readlines()
        with open(mutant_path, "r") as file:
            mutant = file.readlines()
        diff = difflib.unified_diff(original, mutant, lineterm="")
        return list(diff)

    def process_test_result(self, result: Any, mutant) -> None:
        """
        Processes the result of a test run.

        Args:
            result (Any): The result of the test command execution.
            mutant (Mutant): The mutant being tested.
        """
        if result.returncode == 0:
            self.logger.info(f"🛡️ Mutant {mutant.id} survived 🛡️\n")
            mutant.status = "SURVIVED"
        elif result.returncode == 1:
            self.logger.info(f"🗡️ Mutant {mutant.id} killed 🗡️\n")
            lang = self.analyzer.get_language_by_filename(mutant.source_path)
            error_output = extract_error_message(lang, result.stderr + result.stdout)
            mutant.error_msg = error_output
            mutant.status = "KILLED"
        else:
            error_output = result.stderr + result.stdout
            self.logger.info(f"🔧 Mutant {mutant.id} caused a compile error 🔧\n")
            mutant.error_msg = error_output
            mutant.status = "COMPILE_ERROR"

    def get_modified_files(self) -> List[str]:
        """
        Identifies the files that were modified based on the current context (PR stage or local development).

        Returns:
            List[str]: A list of modified file paths.
        """
        try:
            unstaged_changes = (
                subprocess.check_output(["git", "diff", "--name-only"])
                .decode("utf-8")
                .splitlines()
            )
            if unstaged_changes:
                modified_files = (
                    subprocess.check_output(["git", "diff", "--name-only", "HEAD"])
                    .decode("utf-8")
                    .splitlines()
                )
            else:
                try:
                    modified_files = (
                        subprocess.check_output(
                            ["git", "diff", "--name-only", "HEAD^..HEAD"]
                        )
                        .decode("utf-8")
                        .splitlines()
                    )
                except subprocess.CalledProcessError as e:
                    if "ambiguous argument 'HEAD^'" in e.stderr.decode("utf-8"):
                        self.logger.warning(
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

            covered_files = list(self.coverage_processor.file_lines_executed.keys())
            modified_files = [
                file_path for file_path in modified_files if file_path in covered_files
            ]
            self.logger.info(f"Modified files: {modified_files}")
            return modified_files
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error identifying modified files: {e}")
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
            unstaged_changes = (
                subprocess.check_output(["git", "diff", "--name-only"])
                .decode("utf-8")
                .splitlines()
            )
            if unstaged_changes:
                diff_output = (
                    subprocess.check_output(["git", "diff", "-U0", file_path])
                    .decode("utf-8")
                    .splitlines()
                )
            else:
                try:
                    diff_output = (
                        subprocess.check_output(
                            ["git", "diff", "-U0", "HEAD^..HEAD", file_path]
                        )
                        .decode("utf-8")
                        .splitlines()
                    )
                except subprocess.CalledProcessError as e:
                    if "ambiguous argument 'HEAD^'" in e.stderr.decode("utf-8"):
                        self.logger.warning(
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
                    parts = line.split()
                    line_info = parts[2]
                    start_line = int(line_info.split(",")[0][1:])
                    line_count = int(line_info.split(",")[1]) if "," in line_info else 1
                    modified_lines.extend(range(start_line, start_line + line_count))
            self.logger.info(f"Modified lines in file {file_path}: {modified_lines}")
            return modified_lines

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error identifying modified lines in {file_path}: {e}")
            return []

    def run_mutant_analysis(self) -> None:
        """
        Runs mutant analysis on the generated mutants.
        """
        survived_mutants = [m for m in self.mutants if m.status == "SURVIVED"]

        source_file_paths = []
        for mutant in survived_mutants:
            if mutant.source_path not in source_file_paths:
                source_file_paths.append(mutant.source_path)

        src_code_list = []
        for file_path in source_file_paths:
            with open(file_path, "r", encoding="utf-8") as f:
                src_code = f.read()
            src_code_list.append(
                f"## Source File: {file_path}\n```{filename_to_lang(file_path)}\n{src_code}\n```"
            )

        prompt = {
            "system": "",
            "user": Template(MUTANT_ANALYSIS).render(
                source_code="\n".join(src_code_list),
                surviving_mutants=survived_mutants,
            ),
        }
        mode_response, _, _ = self.router.generate_response(
            prompt=prompt, streaming=False
        )
        with open("logs/_latest/mutant_analysis.md", "w") as f:
            f.write(mode_response)
