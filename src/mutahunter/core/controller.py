import os
import time
from subprocess import CompletedProcess
from typing import Any, Dict, List, Optional
from uuid import uuid4

from tqdm import tqdm

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.coverage_processor import CoverageProcessor
from mutahunter.core.db import MutationDatabase
from mutahunter.core.entities.config import MutationTestControllerConfig
from mutahunter.core.error_parser import extract_error_message
from mutahunter.core.exceptions import (CoverageAnalysisError,
                                        MutantKilledError, MutantSurvivedError,
                                        MutationTestingError,
                                        ReportGenerationError,
                                        UnexpectedTestResultError)
from mutahunter.core.git_handler import GitHandler
from mutahunter.core.io import FileOperationHandler
from mutahunter.core.llm_mutation_engine import LLMMutationEngine
from mutahunter.core.logger import logger
from mutahunter.core.prompts.mutant_generator import MUTANT_ANALYSIS
from mutahunter.core.report import MutantReport
from mutahunter.core.router import LLMRouter
from mutahunter.core.runner import MutantTestRunner


class MutationTestController:
    def __init__(
        self,
        config: MutationTestControllerConfig,
        coverage_processor: CoverageProcessor,
        analyzer: Analyzer,
        test_runner: MutantTestRunner,
        router: LLMRouter,
        engine: LLMMutationEngine,
        db: MutationDatabase,
        mutant_report: MutantReport,
        file_handler: FileOperationHandler,
    ) -> None:
        self.config = config
        self.coverage_processor = coverage_processor
        self.analyzer = analyzer
        self.test_runner = test_runner
        self.router = router
        self.engine = engine
        self.db = db
        self.mutant_report = mutant_report
        self.file_handler = file_handler

    def run(self) -> None:
        start = time.time()
        try:
            self.run_coverage_analysis()
        except CoverageAnalysisError as e:
            logger.error(f"Coverage analysis failed: {str(e)}")
            return
        try:
            self.run_mutation_testing()
        except MutationTestingError as e:
            logger.error(f"Mutation testing failed: {str(e)}")
        try:
            self.generate_report()
        except ReportGenerationError as e:
            logger.error(f"Report generation failed: {str(e)}")
        # self._run_mutant_analysis()
        logger.info(f"Mutation Testing Ended. Took {round(time.time() - start)}s")

    def run_coverage_analysis(self) -> None:

        logger.info("Starting Coverage Analysis...")
        try:
            self.test_runner.dry_run()
            self.coverage_processor.parse_coverage_report()
        except Exception as e:
            raise CoverageAnalysisError(
                f"Failed to complete coverage analysis: {str(e)}"
            )

    def run_mutation_testing(self) -> None:
        try:
            if self.config.diff:
                logger.info("Running mutation testing on modified files...")
                self.run_mutation_testing_diff()
            else:
                logger.info("Running mutation testing on entire codebase...")
                self.run_mutation_testing_all()
        except Exception as e:
            raise MutationTestingError(f"Failed to complete mutation testing: {str(e)}")

    def run_mutation_testing_all(self) -> None:
        all_covered_files = self.coverage_processor.file_lines_executed.keys()
        for covered_file_path in tqdm(all_covered_files):
            if FileOperationHandler.should_skip_file(
                covered_file_path, self.config.exclude_files
            ):
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

    def run_mutation_testing_diff(self) -> None:
        modified_files = GitHandler.get_modified_files(
            covered_files=self.coverage_processor.file_lines_executed.keys()
        )
        for file_path in tqdm(modified_files):
            if FileOperationHandler.should_skip_file(
                file_path, self.config.exclude_files
            ):
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

    def process_mutations(
        self, mutations: List[Dict[str, Any]], source_file_path: str
    ) -> None:
        file_version_id, _, is_new_version = self.db.get_file_version(source_file_path)

        if not is_new_version:
            self.db.remove_mutants_by_file_version_id(file_version_id)

        for mutant_data in mutations:
            mutant_data["source_path"] = source_file_path
            try:
                mutant_path = self.file_handler.prepare_mutant_file(
                    mutant_data, source_file_path
                )
                logger.debug(f"Mutant file prepared: {mutant_path}")
                mutant_data["mutant_path"] = mutant_path
                self.test_mutant(
                    source_file_path=source_file_path, mutant_path=mutant_path
                )
            except MutantSurvivedError as e:
                mutant_data["status"] = "SURVIVED"
                mutant_data["error_msg"] = str(e)
            except MutantKilledError as e:
                mutant_data["status"] = "KILLED"
                mutant_data["error_msg"] = str(e)
            except SyntaxError as e:
                logger.error(str(e))
                mutant_data["status"] = "SYNTAX_ERROR"
                mutant_data["error_msg"] = str(e)
            except UnexpectedTestResultError as e:
                logger.error(str(e))
                mutant_data["status"] = "UNEXPECTED_TEST_ERROR"
                mutant_data["error_msg"] = str(e)
            except Exception as e:
                logger.error(f"Unexpected error processing mutant: {str(e)}")
                mutant_data["status"] = "ERROR"
                mutant_data["error_msg"] = str(e)

            # Write complete mutant data to database
            self.db.add_mutant(file_version_id, mutant_data)

    def test_mutant(
        self,
        source_file_path: str,
        mutant_path: str,
    ) -> None:

        params = {
            "module_path": source_file_path,
            "replacement_module_path": mutant_path,
            "test_command": self.config.test_command,
        }
        logger.info(
            f"'{params['test_command']}' - '{params['replacement_module_path']}'"
        )
        result = self.test_runner.run_test(params)
        self.process_test_result(result)

    def process_test_result(self, result: CompletedProcess) -> None:
        if result.returncode == 0:
            logger.info(f"🛡️ Mutant survived 🛡️\n")
            raise MutantSurvivedError("Mutant survived the tests")
        elif result.returncode == 1:
            logger.info(f"🗡️ Mutant killed 🗡️\n")
            raise MutantKilledError("Mutant killed by the tests")
        else:
            error_output = result.stderr + result.stdout
            logger.info(
                f"⚠️ Unexpected test result (return code: {result.returncode}) ⚠️\n"
            )
            raise UnexpectedTestResultError(
                f"Unexpected test result. Return code: {result.returncode}. Error output: {error_output}"
            )

    def generate_report(self) -> None:
        """
        Generates the mutation testing report.
        """
        try:
            self.mutant_report.generate_report(
                total_cost=self.router.total_cost,
                line_rate=self.coverage_processor.line_coverage_rate,
            )
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate report: {str(e)}")

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
