from dataclasses import dataclass
from typing import Union


@dataclass
class Mutant:
    id: str
    source_path: str
    mutant_path: str
    status: Union[None, str] = None
    error_msg: str = ""
    test_file_path: str = ""
    diff: str = ""
