from grep_ast import filename_to_lang
from tree_sitter_languages import get_language, get_parser

from mutahunter.core.logger import logger
from mutahunter.core.utils import FileUtils


def merge_code(
    org_src_code: str,
    code_to_insert: str,
    indent_level: int,
    line_number: int,
) -> None:
    org_src_code_lines = org_src_code.splitlines()
    code_to_insert = reset_indentation(code_to_insert)
    code_to_insert = adjust_indentation(code_to_insert, indent_level)
    if line_number < 0:
        org_src_code_lines.append(code_to_insert)
    else:
        org_src_code_lines.insert(line_number, code_to_insert)
    modified_src_code = "\n".join(org_src_code_lines)
    return modified_src_code


def reset_indentation(code: str) -> str:
    """Reset the indentation of the given code to zero-based indentation."""
    lines = code.splitlines()
    if not lines:
        return code
    min_indent = min(len(line) - len(line.lstrip()) for line in lines if line.strip())
    return "\n".join(line[min_indent:] if line.strip() else line for line in lines)


def adjust_indentation(code: str, indent_level: int) -> str:
    """Adjust the given code to the specified base indentation level."""
    lines = code.splitlines()
    adjusted_lines = [" " * indent_level + line for line in lines]
    return "\n".join(adjusted_lines)
