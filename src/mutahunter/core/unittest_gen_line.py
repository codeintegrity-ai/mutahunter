import json
import os
import shutil
import subprocess

import yaml
from grep_ast import filename_to_lang
from jinja2 import Template

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.coverage_processor import CoverageProcessor
from mutahunter.core.entities.config import UnittestGeneratorLineConfig
from mutahunter.core.error_parser import extract_error_message
from mutahunter.core.logger import logger
from mutahunter.core.prompts.unittest_generator import (
    FAILED_TESTS_TEXT,
    LINE_COV_UNITTEST_GENERATOR_USER_PROMPT,
)
from mutahunter.core.router import LLMRouter
from mutahunter.core.utils import FileUtils

SYSTEM_YAML_FIX = """
Based on the error message, the YAML content provided is not in the correct format. Please ensure the YAML content is in the correct format and try again.
"""

USER_YAML_FIX = """
YAML content:
```yaml
{{yaml_content}}
```

Error:
{{error}}

Output must be wrapped in triple backticks and in YAML format:
```yaml
...fix the yaml content here...
```
"""


class UnittestGenLine:
    def __init__(
        self,
        config: UnittestGeneratorLineConfig,
        coverage_processor: CoverageProcessor,
        analyzer: Analyzer,
        router: LLMRouter,
    ):
        self.config = config
        self.coverage_processor = coverage_processor
        self.analyzer = analyzer
        self.router = router

        self.failed_tests = []

        self.num = 0

        self.current_line_coverage_rate = 0.0

    def run(self) -> None:
        self.coverage_processor.parse_coverage_report()
        initial_line_coverage_rate = self.coverage_processor.get_line_coverage_for_file(
            self.config.source_file_path
        )
        self.current_line_coverage_rate = initial_line_coverage_rate

        logger.info(f"Initial Line Coverage: {initial_line_coverage_rate*100:.2f}%")
        self.increase_line_coverage()
        # logger.info(
        #     f"Line coverage increased from {initial_line_coverage_rate*100:.2f}% to {self.current_line_coverage_rate*100:.2f}%"
        # )

    def increase_line_coverage(self):
        attempt = 0
        while (
            self.current_line_coverage_rate < self.config.target_line_coverage_rate
            and attempt < self.config.max_attempts
        ):
            attempt += 1
            response = self.generate_tests()
            self._process_generated_tests(response)
            self.coverage_processor.parse_coverage_report()

    def generate_tests(self):
        try:
            source_code = FileUtils.read_file(self.config.source_file_path)
            test_code = FileUtils.read_file(self.config.test_file_path)
            source_code_with_lines = self._number_lines(source_code)
            language = filename_to_lang(self.config.source_file_path)
            lines_to_cover = self.coverage_processor.file_lines_not_executed.get(
                self.config.source_file_path, []
            )
            user_template = Template(LINE_COV_UNITTEST_GENERATOR_USER_PROMPT).render(
                language=language,
                source_file_numbered=source_code_with_lines,
                source_file_name=self.config.source_file_path,
                test_file_name=self.config.test_file_path,
                test_file=test_code,
                lines_to_cover=lines_to_cover,
                failed_tests_section=(
                    Template(FAILED_TESTS_TEXT).render(
                        failed_test_runs=json.dumps(self.failed_tests[:-5], indent=2)
                    )
                    if self.failed_tests
                    else ""
                ),
            )
            response, _, _ = self.router.generate_response(
                prompt={"system": "", "user": user_template}, streaming=True
            )
            output = self.extract_response(response)
            self._save_yaml(output, "line")
            return output
        except Exception as e:
            raise

    def _save_yaml(self, data, type):
        if not os.path.exists("logs/_latest"):
            os.makedirs("logs/_latest")
        if not os.path.exists("logs/_latest/unittest"):
            os.makedirs("logs/_latest/unittest")
        if not os.path.exists(f"logs/_latest/unittest/{type}"):
            os.makedirs(f"logs/_latest/unittest/{type}")
        output = f"unittest_{self.num}.yaml"
        with open(os.path.join(f"logs/_latest/unittest/{type}", output), "w") as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)

    def _process_generated_tests(self, response: dict) -> list:
        new_tests = response.get("new_tests", [])
        insertion_point_marker = response.get("insertion_point_marker", {})

        for generated_unittest in new_tests:
            self.validate_unittest(
                generated_unittest,
                insertion_point_marker,
            )

    def validate_unittest(
        self,
        generated_unittest: dict,
        insertion_point_marker,
    ) -> None:
        try:
            class_name = insertion_point_marker.get("class_name")
            method_name = insertion_point_marker.get("method_name")
            test_code = self._reset_indentation(generated_unittest["test_code"])
            new_imports_code = generated_unittest.get("new_imports_code", "")
            FileUtils.backup_code(self.config.test_file_path)
            if method_name:
                insertion_node = (
                    self.analyzer.find_function_block_by_name(
                        self.config.test_file_path, method_name=method_name
                    )
                    if method_name
                    else None
                )
                test_code = (
                    "\n"
                    + self._adjust_indentation(
                        test_code,
                        insertion_node.start_point[1] if insertion_node else 0,
                    )
                    + "\n"
                )
                position = (
                    insertion_node.end_point[0] + 1
                    if insertion_node
                    else len(
                        FileUtils.read_file(self.config.test_file_path).splitlines()
                    )
                )
                FileUtils.insert_code(self.config.test_file_path, test_code, position)
            else:
                test_code = "\n" + test_code + "\n"
                # just append it to the end of the file
                FileUtils.insert_code(self.config.test_file_path, test_code, -1)

            for new_import in new_imports_code.splitlines():
                FileUtils.insert_code(self.config.test_file_path, new_import, 0)

            result = subprocess.run(
                self.config.test_command.split(),
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )
            if result.returncode == 0:
                if self.check_line_coverage_increase():
                    logger.info(f"Test passed and increased line cov:\n{test_code}")

                    return True
                else:
                    logger.info(
                        f"Test passed but failed to increase line cov for\n{test_code}"
                    )
            else:
                logger.info(f"Test failed for\n{test_code}")
                self._handle_failed_test(result, test_code)
        except Exception as e:
            logger.info(f"Failed to validate unittest: {e}")
            raise
        else:
            FileUtils.revert(self.config.test_file_path)
            return False

    def check_line_coverage_increase(self):
        self.coverage_processor.parse_coverage_report()
        new_line_coverage_rate = self.coverage_processor.get_line_coverage_for_file(
            self.config.source_file_path
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

    @staticmethod
    def _number_lines(code: str) -> str:
        return "\n".join(f"{i + 1} {line}" for i, line in enumerate(code.splitlines()))

    def extract_response(self, response: str) -> dict:
        retries = 2
        for attempt in range(retries):
            try:
                response = response.strip().removeprefix("```yaml").rstrip("`")
                data = yaml.safe_load(response)
                return data
            except Exception as e:
                if attempt < retries - 1:
                    response = self.fix_format(e, response)
                else:
                    return {"new_tests": []}

    def fix_format(self, error, content):
        system_template = Template(SYSTEM_YAML_FIX).render()
        user_template = Template(USER_YAML_FIX).render(
            yaml_content=content,
            error=error,
        )
        prompt = {
            "system": system_template,
            "user": user_template,
        }
        model_response, _, _ = self.router.generate_response(
            prompt=prompt, streaming=False
        )
        return model_response

    @staticmethod
    def _reset_indentation(code: str) -> str:
        """Reset the indentation of the given code to zero-based indentation."""
        lines = code.splitlines()
        if not lines:
            return code
        min_indent = min(
            len(line) - len(line.lstrip()) for line in lines if line.strip()
        )
        return "\n".join(line[min_indent:] if line.strip() else line for line in lines)

    @staticmethod
    def _adjust_indentation(code: str, indent_level: int) -> str:
        """Adjust the given code to the specified base indentation level."""
        lines = code.splitlines()
        adjusted_lines = [" " * indent_level + line for line in lines]
        return "\n".join(adjusted_lines)