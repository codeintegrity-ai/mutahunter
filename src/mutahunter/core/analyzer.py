import os
import subprocess
import xml.etree.ElementTree as ET
from importlib import resources
from shlex import split
from typing import Any, Dict, List

from grep_ast import filename_to_lang
from tree_sitter_languages import get_language, get_parser
from mutahunter.core.logger import logger


class Analyzer:
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initializes the Analyzer with the given configuration.

        Args:
            config (Dict[str, Any]): The configuration dictionary.
        """
        super().__init__()
        self.config = config

        if self.config["coverage_type"] == "cobertura":
            self.file_lines_executed = self.parse_coverage_report_cobertura()
        elif self.config["coverage_type"] == "jacoco":
            self.file_lines_executed = self.parse_coverage_report_jacoco()
        elif self.config["coverage_type"] == "lcov":
            self.file_lines_executed = self.parse_coverage_report_lcov()
        else:
            raise ValueError(
                "Invalid coverage tool. Please specify either 'cobertura' or 'jacoco'."
            )

    def parse_coverage_report_lcov(self) -> Dict[str, List[int]]:
        """
        Parses an LCOV code coverage report to extract covered line numbers for each file.

        Returns:
            Dict[str, List[int]]: A dictionary where keys are filenames and values are lists of covered line numbers.
        """
        result = {}
        current_file = None

        with open(self.config["code_coverage_report_path"], "r") as file:
            for line in file:
                if line.startswith("SF:"):
                    current_file = line.strip().split(":", 1)[1]
                    result[current_file] = []
                elif line.startswith("DA:") and current_file:
                    parts = line.strip().split(":")[1].split(",")
                    hits = int(parts[1])
                    if hits > 0:
                        line_number = int(parts[0])
                        result[current_file].append(line_number)
                elif line.startswith("end_of_record"):
                    current_file = None

        return result

    def parse_coverage_report_cobertura(self) -> Dict[str, List[int]]:
        """
        Parses a Cobertura XML code coverage report to extract covered line numbers for each file.

        Returns:
            Dict[str, List[int]]: A dictionary where keys are filenames and values are lists of covered line numbers.
        """
        tree = ET.parse(self.config["code_coverage_report_path"])
        root = tree.getroot()
        result = {}
        for cls in root.findall(".//class"):
            name_attr = cls.get("filename")
            executed_lines = []
            for line in cls.findall(".//line"):
                line_number = int(line.get("number"))
                hits = int(line.get("hits"))
                if hits > 0:
                    executed_lines.append(line_number)
            if executed_lines:
                result[name_attr] = executed_lines
        return result

    def parse_coverage_report_jacoco(self) -> Dict[str, List[int]]:
        """
        Parses a JaCoCo XML code coverage report to extract covered line numbers for each file.

        Returns:
            Dict[str, List[int]]: A dictionary where keys are file paths and values are lists of covered line numbers.
        """
        tree = ET.parse(self.config["code_coverage_report_path"])
        root = tree.getroot()
        result = {}

        for package in root.findall(".//package"):
            package_name = package.get("name").replace("/", ".")
            for sourcefile in package.findall(".//sourcefile"):
                filename = sourcefile.get("name")
                # Construct the full file path with the src/main/java directory
                full_filename = (
                    f"src/main/java/{package_name.replace('.', '/')}/{filename}"
                )
                executed_lines = []
                for line in sourcefile.findall(".//line"):
                    line_number = int(line.get("nr"))
                    int(line.get("mi"))
                    covered = int(line.get("ci"))
                    if covered > 0:
                        executed_lines.append(line_number)
                if executed_lines:
                    result[full_filename] = executed_lines

        return result

    def dry_run(self) -> None:
        """
        Performs a dry run of the tests to ensure they pass before mutation testing.

        Raises:
            Exception: If any tests fail during the dry run.
        """
        test_command = self.config["test_command"]
        result = subprocess.run(split(test_command), cwd=os.getcwd())
        if result.returncode != 0:
            raise Exception(
                "Tests failed. Please ensure all tests pass before running mutation testing."
            )

    def get_covered_function_blocks(
        self, executed_lines: List[int], source_file_path: str
    ) -> List[Any]:
        """
        Retrieves covered function blocks based on executed lines and source_file_path.

        Args:
            executed_lines (List[int]): List of executed line numbers.
            source_file_path (str): The name of the file being analyzed.

        Returns:
            List[Any]: A list of covered function blocks.
        """
        covered_function_blocks = []
        covered_function_block_executed_lines = []
        function_blocks = self.get_function_blocks(source_file_path=source_file_path)
        for function_block in function_blocks:
            start_point = function_block.start_point
            end_point = function_block.end_point

            # start_byte = function_block.start_byte
            # end_byte = function_block.end_byte

            start_line = start_point[0] + 1
            end_line = end_point[0] + 1

            if any(
                line in executed_lines for line in range(start_line + 1, end_line + 1)
            ):  # start_line + 1 to exclude the function definition line
                function_executed_lines = [
                    line - start_line + 1 for line in range(start_line, end_line + 1)
                ]
                covered_function_blocks.append(function_block)
                covered_function_block_executed_lines.append(function_executed_lines)

        return covered_function_blocks, covered_function_block_executed_lines

    def get_function_blocks(self, source_file_path: str) -> List[Any]:
        """
        Retrieves function blocks from a given file.

        Args:
            filename (str): The name of the file being analyzed.

        Returns:
            List[Any]: A list of function block nodes.
        """
        with open(source_file_path, "rb") as f:
            source_code = f.read()
        return self.find_function_blocks_nodes(
            source_file_path=source_file_path, source_code=source_code
        )

    def check_syntax(self, source_file_path: str, source_code: str) -> bool:
        """
        Checks the syntax of the provided source code.

        Args:
            source_code (str): The source code to check.

        Returns:
            bool: True if the syntax is correct, False otherwise.
        """

        lang = filename_to_lang(source_file_path)
        parser = get_parser(lang)
        tree = parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node
        return not root_node.has_error

    def find_function_blocks_nodes(
        self, source_file_path: str, source_code: bytes
    ) -> List[Any]:
        """
        Finds function block nodes in the provided source code.

        Args:
            source_code (bytes): The source code to analyze.

        Returns:
            List[Any]: A list of function block nodes.
        """
        lang = filename_to_lang(source_file_path)
        if lang is None:
            raise ValueError(f"Language not supported for file: {source_file_path}")
        parser = get_parser(lang)
        language = get_language(lang)

        tree = parser.parse(source_code)
        # Load the tags queries
        try:
            scm_fname = resources.files(__package__).joinpath(
                "pilot", "aider", "queries", f"tree-sitter-{lang}-tags.scm"
            )
        except KeyError:
            return
        query_scm = scm_fname
        if not query_scm.exists():
            return
        query_scm = query_scm.read_text()
        query = language.query(query_scm)
        captures = query.captures(tree.root_node)

        captures = list(captures)
        if not captures:
            logger.error("Tree-sitter query failed to find any captures.")
            return []
        return [
            node
            for node, tag in captures
            if tag in ["definition.function", "definition.method"]
        ]
