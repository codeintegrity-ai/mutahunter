import os
import xml.etree.ElementTree as ET
from typing import Dict, List


class CoverageProcessor:
    def __init__(self, coverage_type: str, code_coverage_report_path: str) -> None:
        """
        Initializes the CoverageProcessor with the given configuration.

        Args:
            config (Dict[str, Any]): The configuration dictionary.
        """
        self.coverage_type = coverage_type
        self.code_coverage_report_path = code_coverage_report_path

        self.line_coverage_rate = 0.00
        self.file_lines_executed = {}  # src_file -> [line_numbers]
        self.file_lines_not_executed = {}  # src_file -> [line_numbers]

    def parse_coverage_report(self) -> Dict[str, List[int]]:
        """
        Parses the appropriate coverage report based on the coverage type.

        Returns:
            Dict[str, List[int]]: A dictionary where keys are filenames and values are lists of covered line numbers.
        """
        coverage_type_parsers = {
            "lcov": self.parse_coverage_report_lcov,
            "cobertura": self.parse_coverage_report_cobertura,
            "jacoco": self.parse_coverage_report_jacoco,
        }

        if self.coverage_type in coverage_type_parsers:
            coverage_type_parsers[self.coverage_type]()
            self.line_coverage_rate = self.calculate_line_coverage_rate()
        else:
            raise ValueError(
                "Invalid coverage tool. Please specify either 'cobertura', 'jacoco', or 'lcov'."
            )

    def parse_coverage_report_lcov(self):
        self._check_file_exists(self.code_coverage_report_path)
        self._check_file_extension([".info"], self.code_coverage_report_path)

        self.file_lines_executed.clear()
        self.file_lines_not_executed.clear()

        current_file = None
        with open(self.code_coverage_report_path, "r") as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith("SF:"):
                    current_file = line.strip().split(":", 1)[1]
                    if current_file not in self.file_lines_executed:
                        self.file_lines_executed[current_file] = []
                    if current_file not in self.file_lines_not_executed:
                        self.file_lines_not_executed[current_file] = []
                elif line.startswith("DA:") and current_file:
                    parts = line.strip().split(":")[1].split(",")
                    hits = int(parts[1])
                    if hits > 0:
                        line_number = int(parts[0])
                        self.file_lines_executed[current_file].append(line_number)
                    else:
                        line_number = int(parts[0])
                        self.file_lines_not_executed[current_file].append(line_number)
                elif line.startswith("end_of_record"):
                    current_file = None

    def parse_coverage_report_cobertura(self):
        self._check_file_exists(self.code_coverage_report_path)
        self._check_file_extension([".xml"], self.code_coverage_report_path)

        self.file_lines_executed.clear()
        self.file_lines_not_executed.clear()

        tree = ET.parse(self.code_coverage_report_path)
        root = tree.getroot()

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
                    self.file_lines_executed[name_attr].append(line_number)
                else:
                    self.file_lines_not_executed[name_attr].append(line_number)

    def parse_coverage_report_jacoco(self):
        self._check_file_exists(self.code_coverage_report_path)
        self._check_file_extension([".xml"], self.code_coverage_report_path)
        self.file_lines_executed.clear()
        self.file_lines_not_executed.clear()
        tree = ET.parse(self.code_coverage_report_path)
        root = tree.getroot()

        for package in root.findall(".//package"):
            # package_name = package.get("name").replace("/", ".")
            for sourcefile in package.findall(".//sourcefile"):
                filename = sourcefile.get("name")
                full_filename = self.find_source_file(filename)
                full_filename = full_filename.replace(os.getcwd() + "/", "")
                if full_filename not in self.file_lines_executed:
                    self.file_lines_executed[full_filename] = []
                if full_filename not in self.file_lines_not_executed:
                    self.file_lines_not_executed[full_filename] = []

                for line in sourcefile.findall(".//line"):
                    line_number = int(line.get("nr"))  # nr is the line number
                    covered = int(line.get("ci"))  # ci is the covered lines
                    # missing = int(line.get("mi"))  # mi is the missed lines
                    if covered > 0:
                        self.file_lines_executed[full_filename].append(line_number)
                    else:
                        self.file_lines_not_executed[full_filename].append(line_number)

    def find_source_file(self, filename: str):
        for root, dirs, files in os.walk(os.getcwd()):
            for file in files:
                if "src" in root and filename in file:
                    return os.path.join(root, file)

    def calculate_line_coverage_rate_for_file(self, src_file: str):
        lines_executed = self.file_lines_executed.get(src_file, [])
        lines_not_executed = self.file_lines_not_executed.get(src_file, [])
        if len(lines_executed) + len(lines_not_executed) == 0:
            line_cov = 0.00
        else:
            line_cov = len(lines_executed) / (
                len(lines_executed) + len(lines_not_executed)
            )
        return line_cov

    def calculate_line_coverage_rate(self) -> float:
        total_executed_lines = sum(
            len(lines) for lines in self.file_lines_executed.values()
        )
        total_missed_lines = sum(
            len(lines) for lines in self.file_lines_not_executed.values()
        )
        if total_executed_lines + total_missed_lines == 0:
            return 0.00
        return round(
            total_executed_lines / (total_executed_lines + total_missed_lines), 2
        )

    def _check_file_exists(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File '{file_path}' not found.")

    def _check_file_extension(self, exts: List[str], file_path: str):
        if not any(file_path.endswith(ext) for ext in exts):
            raise ValueError(f"File '{file_path}' is not in {exts} format.")
