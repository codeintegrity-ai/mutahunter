import re
import shlex
import subprocess
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Tuple

from tree_sitter_languages import get_parser


class Analyzer:
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initializes the Analyzer with the given configuration.

        Args:
            config (Dict[str, Any]): The configuration dictionary.
        """
        super().__init__()
        self.config = config
        self.tree_sitter_parser = get_parser(self.config["language"])

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
                    line_number = int(parts[0])
                    hits = int(parts[1])
                    if hits > 0:
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
                    missed = int(line.get("mi"))
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
        result = subprocess.run(shlex.split(test_command))
        if result.returncode != 0:
            raise Exception(
                "Tests failed. Please ensure all tests pass before running mutation testing."
            )

    def get_covered_function_blocks(
        self, executed_lines: List[int], filename: str
    ) -> List[Any]:
        """
        Retrieves covered function blocks based on executed lines and filename.

        Args:
            executed_lines (List[int]): List of executed line numbers.
            filename (str): The name of the file being analyzed.

        Returns:
            List[Any]: A list of covered function blocks.
        """
        covered_function_blocks = []
        covered_function_block_executed_lines = []
        function_blocks = self.get_function_blocks(filename=filename)
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
                function_executed_lines = []
                for line in range(start_line, end_line + 1):
                    function_executed_lines.append(line - start_line + 1)

                covered_function_blocks.append(function_block)
                covered_function_block_executed_lines.append(function_executed_lines)

        return covered_function_blocks, covered_function_block_executed_lines

    def get_function_blocks(self, filename: str) -> List[Any]:
        """
        Retrieves function blocks from a given file.

        Args:
            filename (str): The name of the file being analyzed.

        Returns:
            List[Any]: A list of function block nodes.
        """
        with open(filename, "rb") as f:
            source_code = f.read()
        function_blocks = self.find_function_blocks_nodes(source_code=source_code)
        return function_blocks

    def check_syntax(self, source_code: str) -> bool:
        """
        Checks the syntax of the provided source code.

        Args:
            source_code (str): The source code to check.

        Returns:
            bool: True if the syntax is correct, False otherwise.
        """
        tree = self.tree_sitter_parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node
        return not root_node.has_error

    def traverse_ast(self, node: Any, callback: Any) -> bool:
        """
        Recursively traverses an AST starting from the given node.

        Args:
            node (Any): The starting AST node for traversal.
            callback (Any): A function that will be called for each node.
                            The callback can return True to stop the traversal.

        Returns:
            bool: True if traversal is stopped by the callback, False otherwise.
        """
        stop = callback(node)
        if stop:
            return True
        for child in node.children:
            if self.traverse_ast(child, callback):
                return True
        return False

    def find_function_blocks_nodes(self, source_code: bytes) -> List[Any]:
        """
        Finds function block nodes in the provided source code.

        Args:
            source_code (bytes): The source code to analyze.

        Returns:
            List[Any]: A list of function block nodes.
        """
        tree = self.tree_sitter_parser.parse(source_code)
        function_blocks = []

        def callback(node: Any) -> bool:
            if (
                node.type == "function_definition"
                or node.type == "method_definition"
                or node.type == "function_declaration"  #
                or node.type == "method_declaration"  # java
            ):
                function_blocks.append(node)
            return False

        self.traverse_ast(tree.root_node, callback)
        return function_blocks
