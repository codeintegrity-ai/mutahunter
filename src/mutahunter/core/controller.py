import json
import time
from subprocess import CompletedProcess
from typing import Any, Dict, List

from tqdm import tqdm

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.entities.config import MutationTestControllerConfig
from mutahunter.core.exceptions import (
    MutantKilledError,
    MutantSurvivedError,
    MutationTestingError,
    ReportGenerationError,
    UnexpectedTestResultError,
)
from mutahunter.core.io import FileOperationHandler
from mutahunter.core.llm_mutation_engine import LLMMutationEngine
from mutahunter.core.logger import logger
from mutahunter.core.prompt_factory import MutationTestingPrompt
from mutahunter.core.report import MutantReport
from mutahunter.core.router import LLMRouter
from mutahunter.core.runner import MutantTestRunner


class MutationTestController:
    def __init__(
        self,
        config: MutationTestControllerConfig,
        analyzer: Analyzer,
        test_runner: MutantTestRunner,
        router: LLMRouter,
        engine: LLMMutationEngine,
        mutant_report: MutantReport,
        file_handler: FileOperationHandler,
        prompt: MutationTestingPrompt,
    ) -> None:
        self.config = config
        self.analyzer = analyzer
        self.test_runner = test_runner
        self.router = router
        self.engine = engine
        self.mutant_report = mutant_report
        self.file_handler = file_handler
        self.prompt = prompt

        # mutant details
        self.survived_mutants = 0
        self.killed_mutants = 0
        self.compile_error_mutants = 0
        self.timeout_mutants = 0

    def run(self) -> None:
        start = time.time()
        try:
            self.test_runner.dry_run()
            self.run_mutation_testing()
        except MutationTestingError as e:
            logger.error(f"Mutation testing failed: {str(e)}")
        try:
            # implement mutation coverage. killed / total mutants
            mutation_coverage = self.killed_mutants / (
                self.survived_mutants + self.killed_mutants
            )
            self.mutant_report.generate_report(
                total_cost=self.router.total_cost,
                mutation_coverage=mutation_coverage,
                killed_mutants=self.killed_mutants,
                survived_mutants=self.survived_mutants,
                compile_error_mutants=self.compile_error_mutants,
                timeout_mutants=self.timeout_mutants,
            )
        except ReportGenerationError as e:
            logger.error(f"Report generation failed: {str(e)}")
        logger.info(f"Mutation Testing Ended. Took {round(time.time() - start)}s")



    def run_mutation_testing(self) -> None:
        mutations = self.engine.generate(
            source_file_path=self.config.source_path,
        )["mutants"]
        mutants = self.process_mutations(mutations)
        return mutants

    def process_mutations(
        self, mutations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        for mutant_data in mutations:
            mutant_data["source_path"] = self.config.source_path
            try:
                mutant_path = self.file_handler.prepare_mutant_file(
                    mutant_data, self.config.source_path
                )
                logger.debug(f"Mutant file prepared: {mutant_path}")
                mutant_data["mutant_path"] = mutant_path
                self.test_mutant(
                    source_file_path=self.config.source_path, mutant_path=mutant_path
                )
            except MutantSurvivedError as e:
                mutant_data["status"] = "SURVIVED"
                mutant_data["error_msg"] = str(e)
                self.survived_mutants += 1
            except MutantKilledError as e:
                mutant_data["status"] = "KILLED"
                mutant_data["error_msg"] = str(e)
                self.killed_mutants += 1
            except SyntaxError as e:
                logger.error(str(e))
                mutant_data["status"] = "SYNTAX_ERROR"
                mutant_data["error_msg"] = str(e)
                self.compile_error_mutants += 1
            except UnexpectedTestResultError as e:
                logger.error(str(e))
                mutant_data["status"] = "UNEXPECTED_TEST_ERROR"
                mutant_data["error_msg"] = str(e)
                self.unexpected_test_error_mutants += 1
            except Exception as e:
                logger.error(f"Unexpected error processing mutant: {str(e)}")
                mutant_data["status"] = "ERROR"
                mutant_data["error_msg"] = str(e)

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
