import json
import os
import subprocess

import yaml
from grep_ast import filename_to_lang

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.code_merger import merge_code
from mutahunter.core.coverage_processor import CoverageProcessor
from mutahunter.core.entities.config import UnittestGeneratorLineConfig
from mutahunter.core.error_parser import extract_error_message
from mutahunter.core.logger import logger
from mutahunter.core.prompt_factory import TestGenerationPrompt
from mutahunter.core.router import LLMRouter
from mutahunter.core.utils import FileUtils


class UnittestGenLine:
    def __init__(
        self,
        config: UnittestGeneratorLineConfig,
        coverage_processor: CoverageProcessor,
        analyzer: Analyzer,
        router: LLMRouter,
        prompt: TestGenerationPrompt,
    ):
        self.config = config
        self.coverage_processor = coverage_processor
        self.analyzer = analyzer
        self.router = router

        self.failed_tests = []
        self.num = 0
        self.current_line_coverage_rate = 0.0
        self.prompt = prompt

    def run(self) -> None:
        self.coverage_processor.parse_coverage_report()
        initial_line_coverage_rate = (
            self.coverage_processor.calculate_line_coverage_rate_for_file(
                self.config.source_file_path
            )
        )
        self.current_line_coverage_rate = initial_line_coverage_rate
        logger.info(f"Initial Line Coverage: {initial_line_coverage_rate*100:.2f}%")
        self.increase_line_coverage()
        logger.info(
            f"Line Coverage increased from {initial_line_coverage_rate*100:.2f}% to {self.current_line_coverage_rate*100:.2f}%"
        )

    def increase_line_coverage(self):
        attempt = 0
        while (
            self.current_line_coverage_rate < self.config.target_line_coverage_rate
            and attempt < self.config.max_attempts
        ):
            attempt += 1
            test_plan = self.analyze_code()
            response = self.generate_tests(test_plan)
            new_tests = response.get("new_tests", [])
            for new_test in new_tests:
                self.validate_unittest(
                    new_test,
                )
                self.check_line_coverage_increase()
            self.coverage_processor.parse_coverage_report()

    def analyze_code(self):
        system_template = self.prompt.analyzer_system_prompt.render()
        src_code = FileUtils.read_file(self.config.source_file_path)
        language = filename_to_lang(self.config.source_file_path)
        source_file_numbered = FileUtils.number_lines(src_code)
        lines_to_cover = self.coverage_processor.file_lines_not_executed.get(
            self.config.source_file_path, []
        )
        test_code = FileUtils.read_file(self.config.test_file_path)
        user_template = self.prompt.analyzer_user_prompt.render(
            {
                "language": language,
                "source_file_name": self.config.source_file_path,
                "source_file_numbered": source_file_numbered,
                "lines_to_cover": lines_to_cover,
                "test_file_name": self.config.test_file_path,
                "test_file": test_code,
            }
        )
        response, _, _ = self.router.generate_response(
            prompt={"system": system_template, "user": user_template}, streaming=True
        )
        return self.router.extract_yaml_from_response(response)

    def generate_tests(self, test_plan: dict = None) -> dict:
        try:
            source_code = FileUtils.read_file(self.config.source_file_path)
            test_code = FileUtils.read_file(self.config.test_file_path)
            language = filename_to_lang(self.config.source_file_path)

            system_prompt = self.prompt.test_generator_system_prompt.render(
                {
                    "test_framework": test_plan.get("test_framework", ""),
                    "language": language,
                }
            )
            user_prompt = self.prompt.test_generator_user_prompt.render(
                language=language,
                source_code=source_code,
                source_file_name=self.config.source_file_path,
                test_framework=test_plan.get("test_framework", None),
                test_file_name=self.config.test_file_path,
                test_file=test_code,
                test_plan=json.dumps(test_plan, indent=2) if test_plan else None,
                failed_tests=(
                    json.dumps(self.failed_tests, indent=2)
                    if self.failed_tests
                    else None
                ),
            )
            response, _, _ = self.router.generate_response(
                prompt={"system": system_prompt, "user": user_prompt}, streaming=True
            )
            response = self.router.extract_yaml_from_response(response)
            return response
        except Exception as e:
            raise

    def validate_unittest(
        self,
        generated_unittest: dict,
    ) -> None:
        try:

            new_test_code = generated_unittest.get("test_code", "")
            new_imports_code = generated_unittest.get("new_imports_code", "")
            assert (
                new_test_code != ""
            ), "New test code is empty in the generated unittest"
            FileUtils.backup_code(self.config.test_file_path)
            test_file_code = FileUtils.read_file(self.config.test_file_path)
            test_block_nodes = self.analyzer.get_test_nodes(
                source_file_path=self.config.test_file_path
            )
            # import_nodes = self.analyzer.get_import_nodes(
            #     source_file_path=self.config.test_file_path
            # )
            # imports_lists = []
            # for import_node in import_nodes:
            #     imports_lists.append(import_node.text.decode("utf-8"))
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
                    if new_import not in test_file_code:
                        modified_src_code = merge_code(
                            code_to_insert=new_import,
                            org_src_code=modified_src_code,
                            indent_level=0,
                            line_number=1,
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
                    if new_import not in test_file_code:
                        modified_src_code = merge_code(
                            code_to_insert=new_import,
                            org_src_code=modified_src_code,
                            indent_level=0,
                            line_number=1,
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
                if result.returncode == 0:
                    logger.info(f"Test passed for\n{new_test_code}")
                    return
                else:
                    logger.info(f"Test failed for\n{new_test_code}")
                    self._handle_failed_test(result, new_test_code)
                    FileUtils.revert(self.config.test_file_path)
        except Exception as e:
            logger.info(f"Failed to validate unittest: {e}")
            FileUtils.revert(self.config.test_file_path)
            raise

    def check_line_coverage_increase(self):
        self.coverage_processor.parse_coverage_report()
        new_line_coverage_rate = (
            self.coverage_processor.calculate_line_coverage_rate_for_file(
                self.config.source_file_path
            )
        )
        if new_line_coverage_rate > self.current_line_coverage_rate:
            logger.info(
                f"Line coverage increased from {self.current_line_coverage_rate*100:.2f}% to {new_line_coverage_rate*100:.2f}%"
            )
            self.current_line_coverage_rate = new_line_coverage_rate
            return True
        else:
            return False

    def _handle_failed_test(self, result, test_code):
        lang = self.analyzer.get_language_by_filename(self.config.test_file_path)
        error_msg = extract_error_message(lang, result.stdout + result.stderr)
        self.failed_tests.append({"code": test_code, "error_message": error_msg})
