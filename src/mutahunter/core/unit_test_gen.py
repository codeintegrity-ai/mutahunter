import json
import os
import subprocess

import yaml
from grep_ast import filename_to_lang

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.coverage_processor import CoverageProcessor
from mutahunter.core.entities.config import UnittestGeneratorLineConfig
from mutahunter.core.error_parser import extract_error_message
from mutahunter.core.logger import logger
from mutahunter.core.router import LLMRouter
from mutahunter.core.utils import FileUtils
from mutahunter.core.prompt_factory import TestGenerationPrompt


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
            f"Coverage increased from {initial_line_coverage_rate*100:.2f}% to {self.current_line_coverage_rate*100:.2f}%"
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

            for generated_unittest in new_tests:
                self.validate_unittest(
                    generated_unittest,
                )
                self.check_line_coverage_increase()
            self.coverage_processor.parse_coverage_report()

    def analyze_code(self):
        system_template = self.prompt.analyzer_system_prompt.render()
        src_code = FileUtils.read_file(self.config.source_file_path)
        language = filename_to_lang(self.config.source_file_path)
        source_file_numbered = self._number_lines(src_code)
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
        output = self.extract_response(response)
        self._save_yaml(output, "line")
        return output

    def generate_tests(self, test_plan: dict = None) -> dict:
        try:
            test_plan = self.extract_response(test_plan)
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

    def validate_unittest(
        self,
        generated_unittest: dict,
    ) -> None:
        try:
            new_test_code = self._reset_indentation(generated_unittest["test_code"])
            new_imports_code = generated_unittest.get("new_imports_code", "")
            FileUtils.backup_code(self.config.test_file_path)
            test_block_nodes = self.analyzer.get_test_nodes(
                source_file_path=self.config.test_file_path
            )
            # get last test block node
            last_test_block_node = test_block_nodes[-1] if test_block_nodes else None
            test_file_code = FileUtils.read_file(self.config.test_file_path)
            test_code_split = test_file_code.splitlines()
            if last_test_block_node:
                # get last test node's line number and indentation to insert new test
                indent_level_to_indent = (
                    last_test_block_node.start_point[1] if last_test_block_node else 0
                )
                line_number_to_insert = (
                    last_test_block_node.end_point[0] + 1
                    if last_test_block_node
                    else len(test_code_split)
                )
                # print("indent_level_to_indent", indent_level_to_indent)
                # print("line_number_to_insert", line_number_to_insert)

                test_code = "\n" + self._adjust_indentation(
                    new_test_code, indent_level_to_indent
                )
                test_code_split.insert(line_number_to_insert, test_code)
                for new_import in new_imports_code.splitlines():
                    test_code_split.insert(0, new_import)

                new_code = "\n".join(test_code_split)
                if self.analyzer.check_syntax(self.config.test_file_path, new_code):
                    with open(self.config.test_file_path, "w") as file:
                        file.write(new_code)
            else:
                # TODO:// Find a better way to handle this case
                test_code = "\n" + new_test_code + "\n"
                test_code_split.insert(len(test_code_split), test_code)
                # NOTE: Add new imports at the beginning of the file
                for new_import in new_imports_code.splitlines():
                    test_code_split.insert(0, new_import)

                new_code = "\n".join(test_code_split)
                if self.analyzer.check_syntax(self.config.test_file_path, new_code):
                    with open(self.config.test_file_path, "w") as file:
                        file.write(new_code)

            result = subprocess.run(
                self.config.test_command.split(),
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )
            # print("result", result)
            if result.returncode == 0:
                return
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
        user_prompt = self.prompt.yaml_fixer_user_prompt.render(
            {
                "yaml_content": content,
                "error": error,
            }
        )
        model_response, _, _ = self.router.generate_response(
            prompt={"system": "", "user": user_prompt}, streaming=False
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
