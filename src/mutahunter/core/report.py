import json
from dataclasses import asdict

from mutahunter.core.entities.mutant import Mutant
from mutahunter.core.logger import logger


class MutantReport:
    def __init__(self) -> None:
        pass

    def generate_report(self, mutants: list[Mutant]) -> None:
        self.generate_killed_mutants(mutants)
        self.generate_survived_mutants(mutants)
        mutation_coverage_by_test_file = self.generate_mutation_coverage_by_source_file(
            mutants
        )
        with open("logs/_latest/mutation_coverage.json", "w") as f:
            json.dump(mutation_coverage_by_test_file, f, indent=2)
        self.generate_mutant_report(mutants)

    def generate_killed_mutants(self, mutants: list[Mutant]) -> None:
        killed_mutants = [mutant for mutant in mutants if mutant.status == "KILLED"]
        killed_mutants = [asdict(mutant) for mutant in killed_mutants]
        with open("logs/_latest/mutants_killed.json", "w") as f:
            json.dump(killed_mutants, f, indent=2)

    def generate_survived_mutants(self, mutants: list[Mutant]) -> None:
        survived_mutants = [mutant for mutant in mutants if mutant.status == "SURVIVED"]
        survived_mutants = [asdict(mutant) for mutant in survived_mutants]
        with open("logs/_latest/mutants_survived.json", "w") as f:
            json.dump(survived_mutants, f, indent=2)

    def generate_mutation_coverage_by_source_file(self, mutants: list[Mutant]) -> None:
        # NOTE: Based on all the mutants, calcaulte the mutation score for each source file.
        mutation_coverage_by_source_file = {}
        for mutant in mutants:
            source_path = mutant.source_path
            if source_path not in mutation_coverage_by_source_file:
                mutation_coverage_by_source_file[source_path] = {
                    "killed": 0,
                    "total": 0,
                }
            if mutant.status == "KILLED":
                mutation_coverage_by_source_file[source_path]["killed"] += 1
            mutation_coverage_by_source_file[source_path]["total"] += 1

        for source_path, data in mutation_coverage_by_source_file.items():
            killed = data["killed"]
            total = data["total"]
            score = round(killed / total * 100 if total > 0 else 0, 2)
            mutation_coverage_by_source_file[source_path]["mutation_score"] = (
                str(score) + "%"
            )
        return mutation_coverage_by_source_file

    def generate_mutant_report(self, mutants: list[Mutant]) -> None:
        killed_mutants_cnt = sum(1 for mutant in mutants if mutant.status == "KILLED")
        survived_mutants_cnt = sum(
            1 for mutant in mutants if mutant.status == "SURVIVED"
        )
        total_mutants = len(mutants)
        score = round(
            killed_mutants_cnt / total_mutants * 100 if total_mutants > 0 else 0, 2
        )
        report = {
            "Total Mutants": total_mutants,
            "Killed Mutants": killed_mutants_cnt,
            "Survived Mutants": survived_mutants_cnt,
            "Mutation Coverage": str(score) + "%",
        }
        logger.info(f"🦠 Total Mutants: {total_mutants} 🦠")
        logger.info(f"🛡️ Survived Mutants: {survived_mutants_cnt} 🛡️")
        logger.info(f"🗡️ Killed Mutants: {killed_mutants_cnt} 🗡️")
        logger.info(f"🎯 Mutation Coverage: {str(score)}% 🎯")
        return report
