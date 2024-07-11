import xml.etree.ElementTree as ET
from importlib import resources
from typing import Any, Dict, List

from grep_ast import filename_to_lang
from tree_sitter_languages import get_language, get_parser

from mutahunter.core.entities.config import MutahunterConfig
from mutahunter.core.logger import logger


class Analyzer:
    def __init__(self, config: MutahunterConfig) -> None:
        """
        Initializes the Analyzer with the given configuration.

        Args:
            config (Dict[str, Any]): The configuration dictionary.
        """
        self.config = config
        self.line_rate = None
        self.file_lines_executed = None

    def run_coverage_analysis(self) -> Dict[str, List[int]]:
        """
        Parses the appropriate coverage report based on the coverage type.

        Returns:
            Dict[str, List[int]]: A dictionary where keys are filenames and values are lists of covered line numbers.
        """
        coverage_type_parsers = {
            "cobertura": self.parse_coverage_report_cobertura,
            "jacoco": self.parse_coverage_report_jacoco,
            "lcov": self.parse_coverage_report_lcov,
        }

        if self.config.coverage_type in coverage_type_parsers:
            return coverage_type_parsers[self.config.coverage_type]()
        else:
            raise ValueError(
                "Invalid coverage tool. Please specify either 'cobertura', 'jacoco', or 'lcov'."
            )

    def parse_coverage_report_lcov(self) -> Dict[str, List[int]]:
        """
        Parses an LCOV code coverage report to extract covered line numbers for each file and calculate overall line coverage.

        Returns:
            Dict[str, Any]: A dictionary where keys are filenames and values are lists of covered line numbers.
                            Additionally, it includes the overall line coverage percentage.
        """
        self.file_lines_executed = {}
        current_file = None
        total_lines_found = 0
        total_lines_hit = 0

        with open(self.config.code_coverage_report_path, "r") as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith("SF:"):
                    current_file = line.strip().split(":", 1)[1]
                    self.file_lines_executed[current_file] = []
                elif line.startswith("DA:") and current_file:
                    parts = line.strip().split(":")[1].split(",")
                    hits = int(parts[1])
                    if hits > 0:
                        line_number = int(parts[0])
                        self.file_lines_executed[current_file].append(line_number)
                elif line.startswith("LF:") and current_file:
                    total_lines_found += int(line.strip().split(":")[1])
                elif line.startswith("LH:") and current_file:
                    total_lines_hit += int(line.strip().split(":")[1])
                elif line.startswith("end_of_record"):
                    current_file = None
        self.line_rate = (
            (total_lines_hit / total_lines_found) if total_lines_found else 0.0
        )

    def parse_coverage_report_cobertura(self) -> Dict[str, List[int]]:
        """
        Parses a Cobertura XML code coverage report to extract covered line numbers for each file.

        Returns:
            Dict[str, List[int]]: A dictionary where keys are filenames and values are lists of covered line numbers.
        """
        tree = ET.parse(self.config.code_coverage_report_path)
        root = tree.getroot()
        self.file_lines_executed = {}
        self.line_rate = float(root.get("line-rate", 0))
        for cls in root.findall(".//class"):
            name_attr = cls.get("filename")
            executed_lines = []
            for line in cls.findall(".//line"):
                line_number = int(line.get("number"))
                hits = int(line.get("hits"))
                if hits > 0:
                    executed_lines.append(line_number)
            if executed_lines:
                self.file_lines_executed[name_attr] = executed_lines

    def parse_coverage_report_jacoco(self) -> Dict[str, Any]:
        """
        Parses a JaCoCo XML code coverage report to extract covered line numbers for each file and calculate overall line coverage.

        Returns:
            Dict[str, Any]: A dictionary where keys are file paths and values are lists of covered line numbers.
                            Additionally, it includes the overall line coverage percentage.
        """
        tree = ET.parse(self.config.code_coverage_report_path)
        root = tree.getroot()
        self.file_lines_executed = {}

        total_lines_missed = 0
        total_lines_covered = 0

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
                    total_lines_missed += missed
                    total_lines_covered += covered
                if executed_lines:
                    self.file_lines_executed[full_filename] = executed_lines

        self.line_rate = (
            (total_lines_covered / (total_lines_covered + total_lines_missed))
            if (total_lines_covered + total_lines_missed) > 0
            else 0.0
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
        function_blocks = self.get_function_blocks(source_file_path=source_file_path)
        return self._get_covered_blocks(function_blocks, executed_lines)

    def get_covered_method_blocks(
        self, executed_lines: List[int], source_file_path: str
    ) -> List[Any]:
        """
        Retrieves covered method blocks based on executed lines and source_file_path.

        Args:
            executed_lines (List[int]): List of executed line numbers.
            source_file_path (str): The name of the file being analyzed.

        Returns:
            List[Any]: A list of covered method blocks.
        """
        method_blocks = self.get_method_blocks(source_file_path=source_file_path)
        return self._get_covered_blocks(method_blocks, executed_lines)

    def _get_covered_blocks(
        self, blocks: List[Any], executed_lines: List[int]
    ) -> List[Any]:
        """
        Retrieves covered blocks based on executed lines.

        Args:
            blocks (List[Any]): List of blocks (function or method).
            executed_lines (List[int]): List of executed line numbers.

        Returns:
            List[Any]: A list of covered blocks.
        """
        covered_blocks = []
        covered_block_executed_lines = []

        for block in blocks:
            # 0 baseed index
            start_point = block.start_point
            end_point = block.end_point

            start_line = start_point[0] + 1
            end_line = end_point[0] + 1

            if any(line in executed_lines for line in range(start_line, end_line + 1)):
                block_executed_lines = [
                    line - start_line + 1 for line in range(start_line, end_line + 1)
                ]
                covered_blocks.append(block)
                covered_block_executed_lines.append(block_executed_lines)

        return covered_blocks, covered_block_executed_lines

    def get_method_blocks(self, source_file_path: str) -> List[Any]:
        """
        Retrieves method blocks from a given file.

        Args:
            source_file_path (str): The name of the file being analyzed.

        Returns:
            List[Any]: A list of method block nodes.
        """
        source_code = self._read_source_file(source_file_path)
        return self.find_method_blocks_nodes(source_file_path, source_code)

    def get_function_blocks(self, source_file_path: str) -> List[Any]:
        """
        Retrieves function blocks from a given file.

        Args:
            source_file_path (str): The name of the file being analyzed.

        Returns:
            List[Any]: A list of function block nodes.
        """
        source_code = self._read_source_file(source_file_path)
        return self.find_function_blocks_nodes(source_file_path, source_code)

    def _read_source_file(self, file_path: str) -> bytes:
        """
        Reads the source code from a file.

        Args:
            file_path (str): The path to the source file.

        Returns:
            bytes: The source code.
        """
        with open(file_path, "rb") as f:
            return f.read()

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
        return not tree.root_node.has_error

    def find_method_blocks_nodes(
        self, source_file_path: str, source_code: bytes
    ) -> List[Any]:
        """
        Finds method block nodes in the provided source code.

        Args:
            source_code (bytes): The source code to analyze.

        Returns:
            List[Any]: A list of method block nodes.
        """
        return self._find_blocks_nodes(
            source_file_path, source_code, ["if_statement", "loop", "return"]
        )

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
        return self._find_blocks_nodes(
            source_file_path, source_code, ["definition.function", "definition.method"]
        )

    def _find_blocks_nodes(
        self, source_file_path: str, source_code: bytes, tags: List[str]
    ) -> List[Any]:
        """
        Finds block nodes (method or function) in the provided source code.

        Args:
            source_code (bytes): The source code to analyze.
            tags (List[str]): List of tags to identify blocks.

        Returns:
            List[Any]: A list of block nodes.
        """
        lang = filename_to_lang(source_file_path)
        if lang is None:
            raise ValueError(f"Language not supported for file: {source_file_path}")
        parser = get_parser(lang)
        language = get_language(lang)

        tree = parser.parse(source_code)
        query_scm = self._load_query_scm(lang)
        if not query_scm:
            return []

        query = language.query(query_scm)
        captures = query.captures(tree.root_node)

        if not captures:
            logger.error("Tree-sitter query failed to find any captures.")
            return []
        return [node for node, tag in captures if tag in tags]

    def _load_query_scm(self, lang: str) -> str:
        """
        Loads the query SCM file content.

        Args:
            lang (str): The language identifier.

        Returns:
            str: The content of the query SCM file.
        """
        try:
            scm_fname = resources.files(__package__).joinpath(
                "queries", f"tree-sitter-{lang}-tags.scm"
            )
        except KeyError:
            return ""
        if not scm_fname.exists():
            return ""
        return scm_fname.read_text()
