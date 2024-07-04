"""
This module defines the Mutant class, which represents a mutant in the mutation testing process.
"""

from dataclasses import dataclass
from typing import Union


@dataclass
class Mutant:
    """
    Represents a mutant in the mutation testing process.

    Attributes:
        id (str): The unique identifier of the mutant.
        source_path (str): The path to the original source file.
        mutant_path (str): The path to the file containing the mutant.
        status (Union[None, str]): The status of the mutant (e.g., "SURVIVED", "KILLED").
        error_msg (str): The error message associated with the mutant, if any.
        diff (str): The diff of the mutation applied to the source code.
    """

    id: str
    source_path: str
    mutant_path: str
    status: Union[None, str] = None
    error_msg: str = ""
    diff: str = ""
