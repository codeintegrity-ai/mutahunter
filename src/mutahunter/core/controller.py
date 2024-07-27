import difflib
import os
from typing import Any, Dict, List, Optional
import time
from grep_ast import filename_to_lang
from jinja2 import Template
from tqdm import tqdm
from uuid import uuid4

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.coverage_processor import CoverageProcessor
from mutahunter.core.entities.config import MutationTestControllerConfig
from mutahunter.core.error_parser import extract_error_message
from mutahunter.core.git_handler import GitHandler
from mutahunter.core.llm_mutation_engine import LLMMutationEngine
from mutahunter.core.logger import logger
from mutahunter.core.prompts.mutant_generator import MUTANT_ANALYSIS
from mutahunter.core.report import MutantReport
from mutahunter.core.router import LLMRouter
from mutahunter.core.runner import MutantTestRunner
from mutahunter.core.db import MutationDatabase

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


class MutationTestController:
    def __init__(self, config: MutationTestControllerConfig) -> None:
        self.config = config
        self.logger = logger
        self.coverage_processor = CoverageProcessor(
            code_coverage_report_path=self.config.code_coverage_report_path,
            coverage_type=self.config.coverage_type,
        )
        self.analyzer = Analyzer()
        self.test_runner = MutantTestRunner(test_command=self.config.test_command)
        self.router = LLMRouter(model=self.config.model, api_base=self.config.api_base)
        self.engine = LLMMutationEngine(
            model=self.config.model,
            router=self.router,
        )
        self.db = MutationDatabase()
        self.mutant_report = MutantReport(db=self.db)

    def run(self) -> None:
        try:
            start = time.time()
            self._run_coverage_analysis()
            self._run_mutation_testing()
            self._generate_report()
            # self._run_mutant_analysis()
            self.logger.info(
                f"Mutation Testing Ended. Took {round(time.time() - start)}s"
            )
        except Exception as e:
            logger.error("Error during mutation testing", exc_info=True)
            raise

    def _run_coverage_analysis(self) -> None:
        logger.info("Starting Coverage Analysis...")
        self.test_runner.dry_run()
        self.coverage_processor.parse_coverage_report()

    def _run_mutation_testing(self) -> None:
        if self.config.modified_files_only:
            logger.info("Running mutation testing on modified files...")
            self._run_mutation_testing_on_modified_files()
        else:
            logger.info("Running mutation testing on entire codebase...")
            self._run_mutation_testing_on_all_files()

    def _run_mutation_testing_on_all_files(self) -> None:
        all_covered_files = self.coverage_processor.file_lines_executed.keys()
        for covered_file_path in tqdm(all_covered_files):
            if self._should_skip_file(covered_file_path):
                continue
            executed_lines = self.coverage_processor.file_lines_executed[
                covered_file_path
            ]
            if not executed_lines:
                continue
            mutations = self.engine.generate(
                source_file_path=covered_file_path,
                executed_lines=executed_lines,
                cov_files=list(self.coverage_processor.file_lines_executed.keys()),
            )["mutants"]
            self.process_mutations(mutations, covered_file_path)

    def _run_mutation_testing_on_modified_files(self) -> None:
        modified_files = GitHandler.get_modified_files()
        logger.info(
            f"Generating mutations for {len(modified_files)} modified files - {','.join(modified_files)}"
        )
        for file_path in tqdm(modified_files):
            if self._should_skip_file(file_path):
                logger.debug(f"Skipping file: {file_path}")
                continue
            modified_lines = GitHandler.get_modified_lines(file_path)
            if not modified_lines:
                logger.debug(f"No modified lines found in file: {file_path}")
                continue
            mutations = self.engine.generate(
                source_file_path=file_path,
                executed_lines=modified_lines,
                cov_files=list(self.coverage_processor.file_lines_executed.keys()),
            )["mutants"]
            self.process_mutations(mutations, file_path)

    def _should_skip_file(self, filename: str) -> bool:
        logger.debug(f"Checking if file should be skipped: {filename}")
        if self.config.only_mutate_file_paths:
            for file_path in self.config.only_mutate_file_paths:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File {file_path} does not exist.")
            return all(
                file_path != filename
                for file_path in self.config.only_mutate_file_paths
            )
        if filename in self.config.exclude_files:
            return True
        return any(keyword in filename for keyword in TEST_FILE_PATTERNS)

    def process_mutations(
        self, mutations: List[Dict[str, Any]], source_file_path: str
    ) -> None:
        file_version_id, _, is_new_version = self.db.get_file_version(source_file_path)
        for mutant_data in mutations:
            mutant_data["source_path"] = source_file_path
            mutant_path = self.prepare_mutant_file(mutant_data, source_file_path)

            if mutant_path:
                status, error_msg = self.test_mutant(
                    mutant_data, mutant_path, source_file_path
                )
            else:
                status, error_msg = "COMPILE_ERROR", "Failed to prepare mutant file"
            # Update mutant_data with final status and error message
            mutant_data["status"] = status
            mutant_data["error_msg"] = error_msg

            # Write complete mutant data to database
            self.db.add_mutant(file_version_id, mutant_data)

    def prepare_mutant_file(
        self, mutant_data: Dict[str, Any], source_file_path: str
    ) -> Optional[str]:
        mutant_id = str(uuid4())[:8]
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
        # original_line = mutant_data["original_line"].strip()
        mutated_line = mutant_data["mutated_code"].strip()
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
        self, mutant_data: Dict[str, any], mutant_path: str, source_file_path: str
    ) -> None:
        result = self.run_test(
            {
                "module_path": source_file_path,
                "replacement_module_path": mutant_path,
                "test_command": self.config.test_command,
            }
        )
        status, error_msg = self.process_test_result(result, mutant_data)
        return status, error_msg

    def process_test_result(self, result: Any, mutant_data: Dict[str, Any]):
        if result.returncode == 0:
            self.logger.info(f"🛡️ Mutant survived 🛡️\n")
            return "SURVIVED", ""
        elif result.returncode == 1:
            self.logger.info(f"🗡️ Mutant killed 🗡️\n")
            lang = self.analyzer.get_language_by_filename(mutant_data["source_path"])
            error_output = extract_error_message(lang, result.stderr + result.stdout)
            return "KILLED", error_output
        else:
            error_output = result.stderr + result.stdout
            self.logger.info(f"🔧 Mutant caused a compile error 🔧\n")
            return "COMPILE_ERROR", error_output

    def _generate_report(self) -> None:
        """
        Generates the mutation testing report.
        """
        self.mutant_report.generate_report(
            total_cost=self.router.total_cost,
            line_rate=self.coverage_processor.line_coverage_rate,
        )

    # def _run_mutant_analysis(self) -> None:
    #     """
    #     Runs mutant analysis on the generated mutants.
    #     """
    #     survived_mutants = [m for m in self.mutants if m.status == "SURVIVED"]

    #     source_file_paths = []
    #     for mutant in survived_mutants:
    #         if mutant.source_path not in source_file_paths:
    #             source_file_paths.append(mutant.source_path)

    #     src_code_list = []
    #     for file_path in source_file_paths:
    #         with open(file_path, "r", encoding="utf-8") as f:
    #             src_code = f.read()
    #         src_code_list.append(
    #             f"## Source File: {file_path}\n```{filename_to_lang(file_path)}\n{src_code}\n```"
    #         )

    #     prompt = {
    #         "system": "",
    #         "user": Template(MUTANT_ANALYSIS).render(
    #             source_code="\n".join(src_code_list),
    #             surviving_mutants=survived_mutants,
    #         ),
    #     }
    #     mode_response, _, _ = self.router.generate_response(
    #         prompt=prompt, streaming=False
    #     )
    #     with open("logs/_latest/mutant_analysis.md", "w") as f:
    #         f.write(mode_response)
