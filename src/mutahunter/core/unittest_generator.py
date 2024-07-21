import json
import os
import shutil
import subprocess

from grep_ast import filename_to_lang
from jinja2 import Template
from mutahunter.core.entities.config import MutatorConfig
from mutahunter.core.mutator import Mutator
from mutahunter.core.runner import TestRunner

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.coverage_processor import CoverageProcessor
from mutahunter.core.entities.config import UnittestGeneratorConfig
from mutahunter.core.error_parser import extract_error_message
from mutahunter.core.prompts.user import (
    FAILED_TESTS_TEXT,
    MUTATION_TEST_PROMPT,
    MUTATION_WEAK_TESTS_TEXT,
    REPORT_PROMPT,
    TEST_GEN_USER_PROMPT,
)
from mutahunter.core.router import LLMRouter
from mutahunter.core.runner import TestRunner


class UnittestGenerator:
    def __init__(self, config: UnittestGeneratorConfig):
        self.config = config
        self.coverage_processor = CoverageProcessor(
            code_coverage_report_path=self.config.code_coverage_report_path,
            coverage_type=self.config.coverage_type,
        )
        self.analyzer = Analyzer()
        self.test_runner = TestRunner(test_command=self.config.test_command)
        self.router = LLMRouter(model=self.config.model, api_base=self.config.api_base)

        self.mutator = Mutator(
            config=MutatorConfig(
                model=self.config.model,
                api_base=self.config.api_base,
                test_command=self.config.test_command,
                code_coverage_report_path=self.config.code_coverage_report_path,
                coverage_type=self.config.coverage_type,
                exclude_files=[],
                only_mutate_file_paths=[self.config.source_file_path],
                modified_files_only=False,
                extreme=False,
            )
        )

        self.failed_unittests = []
        self.weak_unittests = []

    def run(self) -> None:
        self.coverage_processor.parse_coverage_report()
        initial_line_coverage_rate = self.coverage_processor.line_coverage_rate

        current_attempt_for_line = 0
        while (
            self.coverage_processor.line_coverage_rate
            < self.config.target_line_coverage_rate
            and current_attempt_for_line < self.config.max_attempts
        ):
            print(f"Attempt {current_attempt_for_line}")
            current_attempt_for_line += 1
            response = self.generate_unittests()
            self._process_generated_unittests(response)

        self.mutator.run()

        # read mutations
        with open("logs/_latest/mutants.json", "r") as f:
            self.mutants = json.load(f)

        timeout_mutants = [
            mutant for mutant in self.mutants if mutant["status"] == "TIMEOUT"
        ]
        killed_mutants = [
            mutant for mutant in self.mutants if mutant["status"] == "KILLED"
        ]
        compiled_error_mutants = [
            mutant for mutant in self.mutants if mutant["status"] == "COMPILE_ERROR"
        ]
        self.current_mutationn_coverage = len(killed_mutants) / (
            len(self.mutants) - len(compiled_error_mutants) - len(timeout_mutants)
        )
        initial_mutation_coverage_rate = self.current_mutationn_coverage
        print("Mutation coverage rate", self.current_mutationn_coverage)

        current_attempt_for_mutation = 0
        self.failed_unittests = []

        while (
            self.current_mutationn_coverage < self.config.target_mutation_coverage_rate
            and current_attempt_for_mutation < self.config.max_attempts
        ):
            current_attempt_for_mutation += 1
            response = self.generate_unittests_for_mutants()
            self._process_generated_unittests_for_mutation(response)

        print("LINE COVERAGE", self.coverage_processor.line_coverage_rate)
        print("MUTATION COVERAGE", self.current_mutationn_coverage)

        # Based on the failed unittests and the survived mutants generate a report on a potential bug in the code.

        # get updated survived mutants

        survived_mutants = [
            mutant for mutant in self.mutants if mutant["status"] == "SURVIVED"
        ]
        # write updated surived mutants to file
        with open("logs/_latest/survived_mutants.json", "w") as f:
            json.dump(survived_mutants, f, indent=2)
        with open(self.config.source_file_path, "r") as f:
            source_code = f.read()
        with open(self.config.test_file_path, "r") as f:
            test_code = f.read()

        user_template = Template(REPORT_PROMPT).render(
            language=filename_to_lang(self.config.source_file_path),
            source_file=self.config.source_file_path,
            source_code=source_code,
            test_file=self.config.test_file_path,
            test_code=test_code,
            failed_tests=json.dumps(self.failed_unittests[:-5], indent=2),
            survived_mutants=json.dumps(survived_mutants, indent=2),
        )
        response, _, _ = self.router.generate_response(
            prompt={"system": "", "user": user_template}, streaming=True
        )
        with open("logs/_latest/report.md", "w") as f:
            f.write(response)

        print(
            f"Line coverage increased from {initial_line_coverage_rate*100:.2f}% to {self.coverage_processor.line_coverage_rate*100:.2f}%"
        )
        print(
            f"Mutation coverage increased from {initial_mutation_coverage_rate*100:.2f}% to {self.current_mutationn_coverage*100:.2f}%"
        )

    def generate_unittests(self):
        try:
            source_code = FileUtils.read_file(self.config.source_file_path)
            test_code = FileUtils.read_file(self.config.test_file_path)
            source_code_with_lines = self._number_lines(source_code)
            language = filename_to_lang(self.config.source_file_path)
            lines_to_cover = self.coverage_processor.file_lines_not_executed.get(
                self.config.source_file_path, []
            )
            user_template = Template(TEST_GEN_USER_PROMPT).render(
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
            return self._extract_json(response)
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
            print("Test result", result)
            if result.returncode == 0:
                print("Test passed")
                prev_line_coverage_rate = self.coverage_processor.line_coverage_rate
                self.coverage_processor.parse_coverage_report()

                if check_line_coverage:
                    print("checking line coverage")
                    if self.check_line_coverage_increase(prev_line_coverage_rate):
                        return True
                if check_mutantation_coverage:
                    print("checking mutation coverage")
                    if self.check_mutant_coverage_increase(
                        generated_unittest, test_code
                    ):
                        return True
            else:
                print("Test failed")
                print("test code", test_code)
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
        runner = TestRunner(test_command=self.config.test_command)
        survived_mutants = [
            mutant for mutant in self.mutants if mutant["status"] == "SURVIVED"
        ]
        for mutant in survived_mutants:
            if (
                mutant["id"] == generated_unittest["mutant_id"]
                and mutant["status"] == "SURVIVED"
            ):
                result = runner.run_test(
                    {
                        "module_path": self.config.source_file_path,
                        "replacement_module_path": mutant["mutant_path"],
                        "test_command": self.config.test_command,
                    }
                )
                if result.returncode == 0:
                    print("Mutant failed to be killed!")
                    with open("weaktests.txt", "+a") as f:
                        f.write(test_code)
                    self.weak_unittests.append(
                        {
                            "code": test_code,
                            "survived_mutant_id": f"Mutant {mutant['id']} not killed",
                        }
                    )
                else:
                    print("Mutant Successfully Killed")
                    mutant["status"] = "KILLED"
                    with open("logs/_latest/golden_tests.txt", "a") as f:
                        f.write(test_code)
                    return True

        timeout_mutants = [
            mutant for mutant in self.mutants if mutant["status"] == "TIMEOUT"
        ]
        killed_mutants = [
            mutant for mutant in self.mutants if mutant["status"] == "KILLED"
        ]
        compiled_error_mutants = [
            mutant for mutant in self.mutants if mutant["status"] == "COMPILE_ERROR"
        ]
        self.current_mutationn_coverage = len(killed_mutants) / (
            len(self.mutants) - len(compiled_error_mutants) - len(timeout_mutants)
        )
        print("Mutation coverage rate", self.current_mutationn_coverage)
        return False

    def _handle_failed_test(self, result, test_code):
        lang = self.analyzer.get_language_by_filename(self.config.test_file_path)
        error_msg = extract_error_message(lang, result.stdout + result.stderr)
        self.failed_unittests.append({"code": test_code, "error_message": error_msg})

    def generate_unittests_for_mutants(self) -> None:
        survived_mutants = [
            mutant for mutant in self.mutants if mutant["status"] == "SURVIVED"
        ]

        source_code = FileUtils.read_file(self.config.source_file_path)
        language = filename_to_lang(self.config.source_file_path)

        user_template = Template(MUTATION_TEST_PROMPT).render(
            language=language,
            line_coverage=self.coverage_processor.line_coverage_rate * 100,
            mutation_coverage=self.current_mutationn_coverage * 100,
            source_file_name=self.config.source_file_path,
            source_code=source_code,
            test_file_name=self.config.test_file_path,
            test_file=FileUtils.read_file(self.config.test_file_path),
            survived_mutants=json.dumps(survived_mutants, indent=2),
            weak_tests_section=(
                Template(MUTATION_WEAK_TESTS_TEXT).render(
                    weak_tests=f"{json.dumps(self.weak_unittests[:-5], indent=2)}"
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
            prompt={"system": "", "user": user_template}, streaming=True
        )

        resp = self._extract_json(response)
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

    @staticmethod
    def _extract_json(text: str) -> dict:
        if "```json" in text:
            json_content = text.split("```json")[1].split("```")[0]
        else:
            json_content = text.strip()
        return json.loads(json_content, strict=False)

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
            print(f"Backup file created at {backup_path}")
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
                print(f"File reverted to original state from {backup_path}")
            else:
                print(f"No backup file found for {file_path}")
                raise FileNotFoundError(f"No backup file found for {file_path}")
        except Exception as e:
            print(f"Failed to revert file {file_path}: {e}")
            raise


class SubprocessUtils:
    @staticmethod
    def run_command(command: str) -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(command.split(), capture_output=True, text=True)
            return result
        except Exception as e:
            print(f"Failed to run command {command}: {e}")
            raise
