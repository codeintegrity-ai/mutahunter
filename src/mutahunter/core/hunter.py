import os
import time

from tqdm import tqdm

from mutahunter.core.analyzer import Analyzer
from mutahunter.core.entities.mutant import Mutant
from mutahunter.core.logger import logger
from mutahunter.core.mutator import MutantGenerator
from mutahunter.core.report import MutantReport
from mutahunter.core.runner import TestRunner


class MutantHunter:
    def __init__(self, config):
        self.config = config
        self.mutants: list[Mutant] = []
        self.mutant_report = MutantReport()
        self.analyzer = Analyzer(config)
        self.test_runner = TestRunner()

    def run(self):
        """
        Executes the mutation testing process from start to finish.
        """
        try:
            start = time.time()
            logger.info("Starting Coverage Analysis...")
            self.analyzer.dry_run()
            logger.info("🦠 Generating Mutations... 🦠")
            self.run_mutation_testing()
            logger.info("🎯 Generating Mutation Report... 🎯")
            self.mutant_report.generate_report(self.mutants)
            logger.info(f"Mutation Testing Ended. Took {round(time.time() - start)}s")
        except Exception as e:
            logger.error(
                f"Error during mutation testing. Please report this issue. {e}"
            )

    def generate_mutations(self):
        all_covered_files = self.analyzer.file_lines_executed.keys()
        for filename in tqdm(all_covered_files):
            executed_lines = self.analyzer.file_lines_executed[filename]
            if not executed_lines:
                continue
            if self.config["only_mutate_file_paths"]:
                if filename not in self.config["only_mutate_file_paths"]:
                    continue
            if filename in self.config["exclude_files"]:
                continue
            if (
                "test/" in filename
                or "tests/" in filename
                or "test_" in filename
                or "_test" in filename
                or ".test" in filename
            ):
                continue

            covered_function_blocks = self.analyzer.get_covered_function_blocks(
                executed_lines=executed_lines,
                filename=filename,
            )
            if not covered_function_blocks:
                continue

            for function_block in covered_function_blocks:
                start_byte = function_block.start_byte
                end_byte = function_block.end_byte

                with open(filename, "rb") as f:
                    source_code = f.read()
                function_block_source_code = source_code[start_byte:end_byte].decode(
                    "utf-8"
                )
                mutant_generator = MutantGenerator(
                    config=self.config,
                    cov_files=list(all_covered_files),
                    test_file_path=self.config["test_file_path"],
                    filename=filename,
                    function_block_source_code=function_block_source_code,
                    language=self.config["language"],
                )
                mutant_info = mutant_generator.generate()
                yield {
                    "source_path": filename,
                    "start_byte": start_byte,
                    "end_byte": end_byte,
                    "mutant_code_snippet": mutant_info["code_snippet"],
                    "test_file_path": self.config["test_file_path"],
                }

    def run_mutation_testing(self):
        for mutant in self.generate_mutations():
            try:
                # Extract necessary data from the mutant
                source_path = mutant["source_path"]
                start_byte = mutant["start_byte"]
                end_byte = mutant["end_byte"]
                mutant_code = mutant["mutant_code_snippet"]
                test_file_path = mutant["test_file_path"]

                mutant_id = str(len(self.mutants) + 1)
                mutant_path = self.prepare_mutant_file(
                    mutant_id=mutant_id,
                    source_path=source_path,
                    start_byte=start_byte,
                    end_byte=end_byte,
                    mutant_code=mutant_code,
                )
                mutant = Mutant(
                    id=mutant_id,
                    source_path=source_path,
                    mutant_path=mutant_path,
                    test_file_path=test_file_path,
                )
                result = self.run_test(
                    {
                        "module_path": source_path,
                        "replacement_module_path": mutant_path,
                        "test_command": self.config["test_command"],
                    }
                )
                # 0: Mutant survived
                # 1: Mutant was killed
                # 255: Unknown Error occurred
                if result.returncode == 0:
                    logger.info(f"Mutant {mutant_id} survived by {test_file_path}")
                    mutant.status = "SURVIVED"
                    self.mutants.append(mutant)
                elif result.returncode == 1:
                    logger.info(f"Mutant {mutant_id} killed by {test_file_path}")
                    mutant.status = "KILLED"
                    mutant.error_msg = result.stderr + result.stdout
                    self.mutants.append(mutant)
                else:
                    continue
            except Exception as e:
                logger.error(f"Error generating mutant: {e}")
                continue

    def prepare_mutant_file(
        self, mutant_id, source_path, start_byte, end_byte, mutant_code
    ):
        """Prepares the mutant file for testing."""
        mutant_file_name = f"{mutant_id}" + "_" + os.path.basename(source_path)
        mutant_path = os.path.join(
            os.getcwd(), f"logs/_latest/mutants/{mutant_file_name}"
        )

        with open(source_path, "rb") as f:
            source_code = f.read()
        modified_byte_code = (
            source_code[:start_byte]
            + bytes(mutant_code, "utf-8")
            + source_code[end_byte:]
        )
        if self.analyzer.check_syntax(modified_byte_code.decode("utf-8")):
            with open(mutant_path, "wb") as f:
                f.write(modified_byte_code)
            return mutant_path
        else:
            raise Exception("Mutant code has syntax errors.")

    def run_test(self, params: dict[str, str]):
        result = self.test_runner.run_test(params)
        return result
