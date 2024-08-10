import json
import os
import subprocess

import yaml
from grep_ast import filename_to_lang
from jinja2 import Template

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.code_merger import merge_code
from mutahunter.core.controller import MutationTestController
from mutahunter.core.coverage_processor import CoverageProcessor
from mutahunter.core.db import MutationDatabase
from mutahunter.core.entities.config import UnittestGeneratorMutationConfig
from mutahunter.core.error_parser import extract_error_message
from mutahunter.core.logger import logger
from mutahunter.core.prompt_factory import TestGenerationWithMutationPrompt
from mutahunter.core.router import LLMRouter
from mutahunter.core.runner import MutantTestRunner
from mutahunter.core.utils import FileUtils


class UnittestGenMutation:
    def __init__(
        self,
        config: UnittestGeneratorMutationConfig,
        coverage_processor: CoverageProcessor,
        analyzer: Analyzer,
        test_runner: MutantTestRunner,
        router: LLMRouter,
        db: MutationDatabase,
        mutator: MutationTestController,
        prompt: TestGenerationWithMutationPrompt,
    ):
        self.config = config
        self.db = db
        self.coverage_processor = coverage_processor
        self.analyzer = analyzer
        self.test_runner = test_runner
        self.router = router
        self.mutator = mutator
        self.prompt = prompt

        self.failed_unit_tests = []
        self.weak_unit_tests = []

        self.num = 0

    def run(self) -> None:
        self.coverage_processor.parse_coverage_report()
        # self.mutator.run()
        self.latest_run_id = self.db.get_latest_run_id()
        self.latest_run_id = 1
        data = self.db.get_mutant_summary(self.latest_run_id)
        logger.info(f"Data: {data}")
        initial_mutation_coverage_rate = data["mutation_coverage"]
        logger.info(
            f"Initial Mutation Coverage: {initial_mutation_coverage_rate*100:.2f}%"
        )
        self.increase_mutation_coverage()
        data = self.db.get_mutant_summary(self.latest_run_id)
        final_mutation_coverage_rate = data["mutation_coverage"]
        logger.info(
            f"Mutation Coverage increased from {initial_mutation_coverage_rate*100:.2f}% to {final_mutation_coverage_rate*100:.2f}%"
        )

    def increase_mutation_coverage(self):
        attempt = 0
        data = self.db.get_mutant_summary(self.latest_run_id)
        mutation_coverage_rate = data["mutation_coverage"]
        while (
            mutation_coverage_rate < self.config.target_mutation_coverage_rate
            and attempt < self.config.max_attempts
        ):
            attempt += 1
            response = self.generate_unit_tests()
            test_cases = response.get("test_cases", [])
            for test_case in test_cases:
                self.validate_unittest(
                    test_case,
                )
            logger.info(f"Mutation coverage rate: {mutation_coverage_rate*100:.2f}%")

    def generate_unit_tests(self) -> None:
        source_code = FileUtils.read_file(self.config.source_file_path)
        language = filename_to_lang(self.config.source_file_path)
        # filter survived mutants
        survived_mutants = self.db.get_survived_mutants_by_run_id(
            run_id=self.latest_run_id
        )

        if not survived_mutants:
            raise Exception("No survived mutants found")

        system_prompt = self.prompt.test_generator_system_prompt.render(
            {
                "language": language,
            }
        )
        user_prompt = self.prompt.test_generator_user_prompt.render(
            language=language,
            source_file_name=self.config.source_file_path,
            source_code=source_code,
            test_file_name=self.config.test_file_path,
            test_file=FileUtils.read_file(self.config.test_file_path),
            survived_mutants=json.dumps(
                survived_mutants,
                indent=2,
            ),
            weak_tests=(
                {json.dumps(self.weak_unit_tests, indent=2)}
                if self.weak_unit_tests
                else None
            ),
            failed_test=(
                json.dumps(self.failed_unit_tests, indent=2)
                if self.failed_unit_tests
                else None
            ),
        )
        response, _, _ = self.router.generate_response(
            prompt={"system": system_prompt, "user": user_prompt}, streaming=True
        )
        return self.router.extract_yaml_from_response(response)

    def validate_unittest(
        self,
        generated_unittest: dict,
    ) -> None:
        try:
            new_test_code = generated_unittest.get("test_code", "")
            new_imports_code = generated_unittest.get("new_imports_code", "")
            mutant_id = generated_unittest.get("mutant_id", None)
            # check if mutant id is present
            assert (
                mutant_id is not None
            ), "Mutant id is not present in the generated unittest"
            # check if new_test_code is not empty string
            assert (
                new_test_code != ""
            ), "New test code is empty in the generated unittest"

            # print("NEW TEST CODE:", new_test_code)
            # print("NEW IMPORTS CODE:", new_imports_code)

            FileUtils.backup_code(self.config.test_file_path)
            test_file_code = FileUtils.read_file(self.config.test_file_path)
            test_block_nodes = self.analyzer.get_test_nodes(
                source_file_path=self.config.test_file_path
            )
            # get last test block node
            if len(test_block_nodes) > 0:
                last_test_block_node = test_block_nodes[-1]

                indent_level = last_test_block_node.start_point[1]
                line_number = last_test_block_node.end_point[0] + 1

                modified_src_code = merge_code(
                    code_to_insert=new_test_code,
                    org_src_code=test_file_code,
                    indent_level=indent_level,
                    line_number=line_number,
                )
                for new_import in new_imports_code.splitlines():
                    modified_src_code = merge_code(
                        code_to_insert=new_import,
                        org_src_code=modified_src_code,
                        indent_level=0,
                        line_number=0,
                    )
            else:
                # TODO:// Find a better way to handle this case
                modified_src_code = merge_code(
                    code_to_insert=new_test_code,
                    org_src_code=test_file_code,
                    indent_level=0,
                    line_number=-1,
                )
                for new_import in new_imports_code.splitlines():
                    modified_src_code = merge_code(
                        code_to_insert=new_import,
                        org_src_code=modified_src_code,
                        indent_level=0,
                        line_number=0,
                    )
            if self.analyzer.check_syntax(
                self.config.test_file_path, modified_src_code
            ):
                with open(self.config.test_file_path, "w") as file:
                    file.write(modified_src_code)
                result = subprocess.run(
                    self.config.test_command.split(),
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd(),
                )
                # print("result:", result)
                if result.returncode == 0:
                    self.coverage_processor.parse_coverage_report()
                    if self.check_mutant_coverage_increase(mutant_id, new_test_code):
                        logger.info(
                            f"Test passed and increased mutation cov:\n{new_test_code}"
                        )
                        return True
                    else:
                        logger.info(
                            f"Test passed but failed to increase mutation cov for\n{new_test_code}"
                        )
                else:
                    logger.info(f"Test failed for\n{new_test_code}")
                    self._handle_failed_test(result, new_test_code)
            raise Exception("Failed to validate unittest")
        except Exception as e:
            logger.info(f"Failed to validate unittest: {e}")
            FileUtils.revert(self.config.test_file_path)
            raise
        else:
            FileUtils.revert(self.config.test_file_path)
            return False

    def check_mutant_coverage_increase(self, mutant_id, test_code):
        runner = MutantTestRunner(test_command=self.config.test_command)
        mutants = self.db.get_survived_mutants_by_run_id(run_id=self.latest_run_id)
        logger.info(f"Mutants: {json.dumps(mutants, indent=2)}")

        for mutant in mutants:
            if int(mutant["id"]) == int(mutant_id):
                logger.info(f"Mutant {mutant['id']} selected for testing")
                logger.info(f"source file path: {self.config.source_file_path}")
                logger.info(f"replacement module path: {mutant['mutant_path']}")
                logger.info(f"test command: {self.config.test_command}")
                result = runner.run_test(
                    {
                        "module_path": self.config.source_file_path,
                        "replacement_module_path": mutant["mutant_path"],
                        "test_command": self.config.test_command,
                    }
                )
                if result.returncode == 0:
                    logger.info(f"Mutant {mutant['id']} survived")
                    self.weak_unit_tests.append(
                        {
                            "code": test_code,
                            "survived_mutant_id": f"Mutant {mutant['id']} not killed",
                        }
                    )
                else:
                    logger.info(f"Mutant {mutant['id']} killed")
                    self.db.update_mutant_status(mutant["id"], "KILLED")
                    return True
            else:
                logger.info(
                    f"Mutant {mutant['id']} not selected for testing. Generated mutant id: {mutant_id}"
                )
        return False

    def _handle_failed_test(self, result, test_code):
        lang = self.analyzer.get_language_by_filename(self.config.test_file_path)
        error_msg = extract_error_message(lang, result.stdout + result.stderr)
        self.failed_unit_tests.append({"code": test_code, "error_message": error_msg})
