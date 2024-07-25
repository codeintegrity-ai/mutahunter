"""
Module for generating mutation testing reports.
"""

import json
from dataclasses import asdict
from typing import Any, List

from mutahunter.core.entities.mutant import Mutant
from mutahunter.core.logger import logger

MUTAHUNTER_ASCII = r"""
.  . . . .-. .-. . . . . . . .-. .-. .-. 
|\/| | |  |  |-| |-| | | |\|  |  |-  |(  
'  ` `-'  '  ` ' ' ` `-' ' `  '  `-' ' ' 
"""


class MutantReport:
    """Class for generating mutation testing reports."""

    def __init__(
        self,
        extreme: bool,
    ) -> None:
        self.extreme = extreme
        self.log_file = "logs/_latest/coverage.txt"

    def generate_report(
        self, mutants: List[Mutant], total_cost: float, line_rate: float
    ) -> None:
        """
        Generates a comprehensive mutation testing report.

        Args:
            mutants (List[Mutant]): List of mutants generated during mutation testing.
            total_cost (float): The total cost of mutation testing.
            line_rate (float): The line coverage rate.
        """
        mutant_dicts = [asdict(mutant) for mutant in mutants]
        self.save_report("logs/_latest/mutants.json", mutant_dicts)
        print(MUTAHUNTER_ASCII)
        self._generate_summary_report(mutant_dicts, total_cost, line_rate)
        self._generate_detailed_report(mutant_dicts)

    def _generate_summary_report(
        self, mutants: List[dict], total_cost: float, line_rate: float
    ) -> None:
        """
        Generates a summary mutation testing report.

        Args:
            mutants (List[dict]): List of mutant dictionaries.
            total_cost (float): The total cost of mutation testing.
            line_rate (float): The line coverage rate.
        """
        report_data = self._compute_summary_data(mutants)
        summary_text = self._format_summary(report_data, total_cost, line_rate)
        self._log_and_write(summary_text)
        self.killed_mutants = report_data["killed_mutants"]
        self.survived_mutants = report_data["survived_mutants"]
        self.timeout_mutants = report_data["timeout_mutants"]
        self.compile_error_mutants = report_data["compile_error_mutants"]
        self.total_mutants = report_data["total_mutants"]
        self.mutation_coverage_rate = (
            float(report_data["mutation_coverage"].replace("%", "")) / 100
        )

        self.valid_mutants = report_data["valid_mutants"]

    def _compute_summary_data(self, mutants: List[dict]) -> dict:
        """
        Computes summary data from the list of mutants.

        Args:
            mutants (List[dict]): List of mutant dictionaries.

        Returns:
            dict: Summary data including counts of different mutant statuses.
        """
        data = {
            "killed_mutants": len([m for m in mutants if m["status"] == "KILLED"]),
            "survived_mutants": len([m for m in mutants if m["status"] == "SURVIVED"]),
            "timeout_mutants": len([m for m in mutants if m["status"] == "TIMEOUT"]),
            "compile_error_mutants": len(
                [m for m in mutants if m["status"] == "COMPILE_ERROR"]
            ),
        }
        data["total_mutants"] = len(mutants)
        data["valid_mutants"] = (
            data["total_mutants"]
            - data["compile_error_mutants"]
            - data["timeout_mutants"]
        )
        data["mutation_coverage"] = (
            f"{data['killed_mutants'] / data['valid_mutants'] * 100:.2f}%"
            if data["valid_mutants"]
            else "0.00%"
        )
        return data

    def _format_summary(self, data: dict, total_cost: float, line_rate: float) -> str:
        """
        Formats the summary data into a string.

        Args:
            data (dict): Summary data including counts of different mutant statuses.
            total_cost (float): The total cost of mutation testing.
            line_rate (float): The line coverage rate.

        Returns:
            str: Formatted summary report.
        """
        line_coverage = f"{line_rate * 100:.2f}%"
        details = []
        details.append("📊 Overall Mutation Coverage 📊")
        details.append(f"📈 Line Coverage: {line_coverage} 📈")
        details.append(f"🎯 Mutation Coverage: {data['mutation_coverage']} 🎯")
        details.append(f"🦠 Total Mutants: {data['total_mutants']} 🦠")
        details.append(f"🛡️ Survived Mutants: {data['survived_mutants']} 🛡️")
        details.append(f"🗡️ Killed Mutants: {data['killed_mutants']} 🗡️")
        details.append(f"🕒 Timeout Mutants: {data['timeout_mutants']} 🕒")
        details.append(f"🔥 Compile Error Mutants: {data['compile_error_mutants']} 🔥")
        if self.extreme:
            details.append("💰 No Cost for extreme mutation testing 💰")
        else:
            details.append(f"💰 Expected Cost: ${total_cost:.5f} USD 💰")
        return "\n".join(details)

    def _generate_detailed_report(self, mutants: List[dict]) -> None:
        """
        Generates a detailed mutation testing report per source file.

        Args:
            mutants (List[dict]): List of mutant dictionaries.
        """
        report_detail = self._compute_detailed_data(mutants)
        detailed_text = self._format_detailed_report(report_detail)
        self._log_and_write(detailed_text)

    def _compute_detailed_data(self, mutants: List[dict]) -> dict:
        """
        Computes detailed data for each source file from the list of mutants.

        Args:
            mutants (List[dict]): List of mutant dictionaries.

        Returns:
            dict: Detailed data including counts of different mutant statuses per source file.
        """
        detail = {}
        for mutant in mutants:
            source_path = mutant["source_path"]
            if source_path not in detail:
                detail[source_path] = {
                    "total_mutants": 0,
                    "killed_mutants": 0,
                    "survived_mutants": 0,
                    "timeout_mutants": 0,
                    "compile_error_mutants": 0,
                }
            detail[source_path]["total_mutants"] += 1
            if mutant["status"] == "KILLED":
                detail[source_path]["killed_mutants"] += 1
            elif mutant["status"] == "SURVIVED":
                detail[source_path]["survived_mutants"] += 1
            elif mutant["status"] == "TIMEOUT":
                detail[source_path]["timeout_mutants"] += 1
            elif mutant["status"] == "COMPILE_ERROR":
                detail[source_path]["compile_error_mutants"] += 1

        for source_path, data in detail.items():
            valid_mutants = (
                data["total_mutants"]
                - data["compile_error_mutants"]
                - data["timeout_mutants"]
            )
            data["mutation_coverage"] = (
                f"{data['killed_mutants'] / valid_mutants * 100:.2f}%"
                if valid_mutants
                else "0.00%"
            )
        return detail

    def _format_detailed_report(self, report_detail: dict) -> str:
        """
        Formats the detailed report data into a string.

        Args:
            report_detail (dict): Detailed data including counts of different mutant statuses per source file.

        Returns:
            str: Formatted detailed report.
        """
        details = ["📂 Detailed Mutation Coverage 📂"]
        for source_path, detail in report_detail.items():
            details.append(f"📂 Source File: {source_path} 📂")
            details.append(f"🎯 Mutation Coverage: {detail['mutation_coverage']} 🎯")
            details.append(f"🦠 Total Mutants: {detail['total_mutants']} 🦠")
            details.append(f"🛡️ Survived Mutants: {detail['survived_mutants']} 🛡️")
            details.append(f"🗡️ Killed Mutants: {detail['killed_mutants']} 🗡️")
            details.append(f"🕒 Timeout Mutants: {detail['timeout_mutants']} 🕒")
            details.append(
                f"🔥 Compile Error Mutants: {detail['compile_error_mutants']} 🔥"
            )
            details.append("\n")
        return "\n".join(details)

    def _log_and_write(self, text: str) -> None:
        """
        Logs and writes the given text to a file.

        Args:
            text (str): The text to log and write.
        """
        logger.info(text)
        with open(self.log_file, "a") as file:
            file.write(text + "\n")

    def save_report(self, filepath: str, data: Any) -> None:
        """
        Saves the report data to a JSON file.

        Args:
            filepath (str): The path to the file where the data should be saved.
            data (Any): The data to be saved.
        """
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        logger.info(f"Report saved to {filepath}")
