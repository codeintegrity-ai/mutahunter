"""
Module for generating mutation testing reports.
"""

from typing import Any, Dict, List, Union

from mutahunter.core.logger import logger

MUTAHUNTER_ASCII = r"""
.  . . . .-. .-. . . . . . . .-. .-. .-. 
|\/| | |  |  |-| |-| | | |\|  |  |-  |(  
'  ` `-'  '  ` ' ' ` `-' ' `  '  `-' ' ' 
"""


class MutantReport:
    """Class for generating mutation testing reports."""

    def __init__(self) -> None:
        pass

    def generate_report(
        self,
        total_cost: float,
        mutation_coverage: float,
        killed_mutants: int,
        survived_mutants: int,
        compile_error_mutants: int,
        timeout_mutants: int,
    ) -> None:
        """
        Generates a comprehensive mutation testing report.

        Args:
            total_cost (float): The total cost of mutation testing.
            mutation_coverage (float): The mutation coverage rate.
            killed_mutants (int): The number of killed mutants.
            survived_mutants (int): The number of survived mutants.
            compile_error_mutants (int): The number of compile error mutants.
            timeout_mutants (int): The number of timeout mutants.
        """
        print(MUTAHUNTER_ASCII)
        summary_text = self._format_summary(
            mutation_coverage,
            killed_mutants,
            survived_mutants,
            compile_error_mutants,
            timeout_mutants,
            total_cost,
        )
        print(summary_text)

    def _get_source_code(self, file_name: str) -> str:
        with open(file_name, "r") as f:
            return f.read()

    def _format_summary(
        self,
        mutation_coverage: float,
        killed_mutants: int,
        survived_mutants: int,
        compile_error_mutants: int,
        timeout_mutants: int,
        total_cost: float,
    ) -> str:
        """
        Formats the summary data into a string.

        Args:
            data (Dict[str, Any]): Summary data including counts of different mutant statuses.
            total_cost (float): The total cost of mutation testing.
            line_rate (float): The line coverage rate.

        Returns:
            str: Formatted summary report.
        """
        mutation_coverage = f"{mutation_coverage*100:.2f}%"
        details = [
            f"\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n",
            "📊 Overall Mutation Coverage 📊",
            f"🎯 Mutation Coverage: {mutation_coverage} 🎯",
            f"🦠 Total Mutants: {survived_mutants + killed_mutants} 🦠",
            f"🛡️ Survived Mutants: {survived_mutants} 🛡️",
            f"🗡️ Killed Mutants: {killed_mutants} 🗡️",
            f"🕒 Timeout Mutants: {timeout_mutants} 🕒",
            f"🔥 Compile Error Mutants: {compile_error_mutants} 🔥",
            f"💰 Total Cost: ${total_cost:.5f} USD 💰",
            f"\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n",
        ]
        return "\n".join(details)
