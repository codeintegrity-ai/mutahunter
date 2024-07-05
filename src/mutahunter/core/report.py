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

    def __init__(self, config) -> None:
        self.config = config

    def generate_report(
        self,
        mutants: List[Mutant],
        total_cost: float,
        line_rate: float,
    ) -> None:
        """
        Generates a comprehensive mutation testing report.

        Args:
            mutants (List[Mutant]): List of mutants generated during mutation testing.
        """
        mutants = [asdict(mutant) for mutant in mutants]
        self.save_report("logs/_latest/mutants.json", mutants)
        print(MUTAHUNTER_ASCII)
        self.generate_mutant_report(mutants, total_cost, line_rate)
        self.generate_mutant_report_detail(mutants)

    def generate_mutant_report(
        self,
        mutants: List[Mutant],
        total_cost: float,
        line_rate: float,
    ) -> None:
        killed_mutants = [mutant for mutant in mutants if mutant["status"] == "KILLED"]
        survived_mutants = [
            mutant for mutant in mutants if mutant["status"] == "SURVIVED"
        ]
        timeout_mutants = [
            mutant for mutant in mutants if mutant["status"] == "TIMEOUT"
        ]
        compile_error_mutants = [
            mutant for mutant in mutants if mutant["status"] == "COMPILE_ERROR"
        ]
        valid_mutants = [
            m for m in mutants if m["status"] not in ["COMPILE_ERROR", "TIMEOUT"]
        ]

        total_mutation_coverage = (
            f"{len(killed_mutants) / len(valid_mutants) * 100:.2f}%"
            if valid_mutants
            else "0.00%"
        )
        line_coverage = f"{line_rate * 100:.2f}%"

        logger.info("📊 Line Coverage: %.2f%% 📊", line_rate * 100)
        logger.info("🎯 Mutation Coverage: %s 🎯", total_mutation_coverage)
        logger.info("🦠 Total Mutants: %d 🦠", len(mutants))
        logger.info("🛡️ Survived Mutants: %d 🛡️", len(survived_mutants))
        logger.info("🗡️ Killed Mutants: %d 🗡️", len(killed_mutants))
        logger.info("🕒 Timeout Mutants: %d 🕒", len(timeout_mutants))
        logger.info("🔥 Compile Error Mutants: %d 🔥", len(compile_error_mutants))
        logger.info("💰 Expected Cost: $%.5f USD 💰", total_cost)

        mutation_coverage = {
            "total_mutants": len(mutants),
            "killed_mutants": len(killed_mutants),
            "survived_mutants": len(survived_mutants),
            "timeout_mutants": len(timeout_mutants),
            "compile_error_mutants": len(compile_error_mutants),
            "mutation_coverage": total_mutation_coverage,
            "line_coverage": line_coverage,
            "expected_cost": total_cost,
        }

        self.save_report("logs/_latest/mutation_coverage.json", mutation_coverage)

    def generate_mutant_report_detail(self, mutants: List[Mutant]) -> None:
        """
        Generates a detailed mutation testing report per source file.

        Args:
            mutants (List[Mutant]): List of mutants generated during mutation testing.
        """
        report_detail = {}
        for mutant in mutants:
            source_path = mutant["source_path"]
            if source_path not in report_detail:
                report_detail[source_path] = {
                    "total_mutants": 0,
                    "killed_mutants": 0,
                    "survived_mutants": 0,
                    "timeout_mutants": 0,
                    "compile_error_mutants": 0,
                }
            report_detail[source_path]["total_mutants"] += 1
            if mutant["status"] == "KILLED":
                report_detail[source_path]["killed_mutants"] += 1
            elif mutant["status"] == "SURVIVED":
                report_detail[source_path]["survived_mutants"] += 1
            elif mutant["status"] == "TIMEOUT":
                report_detail[source_path]["timeout_mutants"] += 1
            elif mutant["status"] == "COMPILE_ERROR":
                report_detail[source_path]["compile_error_mutants"] += 1

        for source_path, detail in report_detail.items():
            valid_mutants = (
                detail["total_mutants"]
                - detail["compile_error_mutants"]
                - detail["timeout_mutants"]
            )
            mutation_coverage = (
                f"{detail['killed_mutants'] / valid_mutants * 100:.2f}%"
                if valid_mutants
                else "0.00%"
            )
            detail["mutation_coverage"] = mutation_coverage

        self.save_report("logs/_latest/mutation_coverage_detail.json", report_detail)

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
