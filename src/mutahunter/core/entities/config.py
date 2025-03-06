from dataclasses import dataclass
from typing import List


@dataclass
class MutationTestControllerConfig:
    source_path: str
    test_path: str
    model: str
    api_base: str
    test_command: str
    exclude_files: List[str]
