import json
import os
import shutil
import subprocess
from dataclasses import asdict

import yaml
from grep_ast import filename_to_lang
from jinja2 import Template

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.controller import MutationTestController
from mutahunter.core.coverage_processor import CoverageProcessor
from mutahunter.core.db import MutationDatabase
from mutahunter.core.entities.config import (MutationTestControllerConfig,
                                             UnittestGeneratorConfig)
from mutahunter.core.error_parser import extract_error_message
from mutahunter.core.prompts.unittest_generator import (
    FAILED_TESTS_TEXT, LINE_COV_UNITTEST_GENERATOR_USER_PROMPT,
    MUTATION_COV_UNITTEST_GENERATOR_USER_PROMPT, MUTATION_WEAK_TESTS_TEXT)
from mutahunter.core.router import LLMRouter
from mutahunter.core.runner import MutantTestRunner

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


class UnittestGenerator:
    def __init__(
        self,
        config: UnittestGeneratorConfig,
        coverage_processor: CoverageProcessor,
        analyzer: Analyzer,
        test_runner: MutantTestRunner,
        router: LLMRouter,
        db: MutationDatabase,
        mutator: MutationTestController,
    ):
        self.config = config
        self.db = db
        self.coverage_processor = coverage_processor
        self.analyzer = analyzer
        self.test_runner = test_runner
        self.router = router
        self.mutator = mutator

        self.failed_unittests = []
        self.weak_unittests = []

        file_version_id, _, is_new_version = self.db.get_file_version(
            self.config.source_file_path
        )
        self.file_version_id = file_version_id

    def run(self) -> None:
        self.coverage_processor.parse_coverage_report()
        initial_line_coverage_rate = self.coverage_processor.line_coverage_rate
        print("Initial line coverage rate:", initial_line_coverage_rate)
        self.increase_line_coverage()
        self.mutator.run_coverage_analysis()
        self.mutator.run_mutation_testing()
        initial_mutation_coverage_rate = self.db.get_mutation_coverage()
        print("Initial mutation coverage rate:", initial_mutation_coverage_rate)
        self.increase_mutation_coverage()
        print(
            f"Line coverage increased from {initial_line_coverage_rate*100:.2f}% to {self.coverage_processor.line_coverage_rate*100:.2f}%"
        )
        print(
            f"Mutation coverage increased from {initial_mutation_coverage_rate*100:.2f}% to {self.db.get_mutation_coverage()*100:.2f}%"
        )

    def increase_line_coverage(self):
        attempt = 0
        while (
            self.coverage_processor.line_coverage_rate
            < self.config.target_line_coverage_rate
            and attempt < self.config.max_attempts
        ):
            attempt += 1
            response = self.generate_unittests()
            self._process_generated_unittests(response)
            self.coverage_processor.parse_coverage_report()

    def increase_mutation_coverage(self):
        attempt = 0

        self.failed_unittests = []
        while (
            self.db.get_mutation_coverage() < self.config.target_mutation_coverage_rate
            and attempt < self.config.max_attempts
        ):
            attempt += 1
            response = self.generate_unittests_for_mutants()
            self._process_generated_unittests_for_mutation(response)

    def generate_unittests(self):
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
                        failed_test_runs=json.dumps(
                            self.failed_unittests[:-5], indent=2
                        )
                    )
                    if self.failed_unittests
                    else ""
                ),
            )
            response, _, _ = self.router.generate_response(
                prompt={"system": "", "user": user_template}, streaming=True
            )
            otuput = self.extract_response(response)
            return otuput
        except Exception as e:
            raise

    def _process_generated_unittests(self, response: dict) -> list:
        generated_unittests = response.get("new_tests", [])
        insertion_point_marker = response.get("insertion_point_marker", {})

        for generated_unittest in generated_unittests:
            self.validate_unittest(
                generated_unittest,
                insertion_point_marker,
                check_line_coverage=True,
                check_mutantation_coverage=False,
            )

    def validate_unittest(
        self,
        generated_unittest: dict,
        insertion_point_marker,
        check_line_coverage=True,
        check_mutantation_coverage=False,
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
                print("Test passed")
                prev_line_coverage_rate = self.coverage_processor.line_coverage_rate
                self.coverage_processor.parse_coverage_report()

                if check_line_coverage:
                    if self.check_line_coverage_increase(prev_line_coverage_rate):
                        return True
                if check_mutantation_coverage:
                    if self.check_mutant_coverage_increase(
                        generated_unittest, test_code
                    ):
                        return True
            else:
                print("Test failed")
                self._handle_failed_test(result, test_code)
        except Exception as e:
            print(f"Failed to validate unittest: {e}")
            raise
        else:
            FileUtils.revert(self.config.test_file_path)
            return False

    def check_line_coverage_increase(self, prev_line_coverage_rate):
        if self.coverage_processor.line_coverage_rate > prev_line_coverage_rate:
            print(
                f"Line coverage increased from {prev_line_coverage_rate*100:.2f}% to {self.coverage_processor.line_coverage_rate*100:.2f}%"
            )
            return True
        else:
            return False

    def check_mutant_coverage_increase(self, generated_unittest, test_code):
        runner = MutantTestRunner(test_command=self.config.test_command)

        mutants = self.db.get_survived_mutants_by_file_version_id(
            file_version_id=self.file_version_id
        )

        for mutant in mutants:
            if mutant["id"] == generated_unittest["mutant_id"]:
                result = runner.run_test(
                    {
                        "module_path": self.config.source_file_path,
                        "replacement_module_path": mutant["mutant_path"],
                        "test_command": self.config.test_command,
                    }
                )
                if result.returncode == 0:
                    print("Mutation coverage did not increase")
                    self.weak_unittests.append(
                        {
                            "code": test_code,
                            "survived_mutant_id": f"Mutant {mutant['id']} not killed",
                        }
                    )
                else:
                    print("Mutation coverage increased!")
                    self.db.update_mutant_status(mutant["id"], "KILLED")
                    return True
        return False

    def _handle_failed_test(self, result, test_code):
        lang = self.analyzer.get_language_by_filename(self.config.test_file_path)
        error_msg = extract_error_message(lang, result.stdout + result.stderr)
        self.failed_unittests.append({"code": test_code, "error_message": error_msg})

    def generate_unittests_for_mutants(self) -> None:
        source_code = FileUtils.read_file(self.config.source_file_path)
        language = filename_to_lang(self.config.source_file_path)
        self.db
        # filter survived mutants
        survived_mutants = self.db.get_survived_mutants_by_file_version_id(
            self.file_version_id
        )

        if not survived_mutants:
            raise Exception("No survived mutants found")

        user_template = Template(MUTATION_COV_UNITTEST_GENERATOR_USER_PROMPT).render(
            language=language,
            source_file_name=self.config.source_file_path,
            source_code=source_code,
            test_file_name=self.config.test_file_path,
            test_file=FileUtils.read_file(self.config.test_file_path),
            survived_mutants=json.dumps(
                survived_mutants,
                indent=2,
            ),
            weak_tests_section=(
                Template(MUTATION_WEAK_TESTS_TEXT).render(
                    weak_tests=f"{json.dumps(self.weak_unittests, indent=2)}"
                )
                if self.weak_unittests
                else ""
            ),
            failed_tests_section=(
                Template(FAILED_TESTS_TEXT).render(
                    failed_test=json.dumps(self.failed_unittests[:-5], indent=2)
                )
                if self.failed_unittests
                else ""
            ),
        )
        response, _, _ = self.router.generate_response(
            prompt={"system": "", "user": user_template}, streaming=False
        )

        resp = self.extract_response(response)
        return resp

    def _process_generated_unittests_for_mutation(self, response) -> None:
        generated_unittests = response.get("new_tests", [])
        insertion_point_marker = response.get("insertion_point_marker", {})
        for generated_unittest in generated_unittests:
            self.validate_unittest(
                generated_unittest,
                insertion_point_marker,
                check_line_coverage=False,
                check_mutantation_coverage=True,
            )

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


class FileUtils:
    @staticmethod
    def read_file(path: str) -> str:
        try:
            with open(path, "r") as file:
                return file.read()
        except FileNotFoundError:
            print(f"File not found: {path}")
        except Exception as e:
            print(f"Error reading file {path}: {e}")
            raise

    @staticmethod
    def backup_code(file_path: str) -> None:
        backup_path = f"{file_path}.bak"
        try:
            shutil.copyfile(file_path, backup_path)
        except Exception as e:
            print(f"Failed to create backup file for {file_path}: {e}")
            raise

    @staticmethod
    def insert_code(file_path: str, code: str, position: int) -> None:
        try:
            with open(file_path, "r") as file:
                lines = file.read().splitlines()
            if position == -1:
                position = len(lines)
            lines.insert(position, code)
            with open(file_path, "w") as file:
                file.write("\n".join(lines))
        except Exception as e:
            raise

    @staticmethod
    def revert(file_path: str) -> None:
        backup_path = f"{file_path}.bak"
        try:
            if os.path.exists(backup_path):
                shutil.copyfile(backup_path, file_path)
            else:
                print(f"No backup file found for {file_path}")
                raise FileNotFoundError(f"No backup file found for {file_path}")
        except Exception as e:
            print(f"Failed to revert file {file_path}: {e}")
            raise
