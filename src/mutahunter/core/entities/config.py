from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MutatorConfig:
    model: str
    api_base: str
    test_command: str
    code_coverage_report_path: Optional[str]
    coverage_type: str
    exclude_files: List[str]
    only_mutate_file_paths: List[str]
    modified_files_only: bool
    extreme: bool
