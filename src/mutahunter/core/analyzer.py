from importlib import resources
from typing import Any, Dict, List

from grep_ast import filename_to_lang
from tree_sitter_languages import get_language, get_parser

from mutahunter.core.logger import logger


class Analyzer:
    def __init__(self) -> None:
        pass

    def get_language_by_filename(self, filename: str) -> str:
        """
        Gets the language identifier based on the filename.

        Args:
            filename (str): The name of the file.

        Returns:
            str: The language identifier.
        """
        return filename_to_lang(filename)

    def get_covered_function_blocks(
        self, executed_lines: List[int], source_file_path: str
    ) -> List[Any]:
        """
        Retrieves covered function blocks based on executed lines and source_file_path.

        Args:
            executed_lines (List[int]): List of executed line numbers.
            source_file_path (str): The name of the file being analyzed.

        Returns:
            List[Any]: A list of covered function blocks.
        """
        function_blocks = self.get_function_blocks(source_file_path=source_file_path)
        return self._get_covered_blocks(function_blocks, executed_lines)

    def get_covered_method_blocks(
        self, executed_lines: List[int], source_file_path: str
    ) -> List[Any]:
        """
        Retrieves covered method blocks based on executed lines and source_file_path.

        Args:
            executed_lines (List[int]): List of executed line numbers.
            source_file_path (str): The name of the file being analyzed.

        Returns:
            List[Any]: A list of covered method blocks.
        """
        method_blocks = self.get_method_blocks(source_file_path=source_file_path)
        return self._get_covered_blocks(method_blocks, executed_lines)

    def _get_covered_blocks(
        self, blocks: List[Any], executed_lines: List[int]
    ) -> List[Any]:
        """
        Retrieves covered blocks based on executed lines.

        Args:
            blocks (List[Any]): List of blocks (function or method).
            executed_lines (List[int]): List of executed line numbers.

        Returns:
            List[Any]: A list of covered blocks.
        """
        covered_blocks = []
        covered_block_executed_lines = []

        for block in blocks:
            # 0 baseed index
            start_point = block.start_point
            end_point = block.end_point

            start_line = start_point[0] + 1
            end_line = end_point[0] + 1

            if any(line in executed_lines for line in range(start_line, end_line + 1)):
                block_executed_lines = [
                    line - start_line + 1 for line in range(start_line, end_line + 1)
                ]
                covered_blocks.append(block)
                covered_block_executed_lines.append(block_executed_lines)

        return covered_blocks, covered_block_executed_lines

    def get_method_blocks(self, source_file_path: str) -> List[Any]:
        """
        Retrieves method blocks from a given file.

        Args:
            source_file_path (str): The name of the file being analyzed.

        Returns:
            List[Any]: A list of method block nodes.
        """
        source_code = self._read_source_file(source_file_path)
        return self.find_method_blocks_nodes(source_file_path, source_code)

    def get_function_blocks(self, source_file_path: str) -> List[Any]:
        """
        Retrieves function blocks from a given file.

        Args:
            source_file_path (str): The name of the file being analyzed.

        Returns:
            List[Any]: A list of function block nodes.
        """
        source_code = self._read_source_file(source_file_path)
        return self.find_function_blocks_nodes(source_file_path, source_code)

    def _read_source_file(self, file_path: str) -> bytes:
        """
        Reads the source code from a file.

        Args:
            file_path (str): The path to the source file.

        Returns:
            bytes: The source code.
        """
        with open(file_path, "rb") as f:
            return f.read()

    def check_syntax(self, source_file_path: str, source_code: str) -> bool:
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

    def find_method_blocks_nodes(
        self, source_file_path: str, source_code: bytes
    ) -> List[Any]:
        """
        Finds method block nodes in the provided source code.

        Args:
            source_code (bytes): The source code to analyze.

        Returns:
            List[Any]: A list of method block nodes.
        """
        return self._find_blocks_nodes(
            source_file_path, source_code, ["if_statement", "loop", "return"]
        )

    def find_function_blocks_nodes(
        self, source_file_path: str, source_code: bytes
    ) -> List[Any]:
        """
        Finds function block nodes in the provided source code.

        Args:
            source_code (bytes): The source code to analyze.

        Returns:
            List[Any]: A list of function block nodes.
        """
        return self._find_blocks_nodes(
            source_file_path, source_code, ["definition.function", "definition.method"]
        )

    def _find_blocks_nodes(
        self, source_file_path: str, source_code: bytes, tags: List[str]
    ) -> List[Any]:
        """
        Finds block nodes (method or function) in the provided source code.

        Args:
            source_code (bytes): The source code to analyze.
            tags (List[str]): List of tags to identify blocks.

        Returns:
            List[Any]: A list of block nodes.
        """
        lang = filename_to_lang(source_file_path)
        if lang is None:
            raise ValueError(f"Language not supported for file: {source_file_path}")
        parser = get_parser(lang)
        language = get_language(lang)

        tree = parser.parse(source_code)
        query_scm = self._load_query_scm(lang)
        if not query_scm:
            return []

        query = language.query(query_scm)
        captures = query.captures(tree.root_node)

        if not captures:
            logger.error("Tree-sitter query failed to find any captures.")
            return []
        return [node for node, tag in captures if tag in tags]

    def _load_query_scm(self, lang: str) -> str:
        """
        Loads the query SCM file content.

        Args:
            lang (str): The language identifier.

        Returns:
            str: The content of the query SCM file.
        """
        try:
            scm_fname = resources.files(__package__).joinpath(
                "queries", f"tree-sitter-{lang}-tags.scm"
            )
        except KeyError:
            return ""
        if not scm_fname.exists():
            return ""
        return scm_fname.read_text()

    def find_function_block_by_name(
        self, source_file_path: str, method_name: str
    ) -> List[Any]:
        """
        Finds a function block by its name and returns the start and end lines of the function.

        Args:
            source_file_path (str): The path to the source file.
            method_name (str): The name of the method to find.

        Returns:
            Dict[str, int]: A dictionary with 'start_line' and 'end_line' as keys and their corresponding line numbers as values.
        """
        source_code = self._read_source_file(source_file_path)
        lang = filename_to_lang(source_file_path)
        if lang is None:
            raise ValueError(f"Language not supported for file: {source_file_path}")

        parser = get_parser(lang)
        language = get_language(lang)
        tree = parser.parse(source_code)

        query_scm = self._load_query_scm(lang)
        if not query_scm:
            raise ValueError(
                "Failed to load query SCM file for the specified language."
            )

        query = language.query(query_scm)
        captures = query.captures(tree.root_node)

        result = []

        for node, tag in captures:
            if tag == "definition.function" or tag == "definition.method":
                if self._is_function_name(node, method_name, source_code):
                    return node
        raise ValueError(f"Function {method_name} not found in file {source_file_path}")

    def _is_function_name(self, node, method_name: str, source_code: bytes) -> bool:
        """
        Checks if the given node corresponds to the method_name.

        Args:
            node (Node): The AST node to check.
            method_name (str): The method name to find.
            source_code (bytes): The source code.

        Returns:
            bool: True if the node corresponds to the method_name, False otherwise.
        """
        node_text = source_code[node.start_byte : node.end_byte].decode("utf8")
        return method_name in node_text
