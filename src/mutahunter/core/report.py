"""
Module for generating mutation testing reports.
"""

from typing import Dict, Any, List
from mutahunter.core.logger import logger
from mutahunter.core.db import MutationDatabase
from jinja2 import Environment, FileSystemLoader
import os

MUTAHUNTER_ASCII = r"""
.  . . . .-. .-. . . . . . . .-. .-. .-. 
|\/| | |  |  |-| |-| | | |\|  |  |-  |(  
'  ` `-'  '  ` ' ' ` `-' ' `  '  `-' ' ' 
"""


class MutantReport:
    """Class for generating mutation testing reports."""

    def __init__(self, db: MutationDatabase) -> None:
        self.log_file = "logs/_latest/coverage.txt"
        self.db = db
        self.template_env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "html"))
        )
        os.makedirs("logs/_latest/html", exist_ok=True)

    def generate_report(self, total_cost: float, line_rate: float) -> None:
        """
        Generates a comprehensive mutation testing report.

        Args:
            total_cost (float): The total cost of mutation testing.
            line_rate (float): The line coverage rate.
        """
        print(MUTAHUNTER_ASCII)
        self._generate_summary_report(total_cost, line_rate)

        # HTML Report
        summary_data = self.db.get_mutant_summary()
        file_data = self._get_file_data()

        # Generate main report
        main_html = self._generate_main_report(
            summary_data, file_data, total_cost, line_rate
        )
        self._write_html_report(main_html, "mutation_report.html")

        # Generate detailed file reports
        for file_info in file_data:
            file_html = self._generate_file_report(file_info["id"])
            self._write_html_report(file_html, f"{file_info['id']}.html")

    def _get_file_data(self) -> List[Dict[str, Any]]:
        self.db.cursor.execute(
            """
            SELECT 
                sf.id,
                sf.file_path,
                COUNT(m.id) as total_mutants,
                SUM(CASE WHEN m.status = 'KILLED' THEN 1 ELSE 0 END) as killed_mutants,
                SUM(CASE WHEN m.status = 'SURVIVED' THEN 1 ELSE 0 END) as survived_mutants
            FROM SourceFiles sf
            JOIN FileVersions fv ON sf.id = fv.source_file_id
            JOIN Mutants m ON fv.id = m.file_version_id
            GROUP BY sf.file_path
        """
        )
        return [
            {
                "id": row[0],
                "name": row[1],
                "totalMutants": row[2],
                "mutationCoverage": (
                    f"{(row[3] / row[2] * 100):.2f}" if row[2] > 0 else "0.00"
                ),
                "survivedMutants": row[4],
            }
            for row in self.db.cursor.fetchall()
        ]

    def _generate_main_report(
        self,
        summary_data: Dict[str, Any],
        file_data: List[Dict[str, Any]],
        total_cost: float,
        line_rate: float,
    ) -> str:
        valid_mutants = (
            summary_data["total_mutants"]
            - summary_data["compile_error_mutants"]
            - summary_data["timeout_mutants"]
        )
        mutation_coverage = (
            f"{summary_data['killed_mutants'] / valid_mutants * 100:.2f}"
            if valid_mutants > 0
            else "0.00"
        )

        template = self.template_env.get_template("report_template.html")
        return template.render(
            line_coverage=f"{line_rate * 100:.2f}",
            mutation_coverage=mutation_coverage,
            total_mutants=summary_data["total_mutants"],
            killed_mutants=summary_data["killed_mutants"],
            survived_mutants=summary_data["survived_mutants"],
            timeout_mutants=summary_data["timeout_mutants"],
            compile_error_mutants=summary_data["compile_error_mutants"],
            total_cost=f"{total_cost:.7f}",
            file_data=file_data,
        )

    def _generate_file_report(self, file_id: str) -> str:
        file_name = self.db.get_source_file_by_id(file_id)
        source_code = self._get_source_code(file_name)
        mutations = self._get_file_mutations(file_name)

        source_lines = []
        for i, line in enumerate(source_code.splitlines(), start=1):
            line_mutations = [m for m in mutations if m["line_number"] == i]
            gutter = (
                "survived"
                if any(m["status"] == "SURVIVED" for m in line_mutations)
                else "killed" if line_mutations else ""
            )
            source_lines.append(
                {"code": line, "gutter": gutter, "mutations": line_mutations}
            )

        template = self.template_env.get_template("file_detail_template.html")
        return template.render(file_name=file_name, source_lines=source_lines)

    def _get_source_code(self, file_name: str) -> str:
        with open(file_name, "r") as f:
            return f.read()

    def _get_file_mutations(self, file_name: str) -> List[Dict[str, Any]]:
        self.db.cursor.execute(
            """
                SELECT m.id, m.status, m.type, m.description, m.line_number, m.original_code, m.mutated_code
                FROM Mutants m
                JOIN FileVersions fv ON m.file_version_id = fv.id
                JOIN SourceFiles sf ON fv.source_file_id = sf.id
                WHERE sf.file_path = ?
                ORDER BY m.line_number
            """,
            (file_name,),
        )
        return [
            {
                "id": row[0],
                "status": row[1],
                "type": row[2],
                "description": row[3],
                "line_number": row[4],
                "original_code": row[5],
                "mutated_code": row[6],
            }
            for row in self.db.cursor.fetchall()
        ]

    def _write_html_report(self, html_content: str, filename: str) -> None:
        with open(os.path.join("logs/_latest/html", filename), "w") as f:
            f.write(html_content)
        logger.info(f"HTML report generated: {filename}")

    def _generate_summary_report(self, total_cost: float, line_rate: float) -> None:
        """
        Generates a summary mutation testing report.

        Args:
            total_cost (float): The total cost of mutation testing.
            line_rate (float): The line coverage rate.
        """
        report_data = self._compute_summary_data()
        summary_text = self._format_summary(report_data, total_cost, line_rate)
        self._log_and_write(summary_text)

    def _compute_summary_data(self) -> Dict[str, Any]:
        """
        Computes summary data from the mutants in the database.

        Returns:
            Dict[str, Any]: Summary data including counts of different mutant statuses.
        """
        data = self.db.get_mutant_summary()
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

    def _format_summary(
        self, data: Dict[str, Any], total_cost: float, line_rate: float
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
        line_coverage = f"{line_rate * 100:.2f}%"
        details = [
            f"\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n",
            "📊 Overall Mutation Coverage 📊",
            f"📈 Line Coverage: {line_coverage} 📈",
            f"🎯 Mutation Coverage: {data['mutation_coverage']} 🎯",
            f"🦠 Total Mutants: {data['total_mutants']} 🦠",
            f"🛡️ Survived Mutants: {data['survived_mutants']} 🛡️",
            f"🗡️ Killed Mutants: {data['killed_mutants']} 🗡️",
            f"🕒 Timeout Mutants: {data['timeout_mutants']} 🕒",
            f"🔥 Compile Error Mutants: {data['compile_error_mutants']} 🔥",
            f"💰 Expected Cost: ${total_cost:.5f} USD 💰",
            f"\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n",
        ]
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
