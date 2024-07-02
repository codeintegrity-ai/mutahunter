import json
import os
from dataclasses import asdict
from typing import Any, Dict, List

from jinja2 import Template

from mutahunter.core.entities.mutant import Mutant
from mutahunter.core.logger import logger
from mutahunter.core.router import LLMRouter


class MutantReport:
    def __init__(self, config) -> None:
        self.config = config
        self.router = LLMRouter(model=config["model"], api_base=config["api_base"])

    def generate_report(self, mutants: List[Mutant]) -> None:
        """
        Generates a comprehensive mutation testing report.

        Args:
            mutants (List[Mutant]): List of mutants generated during mutation testing.
        """
        self.generate_killed_mutants(mutants)
        self.generate_survived_mutants(mutants)
        mutation_coverage_by_test_file = self.generate_mutation_coverage_by_source_file(
            mutants
        )
        self.save_report(
            "logs/_latest/mutation_coverage.json", mutation_coverage_by_test_file
        )
        self.generate_mutant_report(mutants)

    def generate_killed_mutants(self, mutants: List[Mutant]) -> None:
        """
        Generates a report of killed mutants.

        Args:
            mutants (List[Mutant]): List of mutants generated during mutation testing.
        """
        killed_mutants = [
            asdict(mutant) for mutant in mutants if mutant.status == "KILLED"
        ]
        output = {self.config["test_file_path"]: killed_mutants}
        self.save_report("logs/_latest/mutants_killed.json", output)

    def generate_survived_mutants(self, mutants: List[Mutant]) -> None:
        """
        Generates a report of survived mutants.

        Args:
            mutants (List[Mutant]): List of mutants generated during mutation testing.
        """
        survived_mutants = [
            asdict(mutant) for mutant in mutants if mutant.status == "SURVIVED"
        ]

        # add test file as key to group mutants by test file
        output = {self.config["test_file_path"]: survived_mutants}
        self.save_report("logs/_latest/mutants_survived.json", output)

    def generate_mutation_coverage_by_source_file(
        self, mutants: List[Mutant]
    ) -> Dict[str, Any]:
        """
        Calculates the mutation coverage for each source file.

        Args:
            mutants (List[Mutant]): List of mutants generated during mutation testing.

        Returns:
            Dict[str, Any]: Mutation coverage data for each source file.
        """
        mutation_coverage_by_source_file = {}
        for mutant in mutants:
            source_path = mutant.source_path
            if source_path not in mutation_coverage_by_source_file:
                mutation_coverage_by_source_file[source_path] = {
                    "killed": 0,
                    "survived": 0,
                    "total": 0,
                }
            if mutant.status == "KILLED":
                mutation_coverage_by_source_file[source_path]["killed"] += 1
            if mutant.status == "SURVIVED":
                mutation_coverage_by_source_file[source_path]["survived"] += 1
            mutation_coverage_by_source_file[source_path]["total"] += 1

        for source_path, data in mutation_coverage_by_source_file.items():
            killed = data["killed"]
            total = data["total"]
            score = round((killed / total * 100) if total > 0 else 0, 2)
            mutation_coverage_by_source_file[source_path][
                "mutation_score"
            ] = f"{score}%"

        return mutation_coverage_by_source_file

    def generate_mutant_report(self, mutants: List[Mutant]) -> Dict[str, Any]:
        """
        Generates a summary report of the mutation testing.

        Args:
            mutants (List[Mutant]): List of mutants generated during mutation testing.

        Returns:
            Dict[str, Any]: Summary report data.
        """
        killed_mutants_cnt = sum(1 for mutant in mutants if mutant.status == "KILLED")
        survived_mutants_cnt = sum(
            1 for mutant in mutants if mutant.status == "SURVIVED"
        )
        total_mutants = len(mutants)
        score = round(
            (killed_mutants_cnt / total_mutants * 100) if total_mutants > 0 else 0, 2
        )

        report = {
            "Total Mutants": total_mutants,
            "Killed Mutants": killed_mutants_cnt,
            "Survived Mutants": survived_mutants_cnt,
            "Mutation Coverage": f"{score}%",
        }

        logger.info(f"🦠 Total Mutants: {total_mutants} 🦠")
        logger.info(f"🛡️ Survived Mutants: {survived_mutants_cnt} 🛡️")
        logger.info(f"🗡️ Killed Mutants: {killed_mutants_cnt} 🗡️")
        logger.info(f"🎯 Mutation Coverage: {score}% 🎯")

        return report

    def save_report(self, file_path: str, data: Any) -> None:
        """
        Saves the report data to a file.

        Args:
            file_path (str): The path to the file where the report will be saved.
            data (Any): The data to be saved in the report.
        """
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def generate_test_suite_report(self, mutants: List[Mutant]) -> None:
        """
        Generates a report of the test suite.

        Args:
            test_suite_report (Dict[str, Any]): Test suite report data.
        """

        survived_mutants = [
            asdict(mutant) for mutant in mutants if mutant.status == "SURVIVED"
        ]
        with open(self.config["test_file_path"], "r") as f:
            test_suite = f.read()

        system_template = Template(SYSTEM_PROMPT).render()
        user_template = Template(USER_PROMPT).render(
            report=survived_mutants,
            test_suite=test_suite,
        )
        prompt = {
            "system": system_template,
            "user": user_template,
        }
        model_response, _, _ = self.router.generate_response(
            prompt=prompt, streaming=False
        )

        with open("logs/_latest/test_suite_report.md", "w") as f:
            f.write(model_response)


SYSTEM_PROMPT = """
You are a security expert analyzing the codebase to identify critical weaknesses in the test suite based on survived mutants from mutation testing. Focus on identifying weaknesses without generating specific test cases. Be concise and only include confirmed weaknesses.
"""

USER_PROMPT = """
Analyze the following survived mutant report to identify weaknesses in the test suite. Provide a concise list of specific weaknesses for each mutant.
```json
{{report}}
```

Test Suite: 
```
{{test_suite}}
```

Output format:
1. Clear, concise bullet points describing the weaknesses in the test suite and how they can be improved.
2. Potential bugs that may not be caught by the test suite, if any.
"""
