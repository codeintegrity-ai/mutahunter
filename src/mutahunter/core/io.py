import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

from grep_ast import filename_to_lang
from tree_sitter_languages import get_language, get_parser

TEST_FILE_PATTERNS = [
    "test_",
    "_test",
    ".test",
    ".spec",
    ".tests",
    ".Test",
    "tests/",
    "test/",
]


class FileOperationHandler:
    @staticmethod
    def read_file(file_path: str) -> str:
        with open(file_path, "r") as f:
            return f.read()

    @staticmethod
    def write_file(file_path: str, content: str) -> None:
        with open(file_path, "w") as f:
            f.write(content)

    @staticmethod
    def get_mutant_path(source_file_path: str, mutant_id: str) -> str:
        mutant_file_name = f"{mutant_id}_{os.path.basename(source_file_path)}"
        return os.path.join(os.getcwd(), f"logs/_latest/mutants/{mutant_file_name}")

    @staticmethod
    def prepare_mutant_file(
        mutant_data: Dict[str, Any], source_file_path: str
    ) -> Optional[str]:
        mutant_id = str(uuid4())[:8]
        mutant_path = FileOperationHandler.get_mutant_path(source_file_path, mutant_id)
        source_code = FileOperationHandler.read_file(source_file_path)
        applied_mutant = FileOperationHandler.apply_mutation(source_code, mutant_data)
        if not FileOperationHandler.check_syntax(source_file_path, applied_mutant):
            raise SyntaxError("Mutant syntax is incorrect.")
        FileOperationHandler.write_file(mutant_path, applied_mutant)
        return mutant_path

    @staticmethod
    def should_skip_file(
        filename: str, exclude_files: List[str], only_mutate_file_paths: List[str]
    ) -> bool:
        if only_mutate_file_paths:
            for file_path in only_mutate_file_paths:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File {file_path} does not exist.")
            return all(file_path != filename for file_path in only_mutate_file_paths)
        if filename in exclude_files:
            return True

    @staticmethod
    def check_syntax(source_file_path: str, source_code: str) -> bool:
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

    @staticmethod
    def apply_mutation(source_code: str, mutant_data: Dict[str, Any]) -> str:
        src_code_lines = source_code.splitlines(keepends=True)
        mutated_line = mutant_data["mutated_code"].strip()
        line_number = mutant_data["line_number"]

        indentation = len(src_code_lines[line_number - 1]) - len(
            src_code_lines[line_number - 1].lstrip()
        )
        src_code_lines[line_number - 1] = " " * indentation + mutated_line + "\n"

        return "".join(src_code_lines)
