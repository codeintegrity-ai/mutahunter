"""
This module defines the Mutant class, which represents a mutant in the mutation testing process.
"""

from dataclasses import dataclass
from typing import Union


@dataclass
class Mutant:
    id: Union[None, int] = None
    source_path: str = ""
    mutant_path: Union[None, str] = None
    status: Union[None, str] = None
    error_msg: str = ""
    function_name: str = ""
    line_number: Union[None, int] = None
    type: str = ""
    description: str = ""
    original_line: str = ""
    mutated_line: str = ""
    udiff: str = ""
