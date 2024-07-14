import xml.etree.ElementTree as ET
from importlib import resources
from typing import Any, Dict, List

from grep_ast import filename_to_lang
from tree_sitter_languages import get_language, get_parser

from mutahunter.core.entities.config import MutahunterConfig
from mutahunter.core.logger import logger


class CoverageProcessor:
    def __init__(self, coverage_type, code_coverage_report_path) -> None:
        """
        Initializes the CoverageProcessor with the given configuration.

        Args:
            config (Dict[str, Any]): The configuration dictionary.
        """
        self.coverage_type = coverage_type
        self.code_coverage_report_path = code_coverage_report_path

        self.line_coverage_rate = 0.0
        self.file_lines_executed = {}
        self.file_lines_not_executed = {}

    def parse_coverage_report(self) -> Dict[str, List[int]]:
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

        if self.coverage_type in coverage_type_parsers:
            file_lines_executed, file_lines_not_executed, line_coverage_rate = (
                coverage_type_parsers[self.coverage_type]()
            )
            self.file_lines_executed = file_lines_executed
            self.file_lines_not_executed = file_lines_not_executed
            self.line_coverage_rate = line_coverage_rate
            print("file_lines_executed:", file_lines_executed)
            print("file_lines_not_executed:", file_lines_not_executed)
            print("line_coverage_rate:", line_coverage_rate)
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
        self.file_lines_not_executed = {}
        current_file = None
        total_lines_found = 0
        total_lines_hit = 0

        with open(self.code_coverage_report_path, "r") as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith("SF:"):
                    current_file = line.strip().split(":", 1)[1]
                    self.file_lines_executed[current_file] = []
                    self.file_lines_not_executed[current_file] = []
                elif line.startswith("DA:") and current_file:
                    parts = line.strip().split(":")[1].split(",")
                    hits = int(parts[1])
                    if hits > 0:
                        line_number = int(parts[0])
                        self.file_lines_executed[current_file].append(line_number)
                    else:
                        self.file_lines_not_executed[current_file].append(int(parts[0]))
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
        tree = ET.parse(self.code_coverage_report_path)
        root = tree.getroot()
        source_file_exec_lines, source_file_not_exec_lines = {}, {}
        for cls in root.findall(".//class"):
            name_attr = cls.get("filename")
            if name_attr not in self.file_lines_executed:
                self.file_lines_executed[name_attr] = []
            if name_attr not in self.file_lines_not_executed:
                self.file_lines_not_executed[name_attr] = []
            for line in cls.findall(".//line"):
                line_number = int(line.get("number"))
                hits = int(line.get("hits"))
                if hits > 0:
                    source_file_exec_lines[name_attr].append(line_number)
                else:
                    source_file_not_exec_lines[name_attr].append(line_number)

            total_executed_lines = sum(
                len(lines) for lines in source_file_exec_lines.values()
            )

        total_missed_lines = sum(
            len(lines) for lines in source_file_not_exec_lines.values()
        )

        line_coverage_rate = total_executed_lines / (
            total_executed_lines + total_missed_lines
        )
        return (
            source_file_exec_lines,
            source_file_not_exec_lines,
            line_coverage_rate,
        )

    def parse_coverage_report_jacoco(self) -> Dict[str, Any]:
        """
        Parses a JaCoCo XML code coverage report to extract covered line numbers for each file and calculate overall line coverage.

        Returns:
            Dict[str, Any]: A dictionary where keys are file paths and values are lists of covered line numbers.
                            Additionally, it includes the overall line coverage percentage.
        """
        tree = ET.parse(self.code_coverage_report_path)
        root = tree.getroot()
        source_file_exec_lines, source_file_not_exec_lines = {}, {}

        for package in root.findall(".//package"):
            package_name = package.get("name").replace("/", ".")
            for sourcefile in package.findall(".//sourcefile"):
                filename = sourcefile.get("name")
                # Construct the full file path with the src/main/java directory
                full_filename = (
                    f"src/main/java/{package_name.replace('.', '/')}/{filename}"
                )
                if full_filename not in source_file_exec_lines:
                    source_file_exec_lines[full_filename] = []
                if full_filename not in source_file_not_exec_lines:
                    source_file_not_exec_lines[full_filename] = []

                for line in sourcefile.findall(".//line"):
                    line_number = int(line.get("nr"))  # nr is the line number
                    covered = int(line.get("ci"))  # ci is the covered lines
                    print("covered:", covered)
                    if covered > 0:
                        source_file_exec_lines[full_filename].append(line_number)
                    else:
                        source_file_not_exec_lines[full_filename].append(line_number)

        total_executed_lines = sum(
            len(lines) for lines in source_file_exec_lines.values()
        )

        total_missed_lines = sum(
            len(lines) for lines in source_file_not_exec_lines.values()
        )

        line_coverage_rate = total_executed_lines / (
            total_executed_lines + total_missed_lines
        )

        return source_file_exec_lines, source_file_not_exec_lines, line_coverage_rate
