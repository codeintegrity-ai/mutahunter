import shlex
import subprocess
import xml.etree.ElementTree as ET
from typing import Tuple

from tree_sitter_languages import get_parser


class Analyzer:

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.tree_sitter_parser = get_parser(self.config["language"])
        self.file_lines_executed = self.parse_coverage_report_cobertura()

    def parse_coverage_report_cobertura(self) -> Tuple[list, list, float]:
        """
        Parses a Cobertura XML code coverage report to extract covered and missed line numbers for a specific file,
        and calculates the coverage percentage.

        Returns:
            Tuple[list, list, float]: A tuple containing lists of covered and missed line numbers, and the coverage percentage.
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
            result[name_attr] = executed_lines

        return result

    def dry_run(self):
        test_command = self.config["test_command"]
        result = subprocess.run(shlex.split(test_command))
        if result.returncode != 0:
            raise Exception(
                "Tests failed. Please ensure all tests pass before running mutation testing."
            )

    def get_covered_function_blocks(self, executed_lines, filename):
        covered_function_blocks = []
        function_blocks = self.get_function_blocks(filename=filename)
        for function_block in function_blocks:
            start_point = function_block.start_point
            end_point = function_block.end_point
            # start_byte = function_block.start_byte
            # end_byte = function_block.end_byte

            # NOTE: Python Coverage uses 1-based line numbers, whereas TreeSitter uses 0-based
            start_line = start_point[0] + 1
            end_line = end_point[0] + 1

            if any(
                line in executed_lines for line in range(start_line + 1, end_line + 1)
            ):  # +1 to exclude the first line of the function block
                covered_function_blocks.append(function_block)
        return covered_function_blocks

    def get_function_blocks(self, filename):
        with open(filename, "rb") as f:
            source_code = f.read()
        function_blocks = self.find_function_blocks_nodes(source_code=source_code)
        return function_blocks

    def check_syntax(self, source_code: str) -> bool:
        tree = self.tree_sitter_parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node
        if root_node.has_error:
            return False
        return True

    def traverse_ast(self, node, callback):
        """
        Recursively traverses an AST starting from the given node.

        :param node: The starting AST node for traversal.
        :param callback: A function that will be called for each node.
                        The callback can return True to stop the traversal.
        """
        stop = callback(node)
        if stop:
            return True
        for child in node.children:
            if self.traverse_ast(
                child, callback
            ):  # If callback signals to stop, we stop.
                return True

    def find_function_blocks_nodes(self, source_code: bytes):
        tree = self.tree_sitter_parser.parse(source_code)
        function_blocks = []

        def callback(node):
            # function_definition for python
            # method_definition for javascript
            # function_declaration for go
            if (
                node.type == "function_definition"
                or node.type == "method_definition"
                or node.type == "function_declaration"
            ):
                function_blocks.append(node)

        self.traverse_ast(tree.root_node, callback)
        return function_blocks
